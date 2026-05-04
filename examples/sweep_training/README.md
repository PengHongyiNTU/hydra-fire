# Sweep Training Example

A simulated training loop that shows how to sweep across model architectures,
optimizers, and learning rates. Progress is shown with a tqdm bar. The sweep
command prints the Hydra multirun override list so you can hand it to a Hydra
launcher.

## Config layout

```
configs/
  config.yaml          # trainer.epochs, trainer.seed, trainer.step_sleep
  model/
    small.yaml         # hidden_size=128, num_layers=2
    large.yaml         # hidden_size=512, num_layers=6
  optimizer/
    adam.yaml          # lr=0.001, weight_decay=0.0
    sgd.yaml           # lr=0.01, momentum=0.9
```

## Single run

```bash
# Defaults: small model, adam, 5 epochs
uv run examples/sweep_training/app.py

# Select architecture and optimizer
uv run examples/sweep_training/app.py --model large --optimizer sgd

# Override learning rate and epoch count
uv run examples/sweep_training/app.py --model large --lr 0.01 --epochs 10

# Fast smoke test (no sleep, 2 epochs)
uv run examples/sweep_training/app.py model=small optimizer=adam trainer.epochs=2 trainer.step_sleep=0
```

tqdm prints a live progress bar per epoch:

```
large+sgd  lr=0.01: 100%|████████| 10/10 [00:00<00:00, loss=0.7431, acc=0.714]
```

The function returns compact JSON:

```json
{
  "model": "large",
  "hidden_size": 512,
  "optimizer": "sgd",
  "lr": 0.01,
  "epochs": 10,
  "final_loss": 0.7431,
  "final_acc": 0.714
}
```

## Sweep preview

Comma-separated values on any lifted option print the Hydra multirun override list:

```bash
# Two models × two learning rates = 4 runs
uv run examples/sweep_training/app.py --model small,large --lr 0.001,0.01
# Output: -m model=small,large optimizer.lr=0.001,0.01

# All four optimizer × lr combinations
uv run examples/sweep_training/app.py --optimizer adam,sgd --lr 0.001,0.01,0.1
# Output: -m optimizer=adam,sgd optimizer.lr=0.001,0.01,0.1

# Explicit sweep command (equivalent):
uv run examples/sweep_training/app.py sweep --model small,large --optimizer adam,sgd
# Output: -m model=small,large optimizer=adam,sgd
```

Pass the output to Hydra's multirun launcher to actually execute the sweep:

```bash
# Hydra multirun: runs each combination as a separate process
python -m your_app --multirun model=small,large optimizer.lr=0.001,0.01
```

## Discover

```bash
# All commands and curated options
uv run examples/sweep_training/app.py --help

# Fields table — shows lr, epochs, seed (core/common), step_sleep (debug)
uv run examples/sweep_training/app.py fields

# Groups table — model and optimizer with their choices
uv run examples/sweep_training/app.py groups

# Named presets
uv run examples/sweep_training/app.py recipes

# Preview the composed config before running
uv run examples/sweep_training/app.py show --model large --optimizer sgd
uv run examples/sweep_training/app.py show model=large optimizer=sgd optimizer.lr=0.01
```

## Explain

```bash
# Explain a group (shows choices and CLI usage)
uv run examples/sweep_training/app.py explain model
uv run examples/sweep_training/app.py explain optimizer

# Explain a group choice (resolves and prints full composed config)
uv run examples/sweep_training/app.py explain model=large
uv run examples/sweep_training/app.py explain optimizer=sgd

# Explain a field
uv run examples/sweep_training/app.py explain lr
uv run examples/sweep_training/app.py explain epochs

# Explain a debug-level field (shows raw Hydra syntax)
uv run examples/sweep_training/app.py explain step_sleep

# Explain a preset
uv run examples/sweep_training/app.py explain quick

# Fuzzy search
uv run examples/sweep_training/app.py suggest ep
uv run examples/sweep_training/app.py suggest opt
```

## Interactive launcher

```bash
uv run examples/sweep_training/app.py launch
```

In the launcher, type discovery commands to inspect the config before committing
to a run — the prompt loops back after each command:

```
sweep-training › explain model=large      # prints resolved config, re-prompts
sweep-training › fields                   # prints field table, re-prompts
sweep-training › --model large --lr 0.01  # ready to run — shows preview + confirm
```

Tab completes commands, option names, group choices, and field aliases.

## Global CLI

```bash
hydra-fire fields --config examples/sweep_training/cli.config.yaml
hydra-fire groups --config examples/sweep_training/cli.config.yaml
hydra-fire explain model=large --config examples/sweep_training/cli.config.yaml
hydra-fire show default --config examples/sweep_training/cli.config.yaml --model large --lr 0.01
hydra-fire sweep default --config examples/sweep_training/cli.config.yaml --model small,large --lr 0.001,0.01
```
