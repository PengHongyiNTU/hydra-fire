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

## Curated CLI Config

By default, Pydantic and dataclass schema fields are `advanced` and hidden from
help. Only explicitly declared fields appear as friendly flags.

A curated `cli.config.yaml` with `choices: auto`, a public recipe name, and run
modes looks like:

```yaml
app:
  name: myapp
hydra:
  config_path: configs
  config_name: config
presets:
  public_name: recipe          # --recipe instead of --preset
groups:
  recipe:
    target: recipe             # Hydra group path
    choices: auto              # auto-discovered from configs/recipe/
    visible: true
  model-profile:
    target: model_profile      # Hydra group path (underscore)
    alias: model-profile       # CLI flag (kebab-case)
    choices: auto
    visible: true
fields:
  output-dir:
    path: local.output_dir
    alias: output-dir
    type: str
    level: core
run_modes:
  - name: recipe
    requires: [recipe, output-dir]
  - name: explicit_axes
    requires: [problem, model-profile, output-dir]
    optional: [method]
```

This exposes only `--recipe`, `--model-profile`, and `--output-dir` in default
help while keeping all raw Hydra overrides available.

### Group `target` and `alias`

`target` is the Hydra config group path used in overrides. `alias` is the CLI
flag name. If omitted, both are derived from `name`:

```yaml
groups:
  model-profile:
    target: model_profile      # override → model_profile=vit_base
    alias: model-profile       # flag → --model-profile vit_base
    choices: [vit_base, vit_small]
```

### `choices: auto`

Set `choices: auto` to auto-discover choices from the Hydra config directory at
load time. The directory is resolved as
`<base_path>/<hydra.config_path>/<target>`.

### Public recipe name

Add `public_name: recipe` under the `presets:` key to change `--preset` to
`--recipe` in help output and completions.

### Run modes

`run_modes` declares valid launch combinations that appear in `[Launch Modes]`:

```text
[Launch Modes]
  Choose one:
    --recipe --output-dir
    --problem --model-profile --output-dir [--method]
```

## Discovery commands

```bash
hydra-fire recipes --config cli.config.yaml
hydra-fire explain mnist_vit_lora --config cli.config.yaml
hydra-fire explain recipe=mnist_vit_lora --config cli.config.yaml
hydra-fire suggest learn --config cli.config.yaml
hydra-fire fields --level core --config cli.config.yaml
hydra-fire fields --search learning --config cli.config.yaml
hydra-fire completion bash
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
