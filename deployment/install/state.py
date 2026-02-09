#!/usr/bin/env python3
"""
HOMESERVER Homerchy first-boot install – shared state.
Copyright (C) 2024 HOMESERVER LLC

State is held by the main process (install.py). Orchestrator receives it and
passes it to phases. Phases only mutate state; they never own display or TTY.
"""

from enum import Enum
from typing import Any, Optional


class Status(Enum):
    """Installation outcome."""
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class State:
    """Runtime state for status display and phase results. Main creates it; orchestrator and phases mutate it."""
    __slots__ = ("status", "current_step", "errors", "children", "recent_logs", "capture_log_content")

    def __init__(self) -> None:
        self.status = Status.IN_PROGRESS
        self.current_step: str = "none"
        self.errors: list[str] = []
        self.children: dict[str, Any] = {}
        self.recent_logs: list[str] = []  # Live log lines; reporting uses these if non-empty, else log file tail
        self.capture_log_content: Optional[str] = None
