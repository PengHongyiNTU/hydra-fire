from pathlib import Path

import pytest

from hydra_fire.core.errors import UnknownArgumentError
from hydra_fire.core.overrides import expand_args
from hydra_fire.hydra.discover import (
    discover_config_groups,
    discover_config_spec,
    discover_presets,
    index_config_fields,
)


def test_discovers_config_groups_from_hydra_folders(tmp_path):
    configs = _write_config_tree(tmp_path)

    groups = discover_config_groups(configs)

    assert groups["model"].choices == ["large", "small"]
    assert groups["model"].default == "large"
    assert groups["optimizer"].choices == ["adam", "sgd"]
    assert groups["launcher/local"].choices == ["debug"]


def test_indexes_root_and_group_yaml_fields(tmp_path):
    configs = _write_config_tree(tmp_path)

    fields = index_config_fields(configs)

    assert fields["seed"].type == "int"
    assert fields["runtime.verbose"].type == "bool"
    assert fields["runtime.tags"].type == "json"
    assert fields["trainer.precision"].type == "str"
    assert fields["trainer.max_steps"].type == "int"
    assert fields["trainer.max_steps"].level == "advanced"
    assert fields["trainer.max_steps"].visible is True
    assert fields["optimizer.lr"].type == "float"
    assert fields["model.hidden_size"].type == "int"
    assert fields["model.name"].alias == "model-name"
    assert "defaults" not in fields
    assert "model._target_" not in fields


def test_discovered_spec_translates_groups_and_nested_field_flags(tmp_path):
    configs = _write_config_tree(tmp_path)
    spec = discover_config_spec(configs)

    assert expand_args(["--model", "small"], spec) == ["model=small"]
    assert expand_args(["optimizer.lr=0.1"], spec) == ["optimizer.lr=0.1"]
    with pytest.raises(UnknownArgumentError):
        expand_args(["--trainer-precision", "bf16"], spec)


def test_discovers_presets_from_recipe_folders(tmp_path):
    configs = _write_config_tree(tmp_path)

    presets = discover_presets(configs)

    assert presets["quick"].description == "Fast smoke test."
    assert presets["quick"].overrides == [
        "model=small",
        "optimizer=adam",
        "trainer.max_steps=10",
        "runtime.verbose=true",
    ]
    assert presets["quick"].aliases == {"bs": "trainer.batch_size"}
    assert presets["nested/large"].overrides == [
        "model=large",
        "optimizer=sgd",
        "trainer.max_steps=20",
    ]


def test_discovers_metadata_only_preset(tmp_path):
    configs = tmp_path / "configs"
    (configs / "presets").mkdir(parents=True)
    (configs / "presets" / "notes.yaml").write_text(
        """
description: Documented preset shell.
aliases:
  bs: trainer.batch_size
examples:
  - train notes --bs 8
"""
    )

    presets = discover_presets(configs)

    assert presets["notes"].description == "Documented preset shell."
    assert presets["notes"].overrides == []
    assert presets["notes"].aliases == {"bs": "trainer.batch_size"}


def test_discovered_spec_includes_presets(tmp_path):
    configs = _write_config_tree(tmp_path)

    spec = discover_config_spec(configs)

    assert "quick" in spec.presets
    assert expand_args(["--bs", "8"], spec, preset="quick") == ["trainer.batch_size=8"]


def test_discovery_handles_missing_config_directory(tmp_path):
    missing = tmp_path / "missing"

    assert discover_config_groups(missing) == {}
    assert index_config_fields(missing) == {}
    spec = discover_config_spec(missing)
    assert spec.groups == {}
    assert spec.fields == {}


def _write_config_tree(tmp_path: Path) -> Path:
    configs = tmp_path / "configs"
    (configs / "model").mkdir(parents=True)
    (configs / "optimizer").mkdir(parents=True)
    (configs / "launcher" / "local").mkdir(parents=True)
    (configs / "presets" / "nested").mkdir(parents=True)

    (configs / "config.yaml").write_text(
        """
defaults:
  - model: small
  - optimizer: adam
  - _self_

seed: 1
runtime:
  verbose: false
  tags:
    - smoke
trainer:
  precision: fp32
  max_steps: 100
"""
    )
    (configs / "model" / "small.yaml").write_text(
        """
name: small
hidden_size: 128
_target_: example.SmallModel
"""
    )
    (configs / "model" / "large.yaml").write_text(
        """
name: large
hidden_size: 512
"""
    )
    (configs / "optimizer" / "adam.yaml").write_text(
        """
name: adam
lr: 0.001
"""
    )
    (configs / "optimizer" / "sgd.yaml").write_text(
        """
name: sgd
lr: 0.1
"""
    )
    (configs / "launcher" / "local" / "debug.yaml").write_text(
        """
name: debug
workers: 1
"""
    )
    (configs / "presets" / "quick.yaml").write_text(
        """
description: Fast smoke test.
defaults:
  - model: small
  - optimizer: adam
overrides:
  - trainer.max_steps=10
aliases:
  bs: trainer.batch_size
examples:
  - train quick --bs 8
runtime:
  verbose: true
"""
    )
    (configs / "presets" / "nested" / "large.yaml").write_text(
        """
defaults:
  - model: large
  - optimizer/sgd
trainer:
  max_steps: 20
"""
    )
    (configs / "model" / "_private.yaml").write_text("name: private\n")
    return configs
