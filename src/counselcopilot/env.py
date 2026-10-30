"""Settings that may live in `.env` (gitignored) instead of the environment."""

from __future__ import annotations

import os
from pathlib import Path


def env_value(name: str) -> str | None:
    """The environment wins; otherwise the `.env` file in the working directory."""
    value = os.environ.get(name)
    env = Path(".env")
    if not value and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, _, found = line.strip().partition("=")
            if key == name:
                value = found.strip().strip("'\"")
    return value or None
