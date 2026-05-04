from dataclasses import dataclass, field

import pytest
from pydantic import BaseModel, Field, ValidationError

import hydra_fire as package
from hydra_fire import app as app_module
from hydra_fire import hydra_fire
from hydra_fire.core.config import load_cli_config
from hydra_fire.errors import AmbiguousSweepValueError


def test_hydra_fire_decorator_composes_config_from_aliases():
    seen = {}

    @hydra_fire(
        config_path="configs",
        config_name="config",
        cli_config="tests/fixtures/cli.config.yaml",
    )
    def main(cfg):
        seen["size"] = cfg.job.size
        return "ok"

    assert main(["--size", "32"]) == "ok"
    assert seen["size"] == 32


def test_hydra_cli_is_not_exported():
    assert not hasattr(package, "hydra_cli")


def test_ambiguous_sweep_error_is_publicly_importable():
    assert issubclass(AmbiguousSweepValueError, Exception)
    assert package.AmbiguousSweepValueError is AmbiguousSweepValueError


def test_hydra_fire_decorator_auto_initializes_cli_config(tmp_path):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(size: int = 1):
        return size

    assert main(["--size", "2"]) == 2
    spec = load_cli_config(cli_config)
    assert spec.fields["size"].type == "int"


@pytest.mark.parametrize("help_arg", ["--help", "-h", "help"])
def test_hydra_fire_decorator_prints_help_for_script_entrypoints(
    tmp_path,
    capsys,
    help_arg,
    monkeypatch,
):
    monkeypatch.setattr("sys.argv", ["app.py", help_arg])
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(size: int = 1):
        return size

    with pytest.raises(SystemExit) as excinfo:
        main([help_arg])

    output = capsys.readouterr().out
    assert excinfo.value.code == 0
    assert "[Commands]" in output
    assert "python app.py" in output
    assert "[OPTIONS]" in output
    assert "--multirun" in output
    assert "--size" in output
    assert "fields" in output
    assert "groups" in output
    assert "show [OPTIONS] [HYDRA_OVERRIDES...]" in output
    assert "sweep [OPTIONS] [HYDRA_SWEEPS...]" in output
    assert "Print Hydra multirun" in output
    assert "launch" in output
    assert "[Hydra Overrides]" in output
    assert "--install-completion" not in output
    assert "--show-completion" not in output


