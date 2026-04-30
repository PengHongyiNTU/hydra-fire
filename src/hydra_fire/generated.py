from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from .compose import compose_config, to_yaml
from .core.overrides import expand_args
from .core.spec import ArgumentField, ConfigGroup, ConfigSpec, ValueType, is_exposed_field
from .docs import render_markdown_docs
from .errors import HydraFireError, RunNotImplementedError
from .render import render_fields, render_groups
from .tui import launch_interactive

CONTEXT_SETTINGS = {"allow_extra_args": True, "ignore_unknown_options": True}
DRY_RUN_OPTION = typer.Option(False, "--dry-run")
DOCS_OUTPUT_OPTION = typer.Option(None, "--output", "-o")
RESERVED_DYNAMIC_NAMES = {
    "all",
    "config",
    "ctx",
    "dry_run",
    "output",
    "preset",
    "self",
}


def build_app(
    spec: ConfigSpec,
    *,
    name: str | None = None,
    base_path: Path | None = None,
) -> typer.Typer:
    generated = typer.Typer(
        name=name or spec.app.name,
        help=spec.app.description or "Hydra Fire generated CLI.",
        no_args_is_help=True,
        add_completion=False,
    )
    generated_console = Console()

    show_param_to_target: dict[str, str]

    @generated.command(context_settings=CONTEXT_SETTINGS)
    def show(ctx: typer.Context, **kwargs: Any) -> None:
        try:
            argv = [*_kwargs_to_argv(kwargs, show_param_to_target), *list(ctx.args)]
            overrides = expand_args(argv, spec)
            cfg = compose_config(
                spec.hydra.config_path,
                spec.hydra.config_name,
                overrides,
                base_path=base_path,
            )
        except Exception as exc:
            generated_console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc
        generated_console.print(to_yaml(cfg))

    show_param_to_target = _install_generated_signature(show, spec)

    run_param_to_target: dict[str, str]

    @generated.command(context_settings=CONTEXT_SETTINGS)
    def run(
        ctx: typer.Context,
        **kwargs: Any,
    ) -> None:
        try:
            dry_run = bool(kwargs.pop("dry_run", False))
            argv = [*_kwargs_to_argv(kwargs, run_param_to_target), *list(ctx.args)]
            overrides = expand_args(argv, spec)
            if dry_run:
                generated_console.print(" ".join(overrides))
                return
            raise RunNotImplementedError(
                "Non-dry-run execution is not implemented yet. Use --dry-run to inspect overrides."
            )
        except HydraFireError as exc:
            generated_console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc

    run_param_to_target = _install_generated_signature(run, spec, include_dry_run=True)

    @generated.command()
    def fields(
        all: bool = typer.Option(False, "--all"),
    ) -> None:
        render_fields(spec, generated_console, include_hidden=all)

    @generated.command()
    def groups(
        all: bool = typer.Option(False, "--all"),
    ) -> None:
        render_groups(spec, generated_console, include_hidden=all)

    @generated.command()
    def docs(
        output: Path | None = DOCS_OUTPUT_OPTION,
    ) -> None:
        _emit_markdown(render_markdown_docs(spec), generated_console, output)

    @generated.command()
    def launch() -> None:
        overrides = launch_interactive(spec, console=generated_console, base_path=base_path)
        if overrides is None:
            raise typer.Exit(1)
        generated_console.print(" ".join(overrides))

    return generated


def _emit_markdown(markdown: str, console_obj: Console, output: Path | None) -> None:
    if output is None:
        console_obj.file.write(markdown)
        return
    output.write_text(markdown)
    console_obj.print(f"Wrote {output}")


def _install_generated_signature(
    func: Callable[..., Any],
    spec: ConfigSpec,
    *,
    include_dry_run: bool = False,
) -> dict[str, str]:
    params = [
        inspect.Parameter(
            "ctx",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=typer.Context,
        )
    ]
    param_to_target: dict[str, str] = {}
    used_params = {"ctx"}
    used_options: set[str] = set()

    for name, group in _visible_groups(spec):
        param_name = _safe_param_name(name, used_params)
        option_names = _option_names([name, *group.cli_names], used_options)
        if not option_names:
            continue
        params.append(
            inspect.Parameter(
                param_name,
                inspect.Parameter.KEYWORD_ONLY,
                default=typer.Option(
                    None,
                    *option_names,
                    help=group.help or f"Select {group.name} config group.",
                ),
                annotation=str | None,
            )
        )
        param_to_target[param_name] = name

    for name, field in _visible_fields(spec):
        param_name = _safe_param_name(name, used_params)
        option_names = _option_names([name, *field.cli_names], used_options)
        if not option_names:
            continue
        params.append(
            inspect.Parameter(
                param_name,
                inspect.Parameter.KEYWORD_ONLY,
                default=typer.Option(
                    None,
                    *option_names,
                    help=field.help,
                ),
                annotation=_python_type(field.type) | None,
            )
        )
        param_to_target[param_name] = name

    if include_dry_run:
        params.append(
            inspect.Parameter(
                "dry_run",
                inspect.Parameter.KEYWORD_ONLY,
                default=DRY_RUN_OPTION,
                annotation=bool,
            )
        )

    func.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    return param_to_target


def _visible_groups(spec: ConfigSpec) -> Iterable[tuple[str, ConfigGroup]]:
    for name, group in spec.groups.items():
        if group.visible:
            yield name, group


def _visible_fields(spec: ConfigSpec) -> Iterable[tuple[str, ArgumentField]]:
    for name, field in spec.fields.items():
        if is_exposed_field(field):
            yield name, field


def _safe_param_name(name: str, used: set[str]) -> str:
    base = re.sub(r"\W+", "_", name).strip("_") or "value"
    if base[0].isdigit():
        base = f"value_{base}"
    if base in RESERVED_DYNAMIC_NAMES:
        base = f"{base}_value"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}_{index}"
        index += 1
    used.add(candidate)
    return candidate


def _option_names(names: Iterable[str], used: set[str]) -> list[str]:
    options: list[str] = []
    for name in names:
        option = f"--{name}"
        if option in used:
            continue
        options.append(option)
        used.add(option)
    return options


def _python_type(value_type: ValueType) -> type[Any]:
    if value_type == "int":
        return int
    if value_type == "float":
        return float
    if value_type == "bool":
        return bool
    if value_type == "path":
        return Path
    return str


def _kwargs_to_argv(kwargs: dict[str, Any], param_to_target: dict[str, str]) -> list[str]:
    argv: list[str] = []
    for param_name, target_name in param_to_target.items():
        value = kwargs.get(param_name)
        if value is None:
            continue
        if isinstance(value, bool):
            argv.append(f"--{target_name}={str(value).lower()}")
        else:
            argv.extend([f"--{target_name}", str(value)])
    return argv
