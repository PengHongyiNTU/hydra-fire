# CLI Config Reference

`cli.config.yaml` is Hydra Fire's editable UX layer. Hydra remains the backend for
composition; this file controls how Hydra groups, nested fields, schema fields,
aliases, and presets are exposed to users.

Runnable examples are available in `examples/`:

- `examples/function_signature`
- `examples/pydantic_schema`
- `examples/dataclass_schema`
- `examples/hydra_tree`
- `examples/sweep_preview`

The usual generation flow is:

```bash
hydra-fire init --config-path configs --config-name config --target app:main
```

For schema-first programs, the decorator can also generate the file when it first
runs:

```python
from hydra_fire import hydra_fire

@hydra_fire(config_path="configs", config_name="config", schema=TrainConfig)
def main(cfg: TrainConfig):
    ...
```

## Complete Example

```yaml
app:
  name: train
  description: Training CLI for local and remote runs.

hydra:
  config_path: configs
  config_name: config

fields:
  trainer.batch_size:
    path: trainer.batch_size
    alias: batch-size
    type: int
    default: 32
    required: false
    help: Training batch size.
    level: core
    choices: null
    sweepable: true
    visible: true

  optimizer.lr:
    path: optimizer.lr
    alias: lr
    type: float
    default: 0.001
    required: false
    help: Learning rate.
    level: core
    choices: null
    sweepable: true
    visible: true

  trainer.precision:
    path: trainer.precision
    alias: precision
    type: str
    default: bf16
    required: false
    help: Numeric precision.
    level: common
    choices:
      - bf16
      - fp16
      - fp32
    sweepable: true
    visible: true

  runtime.verbose:
    path: runtime.verbose
    alias: verbose
    type: bool
    default: false
    required: false
    help: Enable verbose logging.
    level: debug
    choices: null
    sweepable: false
    visible: true

  callbacks.tensorboard.log_dir:
    path: callbacks.tensorboard.log_dir
    alias: tensorboard-log-dir
    type: path
    default: null
    required: false
    help: TensorBoard log directory.
    level: advanced
    choices: null
    sweepable: false
    visible: false

groups:
  model:
    name: model
    choices:
      - small
      - large
    default: small
    help: Model config group.
    visible: true

  optimizer:
    name: optimizer
    choices:
      - adam
      - sgd
    default: adam
    help: Optimizer config group.
    visible: true

presets:
  quick-test:
    description: Fast local smoke test.
    overrides:
      - model=small
      - optimizer=adam
      - trainer.max_steps=100
    aliases:
      bs: trainer.batch_size
      lr: optimizer.lr
    examples:
      - train run quick-test --bs 16 --lr 0.0003 --dry-run
```

## Sections

### `app`

Controls generated CLI identity:

- `name`: displayed in generated docs and used as the generated app name.
- `description`: displayed in help and Markdown docs.

### `hydra`

Controls Hydra composition:

- `config_path`: path to the Hydra config folder.
- `config_name`: root config name passed to Hydra Compose.

Hydra Fire does not replace Hydra defaults or config groups. It translates user
choices into Hydra overrides, then calls Hydra Compose.

### `fields`

Fields expose nested config values or schema attributes as friendly arguments.

Important keys:

- `path`: Hydra override path, such as `trainer.batch_size`.
- `alias`: short or shell-friendly name, such as `bs` or `batch-size`.
- `type`: one of `str`, `int`, `float`, `bool`, `path`, or `json`.
- `default`: documented default value.
- `required`: whether the source schema marks this field as required.
- `help`: human-readable documentation.
- `level`: `core`, `common`, `advanced`, `debug`, or `raw`.
- `choices`: allowed values, usually from `Literal`, enums, or manual config.
- `sweepable`: whether comma values are allowed when dry-run output is converted to Hydra multirun syntax.
- `visible`: whether generated CLI help shows this as a normal option.

Enum choices are generated from enum values, not enum member names. For example,
an enum member `ACTIVE = 1` becomes the CLI choice `1`.

Example user inputs:

```bash
train run --batch-size 64 --precision bf16 --dry-run
train sweep --batch-size 32,64 --precision bf16,fp16
train run trainer.batch_size=64 trainer.precision=bf16 --dry-run
train run ++trainer.new_value=123 --dry-run
```

All three forms are translated into Hydra override strings.

### `groups`

Groups expose Hydra config groups as choices.

Hydra folder:

```text
configs/
  config.yaml
  model/
    small.yaml
    large.yaml
```

CLI config:

```yaml
groups:
  model:
    name: model
    choices: [small, large]
    default: small
    help: Model config group.
    visible: true
```

User input:

```bash
train run --model large --dry-run
```

Hydra override:

```text
model=large
```

### `presets`

Presets are named recipes that prepend one or more overrides.

```yaml
presets:
  debug-small:
    overrides:
      - model=small
      - trainer.max_steps=10
    aliases:
      bs: trainer.batch_size
```

User input:

```bash
hydra-fire run debug-small --bs 8 --dry-run
```

Hydra override list:

```text
model=small trainer.max_steps=10 trainer.batch_size=8
```

Hydra Fire also discovers presets from convention folders under the Hydra config
root:

```text
configs/
  presets/
    quick-test.yaml
  recipes/
    local-debug.yaml
  experiments/
    ablation.yaml
```

A discovered preset can use explicit overrides:

```yaml
description: Fast local smoke test.
overrides:
  - model=small
  - trainer.max_steps=100
aliases:
  bs: trainer.batch_size
examples:
  - train run quick-test --bs 16 --dry-run
```

It can also use Hydra-style defaults, which are converted to group overrides:

```yaml
defaults:
  - model: small
  - optimizer/adam
trainer:
  max_steps: 100
```

Generated override list:

```text
model=small optimizer=adam trainer.max_steps=100
```

## Source Mapping

Hydra Fire can merge multiple sources into one `ConfigSpec` before writing
`cli.config.yaml`.

Function signature:

```python
def main(batch_size: int = 32, lr: float = 0.001):
    ...
```

Generated fields:

```yaml
fields:
  batch_size:
    path: batch_size
    alias: batch-size
    type: int
    default: 32
  lr:
    path: lr
    alias: lr
    type: float
    default: 0.001
```

Pydantic schema:

```python
class TrainConfig(BaseModel):
    batch_size: int = Field(32, description="Training batch size.")
    precision: Literal["bf16", "fp16", "fp32"] = "bf16"
```

Generated fields include descriptions and choices.

Dataclass schema:

```python
@dataclass
class TrainConfig:
    batch_size: int = 32
    precision: Literal["bf16", "fp16", "fp32"] = "bf16"
```

Generated fields use type hints, defaults, nested dataclasses, and field metadata.

Hydra folders add config groups and discovered nested fields. The editable config
file decides which discovered items are visible in normal CLI help.

## Runtime Behavior

Decorated script mode:

```bash
python app.py --model small --batch-size 64 trainer.max_steps=100
python app.py show --model small --batch-size 64
python app.py sweep --batch-size 32,64
```

Global command mode:

```bash
hydra-fire run quick-test --config cli.config.yaml --batch-size 64 --dry-run
hydra-fire sweep quick-test --config cli.config.yaml --batch-size 32,64
```

Interactive mode:

```bash
hydra-fire launch --config cli.config.yaml
```

All modes produce the same kind of Hydra override list, then Hydra performs
composition.

`sweep` means Hydra multirun translation. It emits a `-m ...` override list and
does not execute a custom sweep engine.
