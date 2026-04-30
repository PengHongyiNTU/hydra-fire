from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field

from hydra_fire.sources.pydantic import spec_from_pydantic


class RuntimeConfig(BaseModel):
    verbose: bool = Field(False, description="Enable verbose output.")


class WorkflowConfig(BaseModel):
    size: int = Field(description="Work item size.")
    rate: float = Field(0.1, description="Processing rate.")
    mode: Literal["fast", "safe"] = "safe"
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)


class Status(IntEnum):
    ACTIVE = 1
    INACTIVE = 2


def test_builds_spec_from_pydantic_model():
    spec = spec_from_pydantic(WorkflowConfig)

    assert spec.fields["size"].type == "int"
    assert spec.fields["size"].required is True
    assert spec.fields["size"].help == "Work item size."
    assert spec.fields["rate"].default == 0.1
    assert spec.fields["rate"].help == "Processing rate."
    assert spec.fields["mode"].choices == ["fast", "safe"]
    assert spec.fields["runtime.verbose"].type == "bool"
    assert spec.fields["runtime.verbose"].help == "Enable verbose output."


def test_pydantic_enum_choices_use_values():
    class Config(BaseModel):
        status: Status = Status.ACTIVE

    spec = spec_from_pydantic(Config)

    assert spec.fields["status"].choices == ["1", "2"]


def test_rejects_non_pydantic_model():
    try:
        spec_from_pydantic(dict)  # type: ignore[arg-type]
    except TypeError as exc:
        assert "Pydantic" in str(exc)
    else:
        raise AssertionError("expected TypeError")
