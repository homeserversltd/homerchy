#!/usr/onmachine/onmachine/bin/env python3
"""
Path Reference Scanner for Homerchy Reorganization
Scans the entire homerchy directory for path references that need updating after reorganization.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set

# Directories to scan for references
HOMERCHY_DIRS = [
    onmachine/onmachine/install', deployment/deployment/isoprep', deployment/deployment/iso-builder', deployment/deployment/prebuild', deployment/deployment/controller',
    onmachine/onmachine/config', onmachine/onmachine/default', onmachine/onmachine/themes', onmachine/onmachine/applications', onmachine/onmachine/autostart', onmachine/onmachine/bin',
    deployment/deployment/merge-tool', deployment/deployment/migrations', deployment/deployment/vmtools'
]

# Patterns to match path references
PATTERNS = [
    # Python imports and paths
    (r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', 'python_import'),
    (r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'python_import'),
    (r'Path\(["\']([^"\']+)[\]\), path_constructor),
    (ros\.path\.join\(([^)]+)\), os_path_join),
    (r[\]([^\]*(?:onmachine/onmachine/install|deployment/deployment/isoprep|deployment/deployment/iso-builder|deployment/deployment/prebuild|deployment/deployment/controller|onmachine/onmachine/config|onmachine/onmachine/default|onmachine/onmachine/themes|onmachine/onmachine/applications|onmachine/onmachine/autostart|onmachine/onmachine/bin|deployment/deployment/merge-tool|deployment/deployment/migrations|deployment/deployment/vmtools)[^"\']*)["\']', 'string_path'),
    (r'["\']([^"\']*\.\./[^"\']*)["\']', 'relative_path'),
    (r'["\']([^"\']*\./[^"\']*)["\'], relative_path),
    
    # Shell/bash paths
    (r\$\{?([A-Z_]+)\}?/, env_var_path),
    (r([a-zA-Z_][a-zA-Z0-9_]*)/, directory_reference),
    
    # JSON paths
    (r([^]*(?:onmachine/onmachine/install|deployment/deployment/isoprep|deployment/deployment/iso-builder|deployment/deployment/prebuild|deployment/deployment/controller|onmachine/onmachine/config|onmachine/onmachine/default|onmachine/onmachine/themes|onmachine/onmachine/applications|onmachine/onmachine/autostart|onmachine/onmachine/bin|deployment/deployment/merge-tool|deployment/deployment/migrations|deployment/deployment/vmtools)[^"]*)"', 'json_path'),
    
    # sys.path manipulations
    (r'sys\.path\.insert\([^,]+,\s*["\']([^"\']+)["\']\)', 'sys_path_insert'),
    (r'sys\.path\.append\(["\']([^"\']+)["\']\)', 'sys_path_append'),
]

def scan_file(file_path: Path, repo_root: Path) -> List[Dict]:
    """Scan a single file for path references."""
    references = []
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return references
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pattern, ref_type in PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                matched_text = match.group(1) if match.groups() else match.group(0)
                
                # Check if this looks like a path reference
                if any(dir_name in matched_text for dir_name in HOMERCHY_DIRS):
                    # Calculate relative path from repo root
                    rel_path = file_path.relative_to(repo_root)
                    
                    references.append({
                        'file': str(rel_path),
                        'line': line_num,
                        'type': ref_type,
                        'match': matched_text,
                        'full_line': line.strip(),
                        'context': get_context(lines, line_num)
                    })
    
    return references

def get_context(lines: List[str], line_num: int, context_lines: int = 2) -> List[str]:
    """Get context lines around the matched line."""
    start = max(0, line_num - context_lines - 1)
    end = min(len(lines), line_num + context_lines)
    return [f"{i+1:4d}: {line}" for i, line in enumerate(lines[start:end], start=start)]

def scan_directory(directory: Path, repo_root: Path) -> List[Dict]:
    """Recursively scan a directory for path references."""
    all_references = []
    
    # File extensions to scan
    extensions = {'.py', '.sh', '.bash', '.json', '.md', '.txt', '.conf', .onmachine/onmachine/config', '.yaml', '.yml'}
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules', '.git'}]
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip hidden files and common ignore patterns
            if file.startswith('.') or file.endswith('.pyc'):
                continue
            
            # Only scan relevant file types
            if file_path.suffix in extensions or file in {'Makefile', 'Dockerfile'}:
                refs = scan_file(file_path, repo_root)
                all_references.extend(refs)
    
    return all_references

def main():
    """Main scanning function."""
    repo_root = Path(__file__).parent
    homerchy_root = repo_root
    
    print(f"Scanning {homerchy_root} for path references...")
    
    all_references = scan_directory(homerchy_root, repo_root)
    
    # Also scan root-level files
    for file in homerchy_root.iterdir():
        if file.is_file() and file.suffix in {'.py', '.sh', '.bash'}:
            refs = scan_file(file, repo_root)
            all_references.extend(refs)
    
    # Group by file
    by_file = {}
    for ref in all_references:
        file_path = ref['file']
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(ref)
    
    # Save results
    output_file = homerchy_root / '.path-refs.json'
    output_data = {
        '_comment': 'Path references found in homerchy codebase. Update these after reorganization.',
        'scanned_at': str(Path(__file__).stat().st_mtime),
        'total_references': len(all_references),
        'files_with_references': len(by_file),
        'references': all_references,
        'by_file': {k: len(v) for k, v in by_file.items()}
    }
    
    output_file.write_text(json.dumps(output_data, indent=2))
    
    print(f"\nFound {len(all_references)} path references in {len(by_file)} files")
    print(f"Results saved to: {output_file}")
    
    # Print summary by type
    by_type = {}
    for ref in all_references:
        ref_type = ref['type']
        by_type[ref_type] = by_type.get(ref_type, 0) + 1
    
    print("\nReferences by type:")
    for ref_type, count in sorted(by_type.items()):
        print(f"  {ref_type}: {count}")

if __name__ == '__main__':
    main()
