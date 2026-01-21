#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Package Utilities
Copyright (C) 2024 HOMESERVER LLC

Package list reading and processing utilities.
"""

from pathlib import Path


def read_package_list(package_file: Path) -> list:
    """
    Read package list from file, filtering out comments and empty lines.
    
    Args:
        package_file: Path to package list file
        
    Returns:
        List of package names
    """
    if not package_file.exists():
        return []
    
    packages = []
    with open(package_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                packages.append(line)
    
    return packages
