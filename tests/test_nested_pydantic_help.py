"""Regression tests: nested Pydantic/dataclass fields must not appear in default help
unless explicitly marked or placed in a curated CLI config.
"""

from __future__ import annotations

import dataclasses
from io import StringIO

from pydantic import BaseModel, Field

from hydra_fire.core.config import load_cli_config
from hydra_fire.core.spec import (
    ArgumentField,
    ConfigGroup,
    ConfigSpec,
    RunMode,
    is_exposed_field,
)
from hydra_fire.render import render_decorator_help, render_suggest
from hydra_fire.sources.dataclass import spec_from_dataclass
from hydra_fire.sources.pydantic import spec_from_pydantic

# ── Pydantic nested schema ─────────────────────────────────────────────────────


class Inner(BaseModel):
    learning_rate: float = Field(0.001, description="Learning rate.")
    momentum: float = 0.9


class Outer(BaseModel):
    trainer: Inner = Field(default_factory=Inner)
    epochs: int = 10


def test_nested_pydantic_fields_are_advanced_by_default():
    spec = spec_from_pydantic(Outer)
    for name, field in spec.fields.items():
        assert field.level == "advanced", f"field '{name}' should be advanced"


def test_nested_pydantic_fields_not_in_default_help():
    spec = spec_from_pydantic(Outer)
    exposed = [name for name, f in spec.fields.items() if is_exposed_field(f)]
    assert exposed == [], f"No fields should be exposed by default, got: {exposed}"


# ── Dataclass nested schema ────────────────────────────────────────────────────


@dataclasses.dataclass
class InnerDC:
    lr: float = 0.001


@dataclasses.dataclass
class OuterDC:
    trainer: InnerDC = dataclasses.field(default_factory=InnerDC)
    epochs: int = 10


def test_nested_dataclass_fields_are_advanced_by_default():
    spec = spec_from_dataclass(OuterDC)
    for name, field in spec.fields.items():
        assert field.level == "advanced", f"field '{name}' should be advanced"


# ── Explicit CLI config exposes only declared fields ──────────────────────────


def test_explicit_cli_config_exposes_only_declared_fields(tmp_path):
    config_yaml = tmp_path / "cli.config.yaml"
    config_yaml.write_text(
        "\n".join(
            [
                "app:",
                "  name: myapp",
                "hydra:",
                "  config_path: configs",
                "  config_name: config",
                "fields:",
                "  output-dir:",
                "    path: local.output_dir",
                "    alias: output-dir",
                "    type: str",
                "    level: core",
                "groups:",
                "  recipe:",
                "    target: recipe",
                "    choices: [mnist_vit_lora, cifar10_resnet]",
                "",
            ]
        )
    )

    spec = load_cli_config(config_yaml)
    assert "output-dir" in spec.fields
    assert spec.fields["output-dir"].level == "core"
    assert is_exposed_field(spec.fields["output-dir"])
    assert "recipe" in spec.groups
    assert spec.groups["recipe"].hydra_group == "recipe"
    assert spec.groups["recipe"].choices == ["mnist_vit_lora", "cifar10_resnet"]

    # Pydantic nested fields should NOT appear — only the declared fields do
    nested_fields = [k for k in spec.fields if "." in k]
    assert nested_fields == [], (
        f"No nested fields expected in explicit config, got: {nested_fields}"
    )


# ── public_name in preset_config ──────────────────────────────────────────────


def test_explicit_cli_config_public_name(tmp_path):
    config_yaml = tmp_path / "cli.config.yaml"
    config_yaml.write_text(
        "\n".join(
            [
                "hydra:",
                "  config_path: configs",
                "  config_name: config",
                "presets:",
                "  public_name: recipe",
                "  mnist_vit_lora:",
                "    overrides: [recipe=mnist_vit_lora]",
                "",
            ]
        )
    )
    spec = load_cli_config(config_yaml)
    assert spec.preset_config.public_name == "recipe"
    assert "mnist_vit_lora" in spec.presets


# ── run_modes ─────────────────────────────────────────────────────────────────


