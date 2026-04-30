from __future__ import annotations

import shlex
from collections.abc import Iterable
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from hydra_fire.compose import compose_config, to_yaml
from hydra_fire.core.overrides import preset_overrides, target_map
from hydra_fire.core.spec import ArgumentField, ConfigGroup, ConfigSpec

HELP_TEXT = """[bold cyan]Type normal CLI arguments, then press Enter.[/bold cyan]

[dim]Examples[/dim]
  [green]--batch-size 64 --lr 0.01[/green]
  [green]--model large trainer.precision=bf16[/green]
  [green]--preset quick --steps 100[/green]

[magenta]Tab[/magenta] completes generated options and known choices. [magenta]Arrow keys[/magenta]
select completion items. Raw Hydra overrides still work.
"""

PROMPT_STYLE = Style.from_dict(
    {
        "prompt": "ansicyan bold",
        "chevron": "ansimagenta bold",
    }
)


class LauncherCompleter(Completer):
    def __init__(self, spec: ConfigSpec) -> None:
        self.spec = spec

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        del complete_event
        text = document.text_before_cursor
        current = document.get_word_before_cursor(WORD=True)
        previous = _previous_token(text)

        if previous == "--preset":
            yield from _matches(self.spec.presets, current)
            return

        if previous and previous.startswith("--"):
            yield from _matches(_choices_for_option(self.spec, previous[2:]), current)
            return

        if "=" in current:
            yield from _key_value_completions(self.spec, current)
            return

        if current.startswith("--"):
            yield from _option_completions(self.spec, current)
            return

        if _is_hydra_prefix(current):
            yield from _raw_override_completions(self.spec, current, include_simple=True)
            return

        yield from _raw_override_completions(self.spec, current, include_simple=False)


def launch_interactive(
    spec: ConfigSpec,
    *,
    console: Console | None = None,
    base_path: str | Path | None = None,
) -> list[str] | None:
    active_console = console or Console()
    session: PromptSession[str] = PromptSession(
        completer=LauncherCompleter(spec),
        style=PROMPT_STYLE,
        complete_while_typing=True,
    )
    active_console.print(Rule("[bold cyan]Hydra Fire Launcher[/bold cyan]"))
    active_console.print(
        Panel(
            HELP_TEXT,
            title=f"[bold]{spec.app.name}[/bold]",
            border_style="cyan",
            expand=False,
        )
    )

    while True:
        try:
            line = session.prompt(_prompt(spec.app.name)).strip()
        except (EOFError, KeyboardInterrupt):
            return None

        if not line:
            return None

        try:
            overrides = parse_launch_args(line, spec)
            _preview(overrides, spec, active_console, base_path=base_path)
        except Exception as exc:
            active_console.print(f"[red]{exc}[/red]")
            continue

        if _confirm(session):
            return overrides


def parse_launch_args(line: str, spec: ConfigSpec) -> list[str]:
    args = shlex.split(line)
    preset, remaining = _extract_preset(args)
    _reject_friendly_key_value_aliases(remaining, spec, preset=preset)
    if preset is None:
        from hydra_fire.core.overrides import expand_args

        return expand_args(remaining, spec)
    return preset_overrides(spec, preset, remaining)


def _extract_preset(args: list[str]) -> tuple[str | None, list[str]]:
    remaining: list[str] = []
    preset: str | None = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--preset":
            if index + 1 >= len(args):
                raise ValueError("--preset requires a value.")
            preset = args[index + 1]
            index += 2
            continue
        if arg.startswith("--preset="):
            preset = arg.split("=", 1)[1]
            index += 1
            continue
        if arg.startswith("preset="):
            preset = arg.split("=", 1)[1]
            index += 1
            continue
        remaining.append(arg)
        index += 1
    return preset, remaining


def _reject_friendly_key_value_aliases(
    args: list[str],
    spec: ConfigSpec,
    *,
    preset: str | None,
) -> None:
    targets = target_map(spec, preset, include_advanced=True)
    for index, arg in enumerate(args):
        key = _key_value_key(arg)
        if key is None and index + 1 < len(args) and args[index + 1] == "=":
            key = arg
        if key is None:
            continue
        plain_key = key.removeprefix("++").removeprefix("+")
        target = targets.get(plain_key)
        if target is None:
            continue
        if target.field is not None and plain_key != target.field.path:
            raise ValueError(
                f"'{plain_key}=...' is not supported in launcher input. "
                f"Use '--{plain_key} VALUE' or raw Hydra path '{target.field.path}=...'."
            )
        if target.group is not None and plain_key != target.group.name:
            raise ValueError(
                f"'{plain_key}=...' is not supported in launcher input. "
                f"Use '--{plain_key} VALUE' or raw Hydra group '{target.group.name}=...'."
            )


def _key_value_key(arg: str) -> str | None:
    if "=" not in arg:
        return None
    key, _value = arg.split("=", 1)
    if key.startswith("--"):
        return None
    return key


