#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Build Phase
Copyright (C) 2024 HOMESERVER LLC

ISO build phase orchestrator - executes mkarchiso.
"""

import sys
from pathlib import Path

# Add parent directory to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import Colors
from .mkarchiso import execute_mkarchiso


def main(phase_path: Path, config: dict) -> dict:
    """
    Main build phase function.
    
    Args:
        phase_path: Path to this phase directory
        config: Phase configuration
        
    Returns:
        dict: Execution result
    """
    print(f"{Colors.BLUE}=== Build Phase ==={Colors.NC}")
    
    # Get paths from parent config
    work_dir = Path(config.get('work_dir', Path(phase_path).parent.parent.parent / 'isoprep' / 'work'))
    out_dir = Path(config.get('out_dir', Path(phase_path).parent.parent.parent / 'isoprep' / 'isoout'))
    profile_dir = Path(config.get('profile_dir', work_dir / 'profile'))
    
    # Execute mkarchiso
    iso_files = execute_mkarchiso(work_dir, out_dir, profile_dir)
    
    print(f"{Colors.GREEN}✓ Build phase complete{Colors.NC}")
    
    return {
        "success": True,
        "iso_files": [str(f) for f in iso_files]
    }


if __name__ == '__main__':
    import json
    phase_path = Path(__file__).parent
    config_path = phase_path / 'index.json'
    config = json.load(open(config_path)) if config_path.exists() else {}
    result = main(phase_path, config)
    sys.exit(0 if result.get('success') else 1)
