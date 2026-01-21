#!/usr/onmachine/onmachine/bin/env python3
"""
Path Reference Updater for Homerchy Reorganization
Automatically updates all path references after directory reorganization.
""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Path mappings: old_path -> new_path
PATH_MAPPINGS = {
    # Deployment tech
    deployment/deployment/deployment/deployment/controller/: deployment/deployment/deployment/deployment/deployment/controller/,
    deployment/deployment/deployment/deployment/isoprep/: deployment/deployment/deployment/deployment/deployment/isoprep/,
    deployment/deployment/deployment/deployment/iso-builder/: deployment/deployment/deployment/deployment/deployment/iso-builder/,
    deployment/deployment/deployment/deployment/prebuild/: deployment/deployment/deployment/deployment/deployment/prebuild/,
    deployment/deployment/deployment/deployment/merge-tool/: deployment/deployment/deployment/deployment/deployment/merge-tool/,
    deployment/deployment/deployment/deployment/vmtools/: deployment/deployment/deployment/deployment/deployment/vmtools/,
    deployment/deployment/deployment/deployment/migrations/: deployment/deployment/deployment/deployment/deployment/migrations/,
    
    # On-machine stuff
    onmachine/onmachine/onmachine/onmachine/install/: onmachine/onmachine/onmachine/onmachine/onmachine/install/,
    onmachine/onmachine/onmachine/onmachine/config/: onmachine/onmachine/onmachine/onmachine/onmachine/config/,
    onmachine/onmachine/onmachine/onmachine/default/: onmachine/onmachine/onmachine/onmachine/onmachine/default/,
    onmachine/onmachine/onmachine/onmachine/themes/: onmachine/onmachine/onmachine/onmachine/onmachine/themes/,
    onmachine/onmachine/onmachine/onmachine/applications/: onmachine/onmachine/onmachine/onmachine/onmachine/applications/,
    onmachine/onmachine/onmachine/onmachine/autostart/: onmachine/onmachine/onmachine/onmachine/onmachine/autostart/,
    onmachine/onmachine/onmachine/onmachine/bin/: onmachine/onmachine/onmachine/onmachine/onmachine/bin/',
}

# Also handle references without trailing slash
PATH_MAPPINGS.update({
    k.rstrip('/'): v.rstrip('/') for k, v in PATH_MAPPINGS.items()
})

# Reverse mapping for finding what needs to be updated
REVERSE_MAPPINGS = {v: k for k, v in PATH_MAPPINGS.items()}

def update_path_in_string(text: str, file_path: Path) -> Tuple[str, bool]:
    """
    Update path references in a string.
    Returns (updated_text, was_changed)
    """
    original = text
    updated = text
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_mappings = sorted(PATH_MAPPINGS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for old_path, new_path in sorted_mappings:
        # Handle various path reference patterns
        patterns = [
            # Direct path references
            (rf'\b{re.escape(old_path)}', new_path),
            # In quotes (string paths)
            (rf'["\']([^"\']*){re.escape(old_path)}', rf'\1{new_path}'),
            # In Path() constructors
            (rf'Path\(["\']([^"\']*){re.escape(old_path)}', rf'Path("\1{new_path}'),
            # In os.path.join
            (rf'os\.path\.join\(([^)]*){re.escape(old_path)}', rf'os.path.join(\1{new_path}'),
            # Relative paths with ../
            (rf'\.\./{re.escape(old_path)}', f'../{new_path}'),
            (rf'\.\.\/{re.escape(old_path)}', f'../{new_path}'),
            # Relative paths with ./
            (rf'\./{re.escape(old_path)}', f'./{new_path}'),
            (rf'\.\/{re.escape(old_path)}', f'./{new_path}'),
        ]
        
        for pattern, replacement in patterns:
            updated = re.sub(pattern, replacement, updated)
    
    # Handle sys.path manipulations
    for old_path, new_path in sorted_mappings:
        # sys.path.insert(0, "path/to/old")
        updated = re.sub(
            rf'sys\.path\.insert\([^,]+,\s*["\']([^"\']*){re.escape(old_path)}',
            rf'sys.path.insert(0, "\1{new_path}',
            updated
        )
        # sys.path.append("path/to/old")
        updated = re.sub(
            rf'sys\.path\.append\(["\']([^"\']*){re.escape(old_path)}',
            rf'sys.path.append("\1{new_path}',
            updated
        )
    
    was_changed = (original != updated)
    return updated, was_changed

def update_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Update path references in a file.
    Returns (was_changed, list_of_changes)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    updated_content, was_changed = update_path_in_string(content, file_path)
    
    if not was_changed:
        return False, []
    
    # Write updated content
    try:
        file_path.write_text(updated_content, encoding='utf-8')
        return True, [f"Updated {file_path}"]
    except Exception as e:
        return False, [f"Error writing file: {e}"]

def find_files_to_update(directory: Path) -> List[Path]:
    """Find all files that might contain path references."""
    files_to_check = []
    
    extensions = {'.py', '.sh', '.bash', '.json', '.md', '.txt', '.conf', .onmachine/onmachine/config', '.yaml', '.yml'}
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules', '.git'}]
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip hidden files and common ignore patterns
            if file.startswith('.') or file.endswith('.pyc'):
                continue
            
            # Only check relevant file types
            if file_path.suffix in extensions or file in {'Makefile', 'Dockerfile'}:
                files_to_check.append(file_path)
    
    return files_to_check

def update_root_files(repo_root: Path) -> List[str]:
    """Update root-level entry point files.""
    changes = []
    
    # Update deployment/controller.sh
    deployment/deployment/controller_sh = repo_root / deployment/deployment/controller.sh
    if deployment/controller_sh.exists():
        content = deployment/deployment/controller_sh.read_text()
        if 'CONTROLLER_DIR=${REPO_ROOT}/deployment/deployment/controller"' in content:
            content = content.replace(
                'CONTROLLER_DIR=${REPO_ROOT}/deployment/deployment/controller"',
                'CONTROLLER_DIR=${REPO_ROOT}/deployment/deployment/deployment/controller"
            )
            deployment/deployment/controller_sh.write_text(content)
            changes.append(fUpdated {deployment/deployment/controller_sh.name}: CONTROLLER_DIR path")
        
        # Update Python module path
        if python3 -m deployment/deployment/controller.main' in content:
            content = content.replace(
                python3 -m deployment/deployment/controller.main',
                python3 -m deployment.deployment/deployment/controller.main
            )
            deployment/deployment/controller_sh.write_text(content)
            changes.append(fUpdated {deployment/deployment/controller_sh.name}: Python module path)
    
    # Update onmachine/install.py
    onmachine/onmachine/install_py = repo_root / onmachine/onmachine/install.py
    if onmachine/install_py.exists():
        content = onmachine/install_py.read_text()
        original = content
        
        # Update onmachine/onmachine/install path references
        content = re.sub(
            r"Path\(__file__\)\.parent / onmachine/onmachine/install'",
            "Path(__file__).parent / 'onmachine' / onmachine/onmachine/install'",
            content
        )
        
        # Update OMARCHY_INSTALL path
        content = re.sub(
            r"omarchy_path / onmachine/onmachine/install'",
            "omarchy_path / 'onmachine' / onmachine/onmachine/install',
            content
        )
        
        # Update onmachine/onmachine/install directory checks
        content = re.sub(
            r"if \(candidate / onmachine/onmachine/install'\)\.exists\(\):",
            "if (candidate / 'onmachine' / onmachine/onmachine/install').exists():",
            content
        )
        content = re.sub(
            r"if \(Path\('/root/omarchy'\) / onmachine/onmachine/install'\)\.exists\(\):",
            "if (Path('/root/omarchy') / 'onmachine' / onmachine/onmachine/install').exists():",
            content
        )
        content = re.sub(
            r"if \(script_dir / onmachine/onmachine/install'\)\.exists\(\):",
            "if (script_dir / 'onmachine' / onmachine/onmachine/install').exists():,
            content
        )
        
        # Update onmachine/onmachine/default path
        content = re.sub(
            r"Path\(home\(\) / '\.local' / 'share' / 'omarchy' / onmachine/onmachine/install'\)",
            "Path(home() / '.local' / 'share' / 'omarchy' / 'onmachine' / onmachine/onmachine/install')",
            content
        )
        content = re.sub(
            r"Path\(/root/omarchy/onmachine/onmachine/install'\)",
            "Path(/root/omarchy/onmachine/onmachine/onmachine/install'),
            content
        )
        
        if content != original:
            onmachine/onmachine/install_py.write_text(content)
            changes.append(fUpdated {onmachine/install_py.name}: onmachine/onmachine/install path references")
    
    return changes

def main():
    """Main update function."""
    repo_root = Path(__file__).parent
    
    print("=" * 70)
    print("Homerchy Path Reference Updater")
    print("=" * 70)
    print("\nPath Mappings:")
    for old, new in sorted(PATH_MAPPINGS.items()):
        print(f"  {old} → {new}")
    print()
    
    # Update root-level files first
    print("Updating root-level entry points...")
    root_changes = update_root_files(repo_root)
    for change in root_changes:
        print(f"✓ {change}")
    print()
    
    # Find all files
    print("Scanning for files to update...")
    files_to_check = find_files_to_update(repo_root)
    print(f"Found {len(files_to_check)} files to check\n")
    
    # Update files
    updated_count = 0
    error_count = 0
    all_changes = []
    
    for file_path in files_to_check:
        was_changed, changes = update_file(file_path)
        if was_changed:
            updated_count += 1
            all_changes.extend(changes)
            print(f"✓ Updated: {file_path.relative_to(repo_root)}")
        elif changes and "Error" in changes[0]:
            error_count += 1
            print(f"✗ Error: {file_path.relative_to(repo_root)} - {changes[0]}")
    
    print("\n" + "=" * 70)
    print(f"Summary:")
    print(f"  Root files updated: {len(root_changes)}")
    print(f"  Other files updated: {updated_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total files checked: {len(files_to_check)}")
    print("=" * 70)
    
    if updated_count > 0:
        print("\n⚠️  IMPORTANT: Review the changes and test the build!")
        print(   Run: cd homerchy && ./deployment/deployment/controller.sh -b")
    
    return 0 if error_count == 0 else 1

if __name__ == '__main__':
    exit(main())
