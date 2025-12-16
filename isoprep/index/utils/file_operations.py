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


def guaranteed_copytree(src, dst, ignore=None, show_progress=False):
    """
    Copy directory tree with guaranteed file updates.
    
    Unlike safe_copytree, this function ensures all files are copied/updated
    by checking timestamps and overwriting when source is newer or missing.
    This guarantees new files are always transferred.
    
    Args:
        src: Source directory path
        dst: Destination directory path
        ignore: Optional ignore function (returns list/set of ignored names)
        show_progress: If True, show progress indicator for long-running operations
    """
    import sys
    import time
    from utils import Colors
    
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Create destination directory
    dst_path.mkdir(parents=True, exist_ok=True)
    
    # Count total files first for progress (if showing progress)
    total_files = 0
    if show_progress:
        print(f"{Colors.YELLOW}⚠ This operation may take several minutes...{Colors.NC}")
        print(f"{Colors.BLUE}Counting files to copy...{Colors.NC}", end='', flush=True)
        for root, dirs, files in os.walk(src_path, followlinks=False):
            if ignore:
                ignored = ignore(root, dirs + files)
                if isinstance(ignored, (list, tuple)):
                    ignored_set = set(ignored)
                elif isinstance(ignored, set):
                    ignored_set = ignored
                else:
                    ignored_set = set()
                files = [f for f in files if f not in ignored_set]
            total_files += len(files)
        if show_progress:
            print(f"\r{Colors.GREEN}✓ Found {total_files} files to copy{Colors.NC}")
            print(f"{Colors.BLUE}Copying files...{Colors.NC}", end='', flush=True)
    
    copied_files = 0
    spinner_chars = ['|', '/', '-', '\\']
    spinner_idx = 0
    last_update = time.time()
    
    # Walk source directory and copy/update all files
    # Use followlinks=False to prevent following symlinks (avoids infinite loops from recursive symlinks)
    for root, dirs, files in os.walk(src_path, followlinks=False):
        # Skip if root path is suspiciously long (might be recursive symlink)
        # Linux max path length is 4096, but we'll be more conservative
        if len(str(root)) > 2000:
            continue
        
        # Filter out symlinks from dirs to prevent following them
        # Check each directory to see if it's a symlink
        dirs_to_remove = []
        for d in dirs:
            dir_path = Path(root) / d
            try:
                if dir_path.is_symlink():
                    dirs_to_remove.append(d)
            except OSError:
                # If we can't check (recursive symlink, etc.), skip it
                dirs_to_remove.append(d)
        for d in dirs_to_remove:
            dirs.remove(d)
        
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
        try:
            rel_path = Path(root).relative_to(src_path)
            dst_dir = dst_path / rel_path
        except (ValueError, OSError) as e:
            # If path resolution fails (recursive symlink), skip this directory
            if 'File name too long' in str(e) or 'ENAMETOOLONG' in str(e):
                continue
            raise
        
        # Create destination directory (handle recursive symlink errors)
        try:
            dst_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # If directory creation fails due to recursive symlink, skip this path
            if 'File name too long' in str(e) or 'ENAMETOOLONG' in str(e):
                continue
            # Re-raise if it's a different error (permission, etc.)
            raise
        
        # Copy/update all files
        for file in files:
            src_file = Path(root) / file
            dst_file = dst_dir / file
            
            # Skip if source doesn't exist (shouldn't happen, but be safe)
            if not src_file.exists():
                continue
            
            # Check if source is a symlink (use lstat to avoid following)
            is_symlink = src_file.is_symlink()
            
            # For symlinks, check if they would create problematic paths
            if is_symlink:
                try:
                    symlink_target = src_file.readlink()
                    # Check if symlink target would create a problematic path
                    # Skip symlinks that point to paths containing work directory, profile, or archiso-tmp
                    problematic_patterns = [
                        'HOMERCHY_WORK_DIR',
                        'homerchy-isoprep-work',
                        '/profile/',
                        '/archiso-tmp/',
                        'archiso-tmp',
                    ]
                    target_str = str(symlink_target)
                    if any(pattern in target_str for pattern in problematic_patterns):
                        # Skip this symlink - it would create a problematic path
                        continue
                    
                    # For relative symlinks, check if they would resolve to a very long path
                    if not symlink_target.is_absolute():
                        # Skip symlinks with too many ../ components (likely to cause issues)
                        target_str = str(symlink_target)
                        if target_str.count('../') > 3:
                            # Too many parent directory references - skip to avoid issues
                            continue
                        
                        # Try to resolve the symlink target relative to the source file's parent
                        try:
                            resolved_target = (src_file.parent / symlink_target).resolve()
                            # Check if resolved path is suspiciously long or contains problematic patterns
                            resolved_str = str(resolved_target)
                            if len(resolved_str) > 1000 or any(pattern in resolved_str for pattern in problematic_patterns):
                                # Skip this symlink - it would create a problematic path
                                continue
                        except (OSError, RuntimeError, ValueError):
                            # If we can't resolve it, skip it to be safe
                            continue
                except (OSError, RuntimeError):
                    # If we can't read the symlink, skip it to be safe
                    continue
            
            # Copy if destination doesn't exist or source is newer
            try:
                # For symlinks, check existence without following (use lstat)
                # This prevents infinite loops from recursive symlinks
                # Wrap in try/except to handle recursive symlinks gracefully
                if is_symlink:
                    try:
                        dst_exists = dst_file.is_symlink() or dst_file.exists()
                    except OSError as check_err:
                        # If checking existence fails (recursive symlink), assume it doesn't exist
                        # and we'll copy it (which will fail gracefully if needed)
                        if 'File name too long' in str(check_err) or 'ENAMETOOLONG' in str(check_err):
                            dst_exists = False
                        else:
                            raise
                else:
                    dst_exists = dst_file.exists()
                
                if not dst_exists:
                    shutil.copy2(src_file, dst_file, follow_symlinks=False)
                    copied_files += 1
                    # Update progress spinner more frequently for large file counts
                    # Update every 1% progress, every 100 files, or every 0.2 seconds
                    if show_progress:
                        should_update = False
                        if total_files > 0:
                            progress_pct = int((copied_files / total_files) * 100)
                            # Update every 1% or every 100 files
                            should_update = (copied_files % 100 == 0) or (copied_files % max(1, total_files // 100) == 0)
                        else:
                            should_update = (copied_files % 100 == 0)
                        # Also update based on time
                        should_update = should_update or (time.time() - last_update > 0.2)
                        
                        if should_update:
                            spinner_idx = (spinner_idx + 1) % len(spinner_chars)
                            progress_pct = int((copied_files / total_files) * 100) if total_files > 0 else 0
                            print(f"\r{Colors.BLUE}Copying files... {spinner_chars[spinner_idx]} {copied_files}/{total_files} ({progress_pct}%){Colors.NC}", end='', flush=True)
                            last_update = time.time()
                else:
                    # Check if source is newer (use lstat for symlinks to avoid following)
                    if is_symlink:
                        src_mtime = src_file.lstat().st_mtime
                        # For destination, try lstat first (if it's a symlink), fallback to stat
                        # Handle recursive symlinks that cause "File name too long"
                        try:
                            dst_mtime = dst_file.lstat().st_mtime
                        except OSError as lstat_err:
                            # If lstat fails due to recursive symlink, skip timestamp check and copy
                            if 'File name too long' in str(lstat_err) or 'ENAMETOOLONG' in str(lstat_err):
                                # Remove destination and copy (skip timestamp check)
                                try:
                                    if dst_file.is_symlink() or dst_file.exists():
                                        dst_file.unlink()
                                except OSError:
                                    pass  # Skip if we can't remove it
                                shutil.copy2(src_file, dst_file, follow_symlinks=False)
                                copied_files += 1
                                if show_progress and (copied_files % 10 == 0 or time.time() - last_update > 0.1):
                                    spinner_idx = (spinner_idx + 1) % len(spinner_chars)
                                    progress_pct = int((copied_files / total_files) * 100) if total_files > 0 else 0
                                    print(f"\r{Colors.BLUE}Copying files... {spinner_chars[spinner_idx]} {copied_files}/{total_files} ({progress_pct}%){Colors.NC}", end='', flush=True)
                                    last_update = time.time()
                                continue
                            # For other errors, try stat as fallback
                            try:
                                dst_mtime = dst_file.stat().st_mtime
                            except (OSError, RuntimeError):
                                # If both fail, skip this file
                                continue
                        except (RuntimeError, ValueError):
                            # Non-OS errors, try stat as fallback
                            try:
                                dst_mtime = dst_file.stat().st_mtime
                            except (OSError, RuntimeError):
                                continue
                    else:
                        src_mtime = src_file.stat().st_mtime
                        dst_mtime = dst_file.stat().st_mtime
                    
                    if src_mtime > dst_mtime:
                        # Remove existing destination before copying
                        # Wrap in try/except to handle recursive symlinks
                        try:
                            if dst_file.exists() or dst_file.is_symlink():
                                dst_file.unlink()
                        except OSError as unlink_err:
                            # If checking/removing fails due to recursive symlink, skip
                            if 'File name too long' in str(unlink_err) or 'ENAMETOOLONG' in str(unlink_err):
                                continue
                            raise
                        shutil.copy2(src_file, dst_file, follow_symlinks=False)
                        copied_files += 1
                        # Update progress spinner
                        if show_progress and (copied_files % 10 == 0 or time.time() - last_update > 0.1):
                            spinner_idx = (spinner_idx + 1) % len(spinner_chars)
                            progress_pct = int((copied_files / total_files) * 100) if total_files > 0 else 0
                            print(f"\r{Colors.BLUE}Copying files... {spinner_chars[spinner_idx]} {copied_files}/{total_files} ({progress_pct}%){Colors.NC}", end='', flush=True)
                            last_update = time.time()
            except (OSError, shutil.Error) as e:
                # Handle FileExistsError for symlinks (destination already exists)
                if 'File exists' in str(e) or 'FileExistsError' in str(type(e).__name__):
                    # Remove existing destination and retry (use unlink which works for symlinks)
                    try:
                        # Wrap existence check in try/except for recursive symlinks
                        try:
                            if dst_file.is_symlink() or dst_file.exists():
                                dst_file.unlink()
                        except OSError as check_err:
                            # If checking fails due to recursive symlink, try unlink anyway
                            if 'File name too long' in str(check_err) or 'ENAMETOOLONG' in str(check_err):
                                try:
                                    dst_file.unlink()
                                except OSError:
                                    pass  # Skip if we can't remove it
                            else:
                                raise
                        shutil.copy2(src_file, dst_file, follow_symlinks=False)
                        copied_files += 1
                        if show_progress and (copied_files % 10 == 0 or time.time() - last_update > 0.1):
                            spinner_idx = (spinner_idx + 1) % len(spinner_chars)
                            progress_pct = int((copied_files / total_files) * 100) if total_files > 0 else 0
                            print(f"\r{Colors.BLUE}Copying files... {spinner_chars[spinner_idx]} {copied_files}/{total_files} ({progress_pct}%){Colors.NC}", end='', flush=True)
                            last_update = time.time()
                    except (OSError, shutil.Error):
                        # Skip if we still can't copy (broken symlink, permission, etc.)
                        pass
                # Handle "File name too long" - indicates recursive symlink loop
                elif 'File name too long' in str(e) or 'ENAMETOOLONG' in str(e):
                    # Skip recursive symlinks that create infinite paths
                    pass
                # Skip missing files or broken symlinks
                elif 'No such file or directory' not in str(e):
                    raise
    
    # Clear progress line and show completion
    if show_progress:
        # Clear the progress line
        print(f"\r{' ' * 80}\r", end='', flush=True)
        # Only show completion if files were actually copied
        if copied_files > 0:
            print(f"{Colors.GREEN}✓ Copied {copied_files} files{Colors.NC}")
        else:
            # If no files copied (all skipped), show a brief message
            print(f"{Colors.BLUE}✓ No files needed copying (all up to date or skipped){Colors.NC}")

