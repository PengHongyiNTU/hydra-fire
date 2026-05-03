from __future__ import annotations

from dataclasses import dataclass

from .errors import (
    InvalidChoiceError,
    MissingArgumentValueError,
    NonSweepableFieldError,
    UnknownArgumentError,
)
from .spec import ArgumentField, ConfigGroup, ConfigSpec, is_exposed_field


@dataclass(frozen=True)
class OverrideTarget:
    path: str
    field: ArgumentField | None = None
    group: ConfigGroup | None = None

    @property
    def sweepable(self) -> bool:
        if self.field is None:
            return True
        return self.field.sweepable

    @property
    def type(self) -> str:
        if self.field is None:
            return "str"
        return self.field.type


def target_map(
    spec: ConfigSpec,
    preset: str | None = None,
    *,
    include_advanced: bool = False,
) -> dict[str, OverrideTarget]:
    targets: dict[str, OverrideTarget] = {}

    for name, field in spec.fields.items():
        if not include_advanced and not is_exposed_field(field):
            continue
        target = OverrideTarget(field.path, field=field)
        if _is_field_cli_name(name):
            targets[name] = target
        for cli_name in field.cli_names:
            targets[cli_name] = target

    for name, group in spec.groups.items():
        if not group.visible:
            continue
        target = OverrideTarget(group.hydra_group, group=group)
        targets[name] = target
        for cli_name in group.cli_names:
            targets[cli_name] = target

    if preset is not None and preset in spec.presets:
        for name, path in spec.presets[preset].aliases.items():
            preset_field = spec.fields.get(name)
            targets[name] = OverrideTarget(path, field=preset_field)

    return targets


def _is_field_cli_name(name: str) -> bool:
    return "." not in name and "/" not in name and "_" not in name


def expand_args(
    argv: list[str],
    spec: ConfigSpec,
    *,
    preset: str | None = None,
    sweep: bool = False,
) -> list[str]:
    expanded: list[str] = []
    targets = target_map(spec, preset)
    i = 0

    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--") and len(arg) > 2:
            name_value = arg[2:]
            if "=" in name_value:
                name, value = name_value.split("=", 1)
            else:
                name = name_value
                target = targets.get(name)
                if target is not None and target.type == "bool":
                    if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
                        expanded.append(f"{target.path}=true")
                        i += 1
                        continue
                if i + 1 >= len(argv):
                    if name in targets:
                        raise MissingArgumentValueError(name)
                    raise UnknownArgumentError(name, set(targets))
                value = argv[i + 1]
                i += 1

            target = targets.get(name)
            if target is None:
                raise UnknownArgumentError(name, set(targets))
            _validate_choice(name, value, target, sweep=sweep)
            _validate_sweep(name, value, target, sweep=sweep)
            value = _quote_single_run_comma_value(value, target, sweep=sweep)
            expanded.append(f"{target.path}={value}")
        else:
            expanded.append(arg)

        i += 1

    return expanded


def preset_overrides(
    spec: ConfigSpec,
    preset: str,
    argv: list[str],
    *,
    sweep: bool = False,
) -> list[str]:
    card = spec.preset(preset)
    return [*card.overrides, *expand_args(argv, spec, preset=preset, sweep=sweep)]


def _validate_sweep(name: str, value: str, target: OverrideTarget, *, sweep: bool) -> None:
    if sweep and not target.sweepable and "," in value:
        raise NonSweepableFieldError(
            f"Field '{name}' is marked sweepable=false, but was used with comma values."
        )


def _validate_choice(name: str, value: str, target: OverrideTarget, *, sweep: bool) -> None:
    choices = None
    label = "argument"
    if target.group is not None and target.group.choices:
        choices = target.group.choices
        label = "group"
    elif target.field is not None and target.field.choices:
        choices = target.field.choices
        label = "field"

    values = value.split(",") if sweep and "," in value else [value]
    invalid_values = [item for item in values if item not in choices] if choices is not None else []
    if choices is not None and invalid_values:
        formatted = ", ".join(choices)
        invalid = ", ".join(invalid_values)
        raise InvalidChoiceError(
            f"Invalid value for {label} '{name}': {invalid}. Choices: {formatted}"
        )


def _quote_single_run_comma_value(value: str, target: OverrideTarget, *, sweep: bool) -> str:
    stripped = value.strip()
    if (
        sweep
        or target.sweepable
        or "," not in stripped
        or stripped.startswith(("[", "{", "'", '"'))
    ):
        return value
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"
