import pytest

from hydra_fire.core.errors import UnknownArgumentError, UnknownPresetError
from hydra_fire.core.spec import ArgumentField, ConfigGroup, ConfigSpec, Preset, RunMode
from hydra_fire.tui.state import LauncherState


def _spec() -> ConfigSpec:
    return ConfigSpec(
        fields={
            "size": ArgumentField(path="job.size", type="int"),
            "mode": ArgumentField(path="job.mode", choices=["fast", "safe"]),
        },
        groups={"job": ConfigGroup(name="job", choices=["baseline", "large"])},
        presets={"quick": Preset(overrides=["job=baseline"])},
    )


def test_launcher_state_builds_overrides_from_preset_selections_and_raw_overrides():
    state = LauncherState(_spec())

    state.set_preset("quick")
    state.set_argument("size", "16")
    state.add_raw("runtime.verbose=true")

    assert state.overrides() == ["job=baseline", "job.size=16", "runtime.verbose=true"]


def test_launcher_state_validates_presets_arguments_and_choices():
    state = LauncherState(_spec())

    with pytest.raises(UnknownPresetError):
        state.set_preset("missing")
    with pytest.raises(UnknownArgumentError):
        state.set_argument("missing", "1")
    with pytest.raises(ValueError):
        state.set_argument("job", "unknown")
    with pytest.raises(ValueError):
        state.set_argument("mode", "unknown")


def test_launcher_state_exposes_completion_sources_and_summary():
    state = LauncherState(_spec())
    state.set_preset("quick")
    state.set_argument("job", "baseline")

    assert "quick" in state.preset_names()
    assert "size" in state.argument_names()
    assert state.values_for("job") == ["baseline", "large"]
    assert "preset: quick" in state.summary()
    assert "job=baseline" in state.summary()

    state.clear()
    assert state.summary() == "No selections."


def _spec_with_run_modes() -> ConfigSpec:
    return ConfigSpec(
        fields={
            "output-dir": ArgumentField(path="local.output_dir", level="core"),
        },
        groups={
            "recipe": ConfigGroup(name="recipe", choices=["mnist_vit_lora", "cifar10_resnet"]),
            "problem": ConfigGroup(name="problem", choices=["mnist", "cifar10"]),
        },
        presets={"mnist_vit_lora": Preset(overrides=["recipe=mnist_vit_lora"])},
        run_modes=[
            RunMode(name="recipe", requires=["recipe", "output-dir"]),
            RunMode(name="explicit_axes", requires=["problem", "output-dir"], optional=["method"]),
        ],
    )


def test_launcher_state_run_mode_names():
    state = LauncherState(_spec_with_run_modes())
    assert state.run_mode_names() == ["recipe", "explicit_axes"]


def test_launcher_state_set_run_mode_valid():
    state = LauncherState(_spec_with_run_modes())
    state.set_run_mode("recipe")
    assert state.run_mode == "recipe"


def test_launcher_state_set_run_mode_invalid():
    state = LauncherState(_spec_with_run_modes())
    with pytest.raises(ValueError, match="Unknown run mode"):
        state.set_run_mode("nonexistent")


def test_launcher_state_required_and_optional_fields():
    state = LauncherState(_spec_with_run_modes())
    state.set_run_mode("explicit_axes")
    assert state.required_fields() == ["problem", "output-dir"]
    assert state.optional_fields() == ["method"]


def test_launcher_state_required_fields_empty_when_no_run_mode():
    state = LauncherState(_spec_with_run_modes())
    assert state.required_fields() == []
    assert state.optional_fields() == []


def test_launcher_state_clear_resets_run_mode():
    state = LauncherState(_spec_with_run_modes())
    state.set_run_mode("recipe")
    state.clear()
    assert state.run_mode is None


def test_launcher_state_summary_includes_run_mode():
    state = LauncherState(_spec_with_run_modes())
    state.set_run_mode("recipe")
    assert "run mode: recipe" in state.summary()
