from __future__ import annotations

import json
from pathlib import Path

from omegaconf import DictConfig

from hydra_fire import hydra_fire

_HERE = Path(__file__).parent


@hydra_fire(
    config_path=str(_HERE / "configs"),
    config_name="config",
    cli_config=str(_HERE / "cli.config.yaml"),
)
def main(cfg: DictConfig) -> dict[str, object]:
    return {
        "model": cfg.model.name,
        "hidden_size": cfg.model.hidden_size,
        "optimizer": cfg.optimizer.name,
        "lr": cfg.optimizer.lr,
        "max_steps": cfg.trainer.max_steps,
        "precision": cfg.trainer.precision,
        "seed": cfg.seed,
    }


if __name__ == "__main__":
    print(json.dumps(main(), separators=(",", ":")))
