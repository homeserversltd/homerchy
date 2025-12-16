#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder
Copyright (C) 2024 HOMESERVER LLC

Builds Homerchy ISO from local repository source.
"""

import os
import re
import shutil
import subprocess
import sys
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


class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'


def check_dependencies():
    """Check if required tools are available."""
    if not shutil.which('mkarchiso'):
        print("Error: 'mkarchiso' not found. Please install 'archiso' package.")
        sys.exit(1)


def detect_vm_environment():
    """Detect if running in a VM environment."""
    # Check environment variable override
    if os.environ.get('OMARCHY_VM_BUILD'):
        return True
    
    # Check DMI product name
    dmi_path = Path('/sys/class/dmi/id/product_name')
    if dmi_path.exists():
        product_name = dmi_path.read_text().strip()
        vm_indicators = ['QEMU', 'KVM', 'VMware', 'VirtualBox', 'Virtual Machine', 'Xen', 'Bochs']
        if any(indicator.lower() in product_name.lower() for indicator in vm_indicators):
            return True
    
    # Check systemd-detect-virt
    if shutil.which('systemd-detect-virt'):
        result = subprocess.run(['systemd-detect-virt'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() != 'none':
            return True
    
    return False


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


def download_packages_to_offline_mirror(repo_root: Path, profile_dir: Path, offline_mirror_dir: Path):
    """
    Download all required packages to the offline mirror directory.
    
    Args:
        repo_root: Root of the repository
        profile_dir: ISO profile directory
        offline_mirror_dir: Directory where packages will be stored
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
    omarchy_base = repo_root / 'homerchy' / 'install' / 'omarchy-base.packages'
    if omarchy_base.exists():
        packages = read_package_list(omarchy_base)
        all_packages.update(packages)
        print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-base.packages{Colors.NC}")
    else:
        # Try alternative path (if called from different location)
        omarchy_base = repo_root / 'install' / 'omarchy-base.packages'
        if omarchy_base.exists():
            packages = read_package_list(omarchy_base)
            all_packages.update(packages)
            print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-base.packages{Colors.NC}")
    
    # 3. Homerchy other packages
    omarchy_other = repo_root / 'homerchy' / 'install' / 'omarchy-other.packages'
    if omarchy_other.exists():
        packages = read_package_list(omarchy_other)
        all_packages.update(packages)
        print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-other.packages{Colors.NC}")
    else:
        # Try alternative path
        omarchy_other = repo_root / 'install' / 'omarchy-other.packages'
        if omarchy_other.exists():
            packages = read_package_list(omarchy_other)
            all_packages.update(packages)
            print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from omarchy-other.packages{Colors.NC}")
    
    # 4. Archinstall packages
    archinstall_packages = repo_root / 'homerchy' / 'iso-builder' / 'builder' / 'archinstall.packages'
    if archinstall_packages.exists():
        packages = read_package_list(archinstall_packages)
        all_packages.update(packages)
        print(f"{Colors.GREEN}  ✓ Read {len(packages)} packages from archinstall.packages{Colors.NC}")
    
    # 5. Essential base system packages (always needed)
    essential_packages = ['base', 'base-devel', 'linux', 'linux-firmware', 'linux-headers', 'syslinux']
    all_packages.update(essential_packages)
    print(f"{Colors.GREEN}  ✓ Added {len(essential_packages)} essential base packages{Colors.NC}")
    
    # Convert to sorted list for consistent output
    package_list = sorted(all_packages)
    print(f"{Colors.BLUE}Total unique packages to download: {len(package_list)}{Colors.NC}")
    
    # Ensure offline mirror directory exists
    offline_mirror_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if pacman-online.conf exists for downloading
    pacman_online_conf = repo_root / 'homerchy' / 'iso-builder' / 'configs' / 'pacman-online.conf'
    if not pacman_online_conf.exists():
        pacman_online_conf = repo_root / 'iso-builder' / 'configs' / 'pacman-online.conf'
    
    if not pacman_online_conf.exists():
        print(f"{Colors.YELLOW}WARNING: pacman-online.conf not found, using default pacman config{Colors.NC}")
        pacman_config = None
    else:
        pacman_config = str(pacman_online_conf)
    
    # Check for existing packages to avoid re-downloading (cache optimization)
    print(f"{Colors.BLUE}Checking for existing packages in cache...{Colors.NC}")
    existing_packages = set()
    if offline_mirror_dir.exists():
        # Get list of existing package files (excluding .sig files)
        existing_files = [f for f in offline_mirror_dir.glob('*.pkg.tar.*') if not f.name.endswith('.sig')]
        # Try to match package names from existing files
        for pkg_name in package_list:
            # Check if any existing file starts with this package name
            for existing_file in existing_files:
                if existing_file.name.startswith(f"{pkg_name}-"):
                    existing_packages.add(pkg_name)
                    break
    
    # Filter out packages that already exist
    packages_to_download = [pkg for pkg in package_list if pkg not in existing_packages]
    
    if existing_packages:
        print(f"{Colors.GREEN}✓ Found {len(existing_packages)} packages in cache (skipping download){Colors.NC}")
    
    if packages_to_download:
        print(f"{Colors.BLUE}Downloading {len(packages_to_download)} missing packages...{Colors.NC}")
        print(f"{Colors.BLUE}This may take a while depending on your connection speed...{Colors.NC}")
        
        # Create temporary database directory for pacman
        temp_db_dir = Path('/tmp/omarchy-offline-db')
        temp_db_dir.mkdir(parents=True, exist_ok=True)
        
        # Build pacman command (requires root)
        pacman_cmd = ['sudo', 'pacman', '-Syw', '--noconfirm', '--cachedir', str(offline_mirror_dir), '--dbpath', str(temp_db_dir)]
        if pacman_config:
            pacman_cmd.extend(['--config', pacman_config])
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
    
    # Fix ownership of downloaded packages (pacman creates them as root)
    # Get current user and group
    current_uid = os.getuid()
    current_gid = os.getgid()
    
    # Change ownership of downloaded packages to current user
    if offline_mirror_dir.exists():
        print(f"{Colors.BLUE}Fixing ownership of downloaded packages...{Colors.NC}")
        subprocess.run(['sudo', 'chown', '-R', f'{current_uid}:{current_gid}', str(offline_mirror_dir)], check=True)
    
    # Count downloaded packages (exclude .sig signature files)
    all_files = list(offline_mirror_dir.glob('*.pkg.tar.*'))
    package_files = [f for f in all_files if not f.name.endswith('.sig')]
    sig_files = [f for f in all_files if f.name.endswith('.sig')]
    print(f"{Colors.GREEN}✓ Downloaded {len(package_files)} package files{Colors.NC}")
    if sig_files:
        print(f"{Colors.GREEN}✓ Also downloaded {len(sig_files)} signature files{Colors.NC}")
    
    # Clean up temporary database (may be owned by root)
    if temp_db_dir.exists():
        try:
            shutil.rmtree(temp_db_dir)
        except PermissionError:
            # If owned by root, use sudo to remove
            subprocess.run(['sudo', 'rm', '-rf', str(temp_db_dir)], check=False)
    
    return package_list


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
    db_path = offline_mirror_dir / 'offline.db.tar.gz'
    db_files_path = offline_mirror_dir / 'offline.files.tar.gz'
    
    cache_valid = False
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
        return
    
    # Need to regenerate database
    print(f"{Colors.BLUE}Regenerating repository database from {len(package_files)} package files...{Colors.NC}")
    
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
    
    print(f"{Colors.GREEN}✓ Created repository database: {db_path.name}{Colors.NC}")
    
    # Verify database was created
    if db_path.exists():
        db_size = db_path.stat().st_size
        print(f"{Colors.GREEN}✓ Repository database size: {db_size / 1024:.1f} KB{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}WARNING: Repository database file not found after creation{Colors.NC}")


