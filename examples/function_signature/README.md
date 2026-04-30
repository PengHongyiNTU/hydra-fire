# Function Signature Example

This example starts from a normal Python function:

```python
@hydra_fire(config_path="configs", config_name="config")
def main(batch_size: int = 32, lr: float = 0.001, debug: bool = False):
    ...
```

Hydra Fire reads the function signature, maps friendly arguments to Hydra
overrides, composes the config, and calls the function with typed values.

## Run

```bash
python app.py
python app.py --batch-size 64 --lr 0.01 --debug
python app.py --batch-size 128 --debug
python app.py --help
```

Expected output is JSON:

```json
{"batch_size":64,"lr":0.01,"debug":true}
```

## Discover And Preview

The script entrypoint also exposes lightweight discovery commands:

```bash
python app.py fields
python app.py groups
python app.py show --batch-size 64
python app.py launch
```

`launch` opens the prompt_toolkit/Rich interactive launcher. It lets you type
normal CLI arguments with Tab completion, then previews generated Hydra
overrides and the composed config before confirmation. After confirmation it
invokes the decorated function with those overrides.

## Preview With Global CLI

```bash
hydra-fire run default --config cli.config.yaml --batch-size 64 --dry-run
hydra-fire show default --config cli.config.yaml --batch-size 64
hydra-fire fields --config cli.config.yaml
```
