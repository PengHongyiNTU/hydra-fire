from __future__ import annotations

from pathlib import Path

from hydra import compose, initialize_config_dir
from omegaconf import DictConfig, OmegaConf


def compose_config(
    config_path: str,
    config_name: str,
    overrides: list[str],
    *,
    base_path: str | Path | None = None,
) -> DictConfig:
    path = Path(config_path)
    if not path.is_absolute() and base_path is not None:
        path = Path(base_path) / path
    config_dir = str(path.resolve())
    with initialize_config_dir(config_dir=config_dir, version_base=None):
        return compose(config_name=config_name, overrides=overrides)


def to_yaml(config: DictConfig) -> str:
    return OmegaConf.to_yaml(config, resolve=True)
