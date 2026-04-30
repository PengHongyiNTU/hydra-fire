from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from types import NoneType, UnionType
from typing import Any, Literal, Union, get_args, get_origin

from hydra_fire.core.spec import ValueType, cli_name_from_path


def infer_annotation_type(annotation: Any) -> ValueType:
    annotation = _strip_optional(annotation)
    origin = get_origin(annotation)

    if annotation is bool:
        return "bool"
    if annotation is int:
        return "int"
    if annotation is float:
        return "float"
    if annotation is str:
        return "str"
    if annotation is Path:
        return "path"
    if origin is Literal:
        values = get_args(annotation)
        if values:
            return infer_value_type(values[0])
        return "str"
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return "str"
    return "json"


def infer_value_type(value: Any) -> ValueType:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, Path):
        return "path"
    return "json"


def choices_from_annotation(annotation: Any) -> list[str] | None:
    annotation = _strip_optional(annotation)
    origin = get_origin(annotation)
    if origin is Literal:
        return [str(value) for value in get_args(annotation)]
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return [str(item.value) for item in annotation]
    return None


def path_to_alias(path: str) -> str:
    return cli_name_from_path(path)


def flatten_path(parent: str, child: str) -> str:
    return f"{parent}.{child}" if parent else child


def _strip_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin in {Union, UnionType}:
        args = [arg for arg in get_args(annotation) if arg is not NoneType]
        if len(args) == 1:
            return args[0]
    return annotation


def first_doc_line(doc: str | None) -> str:
    if not doc:
        return ""
    lines = [line.strip() for line in doc.strip().splitlines() if line.strip()]
    return lines[0] if lines else ""


def ensure_choices(values: Iterable[Any] | None) -> list[str] | None:
    if values is None:
        return None
    return [str(value) for value in values]