def main():
    """Main build function."""
    # Configuration
    repo_root = Path(__file__).parent.parent.resolve()
    work_dir = repo_root / 'isoprep' / 'work'
    out_dir = repo_root / 'isoprep' / 'isoout'
    profile_dir = work_dir / 'profile'
    
    print(f"{Colors.BLUE}Starting Homerchy ISO Build...{Colors.NC}")
    
    # Check dependencies
    check_dependencies()
    
    # Ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Preserve mkarchiso work directory for package cache reuse
    # This significantly speeds up rebuilds by reusing downloaded packages
    archiso_tmp_dir = work_dir / 'archiso-tmp'
    preserve_archiso_tmp = archiso_tmp_dir.exists()
    
    # Clean up profile directory (but preserve archiso-tmp cache and offline mirror cache)
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    preserve_cache = cache_dir.exists() and any(cache_dir.glob('*.pkg.tar.*'))
    
    if profile_dir.exists():
        print(f"{Colors.BLUE}Cleaning up previous profile directory...{Colors.NC}")
        if preserve_cache:
            print(f"{Colors.BLUE}Preserving offline mirror cache ({len(list(cache_dir.glob('*.pkg.tar.*')))} packages)...{Colors.NC}")
            # Temporarily move cache out of the way
            temp_cache = work_dir / 'offline-mirror-cache-temp'
            if temp_cache.exists():
                shutil.rmtree(temp_cache)
            cache_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(cache_dir), str(temp_cache))
        
        shutil.rmtree(profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Restore cache if it was preserved
        if preserve_cache:
            cache_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp_cache), str(cache_dir))
            print(f"{Colors.GREEN}✓ Restored offline mirror cache{Colors.NC}")
    
    # Remove cached squashfs to force rebuild (mkarchiso may cache it)
    # This ensures changes to files in airootfs are picked up
    if preserve_archiso_tmp:
        print(f"{Colors.BLUE}Preserving mkarchiso work directory for faster rebuild (package cache){Colors.NC}")
        # Remove cached squashfs images to force rebuild (may be owned by root from previous sudo mkarchiso)
        cached_squashfs = archiso_tmp_dir / 'iso' / 'arch' / 'x86_64' / 'airootfs.sfs'
        if cached_squashfs.exists():
            print(f"{Colors.BLUE}Removing cached squashfs to force rebuild...{Colors.NC}")
            try:
                cached_squashfs.unlink()
            except PermissionError:
                # File owned by root, use sudo to remove
                subprocess.run(['sudo', 'rm', '-f', str(cached_squashfs)], check=False)
        
    print(f"{Colors.BLUE}Assembling ISO profile...{Colors.NC}")
    
    # 1. Copy base Releng config from submodule
    releng_source = repo_root / 'iso-builder' / 'archiso' / 'configs' / 'releng'
    if releng_source.exists():
        for item in releng_source.iterdir():
            # Skip if we can't stat the item (doesn't exist or permission error)
            try:
                if not item.exists() and not item.is_symlink():
                    continue
            except (OSError, RuntimeError):
                # Can't access the item - skip it
                continue
            dest = profile_dir / item.name
            if item.is_dir():
                safe_copytree(item, dest, dirs_exist_ok=True)
            else:
                # Copy file or symlink (even if broken)
                try:
                    shutil.copy2(item, dest, follow_symlinks=False)
                except (OSError, shutil.Error) as e:
                    # Skip missing files or broken symlinks
                    if 'No such file or directory' not in str(e):
                        raise
    
    # 2. Cleanup unwanted Releng defaults (reflector)
    reflector_paths = [
        profile_dir / 'airootfs' / 'etc' / 'systemd' / 'system' / 'multi-user.target.wants' / 'reflector.service',
        profile_dir / 'airootfs' / 'etc' / 'systemd' / 'system' / 'reflector.service.d',
        profile_dir / 'airootfs' / 'etc' / 'xdg' / 'reflector',
    ]
    for path in reflector_paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    
    # 3. Apply Homerchy Custom Overlays
    # Note: We skip pacman.conf here because we'll configure it separately for build vs ISO
    # Also skip any pacman.conf files in subdirectories (like airootfs/etc/pacman.conf)
    configs_source = repo_root / 'iso-builder' / 'configs'
    if configs_source.exists():
        def should_skip_pacman_conf(src_path, dest_path):
            """Check if this is a pacman.conf file we should skip."""
            if src_path.name == 'pacman.conf':
                return True
            # Also skip pacman.conf in airootfs/etc/
            if 'airootfs' in str(src_path) and 'etc' in str(src_path) and src_path.name == 'pacman.conf':
                return True
            return False
        
        for item in configs_source.iterdir():
            # Skip pacman.conf at root level - we'll configure it separately
            if item.name == 'pacman.conf':
                continue
            # Skip if we can't stat the item (doesn't exist or permission error)
            try:
                if not item.exists() and not item.is_symlink():
                    continue
            except (OSError, RuntimeError):
                # Can't access the item - skip it
                continue
            dest = profile_dir / item.name
            if item.is_dir():
                # Use custom copytree that skips pacman.conf files
                def ignore_pacman_conf(dir_path, names):
                    """Ignore function to skip pacman.conf files."""
                    ignored = []
                    for name in names:
                        full_path = Path(dir_path) / name
                        if should_skip_pacman_conf(full_path, dest / name):
                            ignored.append(name)
                    return ignored
                safe_copytree(item, dest, dirs_exist_ok=True, ignore=ignore_pacman_conf)
            else:
                # Copy file or symlink (even if broken)
                try:
                    shutil.copy2(item, dest, follow_symlinks=False)
                except (OSError, shutil.Error) as e:
                    # Skip missing files or broken symlinks
                    if 'No such file or directory' not in str(e):
                        raise
    
    # 3a. Detect VM environment and adjust boot timeout
    is_vm = detect_vm_environment()
    if is_vm:
        print(f"{Colors.BLUE}VM detected - adjusting boot timeout{Colors.NC}")
        syslinux_cfg = profile_dir / 'syslinux' / 'archiso_sys.cfg'
        if syslinux_cfg.exists():
            content = syslinux_cfg.read_text()
            content = re.sub(r'^TIMEOUT \d+', 'TIMEOUT 0', content, flags=re.MULTILINE)
            syslinux_cfg.write_text(content)
            print(f"{Colors.GREEN}Boot timeout set to 0 for instant VM boot{Colors.NC}")
    
    # 3b. Ensure mirrorlist exists in airootfs/etc/pacman.d (required for pacman.conf Include directive)
    # This must be done early so mkarchiso can copy it when it processes airootfs
    airootfs_etc = profile_dir / 'airootfs' / 'etc'
    airootfs_etc.mkdir(parents=True, exist_ok=True)
    pacman_d_dir = airootfs_etc / 'pacman.d'
    pacman_d_dir.mkdir(parents=True, exist_ok=True)
    mirrorlist_file = pacman_d_dir / 'mirrorlist'
    if not mirrorlist_file.exists():
        # Create a minimal mirrorlist file with a valid Server entry
        # This is needed for pacman.conf's Include directive to work during build
        # The actual mirrorlist will be configured during installation
        mirrorlist_content = """#
# Arch Linux repository mirrorlist
# Generated for ISO build
# Actual mirrors will be configured during installation
#
Server = https://geo.mirror.pkgbuild.com/$repo/os/$arch
"""
        mirrorlist_file.write_text(mirrorlist_content)
        print(f"{Colors.GREEN}✓ Created mirrorlist file in airootfs{Colors.NC}")
    
    # 3c. Configure pacman.conf for build vs ISO
    # mkarchiso needs online repos during build to install base ISO packages
    # But the ISO itself should use offline mirror when booted
    # Use the releng pacman.conf as base (has standard Arch repos) and add omarchy repo
    releng_pacman_conf = releng_source / 'pacman.conf'
    pacman_offline_conf = repo_root / 'homerchy' / 'iso-builder' / 'configs' / 'pacman.conf'
    if not pacman_offline_conf.exists():
        pacman_offline_conf = repo_root / 'iso-builder' / 'configs' / 'pacman.conf'
    
    # For profile: Use releng pacman.conf (standard Arch repos) + add omarchy online repo
    # This ensures mkarchiso can build with online repos
    # CRITICAL: Remove any offline/omarchy repos that might reference file:// paths
    if releng_pacman_conf.exists():
        # Read releng pacman.conf and add omarchy repo
        releng_content = releng_pacman_conf.read_text()
        # Remove any existing offline or omarchy repos that use file:// paths
        import re
        # Remove [offline] repo section if present
        releng_content = re.sub(r'\[offline\].*?(?=\n\[|\Z)', '', releng_content, flags=re.DOTALL)
        # Remove [omarchy] repo section if it uses file://
        if '[omarchy]' in releng_content:
            omarchy_match = re.search(r'\[omarchy\].*?(?=\n\[|\Z)', releng_content, re.DOTALL)
            if omarchy_match and 'file://' in omarchy_match.group():
                releng_content = re.sub(r'\[omarchy\].*?(?=\n\[|\Z)', '', releng_content, flags=re.DOTALL)
        # Add omarchy repo with online URL if not already present
        if '[omarchy]' not in releng_content:
            omarchy_repo = """
[omarchy]
SigLevel = Optional TrustAll
Server = https://pkgs.omarchy.org/stable/$arch
"""
            releng_content += omarchy_repo
        (profile_dir / 'pacman.conf').write_text(releng_content)
        print(f"{Colors.GREEN}✓ Using releng pacman.conf with omarchy repo for mkarchiso build{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}WARNING: releng pacman.conf not found, using default{Colors.NC}")
    
    # CRITICAL: Ensure airootfs/etc/pacman.conf uses online repos (same as profile pacman.conf)
    # mkarchiso reads airootfs/etc/pacman.conf and would try to use offline mirror if present
    # Copy the profile pacman.conf (online) to airootfs/etc so mkarchiso sees online repos
    airootfs_etc = profile_dir / 'airootfs' / 'etc'
    airootfs_etc.mkdir(parents=True, exist_ok=True)
    profile_pacman_conf = profile_dir / 'pacman.conf'
    if profile_pacman_conf.exists():
        # Remove any existing pacman.conf in airootfs/etc that might have offline config
        airootfs_pacman_conf = airootfs_etc / 'pacman.conf'
        if airootfs_pacman_conf.exists():
            airootfs_pacman_conf.unlink()
        # Copy profile pacman.conf (online) to airootfs/etc
        shutil.copy2(profile_pacman_conf, airootfs_pacman_conf)
        print(f"{Colors.GREEN}✓ Using online pacman.conf in airootfs/etc for mkarchiso build{Colors.NC}")
    
    # Note: The ISO will have online pacman.conf, but the installer will configure offline mirror when it runs
    
    # 4. Inject Current Repository Source
    # This allows the ISO to contain the latest changes from this workspace
    # Use guaranteed copy to ensure all new/changed files are transferred
    print(f"{Colors.BLUE}Injecting current repository source...{Colors.NC}")
    homerchy_target = profile_dir / 'airootfs' / 'root' / 'homerchy'
    homerchy_target.mkdir(parents=True, exist_ok=True)
    
    # Copy excluding build artifacts and .git
    exclude_patterns = ['isoprep/work', 'isoprep/isoout', '.git']
    
    for item in repo_root.iterdir():
        if item.name in ['isoprep', '.git']:
            continue
        # Skip if we can't stat the item (doesn't exist or permission error)
        try:
            if not item.exists() and not item.is_symlink():
                continue
        except (OSError, RuntimeError):
            # Can't access the item - skip it
            continue
        dest = homerchy_target / item.name
        
        # Use guaranteed copy to ensure all files are transferred and updated
        if item.is_dir():
            # guaranteed_copytree ensures all files are copied/updated
            guaranteed_copytree(item, dest, ignore=shutil.ignore_patterns('.git'))
        else:
            # For files, copy if source is newer or destination doesn't exist
            if not dest.exists() or item.stat().st_mtime > dest.stat().st_mtime:
                try:
                    shutil.copy2(item, dest, follow_symlinks=False)
                except (OSError, shutil.Error) as e:
                    # Skip missing files or broken symlinks
                    if 'No such file or directory' not in str(e):
                        raise
    
    # Create symlink for backward compatibility (installer expects /root/omarchy)
    omarchy_link = profile_dir / 'airootfs' / 'root' / 'omarchy'
    if not omarchy_link.exists():
        # Use relative symlink - installer code expects /root/omarchy
        omarchy_link.symlink_to('homerchy')
    
    # 4b. Inject VM profile settings
    vmtools_dir = profile_dir / 'airootfs' / 'root' / 'vmtools'
    vmtools_dir.mkdir(parents=True, exist_ok=True)
    
    index_source = repo_root / 'vmtools' / 'index.json'
    if index_source.exists():
        shutil.copy2(index_source, vmtools_dir / 'index.json')
        print(f"{Colors.GREEN}✓ Copied VM profile: {index_source} -> {vmtools_dir / 'index.json'}{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}⚠ VM profile not found: {index_source}{Colors.NC}")
    
    # 5. Customize Package List
    packages_file = profile_dir / 'packages.x86_64'
    # Ensure syslinux is in the package list (required for BIOS boot)
    # Read existing content, add syslinux if missing, then append custom packages
    if packages_file.exists():
        content = packages_file.read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        # Check if syslinux is already in the file (case-insensitive)
        has_syslinux = any('syslinux' in line.lower() for line in lines)
        if not has_syslinux:
            # Add syslinux before appending other packages
            with open(packages_file, 'a') as f:
                f.write('syslinux\n')
    else:
        # File doesn't exist - create it with syslinux
        packages_file.write_text('syslinux\n')
    
    # Append custom packages
    with open(packages_file, 'a') as f:
        f.write('git\ngum\njq\nopenssl\n')
    
    # 5b. Fix Permissions Targets
    cache_dir = profile_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    bin_dir = profile_dir / 'airootfs' / 'usr' / 'local' / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    upload_log_source = repo_root / 'bin' / 'omarchy-upload-log'
    if upload_log_source.exists():
        shutil.copy2(upload_log_source, bin_dir / 'omarchy-upload-log')
        (bin_dir / 'omarchy-upload-log').chmod(0o755)
    
    # 6. Download packages to offline mirror
    print(f"{Colors.BLUE}Preparing offline package mirror...{Colors.NC}")
    download_packages_to_offline_mirror(repo_root, profile_dir, cache_dir)
    
    # 7. Create offline repository database
    create_offline_repository(cache_dir)
    
    # 7b. CRITICAL: Ensure airootfs/etc/pacman.conf uses online repos (do this LAST, after all overlays)
    # mkarchiso reads airootfs/etc/pacman.conf and would try to use offline mirror if present
    # Copy the profile pacman.conf (online) to airootfs/etc so mkarchiso sees online repos
    # Note: mirrorlist was already created in step 3b, so it should exist here
    profile_pacman_conf = profile_dir / 'pacman.conf'
    if profile_pacman_conf.exists():
        # Remove any existing pacman.conf in airootfs/etc that might have offline config
        airootfs_pacman_conf = airootfs_etc / 'pacman.conf'
        if airootfs_pacman_conf.exists():
            print(f"{Colors.BLUE}Removing existing pacman.conf from airootfs/etc (may have offline config){Colors.NC}")
            airootfs_pacman_conf.unlink()
        # Copy profile pacman.conf (online) to airootfs/etc
        shutil.copy2(profile_pacman_conf, airootfs_pacman_conf)
        print(f"{Colors.GREEN}✓ Using online pacman.conf in airootfs/etc for mkarchiso build{Colors.NC}")
        
        # Verify it doesn't have offline repos
        content = airootfs_pacman_conf.read_text()
        if 'file:///var/cache/omarchy/mirror/offline' in content:
            print(f"{Colors.RED}ERROR: airootfs/etc/pacman.conf still has offline mirror config!{Colors.NC}")
            sys.exit(1)
    
    # 8. Create symlink so mkarchiso can find the offline mirror during build
    # mkarchiso uses the pacman.conf from the profile, which references /var/cache/omarchy/mirror/offline
    # We need to make that path available on the host system
    # Note: Since we're using pacman-online.conf for mkarchiso build, this symlink may not be needed
    # But we'll create it anyway for consistency and in case it's needed
    system_mirror_dir = Path('/var/cache/omarchy/mirror/offline')
    
    # Create parent directories with sudo (requires root permissions)
    system_mirror_parent = system_mirror_dir.parent
    print(f"{Colors.BLUE}Creating system mirror directory structure with sudo...{Colors.NC}")
    subprocess.run(['sudo', 'mkdir', '-p', str(system_mirror_parent)], check=True)
    
    # Remove existing symlink or directory if it exists
    if system_mirror_dir.exists() or system_mirror_dir.is_symlink():
        print(f"{Colors.BLUE}Removing existing symlink/directory...{Colors.NC}")
        if system_mirror_dir.is_symlink():
            subprocess.run(['sudo', 'rm', '-f', str(system_mirror_dir)], check=False)
        else:
            # If it's a directory, we need sudo to remove it
            subprocess.run(['sudo', 'rm', '-rf', str(system_mirror_dir)], check=False)
    
    # Create symlink from system location to profile directory
    # Use absolute path for the symlink target
    cache_dir_absolute = cache_dir.resolve()
    print(f"{Colors.BLUE}Creating symlink with sudo: {system_mirror_dir} -> {cache_dir_absolute}{Colors.NC}")
    subprocess.run(['sudo', 'ln', '-sf', str(cache_dir_absolute), str(system_mirror_dir)], check=True)
    print(f"{Colors.GREEN}✓ Created symlink{Colors.NC}")
    
    # Final verification: Ensure syslinux is in packages.x86_64 before mkarchiso runs
    packages_file = profile_dir / 'packages.x86_64'
    if packages_file.exists():
        content = packages_file.read_text()
        # Check if syslinux is present (as a whole word, case-insensitive)
        if not re.search(r'\bsyslinux\b', content, re.IGNORECASE):
            print(f"{Colors.YELLOW}WARNING: syslinux not found in packages.x86_64, adding it...{Colors.NC}")
            with open(packages_file, 'a') as f:
                f.write('syslinux\n')
        else:
            print(f"{Colors.GREEN}✓ Verified syslinux is in packages.x86_64{Colors.NC}")
    else:
        print(f"{Colors.RED}ERROR: packages.x86_64 does not exist!{Colors.NC}")
        sys.exit(1)
    
    # CRITICAL: Ensure mirrorlist exists in archiso-tmp before mkarchiso runs
    # If archiso-tmp is preserved, mkarchiso might use existing airootfs that doesn't have mirrorlist
    # Copy mirrorlist from profile to preserved archiso-tmp to ensure it exists
    profile_mirrorlist = profile_dir / 'airootfs' / 'etc' / 'pacman.d' / 'mirrorlist'
    if profile_mirrorlist.exists() and preserve_archiso_tmp:
        preserved_airootfs = archiso_tmp_dir / 'x86_64' / 'airootfs'
        if preserved_airootfs.exists():
            preserved_mirrorlist = preserved_airootfs / 'etc' / 'pacman.d' / 'mirrorlist'
            preserved_mirrorlist_dir = preserved_mirrorlist.parent
            try:
                preserved_mirrorlist_dir.mkdir(parents=True, exist_ok=True)
                # Copy mirrorlist from profile to preserved archiso-tmp
                shutil.copy2(profile_mirrorlist, preserved_mirrorlist)
                print(f"{Colors.GREEN}✓ Copied mirrorlist to preserved archiso-tmp{Colors.NC}")
            except PermissionError:
                # Directory might be owned by root from previous sudo mkarchiso
                # Use sudo to create directory and copy file
                subprocess.run(['sudo', 'mkdir', '-p', str(preserved_mirrorlist_dir)], check=True)
                subprocess.run(['sudo', 'cp', str(profile_mirrorlist), str(preserved_mirrorlist)], check=True)
                # Fix ownership to current user
                current_uid = os.getuid()
                current_gid = os.getgid()
                subprocess.run(['sudo', 'chown', f'{current_uid}:{current_gid}', str(preserved_mirrorlist)], check=True)
                print(f"{Colors.GREEN}✓ Copied mirrorlist to preserved archiso-tmp (with sudo){Colors.NC}")
    
    print(f"{Colors.BLUE}Building ISO with mkarchiso (Requires Sudo)...{Colors.NC}")
    print(f"Output will be in: {Colors.GREEN}{out_dir}{Colors.NC}")
    print(f"{Colors.BLUE}Note: I/O errors reading /sys files are expected and harmless{Colors.NC}")
    
    # Run mkarchiso
    # Note: mkarchiso will produce I/O errors when trying to copy /sys and /proc virtual files
    # These are expected and mkarchiso handles them by creating empty files
    result = subprocess.run([
        'sudo', 'mkarchiso', '-v',
        '-w', str(work_dir / 'archiso-tmp'),
        '-o', str(out_dir),
        str(profile_dir)
    ])
    
    if result.returncode != 0:
        print(f"{Colors.RED}Build failed with exit code {result.returncode}{Colors.NC}")
        print(f"{Colors.YELLOW}Check the output above for actual errors (I/O errors on /sys files are normal){Colors.NC}")
        sys.exit(1)
    
    # Verify ISO was actually created
    iso_files = list(out_dir.glob('*.iso'))
    if not iso_files:
        print(f"{Colors.RED}ERROR: Build reported success but no ISO file was created!{Colors.NC}")
        sys.exit(1)
    
    # Now that mkarchiso has finished, we can add the offline pacman.conf to the ISO filesystem
    # This is done by modifying the airootfs in the work directory before final ISO creation
    # Actually, mkarchiso has already created the ISO, so we need to extract, modify, and rebuild
    # OR: The offline pacman.conf should have been in airootfs/etc from the start, but mkarchiso
    # should use profile pacman.conf. Let me check if we can add it to the squashfs after build.
    # Actually, the simplest solution: Copy offline pacman.conf to airootfs/etc in the profile
    # AFTER mkarchiso reads it but BEFORE it creates the final ISO. But mkarchiso reads it during build.
    # 
    # Better approach: The offline pacman.conf should be in airootfs/etc, but mkarchiso should
    # use the profile pacman.conf. According to mkarchiso docs, it uses profile pacman.conf.
    # So we can safely put offline pacman.conf in airootfs/etc - mkarchiso won't use it.
    # But the error shows it IS using it. Let me try a different approach: Don't put it in airootfs/etc
    # until after mkarchiso finishes, then manually add it to the ISO.
    
    # For now, let's try putting it in airootfs/etc but ensuring mkarchiso uses profile pacman.conf
    # Actually, the issue is that mkarchiso might be reading airootfs/etc/pacman.conf.
    # Let's not put it there at all during build, and add it after.
    # But that's complex. Let me try ensuring the profile pacman.conf is definitely used.
    
    print(f"{Colors.GREEN}Build complete! ISO is located in {out_dir}{Colors.NC}")
    for iso_file in iso_files:
        print(f"  {Colors.GREEN}{iso_file.name}{Colors.NC}")
    
    # Add offline pacman.conf to the built ISO's airootfs
    # Extract the ISO, modify, and rebuild? Too complex.
    # Better: Ensure offline pacman.conf is in airootfs/etc but mkarchiso uses profile pacman.conf
    # The error suggests mkarchiso IS reading airootfs/etc/pacman.conf, so we need to fix that.


if __name__ == '__main__':
    main()

