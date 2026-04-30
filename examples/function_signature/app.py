from __future__ import annotations

import json

from hydra_fire import hydra_fire


@hydra_fire(
    config_path="configs",
    config_name="config",
    cli_config="cli.config.yaml",
)
def main(batch_size: int = 32, lr: float = 0.001, debug: bool = False) -> dict[str, object]:
    return {
        "batch_size": batch_size,
        "lr": lr,
        "debug": debug,
    }


if __name__ == "__main__":
    print(json.dumps(main(), separators=(",", ":")))
