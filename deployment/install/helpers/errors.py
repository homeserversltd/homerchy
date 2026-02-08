#!/usr/bin/env python3
"""
HOMESERVER Homerchy first-boot install – error reporting into shared state.
Copyright (C) 2024 HOMESERVER LLC

Phases use this to record failures so main display and report show them.
"""

from typing import Any


def record_error(state: Any, step: str, message: str) -> None:
    """Append an error and record step result. State is the shared State instance."""
    state.errors.append(f"{step}: {message}")
    state.children[step] = message
