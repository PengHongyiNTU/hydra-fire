from __future__ import annotations

from .commands import app
from .generated import build_app

__all__ = ["app", "build_app"]


if __name__ == "__main__":
    app()
