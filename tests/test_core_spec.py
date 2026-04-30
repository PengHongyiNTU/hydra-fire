from hydra_fire.core.spec import (
    ArgumentField,
    ConfigGroup,
    ConfigSpec,
    HydraConfig,
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
