from __future__ import annotations

from collections.abc import Mapping
from dataclasses import MISSING, fields, is_dataclass
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel


def validate_config(config: DictConfig, schema: type[Any]) -> Any:
    data = OmegaConf.to_container(config, resolve=True)
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema.model_validate(data)
    if is_dataclass(schema):
        if not isinstance(data, Mapping):
            raise TypeError("dataclass validation requires a mapping config")
        return _coerce_dataclass(schema, data)
    raise TypeError("schema must be a Pydantic model or dataclass type")


def _coerce_dataclass(schema: type[Any], data: Mapping[Any, Any]) -> Any:
    hints = get_type_hints(schema)
    kwargs: dict[str, Any] = {}
    for field in fields(schema):
        if field.name not in data:
            if field.default is MISSING and field.default_factory is MISSING:
                raise TypeError(f"Missing required config value: {field.name}")
            continue
        annotation = hints.get(field.name, field.type)
        kwargs[field.name] = _coerce_value(annotation, data[field.name])
    return schema(**kwargs)


def _coerce_value(annotation: Any, value: Any) -> Any:
    annotation = _strip_optional(annotation)
    origin = get_origin(annotation)

    if isinstance(annotation, type) and is_dataclass(annotation):
        if not isinstance(value, Mapping):
            raise TypeError(f"Expected mapping for dataclass field: {annotation.__name__}")
        return _coerce_dataclass(annotation, value)

    if origin is list:
        args = get_args(annotation)
        item_type = args[0] if args else Any
        if not isinstance(value, list):
            return value
        return [_coerce_value(item_type, item) for item in value]

    return value


def _strip_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin in {Union, UnionType}:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation
