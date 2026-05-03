from hydra_fire.core.spec import (
    ArgumentField,
    ConfigGroup,
    ConfigSpec,
    HydraConfig,
    PresetConfig,
    RunMode,
    cli_name_from_path,
    merge_specs,
)


def test_merge_specs_combines_fields_groups_and_hydra_settings():
    base = ConfigSpec(
        hydra=HydraConfig(config_path="configs", config_name="config"),
        fields={"size": ArgumentField(path="job.size")},
    )
    discovered = ConfigSpec(
        groups={"model": ConfigGroup(name="model", choices=["small", "large"])},
        fields={"rate": ArgumentField(path="job.rate")},
    )

    merged = merge_specs(base, discovered)

    assert merged.hydra.config_path == "configs"
    assert set(merged.fields) == {"size", "rate"}
    assert merged.groups["model"].choices == ["small", "large"]


def test_later_specs_override_duplicate_fields():
    first = ConfigSpec(fields={"size": ArgumentField(path="job.size", help="old")})
    second = ConfigSpec(fields={"size": ArgumentField(path="job.size", help="new")})

    merged = merge_specs(first, second)

    assert merged.fields["size"].help == "new"


def test_cli_name_from_path_uses_single_kebab_case_spelling():
    assert cli_name_from_path("trainer.max_steps") == "trainer-max-steps"
    assert cli_name_from_path("launcher/local.num_workers") == "launcher-local-num-workers"
    assert ArgumentField(path="trainer.max_steps").cli_names == {"trainer-max-steps"}


def test_config_group_target_and_alias():
    group = ConfigGroup(name="model-profile", target="model_profile", alias="profile")
    assert group.hydra_group == "model_profile"
    assert group.cli_names == {"profile"}


def test_config_group_hydra_group_falls_back_to_name():
    group = ConfigGroup(name="model")
    assert group.hydra_group == "model"
    assert group.cli_names == {"model"}


def test_config_group_cli_names_from_name_when_no_alias():
    group = ConfigGroup(name="model_profile")
    assert group.cli_names == {"model-profile"}


def test_preset_config_public_name():
    pc = PresetConfig(public_name="recipe", source_groups=["recipe", "recipes"])
    assert pc.public_name == "recipe"
    assert pc.source_groups == ["recipe", "recipes"]


def test_run_mode_fields():
    rm = RunMode(name="recipe", requires=["recipe", "output-dir"], optional=["method"])
    assert rm.name == "recipe"
    assert rm.requires == ["recipe", "output-dir"]
    assert rm.optional == ["method"]


def test_merge_specs_merges_preset_config_and_run_modes():
    base = ConfigSpec()
    override = ConfigSpec(
        preset_config=PresetConfig(public_name="recipe"),
        run_modes=[RunMode(name="recipe", requires=["recipe"])],
    )
    merged = merge_specs(base, override)
    assert merged.preset_config.public_name == "recipe"
    assert len(merged.run_modes) == 1
    assert merged.run_modes[0].name == "recipe"
