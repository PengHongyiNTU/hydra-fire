from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any, get_type_hints

from hydra_fire.core.spec import ArgumentField, ConfigSpec

from .types import (
    choices_from_annotation,
    flatten_path,
    infer_annotation_type,
    path_to_alias,
)


def spec_from_dataclass(schema: type[Any], *, prefix: str = "") -> ConfigSpec:
    if not dataclasses.is_dataclass(schema):
        raise TypeError("schema must be a dataclass type")

    fields: dict[str, ArgumentField] = {}
    _collect_dataclass_fields(schema, prefix=prefix, fields=fields)
    return ConfigSpec(fields=fields)


def _collect_dataclass_fields(
    schema: type[Any],
    *,
    prefix: str,
    fields: dict[str, ArgumentField],
) -> None:
    hints = get_type_hints(schema)
    for field in dataclasses.fields(schema):
        path = flatten_path(prefix, field.name)
        annotation = hints.get(field.name, field.type)
        if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
            _collect_dataclass_fields(annotation, prefix=path, fields=fields)
            continue

        default, required = _dataclass_default(field)
        metadata: Mapping[str, Any] = field.metadata or {}
        fields[path] = ArgumentField(
            path=path,
            alias=path_to_alias(path),
            type=infer_annotation_type(annotation),
            default=default,
            required=required,
            help=str(metadata.get("help") or metadata.get("description") or ""),
            choices=choices_from_annotation(annotation),
            level="advanced",
        )


def _dataclass_default(field: dataclasses.Field[Any]) -> tuple[Any | None, bool]:
    if field.default is not dataclasses.MISSING:
        return field.default, False
    if field.default_factory is not dataclasses.MISSING:
        return field.default_factory(), False
    return None, True
