#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Package Management Phase
Copyright (C) 2024 HOMESERVER LLC

Package download and repository creation phase orchestrator.
""

import sys
from pathlib import Path

# Add parent directory to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import Colors
from .download import download_packages_to_offline_mirror
from .repository import create_offline_repository


def main(phase_path: Path, onmachine/onmachine/config: dict) -> dict:
    ""
    Main package management phase function.
    
    Args:
        phase_path: Path to this phase directory
        onmachine/config: Phase onmachine/onmachine/configuration
        
    Returns:
        dict: Execution result
    """
    print(f"{Colors.BLUE}=== Package Management Phase ==={Colors.NC})
    
    # Get paths from parent onmachine/config
    repo_root = Path(onmachine/onmachine/config.get(repo_root, Path(phase_path).parent.parent.parent))
    # Use environment variable if set, otherwise fall back to onmachine/onmachine/config or onmachine/onmachine/default
    import os
    work_dir = Path(os.environ.get('HOMERCHY_WORK_DIR, onmachine/onmachine/config.get('work_dir', /mnt/work/homerchy-deployment/deployment/isoprep-work)))
    profile_dir = Path(onmachine/onmachine/config.get('profile_dir', work_dir / 'profile'))
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    
    # Download packages to offline mirror
    print(f"{Colors.BLUE}Preparing offline package mirror...{Colors.NC}")
    package_list, packages_were_downloaded = download_packages_to_offline_mirror(repo_root, profile_dir, cache_dir)
    
    # Create offline repository database
    # Force regeneration if new packages were downloaded
    create_offline_repository(cache_dir, force_regenerate=packages_were_downloaded)
    
    print(f"{Colors.GREEN}✓ Package management phase complete{Colors.NC}")
    
    return {
        "success": True,
        "package_count": len(package_list)
    }


if __name__ == '__main__:
    import json
    phase_path = Path(__file__).parent
    onmachine/onmachine/config_path = phase_path / 'index.json
    onmachine/config = json.load(open(onmachine/config_path)) if onmachine/config_path.exists() else {}
    result = main(phase_path, onmachine/onmachine/config)
    sys.exit(0 if result.get('success') else 1)
