from pathlib import Path

from hydra_fire.core.config import ensure_cli_config, load_cli_config, save_cli_config
from hydra_fire.core.spec import ArgumentField, ConfigSpec


def test_load_cli_config():
    spec = load_cli_config(Path("tests/fixtures/cli.config.yaml"))

    assert spec.hydra.config_name == "config"
    assert spec.fields["size"].path == "job.size"
    assert spec.groups["job"].choices == ["baseline"]
    assert "baseline" in spec.presets


def test_save_and_load_cli_config_round_trip(tmp_path):
    path = tmp_path / "cli.config.yaml"
    spec = ConfigSpec(fields={"size": ArgumentField(path="job.size", type="int")})

    save_cli_config(spec, path)
    loaded = load_cli_config(path)

    assert loaded.fields["size"].path == "job.size"
    assert loaded.fields["size"].type == "int"


def test_ensure_cli_config_does_not_overwrite_existing_file(tmp_path):
    path = tmp_path / "cli.config.yaml"
    save_cli_config(ConfigSpec(fields={"first": ArgumentField(path="first")}), path)

    loaded = ensure_cli_config(
        ConfigSpec(fields={"second": ArgumentField(path="second")}),
        path,
    )

    assert "first" in loaded.fields
    assert "second" not in loaded.fields


def test_ensure_cli_config_overwrites_when_requested(tmp_path):
    path = tmp_path / "cli.config.yaml"
    save_cli_config(ConfigSpec(fields={"first": ArgumentField(path="first")}), path)

    loaded = ensure_cli_config(
        ConfigSpec(fields={"second": ArgumentField(path="second")}),
        path,
        overwrite=True,
    )

    assert "second" in loaded.fields
    assert "first" not in loaded.fields
