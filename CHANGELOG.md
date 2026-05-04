# Changelog

## [0.2.0] - 2026-05-03

**Curated launcher** — deep schema leaves are now hidden by default; only
explicitly declared fields and groups are shown in help output.

### New features

- `ConfigGroup` gains `target` (Hydra group path) and `alias` (CLI flag name)
  fields. Override paths now use `target` when set, enabling `--model-profile`
  to map to `model_profile=...`.
- `choices: auto` in `cli.config.yaml` group entries auto-discovers choices from
  the Hydra config directory at load time.
- `PresetConfig` model with `public_name` (default `"preset"`) lets apps expose
  `--recipe` instead of `--preset`. Set via the `presets.public_name` key in
  `cli.config.yaml`.
- `RunMode` model and `run_modes` list in `ConfigSpec` declare required launch
  combinations. Help output renders a `[Launch Modes]` section.
- New CLI commands: `recipes` (alias for `list`), `explain <target>` (show
  preset overrides or group-choice config), `suggest <name>` (fuzzy flag search),
  `completion <shell>` (generate shell completion script).
- `fields` command gains `--level` and `--search` filters.
- `LauncherState` gains `run_mode`, `set_run_mode`, `required_fields`,
  `optional_fields`, and `run_mode_names`.
- TUI launcher panel shows declared run modes with required/optional flags.
- `render_groups` table now shows a `Target` column.
- `PresetConfig` and `RunMode` exported from the public API.

### Sweep design — translator model

Hydra Fire now positions itself as a **CLI translator and interactive launcher**,
not a sweep execution engine.

- **Single runs** are executed directly via the Hydra composition API
  (`initialize_config_dir` + `compose`), which is semantically equivalent to
  `@hydra.main` for single-point evaluation.
- **Sweep / multirun**: Hydra Fire translates friendly comma flags to Hydra
  `-m` override syntax, prints a Rich panel with the exact command and launcher
  plugin hints, then exits. Hydra's own `BasicSweeper` — accessible only through
  `@hydra.main --multirun` — is responsible for execution, output directories,
  per-run logging, and launcher plugins (joblib, submitit).
- **`_print_sweep_command`** renders a `╭─── Hydra multirun ───╮` panel showing
  the full `-m` command and copy-paste launcher hints.
- The `sweep` sub-command (script CLI and TUI) remains preview-only: it prints
  the bare `-m` string for scripting/piping.
- The interactive launcher `launch` sweep-confirm prompt now reads "Generate
  sweep command for N combinations?" — it prints the command rather than running
  jobs.
- `_run_sweep` (in-process Cartesian-product loop) removed.
- `expand_sweep_combinations` moved to `src/hydra_fire/core/overrides.py` as a
  public utility, used by the TUI for sweep-preview panels.

### Behavior changes

- **Breaking**: Pydantic and dataclass schema fields now default to
  `level="advanced"` (hidden from default help). Use raw Hydra overrides
  (`key=value`) or mark fields explicitly as `core`/`common` in
  `cli.config.yaml`. Function arguments from `spec_from_function` are
  unaffected (still `common`).
- `_spec()` in `commands.py` now passes `base_path` to `load_cli_config` so
  `choices: auto` resolves correctly relative to the CLI config file.

## [0.1.0] - 2026-04-30

First GitHub source release. This version is intended for installation directly
from GitHub rather than PyPI.

- Added `@hydra_fire` decorator for Hydra-backed script CLIs.
- Added function signature, Pydantic, dataclass, and Hydra config discovery.
- Added editable `cli.config.yaml`.
- Added global `hydra-fire` preview and discovery CLI.
- Added prompt_toolkit/Rich launcher.
- Added Hydra multirun translation through lifted comma options, `sweep`, and
  `--multirun`.
