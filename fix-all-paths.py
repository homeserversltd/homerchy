#!/usr/bin/env python3
""
Comprehensive Path Reference Updater for Homerchy
Updates all path references to match new structure:
- deployment/deployment/install/ (installation framework)
- src/ (runtime files: config, default, themes, applications, autostart, bin)
- images/ (image assets)
"

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Path mappings: old_path -> new_path
PATH_MAPPINGS = {
    # Install moved to deployment
    deployment/deployment/install/: deployment/install/,
    deployment/deployment/install/: deployment/install/,
    deployment/deployment/install: deployment/install,
    deployment/deployment/install: deployment/install',
    /deployment/install: /deployment/deployment/install,
    deployment/deployment/install: "deployment/deployment/install",
    deployment/deployment/install: 'deployment/deployment/install',
    
    # Other runtime files moved to src/
    src/config/: 'src/config/',
    src/default/: 'src/default/',
    src/themes/: 'src/themes/',
    src/applications/: 'src/applications/',
    src/autostart/: 'src/autostart/',
    src/bin/: 'src/bin/',
    src/config: 'src/config',
    src/default: 'src/default',
    src/themes: 'src/themes',
    src/applications: 'src/applications',
    src/autostart: 'src/autostart',
    src/bin: 'src/bin',
}

