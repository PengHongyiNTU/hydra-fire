# Hydra Config Tree Example

Hydra Fire wraps an existing Hydra config tree. The function receives the
composed `DictConfig` object directly. Hydra Fire discovers:

- config groups: `model` (small/large) and `optimizer` (adam/sgd)
- curated fields: `trainer.max_steps` exposed as `--steps`, `trainer.precision`
- a `quick` preset that locks model, optimizer, and step count for smoke tests

## Run

From the project root:

```bash
# Default config
uv run examples/hydra_tree/app.py

# Select a group choice and override a field
uv run examples/hydra_tree/app.py --model large --optimizer sgd trainer.max_steps=50

# Override curated fields directly
uv run examples/hydra_tree/app.py --precision fp16 --steps 25
```

Expected output is compact JSON:

```json
{"model":"large","hidden_size":512,"optimizer":"sgd","lr":0.1,"max_steps":50,"precision":"bf16","seed":7}
```

## Discover

```bash
# Full help with options, groups, and examples
uv run examples/hydra_tree/app.py --help

# Table of curated fields
uv run examples/hydra_tree/app.py fields

# Table of config groups with choices
uv run examples/hydra_tree/app.py groups

# List presets
uv run examples/hydra_tree/app.py recipes

# Preview the composed config without running
uv run examples/hydra_tree/app.py show --model large
uv run examples/hydra_tree/app.py show --model small --optimizer sgd --steps 50
```

## Explain

```bash
# Explain a group — shows choices and CLI usage
uv run examples/hydra_tree/app.py explain model

# Explain a specific group choice — resolves and prints the full composed config
uv run examples/hydra_tree/app.py explain model=large
uv run examples/hydra_tree/app.py explain optimizer=sgd

# Explain a curated field
uv run examples/hydra_tree/app.py explain steps
uv run examples/hydra_tree/app.py explain --steps

# Explain a preset
uv run examples/hydra_tree/app.py explain quick

# Fuzzy search
uv run examples/hydra_tree/app.py suggest opt
```

`explain model=large` resolves and prints the entire composed config so you
can see exactly what Hydra produces for that choice before you commit to it.

## Sweep

```bash
uv run examples/hydra_tree/app.py --model small,large --steps 50,100
# Output: -m model=small,large trainer.max_steps=50,100

uv run examples/hydra_tree/app.py sweep --model small,large --optimizer adam,sgd
```

## Interactive Launcher

```bash
uv run examples/hydra_tree/app.py launch
```

## Global CLI

```bash
hydra-fire fields --config examples/hydra_tree/cli.config.yaml
hydra-fire groups --config examples/hydra_tree/cli.config.yaml
hydra-fire show quick --config examples/hydra_tree/cli.config.yaml --steps 20
hydra-fire run quick --config examples/hydra_tree/cli.config.yaml --steps 20 --dry-run
hydra-fire sweep default --config examples/hydra_tree/cli.config.yaml --model small,large
```
