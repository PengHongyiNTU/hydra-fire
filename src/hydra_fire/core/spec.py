from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

ValueType = Literal["str", "int", "float", "bool", "path", "json"]
FieldKind = Literal["value", "group", "raw"]
FieldLevel = Literal["core", "common", "advanced", "debug", "raw"]


class AppConfig(BaseModel):
    name: str = "hydra-fire"
    description: str = "Hydra-compatible CLI for configurable Python programs."


class HydraConfig(BaseModel):
    config_path: str = "configs"
    config_name: str = "config"


class ArgumentField(BaseModel):
    path: str
    alias: str | None = None
    type: ValueType = "str"
    kind: FieldKind = "value"
    default: Any | None = None
    required: bool = False
    help: str = ""
    level: FieldLevel = "common"
    choices: list[str] | None = None
    sweepable: bool = True
    visible: bool = True

    @property
    def cli_names(self) -> set[str]:
        if self.alias:
            return {self.alias}
        return {cli_name_from_path(self.path)}


class ConfigGroup(BaseModel):
    name: str
    choices: list[str] = Field(default_factory=list)
    default: str | None = None
    help: str = ""
    visible: bool = True

    @property
    def cli_names(self) -> set[str]:
        return {cli_name_from_path(self.name)}


class Preset(BaseModel):
    description: str = ""
    overrides: list[str] = Field(default_factory=list)
    aliases: dict[str, str] = Field(default_factory=dict)
    examples: list[str] = Field(default_factory=list)


class ConfigSpec(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    hydra: HydraConfig = Field(default_factory=HydraConfig)
    fields: dict[str, ArgumentField] = Field(default_factory=dict)
    groups: dict[str, ConfigGroup] = Field(default_factory=dict)
    presets: dict[str, Preset] = Field(default_factory=dict)

    def preset(self, name: str) -> Preset:
        try:
            return self.presets[name]
        except KeyError as exc:
            from .errors import UnknownPresetError

            raise UnknownPresetError(f"Unknown preset: {name}") from exc


def merge_specs(*specs: ConfigSpec) -> ConfigSpec:
    merged = ConfigSpec()
    for spec in specs:
        if spec.app != AppConfig():
            merged.app = spec.app
        if spec.hydra != HydraConfig():
            merged.hydra = spec.hydra
        merged.fields.update(spec.fields)
        merged.groups.update(spec.groups)
        merged.presets.update(spec.presets)
    return merged


def cli_name_from_path(path: str) -> str:
    name = re.sub(r"[./_]+", "-", path.strip())
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "value"


def is_exposed_field(field: ArgumentField) -> bool:
    return field.visible and field.level in {"core", "common"}
