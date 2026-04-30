from __future__ import annotations

from dataclasses import dataclass, field

from hydra_fire.core.errors import UnknownArgumentError, UnknownPresetError
from hydra_fire.core.overrides import expand_args, preset_overrides, target_map
from hydra_fire.core.spec import ConfigSpec


@dataclass
class LauncherState:
    spec: ConfigSpec
    preset: str | None = None
    selections: dict[str, str] = field(default_factory=dict)
    raw_overrides: list[str] = field(default_factory=list)

    def set_preset(self, name: str | None) -> None:
        if name is not None and name not in self.spec.presets:
            raise UnknownPresetError(f"Unknown preset: {name}")
        self.preset = name

    def set_argument(self, name: str, value: str) -> None:
        targets = target_map(self.spec, self.preset)
        target = targets.get(name)
        if target is None:
            raise UnknownArgumentError(name, set(targets))
        if target.group is not None and target.group.choices and value not in target.group.choices:
            choices = ", ".join(target.group.choices)
            raise ValueError(f"Invalid value for group '{name}': {value}. Choices: {choices}")
        if target.field is not None and target.field.choices and value not in target.field.choices:
            choices = ", ".join(target.field.choices)
            raise ValueError(f"Invalid value for field '{name}': {value}. Choices: {choices}")
        self.selections[name] = value

    def add_raw(self, override: str) -> None:
        if not override:
            raise ValueError("raw override cannot be empty")
        self.raw_overrides.append(override)

    def clear(self) -> None:
        self.preset = None
        self.selections.clear()
        self.raw_overrides.clear()

    def argument_names(self) -> list[str]:
        return sorted(target_map(self.spec, self.preset))

    def preset_names(self) -> list[str]:
        return sorted(self.spec.presets)

    def values_for(self, name: str) -> list[str]:
        target = target_map(self.spec, self.preset).get(name)
        if target is None:
            return []
        if target.group is not None:
            return target.group.choices
        if target.field is not None and target.field.choices:
            return target.field.choices
        return []

    def args(self) -> list[str]:
        args: list[str] = []
        for name, value in self.selections.items():
            args.extend([f"--{name}", value])
        args.extend(self.raw_overrides)
        return args

    def overrides(self) -> list[str]:
        if self.preset is not None:
            return preset_overrides(self.spec, self.preset, self.args())
        return expand_args(self.args(), self.spec)

    def summary(self) -> str:
        lines: list[str] = []
        if self.preset is not None:
            lines.append(f"preset: {self.preset}")
        if self.selections:
            lines.append("selections:")
            for name, value in self.selections.items():
                lines.append(f"  {name}={value}")
        if self.raw_overrides:
            lines.append("raw overrides:")
            for override in self.raw_overrides:
                lines.append(f"  {override}")
        if not lines:
            return "No selections."
        return "\n".join(lines)
