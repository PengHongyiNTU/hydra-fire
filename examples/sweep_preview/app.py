from __future__ import annotations

import json

from omegaconf import DictConfig

from hydra_fire import hydra_fire


@hydra_fire(
    config_path="configs",
    config_name="config",
    cli_config="cli.config.yaml",
)
def main(cfg: DictConfig) -> dict[str, object]:
    return {
        "optimizer": cfg.optimizer.name,
        "lr": cfg.optimizer.lr,
        "max_steps": cfg.trainer.max_steps,
        "precision": cfg.trainer.precision,
        "seed": cfg.seed,
    }


if __name__ == "__main__":
    print(json.dumps(main(), separators=(",", ":")))
