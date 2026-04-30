# Sweep Syntax Preview Example

This example demonstrates Hydra sweep syntax as comma-separated values with a
normal `@hydra_fire` app.

Hydra remains the owner of sweep execution. In Hydra Fire, `sweep` explicitly
means Hydra multirun syntax: lifted CLI options infer sweep intent from comma
values and translate them into `-m` overrides.

## Single Run

```bash
python app.py --optimizer adam --lr 0.001 --steps 100
```

## Sweep Dry Run

Use comma values on lifted CLI options to check the Hydra multirun override list.
The `sweep` command is the explicit multirun form:

```bash
python app.py --optimizer adam,sgd --lr 1,2,3,4
python app.py sweep --optimizer adam,sgd --lr 1,2,3,4
```

The output preserves Hydra sweep syntax:

```text
-m optimizer=adam,sgd optimizer.lr=1,2,3,4
```

The global preview CLI uses the same policy:

```bash
hydra-fire run default --config cli.config.yaml --optimizer adam,sgd --lr 1,2,3,4 --dry-run
hydra-fire sweep default --config cli.config.yaml --optimizer adam,sgd --lr 1,2,3,4
```

You can also sweep steps:

```bash
python app.py --optimizer adam,sgd --lr 1,2 --steps 50,100
```

Raw Hydra overrides can still use the explicit Hydra-style flag:

```bash
python app.py --multirun optimizer=adam,sgd optimizer.lr=1,2
```
