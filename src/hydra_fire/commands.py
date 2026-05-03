from __future__ import annotations

import importlib
from difflib import get_close_matches
from pathlib import Path
from pydoc import locate
from typing import Any, NoReturn

import click
import typer
from rich.console import Console

from .compose import compose_config, to_yaml
from .core.config import load_cli_config, save_cli_config
from .core.overrides import expand_args, preset_overrides, target_map
from .docs import render_markdown_docs
from .errors import HydraFireError, RunNotImplementedError
from .generated import CONTEXT_SETTINGS
from .render import (
    render_explain,
    render_fields,
    render_groups,
    render_preset_description,
    render_preset_list,
    render_suggest,
)
from .sources import build_config_spec
from .tui import launch_interactive


class HydraFireGroup(typer.core.TyperGroup):
    def resolve_command(
        self,
        ctx: click.Context,
        args: list[str],
    ) -> tuple[str | None, click.Command | None, list[str]]:
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError as exc:
            if args:
                suggestions = get_close_matches(args[0], self.list_commands(ctx), n=1)
                if suggestions:
                    raise click.ClickException(
                        f"Unknown command: {args[0]}\nDid you mean `{suggestions[0]}`?"
                    ) from exc
            raise


app = typer.Typer(
    name="hydra-fire",
    cls=HydraFireGroup,
    help="Schema-aware CLI ergonomics for Hydra-backed Python apps.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
CONFIG_OPTION = typer.Option(Path("cli.config.yaml"), "--config", "-c")
DRY_RUN_OPTION = typer.Option(False, "--dry-run")
CONFIG_PATH_OPTION = typer.Option(Path("configs"), "--config-path")
CONFIG_NAME_OPTION = typer.Option("config", "--config-name")
INIT_OUTPUT_OPTION = typer.Option(Path("cli.config.yaml"), "--output", "-o")
INIT_OVERWRITE_OPTION = typer.Option(False, "--overwrite")
DOCS_OUTPUT_OPTION = typer.Option(None, "--output", "-o")


def _fail(exc: Exception) -> NoReturn:
    console.print(f"[red]{exc}[/red]")
    raise typer.Exit(1) from exc


def _spec(config_path: Path):
    try:
        return load_cli_config(config_path, base_path=config_path.parent)
    except HydraFireError as exc:
        _fail(exc)


def _target(value: str | None):
    if value is None:
        return None
    if ":" in value:
        module_name, object_name = value.split(":", 1)
        try:
            module = importlib.import_module(module_name)
            obj: Any = module
            for part in object_name.split("."):
                obj = getattr(obj, part)
        except (ImportError, AttributeError) as exc:
            raise typer.BadParameter(f"Could not import callable target: {value}") from exc
        if not callable(obj):
            raise typer.BadParameter(f"Target is not callable: {value}")
        return obj
    obj = locate(value)
    if obj is None or not callable(obj):
        raise typer.BadParameter(f"Could not import callable target: {value}")
    return obj


def _emit_markdown(markdown: str, console_obj: Console, output: Path | None) -> None:
    if output is None:
        console_obj.file.write(markdown)
        return
    output.write_text(markdown)
    console_obj.print(f"Wrote {output}")


@app.command()
def init(
    config_path: Path = CONFIG_PATH_OPTION,
    config_name: str = CONFIG_NAME_OPTION,
    target: str | None = typer.Option(None, "--target"),
    output: Path = INIT_OUTPUT_OPTION,
    overwrite: bool = INIT_OVERWRITE_OPTION,
) -> None:
    if output.exists() and not overwrite:
        console.print(f"[red]CLI config already exists: {output}[/red]")
        raise typer.Exit(1)
    try:
        spec = build_config_spec(
            config_path=config_path,
            config_name=config_name,
            target=_target(target),
        )
        save_cli_config(spec, output)
    except Exception as exc:
        _fail(exc)
    console.print(f"Wrote {output}")


@app.command("list")
def list_presets(
    config: Path = CONFIG_OPTION,
) -> None:
    spec = _spec(config)
    render_preset_list(spec, console)


@app.command()
def recipes(
    config: Path = CONFIG_OPTION,
) -> None:
    """List available recipes (presets) with descriptions."""
    spec = _spec(config)
    render_preset_list(spec, console)


@app.command()
def fields(
    config: Path = CONFIG_OPTION,
    all: bool = typer.Option(False, "--all"),
    level: str | None = typer.Option(
        None, "--level", help="Filter by level (core/common/advanced/debug)"
    ),
    search: str | None = typer.Option(
        None, "--search", help="Filter by substring in name/path/help"
    ),
) -> None:
    spec = _spec(config)
    render_fields(spec, console, include_hidden=all, level=level, search=search)


@app.command()
def groups(
    config: Path = CONFIG_OPTION,
    all: bool = typer.Option(False, "--all"),
) -> None:
    spec = _spec(config)
    render_groups(spec, console, include_hidden=all)


@app.command()
def docs(
    config: Path = CONFIG_OPTION,
    output: Path | None = DOCS_OUTPUT_OPTION,
) -> None:
    spec = _spec(config)
    _emit_markdown(render_markdown_docs(spec), console, output)


@app.command()
def launch(
    config: Path = CONFIG_OPTION,
) -> None:
    spec = _spec(config)
    overrides = launch_interactive(spec, console=console, base_path=config.parent)
    if overrides is None:
        raise typer.Exit(1)
    console.print(" ".join(overrides))


@app.command()
def describe(
    preset: str,
    config: Path = CONFIG_OPTION,
) -> None:
    spec = _spec(config)
    try:
        render_preset_description(spec, preset, console)
    except HydraFireError as exc:
        _fail(exc)


@app.command()
def explain(
    target: str,
    config: Path = CONFIG_OPTION,
) -> None:
    """Explain a recipe (preset name) or a group choice (group=choice)."""
    spec = _spec(config)
    try:
        render_explain(
            spec,
            target,
            console,
            config_path=spec.hydra.config_path,
            config_name=spec.hydra.config_name,
            base_path=str(config.parent),
        )
    except HydraFireError as exc:
        _fail(exc)


@app.command()
def suggest(
    name: str,
    config: Path = CONFIG_OPTION,
) -> None:
    """Suggest close matches for a partial flag or field name."""
    spec = _spec(config)
    render_suggest(spec, name, console)


@app.command()
def completion(
    shell: str = typer.Argument("bash", help="Shell type: bash, zsh, or fish"),
) -> None:
    """Generate shell completion script for hydra-fire."""
    import os

    os.environ["_HYDRA_FIRE_COMPLETE"] = f"{shell}_source"
    try:
        app(standalone_mode=False)
    except SystemExit:
        pass
    except Exception:
        console.print(
            f"[yellow]Shell completion generation for '{shell}' requires "
            "the shell to be supported by click/typer.[/yellow]"
        )


@app.command(context_settings=CONTEXT_SETTINGS)
def show(
    ctx: typer.Context,
    preset: str | None = typer.Argument(None),
    config: Path = CONFIG_OPTION,
) -> None:
    spec = _spec(config)
    try:
        overrides = _overrides_from_optional_preset(spec, preset, list(ctx.args))
        cfg = compose_config(
            spec.hydra.config_path,
            spec.hydra.config_name,
            overrides,
            base_path=config.parent,
        )
    except Exception as exc:
        _fail(exc)
    console.print(to_yaml(cfg))


@app.command(context_settings=CONTEXT_SETTINGS)
def run(
    ctx: typer.Context,
    preset: str | None = typer.Argument(None),
    config: Path = CONFIG_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    spec = _spec(config)
    try:
        args = list(ctx.args)
        sweep_args = args if preset is None or preset in spec.presets else [preset, *args]
        sweep_mode = _contains_sweep_value(sweep_args, spec)
        overrides = _overrides_from_optional_preset(spec, preset, args, sweep=sweep_mode)
        if dry_run:
            prefix = ["-m"] if sweep_mode else []
            console.print(" ".join([*prefix, *overrides]))
            return
        raise RunNotImplementedError(
            "Non-dry-run execution is not implemented yet. Use --dry-run to inspect overrides."
        )
    except HydraFireError as exc:
        _fail(exc)


@app.command(context_settings=CONTEXT_SETTINGS)
def sweep(
    ctx: typer.Context,
    preset: str | None = typer.Argument(None),
    config: Path = CONFIG_OPTION,
) -> None:
    """Translate friendly options and Hydra overrides into Hydra multirun syntax."""
    spec = _spec(config)
    try:
        overrides = _overrides_from_optional_preset(spec, preset, list(ctx.args), sweep=True)
    except HydraFireError as exc:
        _fail(exc)
    console.print(" ".join(["-m", *overrides]))


def _overrides_from_optional_preset(
    spec: Any,
    preset: str | None,
    args: list[str],
    *,
    sweep: bool = False,
) -> list[str]:
    if preset is None:
        return expand_args(args, spec, sweep=sweep)
    if preset in spec.presets:
        return preset_overrides(spec, preset, args, sweep=sweep)
    return expand_args([preset, *args], spec, sweep=sweep)


def _contains_sweep_value(args: list[str], spec: Any) -> bool:
    targets = target_map(spec)
    fields_by_path = {field.path: field for field in spec.fields.values()}
    previous_was_option = False
    previous_option = ""
    for arg in args:
        if previous_was_option:
            target = targets.get(previous_option)
            if target is not None and target.sweepable and _is_comma_sweep_value(arg):
                return True
            previous_was_option = False
            previous_option = ""
            continue
        if arg.startswith("--") and len(arg) > 2:
            if "=" in arg:
                name, value = arg[2:].split("=", 1)
                target = targets.get(name)
                if target is not None and target.sweepable and _is_comma_sweep_value(value):
                    return True
            else:
                previous_was_option = True
                previous_option = arg[2:]
            continue
        if "=" in arg:
            key, value = arg.split("=", 1)
            field = fields_by_path.get(key)
            if field is not None and not field.sweepable:
                continue
            if _is_comma_sweep_value(value):
                return True
    return False


def _is_comma_sweep_value(value: str) -> bool:
    stripped = value.strip()
    if "," not in stripped:
        return False
    return not stripped.startswith(("[", "{", "'", '"'))
