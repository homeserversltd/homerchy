#!/usr/bin/env python3
"""
HOMESERVER Homerchy first-boot install – log output into file and optional state.
Copyright (C) 2024 HOMESERVER LLC

Phases use append_log() so lines go to the install log file and, if state
has recent_logs, show up on the next display redraw.
"""

import os
from pathlib import Path
from typing import Any, Optional

LOG_MAX_RECENT = 50


def append_log(message: str, state: Optional[Any] = None) -> None:
    """Write a line to the install log file. If state has recent_logs, append there too (capped)."""
    log_file = os.environ.get("HOMERCHY_INSTALL_LOG_FILE", "/var/log/homerchy-install.log")
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "a") as f:
            f.write(message.rstrip() + "\n")
            f.flush()
    except Exception:
        pass
    if state is not None and getattr(state, "recent_logs", None) is not None:
        state.recent_logs.append(message.rstrip())
        if len(state.recent_logs) > LOG_MAX_RECENT:
            state.recent_logs.pop(0)
