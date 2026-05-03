from __future__ import annotations

from typer.testing import CliRunner

from hydra_fire.cli import app, build_app
from hydra_fire.core.spec import ArgumentField, ConfigSpec


def test_global_cli_does_not_advertise_shell_completion():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "--install-completion" not in result.output
    assert "--show-completion" not in result.output


def test_generated_cli_does_not_advertise_shell_completion():
    generated = build_app(
        ConfigSpec(fields={"size": ArgumentField(path="job.size", type="int")}),
        name="workflow",
    )

    result = CliRunner().invoke(generated, ["--help"])

    assert result.exit_code == 0
    assert "--install-completion" not in result.output
    assert "--show-completion" not in result.output


def test_global_cli_has_completion_command():
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "completion" in result.output
