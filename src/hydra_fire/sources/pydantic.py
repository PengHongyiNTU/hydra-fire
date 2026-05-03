from __future__ import annotations

from pydantic import BaseModel
from pydantic.fields import PydanticUndefined

from hydra_fire.core.spec import ArgumentField, ConfigSpec

from .types import (
    choices_from_annotation,
    flatten_path,
    infer_annotation_type,
    path_to_alias,
)


def spec_from_pydantic(schema: type[BaseModel], *, prefix: str = "") -> ConfigSpec:
    if not isinstance(schema, type) or not issubclass(schema, BaseModel):
        raise TypeError("schema must be a Pydantic BaseModel type")

    fields: dict[str, ArgumentField] = {}
    _collect_pydantic_fields(schema, prefix=prefix, fields=fields)
    return ConfigSpec(fields=fields)


def _collect_pydantic_fields(
    schema: type[BaseModel],
    *,
    prefix: str,
    fields: dict[str, ArgumentField],
) -> None:
    for name, model_field in schema.model_fields.items():
        path = flatten_path(prefix, name)
        annotation = model_field.annotation
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            _collect_pydantic_fields(annotation, prefix=path, fields=fields)
            continue

        fields[path] = ArgumentField(
            path=path,
            alias=path_to_alias(path),
            type=infer_annotation_type(annotation),
            default=None if model_field.default is PydanticUndefined else model_field.default,
            required=model_field.is_required(),
            help=model_field.description or "",
            choices=choices_from_annotation(annotation),
            level="advanced",
        )
