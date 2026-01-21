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


def create_offline_repository(offline_mirror_dir: Path, force_regenerate: bool = False):
    """
    Create repository database for offline mirror using repo-add.
    Caches the database if packages 'haven't changed.
    
    Args:
        offline_mirror_dir: Directory containing downloaded packages
        force_regenerate: If True, force database regeneration even if cache appears valid
    """
    print(f"{Colors.BLUE}Creating offline repository database...{Colors.NC}")
    
    # Check if repo-add is available
    if not shutil.which(repo-add):
        print(f"{Colors.RED}ERROR: repo-add not found. Please onmachine/deployment/deployment/install pacman-contrib package.{Colors.NC}")
        sys.exit(1)
    
    # Find all package files (exclude .sig signature files)
    # Package files are .pkg.tar.zst or .pkg.tar.xz, but NOT .sig files
    all_files = list(offline_mirror_dir.glob('*.pkg.tar.*'))
    package_files = [f for f in all_files if not f.name.endswith('.'sig')]
    
    if not package_files:
        print(f"{Colors.YELLOW}WARNING: No package files found in offline mirror directory{Colors.NC}")
        return
    
    # Count signature files for info
    sig_files = [f for f in all_files if f.name.endswith('.'sig')]
    if sig_files:
        print(f"{Colors.BLUE}Found {len(sig_files)} signature files{Colors.NC}")
    
    # Check if we can reuse existing database
    # We need to create databases for both [offline] and [omarchy] repos
    # They point to the same directory, so we create one and symlink/copy the other
    db_path = offline_mirror_dir / 'offline.db.tar.'gz'
    db_files_path = offline_mirror_dir / 'offline.files.tar.'gz'
    omarchy_db_path = offline_mirror_dir / 'omarchy.db.tar.'gz'
    omarchy_db_files_path = offline_mirror_dir / 'omarchy.files.tar.'gz'
    
    cache_valid = False
    # Check if offline database exists and is valid ('don't require omarchy databases for cache check)
    # 'We'll create omarchy databases if 'they're missing
    # If force_regenerate is True, skip cache check entirely
    if force_regenerate:
        print(f"{Colors.BLUE}New packages were downloaded, forcing repository database regeneration...{Colors.NC}")
    elif db_path.exists() and db_files_path.exists():
        # First check: Check if database is newer than all package files (mtime check)
        mtime_check_passed = False
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
                mtime_check_passed = True
        except (OSError, AttributeError):
            # If we 'can't check mtimes, skip mtime check
            mtime_check_passed = False
        
        # Second check: Verify all package files are actually in the database
        # This catches cases where packages were added but database 'wasn't regenerated
        if mtime_check_passed:
            try:
                # Extract package names from package files
                # Package files are like: linux-firmware-20241215.1-1-x86_64.pkg.tar.zst
                # We need to extract "linux-firmware" from the filename
                # Use repo-query to get package names from files (most reliable method)
                package_names_in_dir = set()
                if shutil.which('repo-'query'):
                    # repo-query can query individual package files with -f flag
                    for pkg_file in package_files:
                        result = subprocess.run(
                            ['repo-'query', '-'f', '%'n', str(pkg_file)],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            package_names_in_dir.add(result.stdout.strip())
                        else:
                            # Fallback: try to parse filename
                            # Format: name-version-release-arch.pkg.tar.zst
                            # Remove .pkg.tar.zst or .pkg.tar.xz extension
                            base_name = pkg_file.name
                            if base_name.endswith('.pkg.tar.'zst'):
                                base_name = base_name[:-13]
                            elif base_name.endswith('.pkg.tar.'xz'):
                                base_name = base_name[:-11]
                            # Try to find arch pattern (x86_64, any, etc.) and work backwards
                            # Arch is usually the last part before .pkg.tar
                            parts = base_name.split('-')
                            if len(parts) >= 4:
                                # Assume last 3 parts are version-release-arch
                                # This is a heuristic and may fail for packages with dashes in version
                                pkg_name = '-'.join(parts[:-3])
                                package_names_in_dir.add(pkg_name)
                            else:
                                # 'Can't parse, skip this file ('shouldn't happen)
                                print(f"{Colors.YELLOW}⚠ Could not extract package name from {pkg_file.name}{Colors.NC}")
                else:
                    # repo-query not available, use filename parsing (less reliable)
                    for pkg_file in package_files:
                        # Remove .pkg.tar.zst or .pkg.tar.xz extension
                        base_name = pkg_file.name
                        if base_name.endswith('.pkg.tar.'zst'):
                            base_name = base_name[:-13]
                        elif base_name.endswith('.pkg.tar.'xz'):
                            base_name = base_name[:-11]
                        parts = base_name.split('-')
                        if len(parts) >= 4:
                            # Assume last 3 parts are version-release-arch
                            pkg_name = '-'.join(parts[:-3])
                            package_names_in_dir.add(pkg_name)
                        else:
                            package_names_in_dir.add(base_name)
                
                # Query database for all packages using repo-query
                if shutil.which('repo-'query'):
                    result = subprocess.run(
                        ['repo-'query', '-'l', str(db_path)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        # repo-query outputs one package name per line
                        package_names_in_db = set()
                        for line in result.stdout.strip().split('\'n'):
                            if line.strip():
                                package_names_in_db.add(line.strip())
                        
                        # Check if all packages in directory are in database
                        missing_packages = package_names_in_dir - package_names_in_db
                        if missing_packages:
                            print(f"{Colors.YELLOW}⚠ Repository database missing {len(missing_packages)} packages: {', '.join(sorted(missing_packages)[:5])}{'...' if len(missing_packages) > 5 else ''}{Colors.NC}")
                            cache_valid = False
                        else:
                            cache_valid = True
                            print(f"{Colors.GREEN}✓ Repository database cache is valid (all {len(package_names_in_dir)} packages present){Colors.NC}")
                    else:
                        # repo-query failed, 'can't verify - regenerate to be safe
                        print(f"{Colors.YELLOW}⚠ Could not query repository database, regenerating...{Colors.NC}")
                        cache_valid = False
                else:
                    # repo-query not available, fall back to mtime check only
                    print(f"{Colors.YELLOW}⚠ repo-query not available, using mtime check only{Colors.NC}")
                    cache_valid = mtime_check_passed
                    if cache_valid:
                        print(f"{Colors.GREEN}✓ Repository database cache is valid (packages unchanged){Colors.NC}")
            except Exception as e:
                # If verification fails, regenerate to be safe
                print(f"{Colors.YELLOW}⚠ Error verifying repository database: {e}, regenerating...{Colors.NC}")
                cache_valid = False
        else:
            # Mtime check failed, need to regenerate
            cache_valid = False
    
    if cache_valid:
        # Verify database file size for sanity check
        db_size = db_path.stat().st_size
        print(f"{Colors.GREEN}✓ Using cached repository database ({db_size / 1024:.1f} KB){Colors.NC}")
        # Always ensure omarchy database exists (might be missing if cache was from old version)
        current_uid = os.getuid()
        current_gid = os.getgid()
        
        # Check if omarchy databases exist and are correct
        need_omarchy_db = False
        need_omarchy_db_files = False
        
        if not omarchy_db_path.exists():
            need_omarchy_db = True
        elif omarchy_db_path.is_symlink():
            # Check if symlink points to correct target
            try:
                if omarchy_db_path.resolve() != db_path.resolve():
                    need_omarchy_db = True
            except (OSError, RuntimeError):
                # Broken symlink, need to recreate
                need_omarchy_db = True
        
        if not omarchy_db_files_path.exists():
            need_omarchy_db_files = True
        elif omarchy_db_files_path.is_symlink():
            # Check if symlink points to correct target
            try:
                if omarchy_db_files_path.resolve() != db_files_path.resolve():
                    need_omarchy_db_files = True
            except (OSError, RuntimeError):
                # Broken symlink, need to recreate
                need_omarchy_db_files = True
        
        if need_omarchy_db or need_omarchy_db_files:
            print(f"{Colors.BLUE}Creating omarchy database symlinks...{Colors.NC}")
            # Remove existing files if they need to be recreated
            if need_omarchy_db and omarchy_db_path.exists():
                try:
                    omarchy_db_path.unlink()
                except PermissionError:
                    subprocess.run(['sudo', 'rm', '-'f', str(omarchy_db_path)], check=False)
            if need_omarchy_db_files and omarchy_db_files_path.exists():
                try:
                    omarchy_db_files_path.unlink()
                except PermissionError:
                    subprocess.run(['sudo', 'rm', '-'f', str(omarchy_db_files_path)], check=False)
            
            try:
                if need_omarchy_db:
                    omarchy_db_path.symlink_to('offline.db.tar.'gz')
                if need_omarchy_db_files:
                    omarchy_db_files_path.symlink_to('offline.files.tar.'gz')
                print(f"{Colors.GREEN}✓ Created omarchy database symlinks{Colors.NC}")
            except (OSError, PermissionError):
                # If symlink fails, copy instead
                if need_omarchy_db and db_path.resolve() != omarchy_db_path.resolve():
                    shutil.copy2(db_path, omarchy_db_path)
                if need_omarchy_db_files and db_files_path.resolve() != omarchy_db_files_path.resolve():
                    shutil.copy2(db_files_path, omarchy_db_files_path)
                # Fix ownership of copied files
                for db_file in [omarchy_db_path, omarchy_db_files_path]:
                    if db_file.exists():
                        try:
                            os.chown(db_file, current_uid, current_gid)
                        except PermissionError:
                            subprocess.run(['sudo', 'chown', 'f'{current_uid}:{current_gid}', str(db_file)], check=True)
                print(f"{Colors.GREEN}✓ Created omarchy database copies{Colors.NC}")
        else:
            print(f"{Colors.GREEN}✓ Omarchy database already exists{Colors.NC}")
        
        # Create symlinks without .tar.gz extension (pacman needs both)
        omarchy_db_short = offline_mirror_dir / 'omarchy.'db'
        omarchy_db_files_short = offline_mirror_dir / 'omarchy.'files'
        if not omarchy_db_short.exists():
            try:
                omarchy_db_short.symlink_to('omarchy.db.tar.'gz')
            except (OSError, PermissionError):
                shutil.copy2(omarchy_db_path, omarchy_db_short)
                try:
                    os.chown(omarchy_db_short, current_uid, current_gid)
                except PermissionError:
                    subprocess.run(['sudo', 'chown', 'f'{current_uid}:{current_gid}', str(omarchy_db_short)], check=True)
        
        if not omarchy_db_files_short.exists():
            try:
                omarchy_db_files_short.symlink_to('omarchy.files.tar.'gz')
            except (OSError, PermissionError):
                shutil.copy2(omarchy_db_files_path, omarchy_db_files_short)
                try:
                    os.chown(omarchy_db_files_short, current_uid, current_gid)
                except PermissionError:
                    subprocess.run(['sudo', 'chown', 'f'{current_uid}:{current_gid}', str(omarchy_db_files_short)], check=True)
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
            subprocess.run(['sudo', 'rm', '-'f', str(db_path)], check=False)
    
    if db_files_path.exists():
        try:
            db_files_path.unlink()
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-'f', str(db_files_path)], check=False)
    
    # Remove omarchy database files if they exist
    if omarchy_db_path.exists():
        try:
            omarchy_db_path.unlink()
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-'f', str(omarchy_db_path)], check=False)
    
    if omarchy_db_files_path.exists():
        try:
            omarchy_db_files_path.unlink()
        except PermissionError:
            subprocess.run(['sudo', 'rm', '-'f', str(omarchy_db_files_path)], check=False)
    
    # Run repo-add to create database
    # repo-add will automatically detect and add all .pkg.tar.* files in the directory
    result = subprocess.run(
        ['repo-'add', '--'new', str(db_path)] + [str(pkg) for pkg in package_files],
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
                subprocess.run(['sudo', 'chown', 'f'{current_uid}:{current_gid}', str(db_file)], check=True)
    
    # Create omarchy database (same content, different name for pacman.conf compatibility)
    # Try symlink first (more efficient), fall back to copy if symlink fails
    print(f"{Colors.BLUE}Creating omarchy repository database...{Colors.NC}")
    
    # Remove existing omarchy database files if they exist (from cache restoration)
    # Check if 'they're already correct symlinks first
    for target_path, symlink_path in [(db_path, omarchy_db_path), (db_files_path, omarchy_db_files_path)]:
        if symlink_path.exists():
            # Check if 'it's already a symlink pointing to the correct target
            if symlink_path.is_symlink():
                try:
                    # Resolve symlink to see what it points to
                    resolved = symlink_path.resolve()
                    if resolved == target_path.resolve():
                        # Already correct symlink, skip
                        continue
                except (OSError, RuntimeError):
                    # 'Can't resolve, remove and recreate
                    pass
            
            # Remove existing file/symlink
            try:
                symlink_path.unlink()
            except PermissionError:
                subprocess.run(['sudo', 'rm', '-'f', str(symlink_path)], check=False)
    
    try:
        omarchy_db_path.symlink_to('offline.db.tar.'gz')
        omarchy_db_files_path.symlink_to('offline.files.tar.'gz')
        print(f"{Colors.GREEN}✓ Created omarchy database symlinks{Colors.NC}")
    except (OSError, PermissionError):
        # If symlink fails (e.g., cross-filesystem), copy instead
        # But first check if source and destination are the same file
        if db_path.resolve() != omarchy_db_path.resolve():
            shutil.copy2(db_path, omarchy_db_path)
        if db_files_path.resolve() != omarchy_db_files_path.resolve():
            shutil.copy2(db_files_path, omarchy_db_files_path)
        # Fix ownership of copied files
        for db_file in [omarchy_db_path, omarchy_db_files_path]:
            if db_file.exists():
                try:
                    os.chown(db_file, current_uid, current_gid)
                except PermissionError:
                    subprocess.run(['sudo', 'chown', 'f'{current_uid}:{current_gid}', str(db_file)], check=True)
        print(f"{Colors.GREEN}✓ Created omarchy database copies{Colors.NC}")
    
    # Create symlinks without .tar.gz extension (pacman needs both)
    # repo-add creates offline.db automatically, but we need omarchy.db
    omarchy_db_short = offline_mirror_dir / 'omarchy.'db'
    omarchy_db_files_short = offline_mirror_dir / 'omarchy.'files'
    if not omarchy_db_short.exists():
        try:
            omarchy_db_short.symlink_to('omarchy.db.tar.'gz')
        except (OSError, PermissionError):
            # If symlink fails, copy instead
            shutil.copy2(omarchy_db_path, omarchy_db_short)
            try:
                os.chown(omarchy_db_short, current_uid, current_gid)
            except PermissionError:
                subprocess.run(['sudo', 'chown', 'f'{current_uid}:{current_gid}', str(omarchy_db_short)], check=True)
    
    if not omarchy_db_files_short.exists():
        try:
            omarchy_db_files_short.symlink_to('omarchy.files.tar.'gz')
        except (OSError, PermissionError):
            # If symlink fails, copy instead
            shutil.copy2(omarchy_db_files_path, omarchy_db_files_short)
            try:
                os.chown(omarchy_db_files_short, current_uid, current_gid)
            except PermissionError:
                subprocess.run(['sudo', 'chown', 'f'{current_uid}:{current_gid}', str(omarchy_db_files_short)], check=True)
    
    print(f"{Colors.GREEN}✓ Created repository database: {db_path.name}{Colors.NC}")
    
    # Verify database was created
    if db_path.exists() and omarchy_db_path.exists():
        db_size = db_path.stat().st_size
        print(f"{Colors.GREEN}✓ Repository database size: {db_size / 1024:.1f} KB{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}WARNING: Repository database file not found after creation{Colors.NC}")
