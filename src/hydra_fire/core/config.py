from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .errors import ConfigError
from .spec import ConfigSpec


def load_cli_config(path: str | Path = "cli.config.yaml") -> ConfigSpec:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"CLI config file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in CLI config file: {config_path}") from exc

    try:
        return ConfigSpec.model_validate(_normalize_cli_config(raw))
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc


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
        return load_cli_config(config_path)
    save_cli_config(spec, config_path)
    return spec


def _normalize_cli_config(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw)
    groups = {}
    for name, value in (data.get("groups") or {}).items():
        item = dict(value or {})
        item.setdefault("name", name)
        groups[name] = item
    data["groups"] = groups
    return data
