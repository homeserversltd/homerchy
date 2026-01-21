#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy ISO Builder
Copyright (C) 2024 HOMESERVER LLC

Builds Homerchy ISO from local repository source.

This is a thin wrapper that calls the modular orchestrator system.
The actual build logic is in index/index.py following the recursive index pattern.
"""

import os
import sys
from pathlib import Path

# Set environment variable for repo root if not already set
if 'ISOPREP_REPO_ROOT' not in os.environ:
    repo_root = Path(__file__).parent.parent.resolve()
    os.environ['ISOPREP_REPO_ROOT'] = str(repo_root)

# Add index directory to path
index_dir = Path(__file__).parent / 'index'
sys.path.insert(0, str(index_dir))

# Import and execute main orchestrator
from index import main

if __name__ == '__main__':
    main()