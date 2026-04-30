from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pytest
from omegaconf import OmegaConf
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from hydra_fire.hydra import discover_presets
from hydra_fire.validate import validate_config


@dataclass
class CallbackConfig:
    name: str


@dataclass
class CallbackTrainConfig:
    callbacks: list[CallbackConfig] = field(default_factory=list)
    callback: CallbackConfig | None = None


@dataclass
class RuntimeConfig:
    verbose: bool = False


@dataclass
class RuntimeTrainConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)


def test_pydantic_schema_rejects_invalid_literal_value():
    class TrainConfig(BaseModel):
        precision: Literal["bf16", "fp16"]

    cfg = OmegaConf.create({"precision": "fp32"})

    with pytest.raises(ValidationError):
        validate_config(cfg, TrainConfig)


def test_dataclass_validation_supports_optional_nested_dataclass_and_lists():
    cfg = OmegaConf.create(
        {
            "callbacks": [{"name": "tensorboard"}, {"name": "checkpoint"}],
            "callback": {"name": "early_stop"},
        }
    )

    result = validate_config(cfg, CallbackTrainConfig)

    assert [item.name for item in result.callbacks] == ["tensorboard", "checkpoint"]
    assert result.callback == CallbackConfig(name="early_stop")


def test_dataclass_validation_rejects_non_mapping_nested_dataclass():
    cfg = OmegaConf.create({"runtime": "bad"})

    with pytest.raises(TypeError, match="Expected mapping for dataclass field"):
        validate_config(cfg, RuntimeTrainConfig)


def test_malformed_preset_yaml_fails_during_discovery(tmp_path):
    configs = tmp_path / "configs"
    (configs / "presets").mkdir(parents=True)
    (configs / "presets" / "broken.yaml").write_text("overrides: [unterminated\n")

    with pytest.raises(YAMLError):
        discover_presets(configs)
