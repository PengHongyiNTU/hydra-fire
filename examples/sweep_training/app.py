from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path

from omegaconf import DictConfig
from tqdm import tqdm

from hydra_fire import hydra_fire

_HERE = Path(__file__).parent


@hydra_fire(
    config_path=str(_HERE / "configs"),
    config_name="config",
    cli_config=str(_HERE / "cli.config.yaml"),
)
def main(cfg: DictConfig) -> dict[str, object]:
    random.seed(cfg.trainer.seed)

    loss = 1.0 + random.random() * 0.2
    final_loss = loss
    final_acc = 0.0
    epochs = cfg.trainer.epochs
    lr = cfg.optimizer.lr
    desc = f"{cfg.model.name}+{cfg.optimizer.name}  lr={lr}"

    with tqdm(range(1, epochs + 1), desc=desc, unit="epoch", ncols=88) as pbar:
        for epoch in pbar:
            time.sleep(cfg.trainer.step_sleep)
            noise = (random.random() - 0.5) * 0.01
            loss = loss * (1 - lr * 0.9) + noise
            loss = max(loss, 0.005)
            acc = 1.0 - math.exp(-epoch * lr * 12)
            pbar.set_postfix(loss=f"{loss:.4f}", acc=f"{acc:.3f}")
            final_loss = loss
            final_acc = acc

    return {
        "model": cfg.model.name,
        "hidden_size": cfg.model.hidden_size,
        "optimizer": cfg.optimizer.name,
        "lr": lr,
        "epochs": epochs,
        "final_loss": round(final_loss, 4),
        "final_acc": round(final_acc, 3),
    }


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
