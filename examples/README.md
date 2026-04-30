# Hydra Fire Examples

These examples are intentionally small and isolated. Each one has its own
Hydra config folder, `cli.config.yaml`, Python entrypoint, and README.

## Examples

| Example | Demonstrates |
| --- | --- |
| [function_signature](function_signature/README.md) | Typed Python function introspection. |
| [pydantic_schema](pydantic_schema/README.md) | Pydantic validation, docs, choices, and nested fields. |
| [dataclass_schema](dataclass_schema/README.md) | Dataclass schema validation and nested config. |
| [hydra_tree](hydra_tree/README.md) | Hydra config groups, discovered fields, and presets. |
| [sweep_preview](sweep_preview/README.md) | Hydra multirun translation through comma values and `sweep`. |

## Run

From the repository root:

```bash
cd examples/function_signature
python app.py --batch-size 64 --lr 0.01 --debug

cd ../pydantic_schema
python app.py --batch-size 16 --precision fp16 runtime.verbose=true

cd ../dataclass_schema
python app.py --batch-size 24 --precision fp32 runtime.verbose=true

cd ../hydra_tree
python app.py --model large --optimizer sgd trainer.max_steps=50

cd ../sweep_preview
python app.py --optimizer adam --lr 0.001 --steps 100
python app.py --optimizer adam,sgd --lr 1,2,3,4
python app.py sweep --optimizer adam,sgd --lr 1,2,3,4
hydra-fire run default --config cli.config.yaml --optimizer adam,sgd --lr 1,2,3,4 --dry-run
hydra-fire sweep default --config cli.config.yaml --optimizer adam,sgd --lr 1,2,3,4
```

The global preview CLI can also inspect examples:

```bash
hydra-fire fields --config examples/hydra_tree/cli.config.yaml
hydra-fire run quick --config examples/hydra_tree/cli.config.yaml --steps 20 --dry-run
hydra-fire show quick --config examples/hydra_tree/cli.config.yaml --steps 20
```
