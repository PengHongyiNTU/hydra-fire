from __future__ import annotations

import inspect
import sys
from collections.abc import Callable
from difflib import get_close_matches
from functools import wraps
from pathlib import Path
from typing import Any

from omegaconf import DictConfig, OmegaConf
from rich.console import Console

from .compose import compose_config, to_yaml
from .core.config import ensure_cli_config
from .core.errors import AmbiguousSweepValueError, HydraFireError
from .core.overrides import expand_args, target_map
from .render import (
    render_decorator_help,
    render_explain,
    render_fields,
    render_groups,
    render_preset_list,
    render_suggest,
)
from .sources import build_config_spec
from .tui import launch_interactive
from .validate import validate_config


def hydra_fire(
    *,
    config_path: str,
    config_name: str = "config",
    cli_config: str = "cli.config.yaml",
    schema: type[Any] | None = None,
    auto_init: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(argv: list[str] | None = None) -> Any:
            config_path_obj = Path(cli_config)
            spec = _load_spec(
                config_path=config_path,
                config_name=config_name,
                cli_config=config_path_obj,
                target=func,
                schema=schema,
                auto_init=auto_init,
            )
            raw_args = list(sys.argv[1:] if argv is None else argv)
            if _is_help(raw_args):
                render_decorator_help(spec, Console(), prog_name=_script_prog_name())
                raise SystemExit(0)
            raw_args, multirun = _pop_multirun_flag(raw_args)
            if raw_args == ["launch"]:
                launcher_overrides = launch_interactive(
                    spec,
                    console=Console(),
                    base_path=config_path_obj.parent,
                )
                if launcher_overrides is None:
                    raise SystemExit(1)
                raw_args = launcher_overrides

            command_result = _run_command(
                raw_args,
                spec=spec,
                config_path=config_path,
                config_name=config_name,
                base_path=config_path_obj.parent,
            )
            if command_result.handled:
                raise SystemExit(0)
            _fail_on_command_typo(raw_args)

            try:
                smart_multirun = multirun or _has_friendly_comma_sweep(raw_args, spec)
                overrides = expand_args(raw_args, spec, sweep=smart_multirun)
                if smart_multirun:
                    Console().print(" ".join(["-m", *overrides]))
                    raise SystemExit(0)
                _raise_on_ambiguous_comma_values(overrides, spec)
                cfg = compose_config(
                    config_path,
                    config_name,
                    overrides,
                    base_path=config_path_obj.parent,
                )
            except Exception as exc:
                _print_expected_error(exc)
                raise SystemExit(1) from exc
            if schema is not None:
                cfg = validate_config(cfg, schema)
            return _invoke(func, cfg)

        return wrapper

    return decorator


class CommandResult:
    def __init__(self, *, handled: bool) -> None:
        self.handled = handled


def _run_command(
    raw_args: list[str],
    *,
    spec: Any,
    config_path: str,
    config_name: str,
    base_path: Path,
) -> CommandResult:
    if not raw_args:
        return CommandResult(handled=False)

    console = Console()
    command, *args = raw_args
    if command == "fields":
        _require_no_command_args(command, args)
        render_fields(spec, console, include_hidden=True)
        return CommandResult(handled=True)
    if command == "groups":
        _require_no_command_args(command, args)
        render_groups(spec, console, include_hidden=True)
        return CommandResult(handled=True)
    if command == "recipes":
        _require_no_command_args(command, args)
        render_preset_list(spec, console)
        return CommandResult(handled=True)
    if command == "explain":
        if not args:
            console.print("[red]explain requires a target (preset name or group=choice)[/red]")
            return CommandResult(handled=True)
        render_explain(
            spec,
            args[0],
            console,
            config_path=config_path,
            config_name=config_name,
            base_path=str(base_path),
        )
        return CommandResult(handled=True)
    if command == "suggest":
        if not args:
            console.print("[red]suggest requires a name to search[/red]")
            return CommandResult(handled=True)
        render_suggest(spec, args[0], console)
        return CommandResult(handled=True)
    if command == "show":
        overrides = expand_args(args, spec)
        cfg = compose_config(
            config_path,
            config_name,
            overrides,
            base_path=base_path,
        )
        console.print(to_yaml(cfg))
        return CommandResult(handled=True)
    if command == "sweep":
        overrides = expand_args(args, spec, sweep=True)
        console.print(" ".join(["-m", *overrides]))
        return CommandResult(handled=True)
    return CommandResult(handled=False)


def _require_no_command_args(command: str, args: list[str]) -> None:
    if args:
        raise ValueError(f"Command '{command}' does not accept extra arguments.")


def _fail_on_command_typo(raw_args: list[str]) -> None:
    if len(raw_args) != 1:
        return
    token = raw_args[0]
    if _looks_like_argument_or_override(token):
        return
    suggestions = get_close_matches(token, sorted(_COMMANDS), n=1)
    if not suggestions:
        return
    console = Console()
    console.print(f"[red]Unknown command:[/red] {token}")
    console.print(f"Did you mean `{suggestions[0]}`?")
    raise SystemExit(1)


def _looks_like_argument_or_override(token: str) -> bool:
    return token.startswith("-") or "=" in token or "." in token or token.startswith(("+", "~"))


def _print_expected_error(exc: Exception) -> None:
    console = Console()
    if isinstance(exc, HydraFireError):
        console.print(f"[red]{exc}[/red]")
        return
    console.print(f"[red]{exc.__class__.__name__}:[/red] {exc}")


_COMMANDS = {"fields", "groups", "show", "sweep", "launch", "help", "recipes", "explain", "suggest"}
_MULTIRUN_FLAGS = {"--multirun", "-m"}


def _pop_multirun_flag(raw_args: list[str]) -> tuple[list[str], bool]:
    args: list[str] = []
    multirun = False
    for arg in raw_args:
        if arg in _MULTIRUN_FLAGS:
            multirun = True
            continue
        args.append(arg)
    return args, multirun


def _has_friendly_comma_sweep(raw_args: list[str], spec: Any) -> bool:
    targets = target_map(spec)
    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if not arg.startswith("--") or len(arg) <= 2:
            i += 1
            continue

        name_value = arg[2:]
        if "=" in name_value:
            name, value = name_value.split("=", 1)
        else:
            name = name_value
            target = targets.get(name)
            if target is not None and target.type == "bool":
                i += 1
                continue
            if i + 1 >= len(raw_args):
                return False
            value = raw_args[i + 1]
            i += 1

        target = targets.get(name)
        if target is not None and target.sweepable and _is_ambiguous_comma_value(value):
            return True
        i += 1
    return False


def _raise_on_ambiguous_comma_values(overrides: list[str], spec: Any) -> None:
    fields_by_path = {field.path: field for field in spec.fields.values()}
    for override in overrides:
        key, separator, value = override.partition("=")
        field = fields_by_path.get(key)
        if field is not None and not field.sweepable:
            continue
        if separator and _is_ambiguous_comma_value(value):
            raise AmbiguousSweepValueError(
                "Comma values look like Hydra multirun syntax, but decorated "
                "entrypoints compose one config at a time.\n\n"
                f"Problem override: {key}={value}\n\n"
                "Use `sweep`, `--multirun`, or `-m` to preview the Hydra multirun "
                "override list. "
                "If the target field is a list, use Hydra list syntax such as "
                "`key=[1,2,3]`."
            )


def _is_ambiguous_comma_value(value: str) -> bool:
    stripped = value.strip()
    if "," not in stripped:
        return False
    return not stripped.startswith(("[", "{", "'", '"'))


def _load_spec(
    *,
    config_path: str,
    config_name: str,
    cli_config: Path,
    target: Callable[..., Any],
    schema: type[Any] | None,
    auto_init: bool,
) -> Any:
    derived_spec = build_config_spec(
        config_path=config_path,
        config_name=config_name,
        target=target,
        schema=schema,
    )
    if not auto_init:
        return derived_spec
    return ensure_cli_config(
        derived_spec,
        cli_config,
        overwrite=False,
    )


def _is_help(raw_args: list[str]) -> bool:
    return tuple(raw_args) in {("--help",), ("-h",), ("help",)}


def _script_prog_name() -> str:
    script = Path(sys.argv[0]).name
    executable = Path(sys.executable).name
    if script and script not in {"pytest", "py.test"}:
        return f"{executable} {script}"
    return script or executable


def _invoke(func: Callable[..., Any], cfg: Any) -> Any:
    signature = inspect.signature(func)
    parameters = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    ]
    if len(parameters) == 1 and parameters[0].name in {"cfg", "config"}:
        return func(cfg)
    if not isinstance(cfg, DictConfig):
        return func(cfg)

    missing = object()
    kwargs: dict[str, Any] = {}
    for parameter in parameters:
        value = _select_value(cfg, parameter.name, default=missing)
        if value is missing:
            if parameter.default is inspect.Parameter.empty:
                raise TypeError(f"Missing required config value: {parameter.name}")
            value = parameter.default
        kwargs[parameter.name] = value
    return func(**kwargs)


def _select_value(cfg: DictConfig, parameter_name: str, *, default: Any) -> Any:
    value = OmegaConf.select(cfg, parameter_name, default=default)
    if value is not default:
        return value
    if "__" in parameter_name:
        return OmegaConf.select(cfg, parameter_name.replace("__", "."), default=default)
    return default
