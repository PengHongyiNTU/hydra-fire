from pathlib import Path

from typer.testing import CliRunner

import hydra_fire.commands as commands_module
from hydra_fire.cli import app

runner = CliRunner()
CONFIG = Path("tests/fixtures/cli.config.yaml")


def test_list_command():
    result = runner.invoke(app, ["list", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "baseline" in result.output


def test_global_cli_reports_command_typos_with_suggestion():
    result = runner.invoke(app, ["fileds", "--config", str(CONFIG)])

    assert result.exit_code == 1
    assert "Unknown command: fileds" in result.output
    assert "fields" in result.output


def test_init_command_generates_cli_config(tmp_path):
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")
    output = tmp_path / "cli.config.yaml"

    result = runner.invoke(
        app,
        [
            "init",
            "--config-path",
            str(configs),
            "--config-name",
            "config",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "Wrote" in result.output


def test_init_command_accepts_colon_target(tmp_path, monkeypatch):
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")
    (tmp_path / "sample_app.py").write_text(
        "\n".join(
            [
                "def workflow(size: int = 1):",
                "    return size",
                "",
            ]
        )
    )
    monkeypatch.syspath_prepend(tmp_path)
    output = tmp_path / "cli.config.yaml"

    result = runner.invoke(
        app,
        [
            "init",
            "--config-path",
            str(configs),
            "--config-name",
            "config",
            "--target",
            "sample_app:workflow",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "Wrote" in result.output
    assert "size" in output.read_text()


def test_init_command_refuses_to_overwrite_without_flag(tmp_path):
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.yaml").write_text("size: 1\n")
    output = tmp_path / "cli.config.yaml"
    output.write_text("app: {}\n")

    result = runner.invoke(
        app,
        [
            "init",
            "--config-path",
            str(configs),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_describe_command():
    result = runner.invoke(app, ["describe", "baseline", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "Work item size" in result.output


def test_fields_command_lists_visible_fields():
    result = runner.invoke(app, ["fields", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "job.size" in result.output
    assert "runtime.verbose" in result.output


def test_groups_command_lists_config_groups():
    result = runner.invoke(app, ["groups", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "job" in result.output
    assert "baseline" in result.output


def test_docs_command_prints_markdown():
    result = runner.invoke(app, ["docs", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "# workflow CLI" in result.output
    assert "## Raw Hydra Overrides" in result.output


def test_docs_command_writes_markdown_file(tmp_path):
    output = tmp_path / "CLI.md"

    result = runner.invoke(
        app,
        ["docs", "--config", str(CONFIG), "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "# workflow CLI" in output.read_text()


def test_launch_command_prints_overrides_from_interactive_launcher(monkeypatch):
    def fake_launch(spec, *, console, base_path):
        assert "baseline" in spec.presets
        assert base_path == CONFIG.parent
        return ["job=baseline", "job.size=16"]

    monkeypatch.setattr(commands_module, "launch_interactive", fake_launch)

    result = runner.invoke(app, ["launch", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "job=baseline job.size=16" in result.output


def test_show_command_expands_aliases_and_composes_config():
    result = runner.invoke(
        app,
        ["show", "baseline", "--size", "16", "--rate", "0.5", "--config", str(CONFIG)],
    )

    assert result.exit_code == 0
    assert "size: 16" in result.output
    assert "rate: 0.5" in result.output


def test_show_command_can_run_without_preset():
    result = runner.invoke(app, ["show", "--size", "16", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "size: 16" in result.output


def test_run_dry_run_prints_expanded_overrides():
    result = runner.invoke(
        app,
        [
            "run",
            "baseline",
            "--size",
            "16",
            "--rate",
            "0.5",
            "--dry-run",
            "--config",
            str(CONFIG),
        ],
    )

    assert result.exit_code == 0
    assert "job=baseline" in result.output
    assert "job.size=16" in result.output
    assert "job.rate=0.5" in result.output


def test_run_dry_run_can_run_without_preset():
    result = runner.invoke(app, ["run", "--size", "16", "--dry-run", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "job.size=16" in result.output


def test_run_dry_run_prints_multirun_overrides_when_values_contain_commas():
    result = runner.invoke(
        app,
        [
            "run",
            "baseline",
            "--size",
            "4,8,16",
            "--dry-run",
            "--config",
            str(CONFIG),
        ],
    )

    assert result.exit_code == 0
    assert "-m job=baseline job.size=4,8,16" in result.output


def test_run_dry_run_does_not_sweep_non_sweepable_comma_value(tmp_path):
    config = tmp_path / "cli.config.yaml"
    config.write_text(
        "\n".join(
            [
                "app:",
                "  name: names",
                "hydra:",
                "  config_path: configs",
                "  config_name: config",
                "fields:",
                "  name:",
                "    path: name",
                "    alias: name",
                "    type: str",
                "    sweepable: false",
                "    visible: true",
                "presets:",
                "  default:",
                "    overrides: []",
                "",
            ]
        )
    )

    result = runner.invoke(
        app,
        ["run", "default", "--config", str(config), "--name", "Smith, John", "--dry-run"],
    )

    assert result.exit_code == 0
    assert "-m" not in result.output
    assert "name='Smith, John'" in result.output


def test_run_without_dry_run_exits_with_not_implemented():
    result = runner.invoke(app, ["run", "baseline", "--config", str(CONFIG)])

    assert result.exit_code == 1
    assert "not implemented" in result.output.lower()


def test_sweep_prints_multirun_overrides():
    result = runner.invoke(
        app,
        [
            "sweep",
            "baseline",
            "--size",
            "4,8,16",
            "--config",
            str(CONFIG),
        ],
    )

    assert result.exit_code == 0
    assert "-m job=baseline job.size=4,8,16" in result.output


def test_recipes_command_lists_presets():
    result = runner.invoke(app, ["recipes", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "baseline" in result.output


def test_fields_command_with_level_filter(tmp_path):
    from hydra_fire.core.config import save_cli_config
    from hydra_fire.core.spec import ArgumentField, ConfigSpec

    spec = ConfigSpec(
        fields={
            "size": ArgumentField(path="job.size", type="int", level="core"),
            "verbose": ArgumentField(path="runtime.verbose", type="bool", level="advanced"),
        }
    )
    config_path = tmp_path / "cli.config.yaml"
    save_cli_config(spec, config_path)

    result = runner.invoke(app, ["fields", "--level", "core", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "size" in result.output
    assert "verbose" not in result.output


def test_fields_command_with_search_filter(tmp_path):
    from hydra_fire.core.config import save_cli_config
    from hydra_fire.core.spec import ArgumentField, ConfigSpec

    spec = ConfigSpec(
        fields={
            "learning-rate": ArgumentField(path="optimizer.lr", help="Learning rate."),
            "epochs": ArgumentField(path="trainer.epochs"),
        }
    )
    config_path = tmp_path / "cli.config.yaml"
    save_cli_config(spec, config_path)

    result = runner.invoke(app, ["fields", "--search", "learn", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "learning-rate" in result.output
    assert "epochs" not in result.output


def test_suggest_command(tmp_path):
    from hydra_fire.core.config import save_cli_config
    from hydra_fire.core.spec import ArgumentField, ConfigSpec

    spec = ConfigSpec(
        fields={
            "output-dir": ArgumentField(path="local.output_dir", level="core"),
        }
    )
    config_path = tmp_path / "cli.config.yaml"
    save_cli_config(spec, config_path)

    result = runner.invoke(app, ["suggest", "outpu", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "output-dir" in result.output


def test_groups_command_shows_target_column():
    result = runner.invoke(app, ["groups", "--config", str(CONFIG)])

    assert result.exit_code == 0
    assert "Target" in result.output
