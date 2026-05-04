from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from hydra_fire import hydra_fire

_HERE = Path(__file__).parent


class RuntimeConfig(BaseModel):
    verbose: bool = Field(False, description="Enable verbose logging.")
    retries: int = Field(2, description="Retry count.")


class TrainConfig(BaseModel):
    batch_size: int = Field(32, description="Training batch size.")
    lr: float = Field(0.001, description="Learning rate.")
    precision: Literal["bf16", "fp16", "fp32"] = Field("bf16", description="Numeric precision.")
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)


@hydra_fire(
    config_path=str(_HERE / "configs"),
    config_name="config",
    cli_config=str(_HERE / "cli.config.yaml"),
    schema=TrainConfig,
)
def main(cfg: TrainConfig) -> dict[str, object]:
    return cfg.model_dump()


if __name__ == "__main__":
    print(json.dumps(main(), separators=(",", ":")))
