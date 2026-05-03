from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .errors import ConfigError
from .spec import ConfigSpec

_PRESET_CONFIG_KEYS = {"public_name", "source_groups"}


def load_cli_config(
    path: str | Path = "cli.config.yaml",
    *,
    base_path: Path | None = None,
) -> ConfigSpec:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"CLI config file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in CLI config file: {config_path}") from exc

    try:
        spec = ConfigSpec.model_validate(_normalize_cli_config(raw))
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc

    _resolve_auto_choices(spec, base_path or config_path.parent)
    return spec


def save_cli_config(spec: ConfigSpec, path: str | Path = "cli.config.yaml") -> None:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = spec.model_dump(mode="json", exclude_none=True)
    config_path.write_text(yaml.safe_dump(data, sort_keys=False))


def ensure_cli_config(
    spec: ConfigSpec,
    path: str | Path = "cli.config.yaml",
    *,
    overwrite: bool = False,
) -> ConfigSpec:
    config_path = Path(path)
    if config_path.exists() and not overwrite:
        return load_cli_config(config_path, base_path=config_path.parent)
    save_cli_config(spec, config_path)
    return spec


def _resolve_auto_choices(spec: ConfigSpec, base_path: Path) -> None:
    from hydra_fire.hydra.discover import _yaml_choices

    config_root = base_path / spec.hydra.config_path
    for group in spec.groups.values():
        if group.choices_auto:
            group_dir = config_root / group.hydra_group.replace("/", "/")
            if group_dir.exists():
                group.choices = _yaml_choices(group_dir)


def _normalize_cli_config(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw)

    # Extract preset_config metadata from the presets section
    raw_presets = data.get("presets") or {}
    preset_config_data: dict[str, Any] = {}
    preset_entries: dict[str, Any] = {}
    for key, value in raw_presets.items():
        if key in _PRESET_CONFIG_KEYS:
            preset_config_data[key] = value
        else:
            preset_entries[key] = value
    if preset_config_data:
        data["preset_config"] = preset_config_data
    data["presets"] = preset_entries

    # Normalize groups: handle choices:auto, target, alias
    groups = {}
    for name, value in (data.get("groups") or {}).items():
        item = dict(value or {})
        item.setdefault("name", name)
        if item.get("choices") == "auto":
            item["choices"] = []
            item["choices_auto"] = True
        groups[name] = item
    data["groups"] = groups

    return data
