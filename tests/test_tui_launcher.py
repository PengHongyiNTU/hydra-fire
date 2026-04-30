import pytest
from prompt_toolkit.document import Document

from hydra_fire.core.spec import ArgumentField, ConfigGroup, ConfigSpec, HydraConfig, Preset
from hydra_fire.tui.launcher import LauncherCompleter, parse_launch_args


def _spec() -> ConfigSpec:
    return ConfigSpec(
        hydra=HydraConfig(config_path="tests/fixtures/configs", config_name="config"),
        fields={
            "size": ArgumentField(path="job.size", type="int", alias="batch-size"),
            "mode": ArgumentField(path="job.mode", type="str", choices=["fast", "safe"]),
            "title": ArgumentField(path="job.title", type="str"),
            "trainer.max_steps": ArgumentField(
                path="trainer.max_steps",
                type="int",
                level="advanced",
            ),
            "debug": ArgumentField(path="debug", type="bool"),
        },
        groups={"job": ConfigGroup(name="job", choices=["baseline", "large"])},
        presets={"quick": Preset(overrides=["job=baseline"])},
    )


def test_launcher_completer_suggests_cli_options_and_raw_keys():
    completer = LauncherCompleter(_spec())

    option_completions = list(completer.get_completions(Document("--ba"), None))
    raw_completions = list(completer.get_completions(Document("job.s"), None))
    bare_completions = list(completer.get_completions(Document("tra"), None))
    bare_debug_completions = list(completer.get_completions(Document("de"), None))
    preset_completions = list(completer.get_completions(Document("--pre"), None))

    assert any(item.text == "--batch-size" for item in option_completions)
    assert any(item.text == "job.size=" for item in raw_completions)
    assert any(item.text == "trainer.max_steps=" for item in bare_completions)
    assert not any(item.text == "debug=" for item in bare_debug_completions)
    assert any(item.text == "--preset" for item in preset_completions)
    assert not any(item.text == "--preset" for item in bare_completions)
    assert not any(item.text == "--debug" for item in bare_debug_completions)
    assert not any(item.text == "--trainer-max-steps" for item in option_completions)


def test_launcher_completer_suggests_values_after_options_and_key_value_pairs():
    completer = LauncherCompleter(_spec())

    group_values = list(completer.get_completions(Document("--job b"), None))
    field_values = list(completer.get_completions(Document("--mode s"), None))
    preset_values = list(completer.get_completions(Document("preset=q"), None))

    assert any(item.text == "baseline" for item in group_values)
    assert any(item.text == "safe" for item in field_values)
    assert any(item.text == "preset=quick" for item in preset_values)


def test_launcher_completer_suggests_hydra_paths_for_raw_override_contexts():
    completer = LauncherCompleter(_spec())

    raw_path_completions = list(completer.get_completions(Document("trainer."), None))
    plus_all_completions = list(completer.get_completions(Document("+"), None))
    plus_completions = list(completer.get_completions(Document("++trainer."), None))
    delete_completions = list(completer.get_completions(Document("~trainer."), None))

    assert any(item.text == "trainer.max_steps=" for item in raw_path_completions)
    assert any(item.text == "+debug=" for item in plus_all_completions)
    assert any(item.text == "++trainer.max_steps=" for item in plus_completions)
    assert any(item.text == "~trainer.max_steps=" for item in delete_completions)


def test_parse_launch_args_expands_friendly_options_and_raw_overrides():
    overrides = parse_launch_args(
        "--batch-size 16 --mode fast job.title=hello runtime.verbose=true",
        _spec(),
    )

    assert overrides == [
        "job.size=16",
        "job.mode=fast",
        "job.title=hello",
        "runtime.verbose=true",
    ]


def test_parse_launch_args_supports_presets():
    overrides = parse_launch_args("--preset quick --size 16", _spec())

    assert overrides == ["job=baseline", "job.size=16"]


@pytest.mark.parametrize("line", ["batch-size=16", "batch-size = 16"])
def test_parse_launch_args_rejects_friendly_key_value_aliases(line):
    with pytest.raises(ValueError, match="not supported"):
        parse_launch_args(line, _spec())


def test_parse_launch_args_still_allows_raw_hydra_paths_and_option_equals():
    raw = parse_launch_args("job.size=16", _spec())
    option_equals = parse_launch_args("--batch-size=16", _spec())

    assert raw == ["job.size=16"]
    assert option_equals == ["job.size=16"]
