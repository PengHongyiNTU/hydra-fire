# Design

Hydra Fire is a translator and UX layer over Hydra.

It does not replace Hydra config composition. It creates a friendlier public CLI
surface, then translates user input back into Hydra overrides.

## Pipeline

```text
source metadata
  -> ConfigSpec
  -> cli.config.yaml
  -> CLI or launcher
  -> Hydra overrides
  -> Hydra composition
  -> function invocation or preview
```

Sources can be:

- function signatures
- Pydantic models
- dataclasses
- Hydra config folders
- an edited `cli.config.yaml`

## ConfigSpec

`ConfigSpec` is the normalized internal model. It contains:

- app metadata
- Hydra config path/name
- argument fields
- Hydra config groups
- presets

Every frontend uses the same spec and override translation layer.

## Visibility Policy

Hydra configs can be large and dynamic. Hydra Fire therefore separates discovery
from normal help output:

- `core` and `common` fields become normal `--options`.
- advanced fields remain discoverable through `fields`, docs, launcher search,
  and raw Hydra path completion.
- raw Hydra overrides always remain available.

This keeps `--help` readable without hiding the full Hydra surface.

## Hydra Discovery Limits

Hydra config trees can be dynamic. Discovery is best-effort and intended to
produce a useful CLI surface, not a perfect static model of every possible
composition.

- Config group choices are discovered from YAML files in group folders.
- Displayed group defaults come from discovered choices or edited
  `cli.config.yaml`; if this differs from Hydra's `defaults:` tree, edit the CLI
  config to make the user-facing default explicit.
- Nested field defaults are sampled from discovered YAML files. If multiple
  group options define the same key, the generated value is documentation, not a
  replacement for Hydra composition.
- Presets are discovered from convention folders when they contain defaults,
  overrides, or top-level config values. Empty metadata-only presets should be
  written directly in `cli.config.yaml`.

## Sweep Policy

Hydra owns multirun semantics. Hydra Fire only translates friendly input into
Hydra multirun syntax.

Supported forms:

```bash
python app.py --lr 1e-4,3e-4
python app.py sweep --lr 1e-4,3e-4
python app.py --multirun optimizer.lr=1e-4,3e-4
```

All produce:

```text
-m optimizer.lr=1e-4,3e-4
```

Hydra Fire does not execute the sweep grid itself.

## Stable Public Surfaces

- `from hydra_fire import hydra_fire`
- `@hydra_fire(config_path=..., config_name=..., schema=...)`
- `cli.config.yaml`
- script commands: `help`, `fields`, `groups`, `show`, `sweep`, `launch`
- global commands: `init`, `fields`, `groups`, `show`, `run`, `sweep`, `launch`,
  `docs`

## Deferred Scope

The following are intentionally out of scope for v1:

- full Textual TUI
- shell-side completion for arbitrary raw Hydra paths
- custom sweep execution
- arbitrary target execution from global `hydra-fire run`
- inference of named presets from every possible Hydra defaults-tree
  combination
