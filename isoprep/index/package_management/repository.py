#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Repository Creation Module
Copyright (C) 2024 HOMESERVER LLC

Create repository database for offline mirror using repo-add.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import Colors


def create_offline_repository(offline_mirror_dir: Path):
    """
    Create repository database for offline mirror using repo-add.
    Caches the database if packages haven't changed.
    
    Args:
        offline_mirror_dir: Directory containing downloaded packages
    """
    print(f"{Colors.BLUE}Creating offline repository database...{Colors.NC}")
    
    # Check if repo-add is available
    if not shutil.which('repo-add'):
        print(f"{Colors.RED}ERROR: repo-add not found. Please install 'pacman-contrib' package.{Colors.NC}")
        sys.exit(1)
    
    # Find all package files (exclude .sig signature files)
    # Package files are .pkg.tar.zst or .pkg.tar.xz, but NOT .sig files
    all_files = list(offline_mirror_dir.glob('*.pkg.tar.*'))
    package_files = [f for f in all_files if not f.name.endswith('.sig')]
    
    if not package_files:
        print(f"{Colors.YELLOW}WARNING: No package files found in offline mirror directory{Colors.NC}")
        return
    
    # Count signature files for info
    sig_files = [f for f in all_files if f.name.endswith('.sig')]
    if sig_files:
        print(f"{Colors.BLUE}Found {len(sig_files)} signature files{Colors.NC}")
    
    # Check if we can reuse existing database
    # We need to create databases for both [offline] and [omarchy] repos
    # They point to the same directory, so we create one and symlink/copy the other
    db_path = offline_mirror_dir / 'offline.db.tar.gz'
    db_files_path = offline_mirror_dir / 'offline.files.tar.gz'
    omarchy_db_path = offline_mirror_dir / 'omarchy.db.tar.gz'
    omarchy_db_files_path = offline_mirror_dir / 'omarchy.files.tar.gz'
    
    cache_valid = False
    # Check if offline database exists and is valid (don't require omarchy databases for cache check)
    # We'll create omarchy databases if they're missing
    if db_path.exists() and db_files_path.exists():
        # Check if database is newer than all package files
        try:
            db_mtime = db_path.stat().st_mtime
            db_files_mtime = db_files_path.stat().st_mtime
            # Use the older of the two database files as the reference time
            db_ref_mtime = min(db_mtime, db_files_mtime)
            
            # Check if any package file is newer than the database
            packages_changed = False
            for pkg_file in package_files:
                if pkg_file.stat().st_mtime > db_ref_mtime:
                    packages_changed = True
                    break
            
            if not packages_changed:
                cache_valid = True
                print(f"{Colors.GREEN}✓ Repository database cache is valid (packages unchanged){Colors.NC}")
        except (OSError, AttributeError):
            # If we can't check mtimes, regenerate to be safe
            cache_valid = False
    
    if cache_valid:
        # Verify database file size for sanity check
        db_size = db_path.stat().st_size
        print(f"{Colors.GREEN}✓ Using cached repository database ({db_size / 1024:.1f} KB){Colors.NC}")
        # Always ensure omarchy database exists (might be missing if cache was from old version)
        current_uid = os.getuid()
        current_gid = os.getgid()
        
        if not omarchy_db_path.exists() or not omarchy_db_files_path.exists():
            print(f"{Colors.BLUE}Creating omarchy database symlinks...{Colors.NC}")
            try:
                if not omarchy_db_path.exists():
                    omarchy_db_path.symlink_to('offline.db.tar.gz')
                if not omarchy_db_files_path.exists():
                    omarchy_db_files_path.symlink_to('offline.files.tar.gz')
                print(f"{Colors.GREEN}✓ Created omarchy database symlinks{Colors.NC}")
            except (OSError, PermissionError):
                # If symlink fails, copy instead
                shutil.copy2(db_path, omarchy_db_path)
                shutil.copy2(db_files_path, omarchy_db_files_path)
                # Fix ownership of copied files
                for db_file in [omarchy_db_path, omarchy_db_files_path]:
                    try:
                        os.chown(db_file, current_uid, current_gid)
                    except PermissionError:
                        subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(db_file)], check=True)
                print(f"{Colors.GREEN}✓ Created omarchy database copies{Colors.NC}")
        else:
            print(f"{Colors.GREEN}✓ Omarchy database already exists{Colors.NC}")
        
        # Create symlinks without .tar.gz extension (pacman needs both)
        omarchy_db_short = offline_mirror_dir / 'omarchy.db'
        omarchy_db_files_short = offline_mirror_dir / 'omarchy.files'
        if not omarchy_db_short.exists():
            try:
                omarchy_db_short.symlink_to('omarchy.db.tar.gz')
            except (OSError, PermissionError):
                shutil.copy2(omarchy_db_path, omarchy_db_short)
                try:
                    os.chown(omarchy_db_short, current_uid, current_gid)
                except PermissionError:
                    subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(omarchy_db_short)], check=True)
        
        if not omarchy_db_files_short.exists():
            try:
                omarchy_db_files_short.symlink_to('omarchy.files.tar.gz')
            except (OSError, PermissionError):
                shutil.copy2(omarchy_db_files_path, omarchy_db_files_short)
                try:
                    os.chown(omarchy_db_files_short, current_uid, current_gid)
                except PermissionError:
                    subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(omarchy_db_files_short)], check=True)
        return
    
    # Need to regenerate database
    print(f"{Colors.BLUE}Regenerating repository database from {len(package_files)} package files...{Colors.NC}")
    print(f"{Colors.YELLOW}⚠ This may take a minute for large package sets...{Colors.NC}")
    
    # Remove existing database if it exists
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            # If owned by root, use sudo to remove
            subprocess.run(['sudo', 'rm', '-f', str(db_path)], check=False)
    
    if db_files_path.exists():
        try:
            db_files_path.unlink()
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-f', str(db_files_path)], check=False)
    
    # Remove omarchy database files if they exist
    if omarchy_db_path.exists():
        try:
            omarchy_db_path.unlink()
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-f', str(omarchy_db_path)], check=False)
    
    if omarchy_db_files_path.exists():
        try:
            omarchy_db_files_path.unlink()
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-f', str(omarchy_db_files_path)], check=False)
    
    # Run repo-add to create database
    # repo-add will automatically detect and add all .pkg.tar.* files in the directory
    result = subprocess.run(
        ['repo-add', '--new', str(db_path)] + [str(pkg) for pkg in package_files],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"{Colors.RED}ERROR: Repository database creation failed!{Colors.NC}")
        print(f"{Colors.RED}repo-add output:{Colors.NC}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    
    # Fix ownership of database files (repo-add may create them as root)
    current_uid = os.getuid()
    current_gid = os.getgid()
    for db_file in [db_path, db_files_path]:
        if db_file.exists():
            try:
                os.chown(db_file, current_uid, current_gid)
            except PermissionError:
                subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(db_file)], check=True)
    
    # Create omarchy database (same content, different name for pacman.conf compatibility)
    # Try symlink first (more efficient), fall back to copy if symlink fails
    print(f"{Colors.BLUE}Creating omarchy repository database...{Colors.NC}")
    try:
        omarchy_db_path.symlink_to('offline.db.tar.gz')
        omarchy_db_files_path.symlink_to('offline.files.tar.gz')
        print(f"{Colors.GREEN}✓ Created omarchy database symlinks{Colors.NC}")
    except (OSError, PermissionError):
        # If symlink fails (e.g., cross-filesystem), copy instead
        shutil.copy2(db_path, omarchy_db_path)
        shutil.copy2(db_files_path, omarchy_db_files_path)
        # Fix ownership of copied files
        for db_file in [omarchy_db_path, omarchy_db_files_path]:
            try:
                os.chown(db_file, current_uid, current_gid)
            except PermissionError:
                subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(db_file)], check=True)
        print(f"{Colors.GREEN}✓ Created omarchy database copies{Colors.NC}")
    
    # Create symlinks without .tar.gz extension (pacman needs both)
    # repo-add creates offline.db automatically, but we need omarchy.db
    omarchy_db_short = offline_mirror_dir / 'omarchy.db'
    omarchy_db_files_short = offline_mirror_dir / 'omarchy.files'
    if not omarchy_db_short.exists():
        try:
            omarchy_db_short.symlink_to('omarchy.db.tar.gz')
        except (OSError, PermissionError):
            # If symlink fails, copy instead
            shutil.copy2(omarchy_db_path, omarchy_db_short)
            try:
                os.chown(omarchy_db_short, current_uid, current_gid)
            except PermissionError:
                subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(omarchy_db_short)], check=True)
    
    if not omarchy_db_files_short.exists():
        try:
            omarchy_db_files_short.symlink_to('omarchy.files.tar.gz')
        except (OSError, PermissionError):
            # If symlink fails, copy instead
            shutil.copy2(omarchy_db_files_path, omarchy_db_files_short)
            try:
                os.chown(omarchy_db_files_short, current_uid, current_gid)
            except PermissionError:
                subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(omarchy_db_files_short)], check=True)
    
    print(f"{Colors.GREEN}✓ Created repository database: {db_path.name}{Colors.NC}")
    
    # Verify database was created
    if db_path.exists() and omarchy_db_path.exists():
        db_size = db_path.stat().st_size
        print(f"{Colors.GREEN}✓ Repository database size: {db_size / 1024:.1f} KB{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}WARNING: Repository database file not found after creation{Colors.NC}")