def test_hydra_fire_decorator_treats_friendly_comma_values_as_multirun(tmp_path, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("lr: 0.001\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(lr: float = 0.001):
        return lr

    with pytest.raises(SystemExit) as excinfo:
        main(["--lr", "1,2,3"])

    output = capsys.readouterr().out
    assert excinfo.value.code == 0
    assert "lr=1,2,3" in output
    assert "-m" in output


def test_hydra_fire_decorator_reports_raw_comma_values_before_hydra(tmp_path, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("lr: 0.001\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(lr: float = 0.001):
        return lr

    with pytest.raises(SystemExit) as excinfo:
        main(["lr=1,2,3"])

    output = capsys.readouterr().out
    assert excinfo.value.code == 1
    assert "Comma values look like Hydra multirun syntax" in output
    assert "Problem override: lr=1,2,3" in output
    assert "-m" in output
    assert "key=[1,2,3]" in output
    assert "ConfigCompositionException" not in output


def test_hydra_fire_decorator_allows_non_sweepable_string_commas(tmp_path):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("name: default\n")
    cli_config.write_text(
        "\n".join(
            [
                "app:",
                "  name: names",
                "hydra:",
                f"  config_path: {configs}",
                "  config_name: config",
                "fields:",
                "  name:",
                "    path: name",
                "    alias: name",
                "    type: str",
                "    sweepable: false",
                "    visible: true",
                "",
            ]
        )
    )

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(name: str = "default"):
        return name

    assert main(["--name", "Smith, John"]) == "Smith, John"


def test_hydra_fire_decorator_multirun_flag_prints_hydra_overrides(tmp_path, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("lr: 0.001\nsteps: 10\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(lr: float = 0.001, steps: int = 10):
        return lr, steps

    with pytest.raises(SystemExit) as excinfo:
        main(["--multirun", "--lr", "1,2,3", "--steps", "10,20"])

    output = capsys.readouterr().out
    assert excinfo.value.code == 0
    assert "lr=1,2,3" in output
    assert "steps=10,20" in output
    assert "-m" in output


def test_hydra_fire_decorator_sweep_command_prints_hydra_overrides(tmp_path, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("lr: 0.001\nsteps: 10\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(lr: float = 0.001, steps: int = 10):
        return lr, steps

    with pytest.raises(SystemExit) as excinfo:
        main(["sweep", "--lr", "1,2,3", "--steps", "10,20"])

    output = capsys.readouterr().out
    assert excinfo.value.code == 0
    assert "-m lr=1,2,3 steps=10,20" in output


def test_hydra_fire_decorator_allows_hydra_list_syntax_in_single_run(tmp_path):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("values: [1]\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(cfg):
        return list(cfg["values"])

    assert main(["values=[1,2,3]"]) == [1, 2, 3]


def test_hydra_fire_decorator_lists_fields_and_groups(tmp_path, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    groups = configs / "model"
    groups.mkdir(parents=True)
    (configs / "config.yaml").write_text("model: small\nsize: 1\n")
    (groups / "small.yaml").write_text("hidden: 16\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(size: int = 1):
        return size

    with pytest.raises(SystemExit) as fields_exit:
        main(["fields"])
    fields_output = capsys.readouterr().out
    assert fields_exit.value.code == 0
    assert "size" in fields_output

    with pytest.raises(SystemExit) as groups_exit:
        main(["groups"])
    groups_output = capsys.readouterr().out
    assert groups_exit.value.code == 0
    assert "model" in groups_output
    assert "small" in groups_output


def test_hydra_fire_decorator_reports_command_typos_cleanly(tmp_path, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(size: int = 1):
        return size

    with pytest.raises(SystemExit) as excinfo:
        main(["fileds"])

    output = capsys.readouterr().out
    assert excinfo.value.code == 1
    assert "Unknown command" in output
    assert "fields" in output
    assert "Traceback" not in output


def test_hydra_fire_decorator_show_previews_composed_config(tmp_path, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(size: int = 1):
        return size

    with pytest.raises(SystemExit) as excinfo:
        main(["show", "--size", "4"])

    output = capsys.readouterr().out
    assert excinfo.value.code == 0
    assert "size: 4" in output


def test_hydra_fire_decorator_launch_invokes_with_selected_overrides(tmp_path, monkeypatch):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(size: int = 1):
        return size

    from hydra_fire.tui import LaunchResult

    def fake_launch_interactive(*args, **kwargs):
        return LaunchResult(overrides=["size=8"])

    monkeypatch.setattr(app_module, "launch_interactive", fake_launch_interactive)

    assert main(["launch"]) == 8


def test_hydra_fire_decorator_launch_sweep_prints_hydra_command(tmp_path, monkeypatch, capsys):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(size: int = 1):
        return size

    from hydra_fire.tui import LaunchResult

    def fake_launch_interactive(*args, **kwargs):
        return LaunchResult(
            overrides=["size=4,8,16"], sweep_combinations=[["size=4"], ["size=8"], ["size=16"]]
        )

    monkeypatch.setattr(app_module, "launch_interactive", fake_launch_interactive)

    with pytest.raises(SystemExit) as excinfo:
        main(["launch"])

    output = capsys.readouterr().out
    assert excinfo.value.code == 0
    assert "-m" in output
    assert "size=4,8,16" in output
    assert "hydra/launcher" in output


def test_hydra_fire_typed_invocation_supports_nested_double_underscore_params(tmp_path):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text(
        "\n".join(
            [
                "optimizer:",
                "  lr: 0.001",
                "runtime:",
                "  retries: 2",
                "",
            ]
        )
    )

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(optimizer__lr: float, runtime__retries: int = 1):
        return optimizer__lr, runtime__retries

    assert main(["optimizer.lr=0.01"]) == (0.01, 2)


def test_hydra_fire_typed_invocation_reports_missing_required_value(tmp_path):
    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("available: true\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
    )
    def main(required_value: int):
        return required_value

    with pytest.raises(TypeError, match="Missing required config value: required_value"):
        main([])


def test_hydra_fire_schema_mode_invokes_with_pydantic_model(tmp_path):
    class RuntimeConfig(BaseModel):
        verbose: bool = Field(False, description="Verbose output.")

    class TrainConfig(BaseModel):
        batch_size: int = Field(32, description="Training batch size.")
        lr: float = Field(0.001, description="Learning rate.")
        runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text(
        "\n".join(
            [
                "batch_size: 16",
                "lr: 0.001",
                "runtime:",
                "  verbose: false",
                "",
            ]
        )
    )

    seen = {}

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
        schema=TrainConfig,
    )
    def main(cfg: TrainConfig):
        seen["cfg"] = cfg
        return cfg.lr

    # schema fields are advanced by default; use raw Hydra overrides to set them
    assert main(["lr=0.01", "runtime.verbose=true"]) == 0.01
    assert isinstance(seen["cfg"], TrainConfig)
    assert seen["cfg"].batch_size == 16
    assert seen["cfg"].runtime.verbose is True
    spec = load_cli_config(cli_config)
    assert spec.fields["batch_size"].help == "Training batch size."
    assert spec.fields["runtime.verbose"].type == "bool"
    assert spec.fields["batch_size"].level == "advanced"


def test_hydra_fire_schema_mode_surfaces_pydantic_validation_errors(tmp_path):
    class TrainConfig(BaseModel):
        batch_size: int

    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("batch_size: 16\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
        schema=TrainConfig,
    )
    def main(cfg: TrainConfig):
        return cfg

    with pytest.raises(ValidationError):
        main(["batch_size=not-an-int"])


def test_hydra_fire_schema_mode_invokes_with_nested_dataclass(tmp_path):
    @dataclass
    class RuntimeConfig:
        verbose: bool = False

    @dataclass
    class TrainConfig:
        batch_size: int = 32
        lr: float = 0.001
        runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text(
        "\n".join(
            [
                "batch_size: 16",
                "lr: 0.001",
                "seed: 123",
                "runtime:",
                "  verbose: false",
                "",
            ]
        )
    )

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
        schema=TrainConfig,
    )
    def main(cfg: TrainConfig):
        return cfg

    # schema fields are advanced by default; use raw Hydra overrides to set them
    cfg = main(["batch_size=64", "runtime.verbose=true"])

    assert isinstance(cfg, TrainConfig)
    assert cfg.batch_size == 64
    assert cfg.lr == 0.001
    assert isinstance(cfg.runtime, RuntimeConfig)
    assert cfg.runtime.verbose is True
    spec = load_cli_config(cli_config)
    assert spec.fields["runtime.verbose"].type == "bool"


def test_hydra_fire_schema_mode_surfaces_missing_dataclass_required_values(tmp_path):
    @dataclass
    class TrainConfig:
        batch_size: int

    cli_config = tmp_path / "cli.config.yaml"
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("lr: 0.001\n")

    @hydra_fire(
        config_path=str(configs),
        config_name="config",
        cli_config=str(cli_config),
        schema=TrainConfig,
    )
    def main(cfg: TrainConfig):
        return cfg

    with pytest.raises(TypeError, match="Missing required config value: batch_size"):
        main([])
