from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import yaml

from hydra_fire.core.spec import (
    ArgumentField,
    ConfigGroup,
    ConfigSpec,
    HydraConfig,
    Preset,
    ValueType,
    cli_name_from_path,
)

IGNORED_MAPPING_KEYS = {"defaults"}
PRESET_DIRECTORIES = {"preset", "presets", "recipe", "recipes", "experiment", "experiments"}
PRESET_METADATA_KEYS = {"aliases", "defaults", "description", "examples", "help", "overrides"}


def discover_config_spec(
    config_path: str | Path,
    *,
    config_name: str = "config",
) -> ConfigSpec:
    root = Path(config_path)
    return ConfigSpec(
        hydra=HydraConfig(config_path=str(config_path), config_name=config_name),
        fields=index_config_fields(root, config_name=config_name),
        groups=discover_config_groups(root),
        presets=discover_presets(root),
    )


def discover_config_groups(config_path: str | Path) -> dict[str, ConfigGroup]:
    root = Path(config_path)
    groups: dict[str, ConfigGroup] = {}
    if not root.exists():
        return groups

    for directory in sorted(path for path in root.rglob("*") if path.is_dir()):
        if _is_in_preset_tree(root, directory):
            continue
        choices = _yaml_choices(directory)
        if not choices:
            continue
        group_name = _group_name(root, directory)
        groups[group_name] = ConfigGroup(
            name=group_name,
            choices=choices,
            default=choices[0],
            help=f"{group_name} config group.",
        )
    return groups


def index_config_fields(
    config_path: str | Path,
    *,
    config_name: str = "config",
) -> dict[str, ArgumentField]:
    root = Path(config_path)
    fields: dict[str, ArgumentField] = {}
    if not root.exists():
        return fields

    root_config = root / f"{config_name}.yaml"
    if root_config.exists():
        _add_yaml_fields(fields, root_config, prefix="")

    for yaml_path in sorted(root.rglob("*.yaml")):
        if (
            yaml_path == root_config
            or _is_private_yaml(yaml_path)
            or _is_in_preset_tree(root, yaml_path)
        ):
            continue
        group = _group_name(root, yaml_path.parent)
        if not group:
            continue
        _add_yaml_fields(fields, yaml_path, prefix=group)

    return fields


def discover_presets(config_path: str | Path) -> dict[str, Preset]:
    root = Path(config_path)
    presets: dict[str, Preset] = {}
    if not root.exists():
        return presets

    for directory in sorted(path for path in root.rglob("*") if path.is_dir()):
        if directory.name not in PRESET_DIRECTORIES:
            continue
        for yaml_path in sorted(directory.rglob("*.yaml")):
            if _is_private_yaml(yaml_path):
                continue
            preset = _preset_from_yaml(yaml_path)
            if preset is None:
                continue
            name = _preset_name(directory, yaml_path)
            presets[name] = preset
    return presets


def _add_yaml_fields(fields: dict[str, ArgumentField], yaml_path: Path, *, prefix: str) -> None:
    data = _load_yaml_mapping(yaml_path)
    for path, value in _iter_leaf_values(data, prefix=prefix):
        fields.setdefault(
            path,
            ArgumentField(
                path=path,
                alias=path_to_flag(path),
                type=_infer_value_type(value),
                default=value if _is_scalar(value) else None,
                help="",
                level="advanced",
                visible=True,
            ),
        )


def _iter_leaf_values(value: Any, *, prefix: str) -> Iterator[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str) or key in IGNORED_MAPPING_KEYS or key.startswith("_"):
                continue
            child_prefix = f"{prefix}.{key}" if prefix else key
            yield from _iter_leaf_values(child, prefix=child_prefix)
        return

    if isinstance(value, list):
        yield prefix, value
        return

    if prefix:
        yield prefix, value


def _load_yaml_mapping(yaml_path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(yaml_path.read_text()) or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def _preset_from_yaml(yaml_path: Path) -> Preset | None:
    data = _load_yaml_mapping(yaml_path)
    overrides = _preset_overrides(data)

    aliases_raw = data.get("aliases") or {}
    aliases = (
        {str(key): str(value) for key, value in aliases_raw.items()}
        if isinstance(aliases_raw, Mapping)
        else {}
    )
    examples_raw = data.get("examples") or []
    examples = [str(item) for item in examples_raw] if isinstance(examples_raw, list) else []
    description = str(data.get("description") or data.get("help") or "")
    if not overrides and not aliases and not examples and not description:
        return None
    return Preset(
        description=description,
        overrides=overrides,
        aliases=aliases,
        examples=examples,
    )


def _preset_overrides(data: Mapping[str, Any]) -> list[str]:
    overrides: list[str] = []

    raw_defaults = data.get("defaults") or []
    if isinstance(raw_defaults, list):
        for item in raw_defaults:
            overrides.extend(_default_to_overrides(item))

    raw_overrides = data.get("overrides") or []
    if isinstance(raw_overrides, list):
        overrides.extend(str(item) for item in raw_overrides if item is not None)

    for path, value in _iter_leaf_values(_preset_value_mapping(data), prefix=""):
        if value is None:
            continue
        overrides.append(f"{path}={_format_override_value(value)}")

    return [override for override in overrides if override]


def _preset_value_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in data.items() if str(key) not in PRESET_METADATA_KEYS}


def _default_to_overrides(value: Any) -> list[str]:
    if isinstance(value, str):
        if value == "_self_":
            return []
        if "/" in value:
            group, choice = value.rsplit("/", 1)
            return [f"{group}={choice}"]
        return [value]

    if isinstance(value, Mapping):
        overrides = []
        for raw_group, raw_choice in value.items():
            group = str(raw_group)
            if group.startswith("override "):
                group = group.removeprefix("override ").strip()
            group = group.lstrip("/")
            overrides.append(f"{group}={raw_choice}")
        return overrides

    return []


def _format_override_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _preset_name(directory: Path, yaml_path: Path) -> str:
    relative = yaml_path.relative_to(directory).with_suffix("")
    return "/".join(relative.parts)


def _yaml_choices(directory: Path) -> list[str]:
    choices = []
    for yaml_path in sorted(directory.glob("*.yaml")):
        if _is_private_yaml(yaml_path):
            continue
        choices.append(yaml_path.stem)
    return choices


def _group_name(root: Path, directory: Path) -> str:
    relative = directory.relative_to(root)
    return "/".join(relative.parts)


def _is_private_yaml(path: Path) -> bool:
    return path.name.startswith("_")


def _is_in_preset_tree(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return any(part in PRESET_DIRECTORIES for part in relative.parts)


def _infer_value_type(value: Any) -> ValueType:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    return "json"


def _is_scalar(value: Any) -> bool:
    return isinstance(value, str | int | float | bool) or value is None


def path_to_flag(path: str) -> str:
    return cli_name_from_path(path)
