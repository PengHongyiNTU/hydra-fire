# Usage Guide

This guide shows the stable user-facing workflows for Hydra Fire.

## Decorated Script

The main API is `@hydra_fire`:

```python
from hydra_fire import hydra_fire


@hydra_fire(config_path="configs", config_name="config")
def main(batch_size: int = 32, lr: float = 0.001):
    return {"batch_size": batch_size, "lr": lr}


if __name__ == "__main__":
    print(main())
```

Run it:

```bash
python app.py --batch-size 64 --lr 0.01
python app.py --help
python app.py show --batch-size 64
python app.py fields
python app.py groups
python app.py launch
```

## Schema Validation

Pass `schema=` to validate the composed config before invocation.

Pydantic:

```python
from pydantic import BaseModel, Field


class TrainConfig(BaseModel):
    batch_size: int = Field(32, description="Training batch size.")


@hydra_fire(config_path="configs", config_name="config", schema=TrainConfig)
def main(cfg: TrainConfig):
    return cfg
```

Dataclass:

```python
from dataclasses import dataclass, field


@dataclass
class TrainConfig:
    batch_size: int = field(default=32, metadata={"help": "Training batch size."})


@hydra_fire(config_path="configs", config_name="config", schema=TrainConfig)
def main(cfg: TrainConfig):
    return cfg
```

## Hydra Groups

Given:

```text
configs/
  config.yaml
  model/
    small.yaml
    large.yaml
```

Hydra Fire exposes:

```bash
python app.py --model large
```

which translates to:

```text
model=large
```

## Friendly Options And Raw Overrides

Use friendly options for common controls:

```bash
python app.py --batch-size 64 --precision bf16
```

Use raw Hydra syntax for advanced cases:

```bash
python app.py trainer.max_steps=100
python app.py ++trainer.new_value=123
python app.py ~callbacks.tensorboard
```

## Sweep And Multirun

Lifted options support comma shorthand:

```bash
python app.py --lr 1e-4,3e-4,1e-3
```

The explicit command form is:

```bash
python app.py sweep --lr 1e-4,3e-4,1e-3
```

Both print Hydra multirun syntax:

```text
-m optimizer.lr=1e-4,3e-4,1e-3
```

For raw Hydra overrides, use Hydra's multirun flag:

```bash
python app.py --multirun optimizer.lr=1e-4,3e-4,1e-3
```

## Global CLI

Generate a CLI config:

```bash
hydra-fire init --config-path configs --config-name config --target app:main
```

Inspect and preview:

```bash
hydra-fire fields --config cli.config.yaml
hydra-fire groups --config cli.config.yaml
hydra-fire show default --config cli.config.yaml --batch-size 64
hydra-fire run default --config cli.config.yaml --batch-size 64 --dry-run
hydra-fire sweep default --config cli.config.yaml --lr 1e-4,3e-4
```

Launch interactively:

```bash
hydra-fire launch --config cli.config.yaml
```

## GitHub Installation

The first release is distributed from GitHub, not PyPI.

```bash
uv add "hydra-fire @ git+https://github.com/PengHongyiNTU/hydra-fire.git@v0.1.0"
```

or:

```bash
pip install "hydra-fire @ git+https://github.com/PengHongyiNTU/hydra-fire.git@v0.1.0"
```

Use `@master` or omit the tag if you want the latest repository state.
