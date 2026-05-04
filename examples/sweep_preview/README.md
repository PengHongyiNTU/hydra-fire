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

Hydra Fire translates sweep args and prints the Hydra command — it does not
execute sweeps. Copy the printed command and run it with `@hydra.main`.

Comma values on any lifted option print a Hydra multirun instruction panel:

```bash
uv run examples/sweep_preview/app.py --optimizer adam,sgd --lr 1e-4,1e-3
```

```
╭─── Hydra multirun ─────────────────────────────────────────────────╮
│ python app.py -m optimizer=adam,sgd optimizer.lr=1e-4,1e-3          │
│                                                                     │
│ hydra-fire translates your flags — Hydra runs the sweep.            │
│ Requires @hydra.main in your script for full multirun support.      │
│                                                                     │
│ To parallelize or run on a cluster, append a launcher:              │
│   hydra/launcher=joblib     parallel on this machine                │
│   hydra/launcher=submitit   SLURM / cluster                         │
╰─────────────────────────────────────────────────────────────────────╯
```

The `sweep` sub-command prints just the bare `-m` string — useful in scripts:

```bash
uv run examples/sweep_preview/app.py sweep --optimizer adam,sgd --lr 1e-4,1e-3
# -m optimizer=adam,sgd optimizer.lr=1e-4,1e-3

uv run examples/sweep_preview/app.py sweep --optimizer adam,sgd --lr 0.001,0.01 --steps 50,100
# -m optimizer=adam,sgd optimizer.lr=0.001,0.01 trainer.max_steps=50,100
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
