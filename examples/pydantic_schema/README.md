# Pydantic Schema Example

A Pydantic model defines the config contract. Hydra Fire reads types, defaults,
descriptions, nested models, and `Literal` choices from the model, then
validates the composed config before calling the function.

```python
class TrainConfig(BaseModel):
    batch_size: int = Field(32, description="Training batch size.")
    precision: Literal["bf16", "fp16", "fp32"] = Field("bf16", description="Numeric precision.")
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

@hydra_fire(..., schema=TrainConfig)
def main(cfg: TrainConfig) -> dict:
    return cfg.model_dump()
```

## Run

From the project root:

```bash
# Default values
uv run examples/pydantic_schema/app.py

# Override curated fields
uv run examples/pydantic_schema/app.py --batch-size 16 --precision fp16

# Use a raw Hydra override for a debug-level field
uv run examples/pydantic_schema/app.py runtime.verbose=true

# Multiple overrides
uv run examples/pydantic_schema/app.py --batch-size 16 --precision fp16 runtime.verbose=true
```

Expected output is compact JSON:

```json
{"batch_size":16,"lr":0.001,"precision":"fp16","runtime":{"verbose":false,"retries":2}}
```

Invalid values are caught by Pydantic validation and produce a clear error:

```bash
uv run examples/pydantic_schema/app.py batch_size=not-an-int
```

## Discover

```bash
# Full help
uv run examples/pydantic_schema/app.py --help

# All config fields
uv run examples/pydantic_schema/app.py fields

# List presets
uv run examples/pydantic_schema/app.py recipes

# Preview composed config
uv run examples/pydantic_schema/app.py show --precision fp32
```

## Explain

```bash
# Explain a field — shows type, default, level, choices
uv run examples/pydantic_schema/app.py explain batch-size
uv run examples/pydantic_schema/app.py explain --batch-size   # leading -- stripped

# Explain a field with choices
uv run examples/pydantic_schema/app.py explain precision

# Explain a nested debug field — shows raw Hydra override syntax
uv run examples/pydantic_schema/app.py explain runtime.verbose

# Explain a preset
uv run examples/pydantic_schema/app.py explain default

# Fuzzy search
uv run examples/pydantic_schema/app.py suggest prec
```

Note: nested Pydantic fields (`runtime.*`) are `advanced` or `debug` by default
and do not appear as `--flags`. Use `explain runtime.verbose` to see the correct
raw Hydra syntax (`runtime.verbose=true`), or mark them explicitly in
`cli.config.yaml` to promote them to a CLI flag.

## Sweep

```bash
uv run examples/pydantic_schema/app.py --batch-size 16,32,64 --lr 0.001,0.01
# Output: -m batch_size=16,32,64 lr=0.001,0.01

uv run examples/pydantic_schema/app.py sweep --batch-size 16,32 --precision bf16,fp16
```

## Interactive Launcher

```bash
uv run examples/pydantic_schema/app.py launch
```

## Global CLI

```bash
hydra-fire fields --config examples/pydantic_schema/cli.config.yaml
hydra-fire show default --config examples/pydantic_schema/cli.config.yaml --batch-size 16
hydra-fire run default --config examples/pydantic_schema/cli.config.yaml --batch-size 16 --dry-run
```
