import pytest

from hydra_fire.core.errors import (
    InvalidChoiceError,
    MissingArgumentValueError,
    NonSweepableFieldError,
    UnknownArgumentError,
)
from hydra_fire.core.overrides import expand_args, preset_overrides
from hydra_fire.core.spec import ArgumentField, ConfigGroup, ConfigSpec, Preset


def test_raw_key_value_tokens_are_not_expanded_as_friendly_aliases():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size")})

    assert expand_args(["size=8"], spec) == ["size=8"]


def test_expands_flag_field_alias():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size")})

    assert expand_args(["--size", "8"], spec) == ["job.size=8"]


def test_expands_equals_flag_alias():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size")})

    assert expand_args(["--size=8"], spec) == ["job.size=8"]


def test_missing_value_for_known_flag_raises_clear_error():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size", type="int")})

    with pytest.raises(MissingArgumentValueError, match="requires a value"):
        expand_args(["--size"], spec)


def test_expands_shell_friendly_path_flag():
    spec = ConfigSpec(fields={"precision": ArgumentField(path="trainer.precision")})

    assert expand_args(["--trainer-precision", "bf16"], spec) == ["trainer.precision=bf16"]


def test_bool_flag_defaults_to_true():
    spec = ConfigSpec(fields={"verbose": ArgumentField(path="runtime.verbose", type="bool")})

    assert expand_args(["--verbose"], spec) == ["runtime.verbose=true"]


def test_config_group_expands_as_choice_argument():
    spec = ConfigSpec(groups={"model": ConfigGroup(name="model", choices=["small", "large"])})

    assert expand_args(["--model", "small"], spec) == ["model=small"]


def test_config_group_rejects_unknown_choice():
    spec = ConfigSpec(groups={"model": ConfigGroup(name="model", choices=["small", "large"])})

    with pytest.raises(InvalidChoiceError):
        expand_args(["--model", "medium"], spec)


def test_config_group_allows_comma_choices_in_sweep_mode():
    spec = ConfigSpec(groups={"model": ConfigGroup(name="model", choices=["small", "large"])})

    assert expand_args(["--model", "small,large"], spec, sweep=True) == ["model=small,large"]

    with pytest.raises(InvalidChoiceError):
        expand_args(["--model", "small,medium"], spec, sweep=True)


def test_field_rejects_unknown_choice():
    spec = ConfigSpec(
        fields={"precision": ArgumentField(path="trainer.precision", choices=["bf16", "fp16"])}
    )

    with pytest.raises(InvalidChoiceError):
        expand_args(["--precision", "fp32"], spec)


def test_raw_hydra_override_passthrough():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size")})

    assert expand_args(["other.value=2"], spec) == ["other.value=2"]


def test_hydra_plus_and_delete_passthrough():
    spec = ConfigSpec()

    assert expand_args(["+foo=bar", "++x=1", "~runtime.verbose"], spec) == [
        "+foo=bar",
        "++x=1",
        "~runtime.verbose",
    ]


def test_plus_raw_override_does_not_expand_friendly_aliases():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size")})

    assert expand_args(["+size=8"], spec) == ["+size=8"]


def test_sweep_raw_override_passthrough():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size")})

    assert expand_args(["-m", "job.size=4,8,16"], spec) == ["-m", "job.size=4,8,16"]


def test_non_sweepable_field_rejects_comma_values_in_sweep_mode():
    spec = ConfigSpec(
        fields={
            "verbose": ArgumentField(
                path="runtime.verbose",
                type="bool",
                sweepable=False,
            )
        }
    )

    with pytest.raises(NonSweepableFieldError):
        expand_args(["--verbose", "true,false"], spec, sweep=True)


def test_unknown_friendly_flag_raises_with_suggestion():
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size")})

    with pytest.raises(UnknownArgumentError) as excinfo:
        expand_args(["--sze", "8"], spec)

    assert "size" in str(excinfo.value)


def test_preset_overrides_are_prepended():
    spec = ConfigSpec(
        fields={"size": ArgumentField(path="job.size")},
        presets={"baseline": Preset(overrides=["job=baseline"])},
    )

    assert preset_overrides(spec, "baseline", ["--size", "2"]) == ["job=baseline", "job.size=2"]


def test_preset_aliases_do_not_apply_to_key_value_tokens():
    spec = ConfigSpec(
        fields={"size": ArgumentField(path="job.size")},
        presets={
            "compact": Preset(
                overrides=["job=compact"],
                aliases={"size": "job.compact_size"},
            )
        },
    )

    assert expand_args(["size=2"], spec, preset="compact") == ["size=2"]
