#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - File Operations Utility
Copyright (C) 2024 HOMESERVER LLC

Safe file and directory copy operations for ISO build process.
"""

import os
import shutil
from pathlib import Path


def safe_copytree(src, dst, dirs_exist_ok=False, ignore=None):
    """
    Safely copy directory tree, skipping missing files and broken symlinks.
    
    This is a wrapper around shutil.copytree that handles cases where
    files or symlinks in the source don't exist (common in archiso configs).
    
    Args:
        src: Source directory path
        dst: Destination directory path
        dirs_exist_ok: Allow destination directory to exist
        ignore: Optional ignore function (will be combined with missing file ignore)
    """
    def ignore_missing(path, names):
        """Ignore function that skips missing files and broken symlinks."""
        ignored = []
        for name in names:
            full_path = Path(path) / name
            try:
                # Check if path exists (this works for files, dirs, and symlinks)
                if not full_path.exists() and not full_path.is_symlink():
                    # File/dir doesn't exist and it's not a symlink
                    ignored.append(name)
                elif full_path.is_symlink():
                    # For symlinks, check if target exists
                    try:
                        target = full_path.readlink()
                        # If absolute symlink, check absolute path
                        if target.is_absolute():
                            if not target.exists():
                                ignored.append(name)
                        # If relative symlink, resolve relative to symlink's parent
                        else:
                            resolved = (full_path.parent / target).resolve()
                            if not resolved.exists():
                                ignored.append(name)
                    except (OSError, RuntimeError):
                        # Can't read symlink or resolve it - skip it
                        ignored.append(name)
            except (OSError, RuntimeError):
                # Can't stat the file - skip it
                ignored.append(name)
        return ignored
    
    def combined_ignore(path, names):
        """Combine missing file ignore with user-provided ignore function."""
        ignored_set = set(ignore_missing(path, names))
        if ignore:
            user_ignored = ignore(path, names)
            if isinstance(user_ignored, (list, tuple)):
                ignored_set.update(user_ignored)
            elif isinstance(user_ignored, set):
                ignored_set.update(user_ignored)
        return list(ignored_set)
    
    try:
        shutil.copytree(src, dst, dirs_exist_ok=dirs_exist_ok, 
                       ignore=combined_ignore if ignore else ignore_missing, 
                       ignore_dangling_symlinks=True)
    except shutil.Error as e:
        # Filter out errors about missing files (they're already ignored)
        errors = []
        for error in e.args[0]:
            src_path, dst_path, error_msg = error
            # Only keep errors that aren't about missing files
            if 'No such file or directory' not in str(error_msg):
                errors.append(error)
        if errors:
            raise shutil.Error(errors)


def guaranteed_copytree(src, dst, ignore=None):
    """
    Copy directory tree with guaranteed file updates.
    
    Unlike safe_copytree, this function ensures all files are copied/updated
    by checking timestamps and overwriting when source is newer or missing.
    This guarantees new files are always transferred.
    
    Args:
        src: Source directory path
        dst: Destination directory path
        ignore: Optional ignore function (returns list/set of ignored names)
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Create destination directory
    dst_path.mkdir(parents=True, exist_ok=True)
    
    # Walk source directory and copy/update all files
    for root, dirs, files in os.walk(src_path):
        # Apply ignore function to filter dirs and files
        if ignore:
            ignored = ignore(root, dirs + files)
            if isinstance(ignored, (list, tuple)):
                ignored_set = set(ignored)
            elif isinstance(ignored, set):
                ignored_set = ignored
            else:
                ignored_set = set()
            dirs[:] = [d for d in dirs if d not in ignored_set]
            files = [f for f in files if f not in ignored_set]
        
        # Calculate relative path from source root
        rel_path = Path(root).relative_to(src_path)
        dst_dir = dst_path / rel_path
        
        # Create destination directory
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy/update all files
        for file in files:
            src_file = Path(root) / file
            dst_file = dst_dir / file
            
            # Skip if source doesn't exist (shouldn't happen, but be safe)
            if not src_file.exists():
                continue
            
            # Copy if destination doesn't exist or source is newer
            try:
                if not dst_file.exists():
                    shutil.copy2(src_file, dst_file, follow_symlinks=False)
                else:
                    # Check if source is newer
                    src_mtime = src_file.stat().st_mtime
                    dst_mtime = dst_file.stat().st_mtime
                    if src_mtime > dst_mtime:
                        shutil.copy2(src_file, dst_file, follow_symlinks=False)
            except (OSError, shutil.Error) as e:
                # Skip missing files or broken symlinks
                if 'No such file or directory' not in str(e):
                    raise

