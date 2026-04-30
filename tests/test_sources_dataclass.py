from dataclasses import dataclass, field
from enum import StrEnum

from hydra_fire.sources.dataclass import spec_from_dataclass


class Mode(StrEnum):
    FAST = "fast"
    SAFE = "safe"


@dataclass
class RuntimeConfig:
    verbose: bool = False


@dataclass
class WorkflowConfig:
    size: int = field(metadata={"help": "Work item size."})
    rate: float = 0.1
    mode: Mode = Mode.SAFE
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)


def test_builds_spec_from_dataclass():
    spec = spec_from_dataclass(WorkflowConfig)

    assert spec.fields["size"].type == "int"
    assert spec.fields["size"].required is True
    assert spec.fields["size"].help == "Work item size."
    assert spec.fields["rate"].default == 0.1
    assert spec.fields["mode"].choices == ["fast", "safe"]
    assert spec.fields["runtime.verbose"].type == "bool"
    assert spec.fields["runtime.verbose"].alias == "runtime-verbose"


def test_rejects_non_dataclass_type():
    try:
        spec_from_dataclass(dict)
    except TypeError as exc:
        assert "dataclass" in str(exc)
    else:
        raise AssertionError("expected TypeError")


def test_dataclass_default_factory_is_not_required_and_shows_value():
    @dataclass
    class Config:
        tags: list[str] = field(default_factory=list)

    spec = spec_from_dataclass(Config)

    assert spec.fields["tags"].required is False
    assert spec.fields["tags"].default == []
