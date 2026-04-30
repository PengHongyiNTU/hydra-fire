from __future__ import annotations

from difflib import get_close_matches


class HydraFireError(Exception):
    """Base exception for expected Hydra Fire errors."""


class ConfigError(HydraFireError):
    """Raised when a CLI config cannot be loaded or validated."""


class UnknownPresetError(HydraFireError):
    """Raised when a preset is not present in the active CLI config."""


class UnknownArgumentError(HydraFireError):
    """Raised when a friendly flag cannot be resolved to a Hydra override."""

    def __init__(self, name: str, known_names: set[str]) -> None:
        suggestions = get_close_matches(name, sorted(known_names), n=3)
        message = f"Unknown argument: {name}"
        if suggestions:
            message += "\n\nDid you mean:\n" + "\n".join(f"  {item}" for item in suggestions)
        message += "\n\nUse raw Hydra overrides as key=value tokens."
        super().__init__(message)
        self.name = name
        self.suggestions = suggestions


class MissingArgumentValueError(HydraFireError):
    """Raised when a known friendly flag is missing its required value."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Argument '--{name}' requires a value.")
        self.name = name


class InvalidChoiceError(HydraFireError):
    """Raised when a value is not one of the allowed choices for a field or group."""


class NonSweepableFieldError(HydraFireError):
    """Raised when a non-sweepable field is used with comma sweep values."""


class AmbiguousSweepValueError(HydraFireError):
    """Raised when comma values are used in single-run composition."""


class RunNotImplementedError(HydraFireError):
    """Raised when non-dry-run execution is requested before launch support exists."""
