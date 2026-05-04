from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from hydra_fire.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_function_signature_example_runs_from_python_entrypoint():
    result = _run_example(
        "function_signature",
        "--batch-size",
        "64",
        "--lr",
        "0.01",
        "--debug",
    )

    assert result == {"batch_size": 64, "lr": 0.01, "debug": True}


def test_pydantic_schema_example_runs_from_python_entrypoint():
    result = _run_example(
        "pydantic_schema",
        "--batch-size",
        "16",
        "--precision",
        "fp16",
        "runtime.verbose=true",
    )

    assert result["batch_size"] == 16
    assert result["precision"] == "fp16"
    assert result["runtime"] == {"verbose": True, "retries": 2}


def test_dataclass_schema_example_runs_from_python_entrypoint():
    result = _run_example(
        "dataclass_schema",
        "--batch-size",
        "24",
        "--precision",
        "fp32",
        "runtime.verbose=true",
    )

    assert result["batch_size"] == 24
    assert result["precision"] == "fp32"
    assert result["runtime"] == {"verbose": True, "retries": 2}


def test_hydra_tree_example_runs_from_python_entrypoint():
    result = _run_example(
        "hydra_tree",
        "--model",
        "large",
        "--optimizer",
        "sgd",
        "trainer.max_steps=50",
    )

    assert result == {
        "model": "large",
        "hidden_size": 512,
        "optimizer": "sgd",
        "lr": 0.1,
        "max_steps": 50,
        "precision": "bf16",
        "seed": 7,
    }


def test_sweep_preview_example_runs_as_normal_decorated_entrypoint():
    result = _run_example(
        "sweep_preview",
        "--optimizer",
        "sgd",
        "--lr",
        "0.2",
        "--steps",
        "50",
    )

    assert result == {
        "optimizer": "sgd",
        "lr": 0.2,
        "max_steps": 50,
        "precision": "bf16",
        "seed": 7,
    }


def test_example_cli_configs_work_with_global_dry_run_and_show():
    runner = CliRunner()
    config = EXAMPLES / "hydra_tree" / "cli.config.yaml"

    dry_run = runner.invoke(
        app,
        ["run", "quick", "--config", str(config), "--steps", "20", "--dry-run"],
    )
    show = runner.invoke(
        app,
        ["show", "quick", "--config", str(config), "--steps", "20"],
    )

    assert dry_run.exit_code == 0
    assert "model=small optimizer=adam trainer.max_steps=10 trainer.max_steps=20" in dry_run.output
    assert show.exit_code == 0
    assert "max_steps: 20" in show.output


def test_sweep_preview_global_cli_preserves_hydra_sweep_syntax():
    runner = CliRunner()
    config = EXAMPLES / "sweep_preview" / "cli.config.yaml"

    result = runner.invoke(
        app,
        [
            "run",
            "default",
            "--config",
            str(config),
            "--optimizer",
            "adam,sgd",
            "--lr",
            "1,2",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "-m optimizer=adam,sgd optimizer.lr=1,2" in result.output


def test_sweep_preview_global_sweep_alias_preserves_hydra_sweep_syntax():
    runner = CliRunner()
    config = EXAMPLES / "sweep_preview" / "cli.config.yaml"

    result = runner.invoke(
        app,
        [
            "sweep",
            "default",
            "--config",
            str(config),
            "--optimizer",
            "adam,sgd",
            "--lr",
            "1,2",
        ],
    )

    assert result.exit_code == 0
    assert "-m optimizer=adam,sgd optimizer.lr=1,2" in result.output


def test_sweep_preview_decorated_cli_comma_values_run_all_combinations():
    example_dir = EXAMPLES / "sweep_preview"
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "app.py",
            "--optimizer",
            "adam,sgd",
            "--lr",
            "1,2",
        ],
        cwd=example_dir,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )

    # All 4 combinations should run (adam×1, adam×2, sgd×1, sgd×2).
    assert "Run 1/4" in completed.stdout
    assert "Run 4/4" in completed.stdout
    assert '"optimizer":"adam"' in completed.stdout
    assert '"optimizer":"sgd"' in completed.stdout


def test_sweep_preview_decorated_sweep_alias_preserves_hydra_sweep_syntax():
    example_dir = EXAMPLES / "sweep_preview"
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "app.py",
            "sweep",
            "--optimizer",
            "adam,sgd",
            "--lr",
            "1,2",
        ],
        cwd=example_dir,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "-m optimizer=adam,sgd optimizer.lr=1,2" in completed.stdout


def _run_example(name: str, *args: str) -> dict[str, object]:
    example_dir = EXAMPLES / name
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
    }
    completed = subprocess.run(
        [sys.executable, "app.py", *args],
        cwd=example_dir,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)
