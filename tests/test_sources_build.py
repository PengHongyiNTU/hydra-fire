from hydra_fire.sources import build_config_spec


def test_build_config_spec_merges_hydra_discovery_and_function_source(tmp_path):
    configs = tmp_path / "configs"
    (configs / "model").mkdir(parents=True)
    (configs / "presets").mkdir(parents=True)
    (configs / "config.yaml").write_text("seed: 1\n")
    (configs / "model" / "small.yaml").write_text("hidden_size: 128\n")
    (configs / "presets" / "quick.yaml").write_text(
        """
defaults:
  - model: small
overrides:
  - seed=2
"""
    )

    def workflow(size: int = 32):
        pass

    spec = build_config_spec(
        config_path=configs,
        config_name="config",
        target=workflow,
    )

    assert spec.hydra.config_path == str(configs)
    assert spec.fields["seed"].type == "int"
    assert spec.fields["size"].type == "int"
    assert spec.groups["model"].choices == ["small"]
    assert spec.presets["quick"].overrides == ["model=small", "seed=2"]