def test_explicit_cli_config_run_modes(tmp_path):
    config_yaml = tmp_path / "cli.config.yaml"
    config_yaml.write_text(
        "\n".join(
            [
                "hydra:",
                "  config_path: configs",
                "  config_name: config",
                "run_modes:",
                "  - name: recipe",
                "    requires: [recipe, output-dir]",
                "  - name: explicit_axes",
                "    requires: [problem, output-dir]",
                "    optional: [method]",
                "",
            ]
        )
    )
    spec = load_cli_config(config_yaml)
    assert len(spec.run_modes) == 2
    assert spec.run_modes[0].name == "recipe"
    assert spec.run_modes[0].requires == ["recipe", "output-dir"]
    assert spec.run_modes[1].optional == ["method"]


# ── choices: auto ─────────────────────────────────────────────────────────────


def test_choices_auto_resolves_from_hydra_config_dir(tmp_path):
    configs_dir = tmp_path / "configs" / "recipe"
    configs_dir.mkdir(parents=True)
    (configs_dir / "mnist_vit_lora.yaml").write_text("{}\n")
    (configs_dir / "cifar10_resnet.yaml").write_text("{}\n")
    (configs_dir / "_default.yaml").write_text("{}\n")  # private, should be skipped

    config_yaml = tmp_path / "cli.config.yaml"
    config_yaml.write_text(
        "\n".join(
            [
                "hydra:",
                f"  config_path: {tmp_path / 'configs'}",
                "  config_name: config",
                "groups:",
                "  recipe:",
                "    target: recipe",
                "    choices: auto",
                "",
            ]
        )
    )
    spec = load_cli_config(config_yaml)
    assert spec.groups["recipe"].choices == ["cifar10_resnet", "mnist_vit_lora"]


# ── render_decorator_help shows run modes ────────────────────────────────────


def test_render_decorator_help_shows_run_modes():
    spec = ConfigSpec(
        run_modes=[
            RunMode(name="recipe", requires=["recipe", "output-dir"]),
            RunMode(name="explicit_axes", requires=["problem"], optional=["method"]),
        ]
    )
    buf = StringIO()
    from rich.console import Console

    console = Console(file=buf, width=120)
    render_decorator_help(spec, console, prog_name="myapp")
    output = buf.getvalue()
    assert "Launch Modes" in output
    assert "--recipe" in output
    assert "--problem" in output


# ── render_suggest ────────────────────────────────────────────────────────────


def test_render_suggest_finds_close_matches():
    spec = ConfigSpec(
        fields={"output-dir": ArgumentField(path="local.output_dir", level="core")},
        groups={"recipe": ConfigGroup(name="recipe", choices=["mnist"])},
    )
    buf = StringIO()
    from rich.console import Console

    console = Console(file=buf, width=120)
    render_suggest(spec, "recip", console)
    assert "recipe" in buf.getvalue()


def test_render_suggest_no_match_message():
    spec = ConfigSpec()
    buf = StringIO()
    from rich.console import Console

    console = Console(file=buf, width=120)
    render_suggest(spec, "zzzzzzz", console)
    assert "No suggestions" in buf.getvalue()


# ── group target used in overrides ───────────────────────────────────────────


def test_group_with_target_produces_correct_hydra_override():
    from hydra_fire.core.overrides import expand_args

    spec = ConfigSpec(
        groups={
            "model-profile": ConfigGroup(
                name="model-profile",
                target="model_profile",
                choices=["vit_base", "vit_small"],
            )
        }
    )
    overrides = expand_args(["--model-profile", "vit_base"], spec)
    assert overrides == ["model_profile=vit_base"]


# ── raw Hydra overrides pass through unchanged ───────────────────────────────


def test_raw_hydra_overrides_pass_through():
    from hydra_fire.core.overrides import expand_args

    spec = ConfigSpec()
    overrides = expand_args(
        ["experiment.trainer.training_args.learning_rate=0.01", "+new.key=val"],
        spec,
    )
    assert overrides == [
        "experiment.trainer.training_args.learning_rate=0.01",
        "+new.key=val",
    ]
