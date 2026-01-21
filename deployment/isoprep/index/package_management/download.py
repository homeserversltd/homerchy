#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - Package Download Module
Copyright (C) 2024 HOMESERVER LLC

Download packages to offline mirror directory.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import Colors, read_package_list


def download_packages_to_offline_mirror(repo_root: Path, profile_dir: Path, offline_mirror_dir: Path):
    """
    Download all required packages to the offline mirror directory.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
        offline_mirror_dir: Directory where packages will be stored
        
    Returns:
        List of package names
    """
    print(f"{Colors.BLUE}Collecting package lists...{Colors.NC}")
    
    # Collect all package lists
    all_packages = set()
    
    # 1. ISO base packages (packages.x86_64)
    packages_x86_64 = profile_dir / 'packages.x86_64'
    if packages_x86_64.exists():
        packages = read_package_list(packages_x86_64)
        all_packages.update(packages)
        print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from packages.x86_64{Colors.NC}")
    
    # 2. Homerchy base packages
    omarchy_base = repo_root / 'homerchy' / 'deployment' / 'install' / 'omarchy-base.packages'
    if omarchy_base.exists():
        packages = read_package_list(omarchy_base)
        all_packages.update(packages)
        print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-base.packages{Colors.NC}")
    else:
        # Try alternative path (if called from different location)
        omarchy_base = repo_root / 'deployment' / 'install' / 'omarchy-base.packages'
        if omarchy_base.exists():
            packages = read_package_list(omarchy_base)
            all_packages.update(packages)
            print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-base.packages{Colors.NC}")
    
    # 3. Homerchy other packages
    omarchy_other = repo_root / 'homerchy' / 'deployment' / 'install' / 'omarchy-other.packages'
    if omarchy_other.exists():
        packages = read_package_list(omarchy_other)
        all_packages.update(packages)
        print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-other.packages{Colors.NC}")
    else:
        # Try alternative path
        omarchy_other = repo_root / 'deployment' / 'install' / 'omarchy-other.packages'
        if omarchy_other.exists():
            packages = read_package_list(omarchy_other)
            all_packages.update(packages)
            print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-other.packages{Colors.NC}")
    
    # 4. Archinstall packages
    archinstall_packages = repo_root / 'homerchy' / 'deployment' / 'iso-builder' / 'builder' / 'arch-install.packages'
    if archinstall_packages.exists():
        packages = read_package_list(archinstall_packages)
        all_packages.update(packages)
        print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from arch-install.packages{Colors.NC}")
    
    # 5. Essential base system packages (always needed)
    essential_packages = ['base', 'base-devel', 'linux', 'linux-firmware', 'linux-headers', 'syslinux']
    all_packages.update(essential_packages)
    print(f"{Colors.GREEN}  ✓ Added {len(essential_packages)} essential base packages{Colors.NC}")
    
    # Convert to sorted list for consistent output
    package_list = sorted(all_packages)
    print(f"{Colors.BLUE}Total unique packages to download: {len(package_list)}{Colors.NC}")
    
    # Restore cache from temp location if it exists (from cache_db_only cleanup)
    work_dir = Path(os.environ.get('HOMERCHY_WORK_DIR', profile_dir.parent))
    temp_cache_dir = Path("/mnt/work/.homerchy-cache-temp")
    prepare_temp_cache = work_dir / 'offline-mirror-cache-temp'
    
    # Check if cache needs to be restored from temp locations
    # Priority: system temp > prepare temp > normal location
    cache_restored = False
    
    # Check system temp location first (from cache_db_only cleanup)
    if temp_cache_dir.exists() and any(temp_cache_dir.glob('*.pkg.tar.*')):
        temp_pkg_count = len(list(temp_cache_dir.glob('*.pkg.tar.*')))
        normal_pkg_count = len(list(offline_mirror_dir.glob('*.pkg.tar.*'))) if offline_mirror_dir.exists() else 0
        
        # Restore if temp has packages and normal location has fewer or none
        if temp_pkg_count > normal_pkg_count:
            print(f"{Colors.BLUE}Restoring preserved cache from system temp location ({temp_pkg_count} packages)...{Colors.NC}")
            offline_mirror_dir.parent.mkdir(parents=True, exist_ok=True)
            # Remove existing cache directory if it exists and has fewer packages
            if offline_mirror_dir.exists():
                try:
                    shutil.rmtree(offline_mirror_dir)
                except PermissionError:
                    subprocess.run(['sudo', 'rm', '-rf', str(offline_mirror_dir)], check=False)
            try:
                shutil.move(str(temp_cache_dir), str(offline_mirror_dir))
            except PermissionError:
                # Use sudo to move if permission denied
                subprocess.run(['sudo', 'mv', str(temp_cache_dir), str(offline_mirror_dir)], check=True)
            # Fix ownership of restored cache (may be owned by root if moved with sudo)
            current_uid = os.getuid()
            current_gid = os.getgid()
            subprocess.run(['sudo', 'chown', '-R', f'{current_uid}:{current_gid}', str(offline_mirror_dir)], check=True)
            print(f"{Colors.GREEN}✓ Restored preserved cache ({temp_pkg_count} packages){Colors.NC}")
            cache_restored = True
    
    # Check prepare temp location (from prepare phase preservation)
    if not cache_restored and prepare_temp_cache.exists() and any(prepare_temp_cache.glob('*.pkg.tar.*')):
        prepare_pkg_count = len(list(prepare_temp_cache.glob('*.pkg.tar.*')))
        normal_pkg_count = len(list(offline_mirror_dir.glob('*.pkg.tar.*'))) if offline_mirror_dir.exists() else 0
        
        # Restore if prepare temp has packages and normal location has fewer or none
        if prepare_pkg_count > normal_pkg_count:
            print(f"{Colors.BLUE}Restoring preserved cache from prepare temp location ({prepare_pkg_count} packages)...{Colors.NC}")
            offline_mirror_dir.parent.mkdir(parents=True, exist_ok=True)
            # Remove existing cache directory if it exists and has fewer packages
            if offline_mirror_dir.exists():
                try:
                    shutil.rmtree(offline_mirror_dir)
                except PermissionError:
                    subprocess.run(['sudo', 'rm', '-rf', str(offline_mirror_dir)], check=False)
            try:
                shutil.move(str(prepare_temp_cache), str(offline_mirror_dir))
            except PermissionError:
                # Use sudo to move if permission denied
                subprocess.run(['sudo', 'mv', str(prepare_temp_cache), str(offline_mirror_dir)], check=True)
            # Fix ownership of restored cache (may be owned by root if moved with sudo)
            current_uid = os.getuid()
            current_gid = os.getgid()
            subprocess.run(['sudo', 'chown', '-R', f'{current_uid}:{current_gid}', str(offline_mirror_dir)], check=True)
            print(f"{Colors.GREEN}✓ Restored preserved cache ({prepare_pkg_count} packages){Colors.NC}")
            cache_restored = True
    
    # Ensure offline mirror directory exists
    offline_mirror_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if pacman-online.conf exists for downloading
    pacman_online_conf = repo_root / 'homerchy' / 'deployment' / 'iso-builder' / 'configs' / 'pacman-online.conf'
    if not pacman_online_conf.exists():
        pacman_online_conf = repo_root / 'deployment' / 'iso-builder' / 'configs' / 'pacman-online.conf'
    
    if not pacman_online_conf.exists():
        print(f"{Colors.YELLOW}WARNING: pacman-online.conf not found, using default pacman config{Colors.NC}")
        pacman_config = None
    else:
        pacman_config = str(pacman_online_conf)
    
    # Check for existing packages to avoid re-downloading (cache optimization)
    print(f"{Colors.BLUE}Checking for existing packages in cache...{Colors.NC}")
    
    # Debug: Check all possible cache locations
    print(f"{Colors.BLUE}  Checking cache locations:{Colors.NC}")
    print(f"{Colors.BLUE}    Normal: {offline_mirror_dir} (exists: {offline_mirror_dir.exists()}){Colors.NC}")
    if offline_mirror_dir.exists():
        pkg_count = len(list(offline_mirror_dir.glob('*.pkg.tar.*')))
        print(f"{Colors.BLUE}      Packages found: {pkg_count}{Colors.NC}")
    print(f"{Colors.BLUE}    System temp: {temp_cache_dir} (exists: {temp_cache_dir.exists()}){Colors.NC}")
    if temp_cache_dir.exists():
        pkg_count = len(list(temp_cache_dir.glob('*.pkg.tar.*')))
        print(f"{Colors.BLUE}      Packages found: {pkg_count}{Colors.NC}")
    print(f"{Colors.BLUE}    Prepare temp: {prepare_temp_cache} (exists: {prepare_temp_cache.exists()}){Colors.NC}")
    if prepare_temp_cache.exists():
        pkg_count = len(list(prepare_temp_cache.glob('*.pkg.tar.*')))
        print(f"{Colors.BLUE}      Packages found: {pkg_count}{Colors.NC}")
    
    existing_packages = set()
    
    # Also check for preserved cache in temp locations (from cache_db_only cleanup or prepare phase)
    cache_locations = []
    if offline_mirror_dir.exists():
        cache_locations.append(offline_mirror_dir)
    if temp_cache_dir.exists():
        cache_locations.append(temp_cache_dir)
        print(f"{Colors.BLUE}  Found preserved cache in system temp location, checking there too...{Colors.NC}")
    if prepare_temp_cache.exists():
        cache_locations.append(prepare_temp_cache)
        print(f"{Colors.BLUE}  Found preserved cache in prepare temp location, checking there too...{Colors.NC}")
    
    if cache_locations:
        # Get list of existing package files from all cache locations (excluding .sig files)
        existing_files = []
        for cache_location in cache_locations:
            if cache_location.exists():
                existing_files.extend([f for f in cache_location.glob('*.pkg.tar.*') if not f.name.endswith('.sig')])
        
        # Extract package names from existing files using repo-query (most reliable)
        # or filename parsing (fallback)
        existing_package_names = set()
        if shutil.which('repo-query'):
            for existing_file in existing_files:
                result = subprocess.run(
                    ['repo-query', '-f', '%n', str(existing_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    existing_package_names.add(result.stdout.strip())
        else:
            # Fallback: parse filenames (less reliable, may miss packages with dashes in version)
            for existing_file in existing_files:
                # Remove .pkg.tar.zst or .pkg.tar.xz extension
                base_name = existing_file.name
                if base_name.endswith('.pkg.tar.zst'):
                    base_name = base_name[:-13]
                elif base_name.endswith('.pkg.tar.xz'):
                    base_name = base_name[:-11]
                # Format: name-version-release-arch
                # Split by '-'' and assume last 3 parts are version-release-arch
                parts = base_name.split('-')
                if len(parts) >= 4:
                    pkg_name = '-'.join(parts[:-3])
                    existing_package_names.add(pkg_name)
        
        # Match package names exactly (not by prefix)
        for pkg_name in package_list:
            if pkg_name in existing_package_names:
                existing_packages.add(pkg_name)
    
    # Filter out packages that already exist
    packages_to_download = [pkg for pkg in package_list if pkg not in existing_packages]
    
    if existing_packages:
        print(f"{Colors.GREEN}✓ Found {len(existing_packages)} packages in cache (skipping download){Colors.NC}")
    
    # Count existing package files BEFORE running pacman (to detect if new files are created)
    package_files_before = set()
    if offline_mirror_dir.exists():
        package_files_before = {f.name for f in offline_mirror_dir.glob('*.pkg.tar.*') if not f.name.endswith('.sig')}
    
    # Initialize temp_db_dir (may or may not be created depending on whether we download)
    temp_db_dir = Path('/tmp/omarchy-offline-db')
    
    if packages_to_download:
        print(f"{Colors.BLUE}Downloading {len(packages_to_download)} missing packages...{Colors.NC}")
        print(f"{Colors.BLUE}This may take a while depending on your connection speed...{Colors.NC}")
        
        # Create temporary database directory for pacman
        temp_db_dir.mkdir(parents=True, exist_ok=True)
        
        # Build pacman command (requires root)
        pacman_cmd = ['sudo', 'pacman', '-Syw', '--noconfirm', '--cachedir', str(offline_mirror_dir), '--dbpath', str(temp_db_dir)]
        if pacman_config:
            pacman_cmd.extend([--config, pacman_src/config])
        pacman_cmd.extend(packages_to_download)
        
        # Run pacman to download packages (requires sudo)
        # Show output in real-time so user can see progress
        print(f"{Colors.BLUE}Running pacman with sudo to download packages...{Colors.NC}")
        print(f"{Colors.BLUE}This will show progress as packages are downloaded...{Colors.NC}")
        print(f"{Colors.YELLOW}Note: You may be prompted for your sudo password{Colors.NC}")
        print()
        
        result = subprocess.run(pacman_cmd, stdout=sys.stdout, stderr=sys.stderr)
        
        if result.returncode != 0:
            print()
            print(f"{Colors.RED}ERROR: Package download failed with exit code {result.returncode}!{Colors.NC}")
            sys.exit(1)
        
        # Clean up temporary database (may be owned by root)
        if temp_db_dir.exists():
            try:
                shutil.rmtree(temp_db_dir)
            except PermissionError:
                # If owned by root, use sudo to remove
                subprocess.run(['sudo', 'rm', '-rf', str(temp_db_dir)], check=False)
    else:
        print(f"{Colors.GREEN}✓ All packages already cached, skipping download{Colors.NC}")
    
    # Check if new package files were actually created (pacman might skip if already in cache)
    package_files_after = set()
    if offline_mirror_dir.exists():
        package_files_after = {f.name for f in offline_mirror_dir.glob('*.pkg.tar.*') if not f.name.endswith('.sig')}
    
    # Track if we actually downloaded new packages (needed for database regeneration)
    # Only set to True if new files were actually created
    new_files_created = package_files_after - package_files_before
    packages_were_downloaded = len(new_files_created) > 0
    
    if packages_were_downloaded:
        print(f"{Colors.BLUE}✓ Actually downloaded {len(new_files_created)} new package files{Colors.NC}")
    elif packages_to_download:
        print(f"{Colors.BLUE}✓ Pacman skipped download (packages already in cache){Colors.NC}")
    
    # Fix ownership of downloaded packages (pacman creates them as root)
    # Get current user and group
    current_uid = os.getuid()
    current_gid = os.getgid()
    
    # Change ownership of downloaded packages to current user
    if offline_mirror_dir.exists():
        print(f"{Colors.BLUE}Fixing ownership of downloaded packages...{Colors.NC}")
        subprocess.run(['sudo', 'chown', '-R', f'{current_uid}:{current_gid}', str(offline_mirror_dir)], check=True)
    
    # Count total package files in cache (exclude .sig signature files)
    all_files = list(offline_mirror_dir.glob('*.pkg.tar.*'))
    package_files = [f for f in all_files if not f.name.endswith('.sig')]
    sig_files = [f for f in all_files if f.name.endswith('.sig')]
    print(f"{Colors.GREEN}✓ Total {len(package_files)} package files in cache{Colors.NC}")
    if sig_files:
        print(f"{Colors.GREEN}✓ Total {len(sig_files)} signature files in cache{Colors.NC}")
    
    # Clean up temporary database (may be owned by root)
    if temp_db_dir.exists():
        try:
            shutil.rmtree(temp_db_dir)
        except PermissionError:
            # If owned by root, use sudo to remove
            subprocess.run(['sudo', 'rm', '-rf', str(temp_db_dir)], check=False)
    
    return package_list, packages_were_downloaded
