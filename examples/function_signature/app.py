from __future__ import annotations

import json
from pathlib import Path

from hydra_fire import hydra_fire

_HERE = Path(__file__).parent


@hydra_fire(
    config_path=str(_HERE / "configs"),
    config_name="config",
    cli_config=str(_HERE / "cli.config.yaml"),
)
def main(batch_size: int = 32, lr: float = 0.001, debug: bool = False) -> dict[str, object]:
    return {
        "batch_size": batch_size,
        "lr": lr,
        "debug": debug,
    }


if __name__ == "__main__":
    print(json.dumps(main(), separators=(",", ":")))
