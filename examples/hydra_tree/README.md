# Hydra Config Tree Example

This example starts from an existing Hydra config tree. Hydra Fire discovers:

- config groups such as `model` and `optimizer`
- nested fields such as `trainer.max_steps`
- convention presets from `configs/presets`

The Python function receives the composed Hydra config object.

## Run

```bash
python app.py
python app.py --model large --optimizer sgd trainer.max_steps=50
python app.py --precision fp16 --steps 25
```

Expected output is JSON containing the selected model, optimizer, trainer
settings, and seed.

## Preview With Global CLI

```bash
hydra-fire fields --config cli.config.yaml
hydra-fire groups --config cli.config.yaml
hydra-fire run quick --config cli.config.yaml --steps 20 --dry-run
hydra-fire show quick --config cli.config.yaml --steps 20
```

The `quick` preset is defined in `configs/presets/quick.yaml` and committed into
`cli.config.yaml` for a stable user-facing interface.
