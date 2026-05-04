# Sweep Syntax Preview Example

Hydra Fire translates friendly CLI comma values into Hydra multirun (`-m`)
override lists. Hydra remains the owner of sweep execution — Hydra Fire only
prints the override list for you to inspect before running.

## Single Run

```bash
uv run examples/sweep_preview/app.py --optimizer adam --lr 0.001 --steps 100
```

Expected output:

```json
{"optimizer":"adam","lr":0.001,"max_steps":100,"precision":"bf16","seed":7}
```

## Sweep Preview

Comma values on any lifted option trigger multirun translation:

```bash
uv run examples/sweep_preview/app.py --optimizer adam,sgd --lr 1e-4,1e-3
# Output: -m optimizer=adam,sgd optimizer.lr=1e-4,1e-3
```

The explicit `sweep` command is equivalent and clearer in scripts:

```bash
uv run examples/sweep_preview/app.py sweep --optimizer adam,sgd --lr 1e-4,1e-3
# Output: -m optimizer=adam,sgd optimizer.lr=1e-4,1e-3
```

Sweep multiple axes together:

```bash
uv run examples/sweep_preview/app.py sweep --optimizer adam,sgd --lr 0.001,0.01 --steps 50,100
# Output: -m optimizer=adam,sgd optimizer.lr=0.001,0.01 trainer.max_steps=50,100
```

Raw Hydra multirun syntax also works:

```bash
uv run examples/sweep_preview/app.py --multirun optimizer=adam,sgd optimizer.lr=1e-4,1e-3
```

## Discover

```bash
# Full help
uv run examples/sweep_preview/app.py --help

# All config fields
uv run examples/sweep_preview/app.py fields

# Config groups with choices
uv run examples/sweep_preview/app.py groups

# Preview composed config
uv run examples/sweep_preview/app.py show --optimizer sgd --steps 50
```

## Explain

```bash
# Explain a group — shows choices and usage
uv run examples/sweep_preview/app.py explain optimizer

# Explain a specific group choice — resolves full composed config
uv run examples/sweep_preview/app.py explain optimizer=sgd

# Explain a field
uv run examples/sweep_preview/app.py explain steps
uv run examples/sweep_preview/app.py explain lr

# Fuzzy search
uv run examples/sweep_preview/app.py suggest opt
```

## Interactive Launcher

```bash
uv run examples/sweep_preview/app.py launch
```

## Global CLI

```bash
hydra-fire fields --config examples/sweep_preview/cli.config.yaml
hydra-fire show default --config examples/sweep_preview/cli.config.yaml --optimizer sgd
hydra-fire run default --config examples/sweep_preview/cli.config.yaml --optimizer adam,sgd --lr 0.001,0.01 --dry-run
hydra-fire sweep default --config examples/sweep_preview/cli.config.yaml --optimizer adam,sgd --lr 0.001,0.01
```
