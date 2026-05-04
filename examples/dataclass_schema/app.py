from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from hydra_fire import hydra_fire

_HERE = Path(__file__).parent


@dataclass
class RuntimeConfig:
    verbose: bool = field(default=False, metadata={"help": "Enable verbose logging."})
    retries: int = field(default=2, metadata={"help": "Retry count."})


@dataclass
class TrainConfig:
    batch_size: int = field(default=32, metadata={"help": "Training batch size."})
    lr: float = field(default=0.001, metadata={"help": "Learning rate."})
    precision: Literal["bf16", "fp16", "fp32"] = field(
        default="bf16",
        metadata={"help": "Numeric precision."},
    )
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)


@hydra_fire(
    config_path=str(_HERE / "configs"),
    config_name="config",
    cli_config=str(_HERE / "cli.config.yaml"),
    schema=TrainConfig,
)
def main(cfg: TrainConfig) -> dict[str, object]:
    return asdict(cfg)


if __name__ == "__main__":
    print(json.dumps(main(), separators=(",", ":")))
