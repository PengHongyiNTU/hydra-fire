# Hydra-Fire Improvement Plan

## Summary

Hydra-fire should be a smart Hydra launcher, not a full config-tree-to-flags
converter. The current FedGaLore entrypoints now use curated `cli.config.yaml`
files to hide deep internals, but this should become first-class library
behavior.

The ideal launcher has three layers:

1. Curated CLI flags for stable, common knobs.
2. Hydra group selection for recipe/problem/model/method style axes.
3. Raw Hydra overrides with autocomplete, search, validation, and suggestions.

Deep YAML and schema leaves should not automatically become visible flags.

## Current Problem

Auto-discovery currently indexes config YAML leaves and Pydantic schema leaves
as visible options. For a deeply nested training config this produces flags such
as:

```text
--experiment-trainer-training-args-learning-rate
--experiment-method-trainable-target-modules
```

These flags are technically valid but poor UX:

- they bury the important choices under many internal details
- they make help output too long to scan
- they blur public interface and implementation structure
- they make it unclear which values are required
- they introduce generic terminology such as `--preset` even when the app has a
  domain-specific concept such as `recipe`

## Design Principles

- Default to hiding nested fields.
- Expose only explicitly curated fields as friendly flags.
- Keep raw Hydra overrides always available.
- Treat config groups as first-class choices.
- Separate user-facing choices from internal composition groups.
- Show required launch modes explicitly.
- Prefer app vocabulary over generic library vocabulary.
- Make discovery searchable rather than dumping everything in help.

## Proposed Public Model

### Field Levels

Keep the existing levels but change defaults:

| Source | Default level |
|--------|---------------|
| Explicit CLI config field | `common` or configured value |
| Function argument | `common` |
| Top-level simple schema field | `advanced` unless marked |
| Nested schema field | `advanced` |
| YAML-discovered leaf | `advanced` |

Only `core` and `common` show in default help.

### Group Exposure

Groups should have explicit visibility and aliases:

```yaml
groups:
  model-profile:
    target: model_profile
    choices: auto
    visible: true
```

This lets the app expose `--model-profile` while still composing
`model_profile=...`.

### Recipe Instead Of Generic Preset

Hydra-fire can keep `Preset` internally, but the app should decide the public
name:

```yaml
presets:
  public_name: recipe
  source_groups: [recipe, recipes]
```

Help should then show `--recipe`, not `--preset`.

### Required Launch Modes

Support declaring valid run modes:

```yaml
run_modes:
  - name: recipe
    requires: [recipe, output-dir]
  - name: explicit_axes
    requires: [problem, model-profile, output-dir]
    optional: [method]
```

Help should render:

```text
Choose one:
  --recipe ...
  --problem ... --model-profile ... [--method ...]

Required:
  --output-dir
```

### Search And Explain Commands

Add commands:

```bash
app recipes
app groups
app fields --level common
app fields --level advanced --search learning
app explain recipe=mnist_vit_lora
app explain problem=cifar10
app suggest learn-rate
```

`explain` should show:

- selected group or recipe
- resulting Hydra overrides
- affected config paths
- short descriptions if available

### Autocomplete

Autocomplete should cover:

- command names
- curated flags
- group choices
- recipe choices
- raw Hydra override paths
- values for known choice fields

Examples:

```text
--recipe <TAB>              -> recipe names
--model-profile <TAB>       -> vit_base, vit_small, roberta_seq_cls, ...
experiment.trainer.<TAB>    -> matching raw Hydra paths
```

### TUI Layout

The interactive launcher should not show one flat tree first. It should show:

1. Launch mode: recipe or explicit axes
2. Required choices
3. Common knobs
4. Logger/callbacks
5. Federated-only choices when applicable
6. Advanced overrides search
7. Resolved YAML preview
8. Final command preview

## Implementation Steps

1. Add `target` and `alias` support to `ConfigGroup`.
2. Add `choices: auto` support for groups and recipes in explicit CLI configs.
3. Change auto-discovered YAML and nested schema fields to `advanced`.
4. Change help rendering to show only curated groups and `core/common` fields.
5. Add configurable public recipe name instead of hardcoded `--preset`.
6. Add `run_modes` to `ConfigSpec` and render required launch modes in help.
7. Add `recipes`, `explain`, and `suggest` commands.
8. Add shell completion generation for Typer/decorator entrypoints.
9. Update the TUI to use sections instead of a flat config list.
10. Add regression tests with a nested Pydantic schema to prove help does not
    expose deep fields by default.

## Acceptance Tests

Hydra-fire should pass these library-level tests:

- Nested Pydantic fields do not appear in default help unless explicitly marked.
- Explicit `cli.config.yaml` can expose `--output-dir`, `--recipe`, and
  `--model-profile`.
- Raw Hydra overrides still pass through unchanged.
- `choices: auto` discovers config-group choices without manually duplicating
  them in CLI config.
- Public recipe name can be `recipe`, while internal implementation can still
  use `Preset`.
- Unknown flag errors suggest close known flags.
- Unknown group choices suggest close known choices.
- `explain recipe=...` prints overrides and a resolved config preview.
- TUI sections match declared run modes.

## Migration Notes For FedGaLore

FedGaLore currently works around the issue with:

- `conf_local/cli.config.yaml`
- `conf_federated/cli.config.yaml`

Once hydra-fire supports `choices: auto` and public recipe naming, those files
can shrink to just the app-specific policy:

```yaml
presets:
  public_name: recipe
groups:
  recipe:
    target: recipe
    choices: auto
  model-profile:
    target: model_profile
    choices: auto
fields:
  output-dir:
    path: local.output_dir
    level: core
run_modes:
  - name: recipe
    requires: [recipe, output-dir]
  - name: explicit_axes
    requires: [problem, model-profile, output-dir]
```

## Copyable Implementation Prompt

Use this prompt when implementing the hydra-fire changes:

```text
Improve hydra-fire so it behaves like a curated Hydra launcher instead of a
full config-tree-to-flags converter.

Requirements:
- Keep raw Hydra overrides working exactly as before.
- Do not expose nested YAML or Pydantic schema leaves in default help unless the
  app explicitly marks them as core/common fields.
- Add explicit group target/alias support so a flag like --model-profile can map
  to Hydra group model_profile.
- Add choices: auto for explicit CLI config groups, using Hydra config discovery
  to populate choices without manual duplication.
- Replace the hardcoded public --preset concept with configurable public naming,
  so an app can expose --recipe while hydra-fire internally still uses Preset.
- Add run mode metadata so help can show required combinations such as either
  --recipe plus --output-dir, or --problem plus --model-profile plus
  --output-dir.
- Add searchable discovery commands: recipes, explain, suggest, and fields with
  --level and --search filters.
- Update shell completion to complete curated flags, group choices, recipe
  choices, and raw Hydra override paths.
- Update the TUI to show launch mode, required choices, common knobs,
  app-specific sections, advanced override search, resolved YAML preview, and
  final command preview.

Add tests for nested schemas, explicit CLI configs, raw override passthrough,
choice validation, suggestions, and TUI state construction. Preserve backward
compatibility for existing hydra_fire(...) users unless they opt into the new
curated behavior.
```
