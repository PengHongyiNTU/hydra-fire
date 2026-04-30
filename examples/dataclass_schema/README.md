# Dataclass Schema Example

This example uses a dataclass schema as the public contract for the CLI.
Hydra composes the config, then Hydra Fire validates and converts it into
`TrainConfig` before invoking the function.

## Try It

```bash
python app.py --help
python app.py --batch-size 24 --precision fp32 runtime.verbose=true
python app.py fields
python app.py show --retries 4
python app.py launch
```

Expected command output is compact JSON from the decorated function.
