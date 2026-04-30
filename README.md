# Hydra Fire

Hydra Fire builds friendly, schema-aware CLIs for Hydra-backed Python programs.

It is a thin UX layer over Hydra:

```text
Python function / Pydantic model / dataclass / Hydra config tree
  -> introspection and Hydra discovery
  -> ConfigSpec
  -> editable cli.config.yaml
  -> script CLI, global preview CLI, or interactive launcher
  -> Hydra override list
  -> Hydra composition
  -> function invocation or preview output
```

Hydra remains the backend for config groups, defaults, composition, raw override
syntax, and multirun semantics. Hydra Fire makes the common path easier to type,
document, inspect, and launch.

## Motivation

This project comes from running a lot of experiments and repeatedly losing track
of which arguments matter, which presets exist, and how a particular run was
configured. Hydra is powerful, but if you do not use it every day, nested
override syntax, config groups, defaults, and multirun commands can be hard to
remember in the middle of experimentation.

Hydra Fire is meant to keep Hydra's power while making the interface feel closer
to a normal CLI: visible options for common controls, searchable config fields,
clear previews, and an interactive launcher when the command gets too long.

## Status

Hydra Fire is pre-release software. The current codebase is suitable for source
installation from GitHub and local project trials. Publish to PyPI after final
API naming review and release notes are complete.

## Install

From a local checkout:

```bash
uv sync
```

Use directly from GitHub before PyPI publication:

```bash
uv add "hydra-fire @ git+https://github.com/PengHongyiNTU/hydra-fire.git"
```

or:

```bash
pip install "hydra-fire @ git+https://github.com/PengHongyiNTU/hydra-fire.git"
```

## Quickstart

Create a normal Python entrypoint:

```python
from hydra_fire import hydra_fire


@hydra_fire(config_path="configs", config_name="config")
def main(batch_size: int = 32, lr: float = 1e-3, debug: bool = False):
    return {"batch_size": batch_size, "lr": lr, "debug": debug}


if __name__ == "__main__":
    print(main())
```

Run it like a normal CLI:

```bash
python app.py --batch-size 64 --lr 0.01 --debug
python app.py --help
python app.py show --batch-size 64
python app.py fields
python app.py launch
```

Friendly options are translated to Hydra overrides, then Hydra composes the
config and Hydra Fire invokes the function.

## Core Usage

### Config Object Mode

Use this when your function wants the full composed Hydra config:

```python
from omegaconf import DictConfig
from hydra_fire import hydra_fire


@hydra_fire(config_path="configs", config_name="config")
def main(cfg: DictConfig):
    train(cfg)
```

### Typed Function Mode

Use this when a small set of arguments is the public CLI surface:

```python
@hydra_fire(config_path="configs", config_name="config")
def main(batch_size: int = 32, lr: float = 1e-3):
    train(batch_size=batch_size, lr=lr)
```

### Pydantic Schema Mode

Use this when you want validation and field documentation from a schema:

```python
from typing import Literal

from pydantic import BaseModel, Field
from hydra_fire import hydra_fire


class TrainConfig(BaseModel):
    batch_size: int = Field(32, description="Training batch size.")
    precision: Literal["bf16", "fp16", "fp32"] = "bf16"


@hydra_fire(config_path="configs", config_name="config", schema=TrainConfig)
def main(cfg: TrainConfig):
    train(cfg)
```

### Dataclass Schema Mode

```python
from dataclasses import dataclass, field
from typing import Literal

from hydra_fire import hydra_fire


@dataclass
class TrainConfig:
    batch_size: int = field(default=32, metadata={"help": "Training batch size."})
    precision: Literal["bf16", "fp16", "fp32"] = "bf16"


@hydra_fire(config_path="configs", config_name="config", schema=TrainConfig)
def main(cfg: TrainConfig):
    train(cfg)
```

## Hydra Config Groups

Hydra Fire scans config folders and exposes Hydra config groups as normal CLI
choices:

```text
configs/
  config.yaml
  model/
    small.yaml
    large.yaml
  optimizer/
    adam.yaml
    sgd.yaml
```

```bash
python app.py --model small --optimizer adam
```

becomes:

```text
model=small optimizer=adam
```

Grouped Hydra semantics remain intact. Hydra Fire does not flatten Hydra into a
new config system.

## Nested Fields And Raw Hydra Overrides

Curated fields can be exposed as friendly options:

```bash
python app.py --precision bf16 --steps 100
```

Advanced or uncommon fields remain available through raw Hydra syntax:

```bash
python app.py trainer.precision=bf16
python app.py ++trainer.new_value=123
python app.py ~callbacks.tensorboard
```

Normal `--help` shows the curated CLI surface. Use `fields`, `groups`, generated
docs, or the launcher to discover the larger config surface.

## Sweep And Multirun

In Hydra Fire, `sweep` explicitly means Hydra multirun translation.

Lifted CLI options support comma shorthand:

```bash
python app.py --lr 1e-4,3e-4,1e-3
```

Output:

```text
-m optimizer.lr=1e-4,3e-4,1e-3
```

The explicit command form is equivalent and more readable in scripts:

```bash
python app.py sweep --lr 1e-4,3e-4,1e-3
```

Raw Hydra overrides can use Hydra's explicit multirun flag:

```bash
python app.py --multirun optimizer.lr=1e-4,3e-4,1e-3
python app.py -m optimizer.lr=1e-4,3e-4,1e-3
```

Hydra Fire does not execute sweeps itself. It prints the Hydra multirun override
list so Hydra-owned launchers or callers can execute the multirun.

## Global CLI

The installed `hydra-fire` command works with `cli.config.yaml`:

```bash
hydra-fire init --config-path configs --config-name config --target app:main
hydra-fire fields --config cli.config.yaml
hydra-fire groups --config cli.config.yaml
hydra-fire show default --config cli.config.yaml --lr 0.001
hydra-fire run default --config cli.config.yaml --lr 0.001 --dry-run
hydra-fire sweep default --config cli.config.yaml --lr 1e-4,3e-4
hydra-fire launch --config cli.config.yaml
```

For v1, global `run` is preview-oriented. Function execution belongs to
decorated Python entrypoints.

## Interactive Launcher

`python app.py launch` and `hydra-fire launch --config cli.config.yaml` open a
prompt_toolkit/Rich launcher. It provides:

- normal CLI-line input
- completion for lifted options, groups, choices, presets, and Hydra paths
- override preview
- composed-config preview
- confirmation before invocation

The launcher and non-interactive CLI use the same override translation layer.

## CLI Config

`cli.config.yaml` is the editable user-facing contract. It controls aliases,
visibility, choices, docs, groups, and presets while Hydra remains responsible
for composition.

See [docs/CLI_CONFIG.md](docs/CLI_CONFIG.md) for the full reference.

## Examples

See [examples/](examples/README.md):

- function signature CLI
- Pydantic schema CLI
- dataclass schema CLI
- Hydra config tree discovery
- sweep/multirun translation

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Design](docs/DESIGN.md)
- [CLI Config Reference](docs/CLI_CONFIG.md)

## Development

```bash
uv sync
uv run pytest
uv run mypy src/hydra_fire
uv run ruff check .
uv build
```

The package includes `py.typed` and is intended to be usable from typed Python
projects.