def _preview(
    overrides: list[str],
    spec: ConfigSpec,
    console: Console,
    *,
    base_path: str | Path | None,
) -> None:
    console.print(
        Panel(
            Text(" ".join(overrides), style="bold green"),
            title="[bold green]Hydra overrides[/bold green]",
            border_style="green",
            expand=False,
        )
    )
    cfg = compose_config(
        spec.hydra.config_path,
        spec.hydra.config_name,
        overrides,
        base_path=base_path,
    )
    console.print(
        Panel(
            to_yaml(cfg),
            title="[bold cyan]Composed config[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )


def _confirm(session: PromptSession[str]) -> bool:
    try:
        answer = (
            session.prompt(HTML("<ansigreen>Use these overrides?</ansigreen> [y/N] "))
            .strip()
            .lower()
        )
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in {"y", "yes"}


def _option_names(spec: ConfigSpec) -> list[str]:
    options = ["--preset"] if spec.presets else []
    options.extend(f"--{name}" for name in target_map(spec))
    return sorted(set(options))


def _raw_key_names(spec: ConfigSpec) -> list[str]:
    keys = ["preset="] if spec.presets else []
    keys.extend(f"{field.path}=" for field in spec.fields.values() if field.visible)
    keys.extend(f"{group.name}=" for group in spec.groups.values() if group.visible)
    return sorted(set(keys))


def _raw_field_names(spec: ConfigSpec, *, include_simple: bool) -> list[str]:
    names: list[str] = []
    for field in spec.fields.values():
        if not field.visible:
            continue
        if not include_simple and "." not in field.path:
            continue
        names.append(f"{field.path}=")
    return sorted(set(names))


def _choices_for_option(spec: ConfigSpec, option_name: str) -> list[str]:
    if option_name == "preset":
        return sorted(spec.presets)
    target = target_map(spec).get(option_name)
    if target is None:
        return []
    if target.group is not None:
        return target.group.choices
    if target.field is not None and target.field.choices:
        return target.field.choices
    return []


def _key_value_completions(spec: ConfigSpec, current: str):
    key, value = current.split("=", 1)
    if key == "preset":
        for match in _matching_values(spec.presets, value):
            yield Completion(f"preset={match}", start_position=-len(current))
        return

    prefix, raw_key = _split_hydra_prefix(key)
    choices = _choices_for_raw_key(spec, raw_key) or _choices_for_option(spec, key)
    if choices:
        for match in _matching_values(choices, value):
            yield Completion(f"{prefix}{raw_key}={match}", start_position=-len(current))
        return

    for name in _raw_key_names(spec):
        candidate = f"{prefix}{name}"
        if name.startswith(current):
            yield Completion(candidate, start_position=-len(current))


def _option_completions(spec: ConfigSpec, current: str):
    metadata = _option_metadata(spec)
    for option in _matching_values(_option_names(spec), current):
        yield Completion(
            option,
            start_position=-len(current),
            display_meta=metadata.get(option.removeprefix("--"), ""),
        )


def _raw_override_completions(spec: ConfigSpec, current: str, *, include_simple: bool):
    prefix, raw_current = _split_hydra_prefix(current)
    metadata = _raw_metadata(spec)
    for raw_name in _raw_field_names(spec, include_simple=include_simple):
        raw_key = raw_name.removesuffix("=")
        if raw_name.startswith(raw_current) or raw_key.startswith(raw_current):
            yield Completion(
                f"{prefix}{raw_name}",
                start_position=-len(current),
                display_meta=metadata.get(raw_key, "Hydra override"),
            )


def _option_metadata(spec: ConfigSpec) -> dict[str, str]:
    metadata = {"preset": "preset"}
    for name, target in target_map(spec).items():
        if target.field is not None:
            metadata[name] = _field_meta(target.field)
        elif target.group is not None:
            metadata[name] = _group_meta(target.group)
    return metadata


def _raw_metadata(spec: ConfigSpec) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for field in spec.fields.values():
        if field.visible:
            metadata[field.path] = _field_meta(field)
    for group in spec.groups.values():
        if group.visible:
            metadata[group.name] = _group_meta(group)
    return metadata


def _choices_for_raw_key(spec: ConfigSpec, raw_key: str) -> list[str]:
    if raw_key == "preset":
        return sorted(spec.presets)
    for field in spec.fields.values():
        if field.visible and field.path == raw_key and field.choices:
            return field.choices
    group = spec.groups.get(raw_key)
    if group is not None and group.visible:
        return group.choices
    return []


def _field_meta(field: ArgumentField) -> str:
    parts = [field.path, field.type, field.level]
    if field.default is not None:
        parts.append(f"default={field.default}")
    return " | ".join(parts)


def _group_meta(group: ConfigGroup) -> str:
    parts = [group.name, "group"]
    if group.default:
        parts.append(f"default={group.default}")
    return " | ".join(parts)


def _is_hydra_prefix(current: str) -> bool:
    return current.startswith(("+", "++", "~")) or "." in current


def _split_hydra_prefix(value: str) -> tuple[str, str]:
    if value.startswith("++"):
        return "++", value[2:]
    if value.startswith("+"):
        return "+", value[1:]
    if value.startswith("~"):
        return "~", value[1:]
    return "", value


def _previous_token(text: str) -> str | None:
    if not text.endswith(" "):
        text = text[: -len(text.split()[-1])] if text.split() else ""
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()
    if not tokens:
        return None
    return tokens[-1]


def _matches(values: Iterable[str], current: str):
    for value in _matching_values(values, current):
        yield Completion(value, start_position=-len(current))


def _matching_values(values: Iterable[str], current: str) -> Iterable[str]:
    for value in values:
        if value.startswith(current):
            yield value


def _prompt(app_name: str) -> HTML:
    return HTML(f"<prompt>{app_name}</prompt> <chevron>›</chevron> ")
