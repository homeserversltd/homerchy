"""
Homerchy Installation Helpers - Python Implementation

This module provides Python equivalents of the shell helper functions.
"""

import os
import sys
from pathlib import Path

from .presentation import init_environment, clear_logo, gum_style
from .logging import start_install_log, stop_install_log

__all__ = [
    'init_environment',
    'start_install_log',
    'stop_install_log',
    'clear_logo',
    'gum_style',
]