# Function Signature Example

Hydra Fire reads the function signature and maps friendly CLI flags to Hydra
overrides:

```python
@hydra_fire(config_path="configs", config_name="config")
def main(batch_size: int = 32, lr: float = 0.001, debug: bool = False):
    ...
```

## Run

From the project root:

```bash
# Default values
uv run examples/function_signature/app.py

# Override values
uv run examples/function_signature/app.py --batch-size 64 --lr 0.01 --debug

# Mix friendly flags and raw Hydra overrides
uv run examples/function_signature/app.py --batch-size 128 batch_size=64
```

Expected output is compact JSON:

```json
{"batch_size":64,"lr":0.01,"debug":true}
```

## Discover

```bash
# Show all commands and options
uv run examples/function_signature/app.py --help

# Table of all config fields with type, default, and level
uv run examples/function_signature/app.py fields

# Table of config groups (empty for this example)
uv run examples/function_signature/app.py groups

# Preview the composed config without running the function
uv run examples/function_signature/app.py show --batch-size 64

# Explain a specific field
uv run examples/function_signature/app.py explain lr
uv run examples/function_signature/app.py explain --batch-size

# Fuzzy-find a field name
uv run examples/function_signature/app.py suggest bat
```

## Sweep

Comma-separated values print the Hydra multirun override list:

```bash
uv run examples/function_signature/app.py --batch-size 32,64,128 --lr 0.001,0.01
# Output: -m batch_size=32,64,128 lr=0.001,0.01

uv run examples/function_signature/app.py sweep --batch-size 32,64 --lr 0.001,0.01
# Output: -m batch_size=32,64 lr=0.001,0.01
```

## Interactive Launcher

```bash
uv run examples/function_signature/app.py launch
```

Opens the prompt_toolkit/Rich launcher with Tab completion, override preview,
and composed config preview before confirmation.

## Global CLI

```bash
hydra-fire fields --config examples/function_signature/cli.config.yaml
hydra-fire show default --config examples/function_signature/cli.config.yaml --batch-size 64
hydra-fire run default --config examples/function_signature/cli.config.yaml --batch-size 64 --dry-run
hydra-fire sweep default --config examples/function_signature/cli.config.yaml --batch-size 32,64
```
