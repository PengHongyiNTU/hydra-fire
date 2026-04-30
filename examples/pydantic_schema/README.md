# Pydantic Schema Example

This example uses a Pydantic model as the schema. Hydra Fire inspects the model
for types, defaults, descriptions, nested fields, and choices.

```python
class TrainConfig(BaseModel):
    batch_size: int = Field(32, description="Training batch size.")
    precision: Literal["bf16", "fp16", "fp32"] = "bf16"

@hydra_fire(config_path="configs", config_name="config", schema=TrainConfig)
def main(cfg: TrainConfig):
    ...
```

## Run

```bash
python app.py
python app.py --batch-size 16 --precision fp16 runtime.verbose=true
python app.py --lr 0.01 --runtime-verbose
```

Invalid values fail during Pydantic validation:

```bash
python app.py --batch-size not-an-int
```

## Preview With Global CLI

```bash
hydra-fire run default --config cli.config.yaml --batch-size 16 --precision fp16 --dry-run
hydra-fire show default --config cli.config.yaml --precision fp32
hydra-fire docs --config cli.config.yaml
```
