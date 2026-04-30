from typer.testing import CliRunner

import hydra_fire.generated as generated_module
from hydra_fire.cli import build_app
from hydra_fire.core.spec import ArgumentField, ConfigGroup, ConfigSpec, HydraConfig


def test_generated_app_run_dry_run_expands_arguments():
    spec = ConfigSpec(
        hydra=HydraConfig(config_path="tests/fixtures/configs", config_name="config"),
        fields={"size": ArgumentField(path="job.size", type="int")},
        groups={"job": ConfigGroup(name="job", choices=["baseline"])},
    )
    app = build_app(spec, name="workflow")

    result = CliRunner().invoke(app, ["run", "--job", "baseline", "--size", "16", "--dry-run"])

    assert result.exit_code == 0
    assert "job=baseline" in result.output
    assert "job.size=16" in result.output


def test_generated_app_run_exposes_visible_fields_and_groups_as_options():
    spec = ConfigSpec(
        hydra=HydraConfig(config_path="tests/fixtures/configs", config_name="config"),
        fields={
            "size": ArgumentField(path="job.size", type="int", help="Work item size."),
            "verbose": ArgumentField(path="runtime.verbose", type="bool", help="Verbose output."),
            "hidden": ArgumentField(path="hidden", visible=False),
        },
        groups={"job": ConfigGroup(name="job", choices=["baseline"], help="Job group.")},
    )
    app = build_app(spec, name="workflow")
    runner = CliRunner()

    help_result = runner.invoke(app, ["run", "--help"])
    run_result = runner.invoke(
        app,
        ["run", "--job", "baseline", "--size", "16", "--verbose", "--dry-run"],
    )

    assert help_result.exit_code == 0
    assert "--job" in help_result.output
    assert "--size" in help_result.output
    assert "--verbose" in help_result.output
    assert "--hidden" not in help_result.output
    assert run_result.exit_code == 0
    assert "job=baseline" in run_result.output
    assert "job.size=16" in run_result.output
    assert "runtime.verbose=true" in run_result.output


def test_generated_app_preserves_raw_override_passthrough_with_generated_options():
    spec = ConfigSpec(
        hydra=HydraConfig(config_path="tests/fixtures/configs", config_name="config"),
        fields={"size": ArgumentField(path="job.size", type="int")},
        groups={"job": ConfigGroup(name="job", choices=["baseline"])},
    )
    app = build_app(spec, name="workflow")

    result = CliRunner().invoke(
        app,
        ["run", "--job", "baseline", "--dry-run", "runtime.verbose=true", "--size", "16"],
    )

    assert result.exit_code == 0
    assert "job=baseline job.size=16 runtime.verbose=true" in result.output


def test_generated_app_show_composes_config():
    spec = ConfigSpec(
        hydra=HydraConfig(config_path="tests/fixtures/configs", config_name="config"),
        fields={"size": ArgumentField(path="job.size", type="int")},
        groups={"job": ConfigGroup(name="job", choices=["baseline"])},
    )
    app = build_app(spec, name="workflow")

    result = CliRunner().invoke(app, ["show", "--job", "baseline", "--size", "16"])

    assert result.exit_code == 0
    assert "size: 16" in result.output


def test_generated_app_rejects_invalid_generated_option_choice():
    spec = ConfigSpec(
        hydra=HydraConfig(config_path="tests/fixtures/configs", config_name="config"),
        groups={"job": ConfigGroup(name="job", choices=["baseline"])},
    )
    app = build_app(spec, name="workflow")

    result = CliRunner().invoke(app, ["run", "--job", "missing", "--dry-run"])

    assert result.exit_code == 1
    assert "Invalid value for group" in result.output


def test_generated_app_fields_and_groups_commands():
    spec = ConfigSpec(
        fields={
            "size": ArgumentField(path="job.size", type="int", help="Work item size."),
            "hidden": ArgumentField(path="hidden", visible=False),
        },
        groups={"job": ConfigGroup(name="job", choices=["baseline"], help="Job group.")},
    )
    app = build_app(spec, name="workflow")
    runner = CliRunner()

    fields = runner.invoke(app, ["fields"])
    groups = runner.invoke(app, ["groups"])
    all_fields = runner.invoke(app, ["fields", "--all"])

    assert fields.exit_code == 0
    assert "job.size" in fields.output
    assert "hidden" not in fields.output
    assert groups.exit_code == 0
    assert "baseline" in groups.output
    assert all_fields.exit_code == 0
    assert "hidden" in all_fields.output


def test_generated_app_docs_command():
    spec = ConfigSpec(
        fields={"size": ArgumentField(path="job.size", type="int")},
        groups={"job": ConfigGroup(name="job", choices=["baseline"])},
    )
    app = build_app(spec, name="workflow")

    result = CliRunner().invoke(app, ["docs"])

    assert result.exit_code == 0
    assert "# hydra-fire CLI" in result.output
    assert "job.size" in result.output


def test_generated_app_launch_uses_interactive_launcher(monkeypatch, tmp_path):
    spec = ConfigSpec(
        fields={"size": ArgumentField(path="job.size", type="int")},
        groups={"job": ConfigGroup(name="job", choices=["baseline"])},
    )

    def fake_launch(received_spec, *, console, base_path):
        assert received_spec is spec
        assert console is not None
        assert base_path == tmp_path
        return ["job=baseline", "job.size=16"]

    monkeypatch.setattr(generated_module, "launch_interactive", fake_launch)
    app = build_app(spec, name="workflow", base_path=tmp_path)

    result = CliRunner().invoke(app, ["launch"])

    assert result.exit_code == 0
    assert "job=baseline job.size=16" in result.output
