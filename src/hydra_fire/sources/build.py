from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from hydra_fire.core.spec import ConfigSpec, HydraConfig, merge_specs
from hydra_fire.hydra import discover_config_spec

from .dataclass import spec_from_dataclass
from .function import spec_from_function
from .pydantic import spec_from_pydantic


def build_config_spec(
    *,
    config_path: str | Path | None = None,
    config_name: str = "config",
    target: Callable[..., Any] | None = None,
    schema: type[Any] | None = None,
    discover_hydra: bool = True,
) -> ConfigSpec:
    specs: list[ConfigSpec] = []

    if config_path is not None and discover_hydra:
        specs.append(discover_config_spec(config_path, config_name=config_name))

    if schema is not None:
        specs.append(_spec_from_schema(schema))
    elif target is not None:
        specs.append(spec_from_function(target))

    if config_path is not None:
        specs.append(
            ConfigSpec(
                hydra=HydraConfig(
                    config_path=str(config_path),
                    config_name=config_name,
                )
            )
        )

    return merge_specs(*specs)


def _spec_from_schema(schema: type[Any]) -> ConfigSpec:
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return spec_from_pydantic(schema)
    return spec_from_dataclass(schema)
