# Dataclass Schema Example

A dataclass defines the public config contract. Hydra composes the config,
then Hydra Fire validates and converts it into `TrainConfig` before calling
the function.

```python
@dataclass
class TrainConfig:
    batch_size: int = field(default=32, metadata={"help": "Training batch size."})
    lr: float = field(default=0.001, metadata={"help": "Learning rate."})
    precision: Literal["bf16", "fp16", "fp32"] = field(default="bf16", ...)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

@hydra_fire(..., schema=TrainConfig)
def main(cfg: TrainConfig) -> dict:
    return asdict(cfg)
```

## Run

From the project root:

```bash
# Default values
uv run examples/dataclass_schema/app.py

# Override curated fields
uv run examples/dataclass_schema/app.py --batch-size 24 --precision fp32

# Use a raw Hydra override for a debug-level field
uv run examples/dataclass_schema/app.py runtime.verbose=true
```

Expected output is compact JSON:

```json
{"batch_size":24,"lr":0.001,"precision":"fp32","runtime":{"verbose":false,"retries":2}}
```

## Discover

```bash
# Show all commands and options
uv run examples/dataclass_schema/app.py --help

# Table of all config fields (core, common, debug levels)
uv run examples/dataclass_schema/app.py fields

# Config groups (none in this example)
uv run examples/dataclass_schema/app.py groups

# List presets
uv run examples/dataclass_schema/app.py recipes

# Preview composed config without running
uv run examples/dataclass_schema/app.py show --retries 4
```

## Explain

`explain` shows details about any field, preset, or (if present) group:

```bash
# Explain a core field by alias or path
uv run examples/dataclass_schema/app.py explain lr
uv run examples/dataclass_schema/app.py explain --lr      # leading -- is stripped

# Explain a common field with choices
uv run examples/dataclass_schema/app.py explain precision

# Explain a debug field — shows raw Hydra override syntax
uv run examples/dataclass_schema/app.py explain runtime.verbose

# Explain a preset — shows description and overrides
uv run examples/dataclass_schema/app.py explain default

# Fuzzy-find when you can't remember the exact name
uv run examples/dataclass_schema/app.py suggest retri
```

The output for `runtime.verbose` explicitly tells you to use raw syntax:

```
Field: runtime.verbose
  CLI flag : --runtime-verbose
  Type     : bool
  Default  : False
  Level    : debug
  Help     : Enable verbose logging.

This field is debug — use raw Hydra override syntax: runtime.verbose=<value>
```

## Sweep

```bash
uv run examples/dataclass_schema/app.py --batch-size 16,32,64 --lr 0.001,0.01
# Output: -m batch_size=16,32,64 lr=0.001,0.01

uv run examples/dataclass_schema/app.py sweep --batch-size 16,32 --lr 0.001,0.01
```

## Interactive Launcher

```bash
uv run examples/dataclass_schema/app.py launch
```

## Global CLI

```bash
hydra-fire fields --config examples/dataclass_schema/cli.config.yaml
hydra-fire show default --config examples/dataclass_schema/cli.config.yaml --batch-size 16
hydra-fire run default --config examples/dataclass_schema/cli.config.yaml --batch-size 16 --dry-run
```
