import pytest

from hydra_fire.core.errors import UnknownArgumentError, UnknownPresetError
from hydra_fire.core.spec import ArgumentField, ConfigGroup, ConfigSpec, Preset
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
