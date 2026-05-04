# Hydra Fire Examples

Each example has its own Hydra config folder, `cli.config.yaml`, Python
entrypoint, and README. All examples can be run from the repository root.

## Examples

| Example | Demonstrates |
| --- | --- |
| [function_signature](function_signature/README.md) | Typed Python function introspection — flags derived directly from the signature. |
| [pydantic_schema](pydantic_schema/README.md) | Pydantic validation, field docs, choices, nested fields. |
| [dataclass_schema](dataclass_schema/README.md) | Dataclass schema validation, nested config, debug-level fields. |
| [hydra_tree](hydra_tree/README.md) | Existing Hydra config tree — groups, curated fields, presets. |
| [sweep_preview](sweep_preview/README.md) | Hydra multirun translation via comma values and the `sweep` command. |
| [sweep_training](sweep_training/README.md) | Full sweep example — multiple model/optimizer configs, tqdm progress, live metrics. |

## Quick Start

```bash
# Run with defaults
uv run examples/function_signature/app.py
uv run examples/dataclass_schema/app.py
uv run examples/hydra_tree/app.py

# Show help (commands, options, examples)
uv run examples/hydra_tree/app.py --help

# Inspect available fields and groups
uv run examples/hydra_tree/app.py fields
uv run examples/hydra_tree/app.py groups

# Explain a field, group, group choice, or preset
uv run examples/hydra_tree/app.py explain model
uv run examples/hydra_tree/app.py explain model=large
uv run examples/hydra_tree/app.py explain quick
uv run examples/dataclass_schema/app.py explain runtime.verbose

# Fuzzy-find a name
uv run examples/hydra_tree/app.py suggest opt

# Preview sweep overrides
uv run examples/sweep_preview/app.py sweep --optimizer adam,sgd --lr 0.001,0.01

# Open the interactive launcher
uv run examples/hydra_tree/app.py launch
```

## Global CLI

The `hydra-fire` command works with any `cli.config.yaml`:

```bash
hydra-fire fields --config examples/hydra_tree/cli.config.yaml
hydra-fire groups --config examples/hydra_tree/cli.config.yaml
hydra-fire show quick --config examples/hydra_tree/cli.config.yaml --steps 20
hydra-fire run quick --config examples/hydra_tree/cli.config.yaml --steps 20 --dry-run
hydra-fire sweep default --config examples/hydra_tree/cli.config.yaml --model small,large
hydra-fire launch --config examples/hydra_tree/cli.config.yaml
```