def update_path_in_string(text: str, file_path: Path) -> Tuple[str, bool]:
    """Update path references in a string. Returns (updated_text, was_changed)"""
    original = text
    updated = text
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_mappings = sorted(PATH_MAPPINGS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for old_path, new_path in sorted_mappings:
        # Escape special regex characters
        old_escaped = re.escape(old_path)
        
        # Handle various path reference patterns
        patterns = [
            # Direct path references in quotes
            (rf'["\']([^"\']*){old_escaped}([^"\']*)["\']', rf'\1{new_path}\2'),
            # Path() constructors
            (rf'Path\(["\']([^"\']*){old_escaped}([^"\']*)["\']\)', rf'Path("\1{new_path}\2")'),
            # os.path.join
            (rf'os\.path\.join\(([^)]*){old_escaped}([^)]*)\)', rf'os.path.join(\1{new_path}\2)'),
            # Relative paths
            (rf'\.\./{old_escaped}', f'../{new_path}'),
            (rf'\./{old_escaped}', f'./{new_path}'),
            # Path operations
            (rf' / ["\']{old_escaped}', f' / "{new_path}'),
            (rf' / {old_escaped}', f' / {new_path}'),
        ]
        
        for pattern, replacement in patterns:
            updated = re.sub(pattern, replacement, updated)
    
    # Handle sys.path manipulations
    for old_path, new_path in sorted_mappings:
        old_escaped = re.escape(old_path)
        updated = re.sub(
            rf'sys\.path\.insert\([^,]+,\s*["\']([^"\']*){old_escaped}([^"\']*)["\']',
            rf'sys.path.insert(0, "\1{new_path}\2"',
            updated
        )
        updated = re.sub(
            rf'sys\.path\.append\(["\']([^"\']*){old_escaped}([^"\']*)["\']',
            rf'sys.path.append("\1{new_path}\2"',
            updated
        )
    
    was_changed = (original != updated)
    return updated, was_changed

def update_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Update path references in a file. Returns (was_changed, list_of_changes)"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    updated_content, was_changed = update_path_in_string(content, file_path)
    
    if not was_changed:
        return False, []
    
    try:
        file_path.write_text(updated_content, encoding='utf-8')
        return True, [f"Updated {file_path}"]
    except Exception as e:
        return False, [f"Error writing file: {e}"]

def find_files_to_update(directory: Path) -> List[Path]:
    """Find all files that might contain path references."""
    files_to_check = []
    extensions = {'.py', '.sh', '.bash', '.json', '.md', '.txt', '.conf', '.config', '.yaml', '.yml', '.script', '.plymouth', '.desktop'}
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules', '.git', 'images'}]
        
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
    """Update root-level entry point files."""
    changes = []
    
    # Update install.py in deployment/
    install_py = repo_root / 'deployment' / 'install.py
    if install_py.exists():
        content = install_py.read_text()
        original = content
        
        # Update install path references to deployment/deployment/install
        content = re.sub(
            rPath\(__file__\)\.parent / ['\"]onmachine['\"] / ['\"]install['\"]",
            Path(__file__).parent / deployment/deployment/install,
            content
        )
        content = re.sub(
            r"Path\(__file__\)\.parent\.parent / ['\"]src['\"] / ['\"]install['\"]",
            Path(__file__).parent / deployment/deployment/install,
            content
        )
        content = re.sub(
            r"omarchy_path / ['\"]onmachine['\"] / ['\"]install['\"]",
            "omarchy_path / 'deployment / deployment/deployment/install,
            content
        )
        content = re.sub(
            r"omarchy_path / ['\"]install['\"]",
            "omarchy_path / 'deployment / deployment/deployment/install,
            content
        )
        content = re.sub(
            r"if \(candidate / ['\"]onmachine['\"] / ['\"]install['\"]\)\.exists\(\):",
            "if (candidate / 'deployment / deployment/deployment/install).exists():,
            content
        )
        content = re.sub(
            r"if \(Path\('/root/omarchy'\) / ['\"]onmachine['\"] / ['\"]install['\"]\)\.exists\(\):",
            "if (Path('/root/omarchy') / 'deployment / deployment/deployment/install).exists():,
            content
        )
        content = re.sub(
            r"if \(script_dir / ['\"]onmachine['\"] / ['\"]install['\"]\)\.exists\(\):",
            "if (script_dir / 'deployment / deployment/deployment/install).exists():,
            content
        )
        content = re.sub(
            r"Path\(home\(\) / '\.local' / 'share' / 'omarchy' / ['\"]onmachine['\"] / ['\"]install['\"]\)",
            "Path(home() / '.local' / 'share' / 'omarchy' / 'deployment / deployment/deployment/install),
            content
        )
        content = re.sub(
            rPath\(/root/omarchy/deployment/deployment/install\),
            "Path(/root/omarchy/deployment/deployment/install)",
            content
        )
        content = re.sub(
            rPath\(/root/omarchy/deployment/deployment/install\),
            "Path(/root/omarchy/deployment/deployment/install)",
            content
        )
        # Update bin path to src/bin
        content = re.sub(
            r"omarchy_path / ['\"]onmachine['\"] / ['\"]bin['\"]",
            "omarchy_path / 'src' / 'bin'",
            content
        )
        content = re.sub(
            r"omarchy_path / ['\"]bin['\"]",
            "omarchy_path / 'src' / 'bin'",
            content
        )
        
        if content != original:
            install_py.write_text(content)
            changes.append(f"Updated {install_py.name}: install path references")
    
    return changes

def main():
    """Main update function."""
    repo_root = Path(__file__).parent
    
    print("=" * 70)
    print("Homerchy Path Reference Updater - Final Structure")
    print("=" * 70)
    print("\nPath Mappings:")
    print(  install/ → deployment/deployment/install/)
    print("  onmachine/* → src/* (except install)")
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
    
    for file_path in files_to_check:
        was_changed, changes = update_file(file_path)
        if was_changed:
            updated_count += 1
            if updated_count <= 30:  # Show first 30
                print(f"✓ Updated: {file_path.relative_to(repo_root)}")
        elif changes and "Error" in changes[0]:
            error_count += 1
            print(f"✗ Error: {file_path.relative_to(repo_root)} - {changes[0]}")
    
    if updated_count > 30:
        print(f"... and {updated_count - 30} more files")
    
    print("\n" + "=" * 70)
    print(f"Summary:")
    print(f"  Root files updated: {len(root_changes)}")
    print(f"  Other files updated: {updated_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total files checked: {len(files_to_check)}")
    print("=" * 70)
    
    if updated_count > 0 or root_changes:
        print("\n⚠️  IMPORTANT: Review the changes and test the build!")
        print("   Run: cd homerchy && ./controller.sh -b")
    
    return 0 if error_count == 0 else 1

if __name__ == '__main__':
    exit(main())
