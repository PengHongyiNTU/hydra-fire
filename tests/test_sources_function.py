from typing import Literal

from hydra_fire.core.overrides import expand_args
from hydra_fire.sources.function import spec_from_function


def test_builds_spec_from_function_signature():
    def workflow(size: int, rate: float = 0.1, verbose: bool = False):
        """Run a configurable workflow."""

    spec = spec_from_function(workflow)

    assert spec.app.name == "workflow"
    assert spec.app.description == "Run a configurable workflow."
    assert spec.fields["size"].type == "int"
    assert spec.fields["size"].required is True
    assert spec.fields["rate"].type == "float"
    assert spec.fields["rate"].default == 0.1
    assert spec.fields["verbose"].type == "bool"
    assert expand_args(["--size", "8", "--verbose"], spec) == ["size=8", "verbose=true"]


def test_function_literal_annotation_becomes_choices():
    def workflow(mode: Literal["fast", "safe"] = "safe"):
        pass

    spec = spec_from_function(workflow)

    assert spec.fields["mode"].type == "str"
    assert spec.fields["mode"].choices == ["fast", "safe"]


def test_function_skips_varargs_and_kwargs():
    def workflow(size: int, *args: str, **kwargs: str):
        pass

    spec = spec_from_function(workflow)

    assert list(spec.fields) == ["size"]


def test_function_skips_positional_only_params():
    def workflow(size: int, /, rate: float = 0.1):
        pass

    spec = spec_from_function(workflow)

    assert "size" not in spec.fields
    assert "rate" in spec.fields
