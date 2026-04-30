from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from hydra_fire.core.spec import AppConfig, ArgumentField, ConfigSpec

from .types import choices_from_annotation, first_doc_line, infer_annotation_type, path_to_alias


def spec_from_function(func: Callable[..., Any]) -> ConfigSpec:
    signature = inspect.signature(func)
    hints = get_type_hints(func)
    fields: dict[str, ArgumentField] = {}

    for name, parameter in signature.parameters.items():
        if name == "self" or parameter.kind in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.VAR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        }:
            continue
        annotation = hints.get(name, parameter.annotation)
        has_default = parameter.default is not inspect.Parameter.empty
        fields[name] = ArgumentField(
            path=name,
            alias=path_to_alias(name),
            type=infer_annotation_type(annotation),
            default=parameter.default if has_default else None,
            required=not has_default,
            help="",
            choices=choices_from_annotation(annotation),
        )

    return ConfigSpec(
        app=AppConfig(
            name=func.__name__,
            description=first_doc_line(func.__doc__),
        ),
        fields=fields,
    )
