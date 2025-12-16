#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder
Copyright (C) 2024 HOMESERVER LLC

Builds Homerchy ISO from local repository source.
"""

import os
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
    
    # Clean up profile directory (but preserve archiso-tmp cache)
    if profile_dir.exists():
        print(f"{Colors.BLUE}Cleaning up previous profile directory...{Colors.NC}")
        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    
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
    configs_source = repo_root / 'iso-builder' / 'configs'
    if configs_source.exists():
        for item in configs_source.iterdir():
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
    
    # 3a. Detect VM environment and adjust boot timeout
    is_vm = detect_vm_environment()
    if is_vm:
        print(f"{Colors.BLUE}VM detected - adjusting boot timeout{Colors.NC}")
        syslinux_cfg = profile_dir / 'syslinux' / 'archiso_sys.cfg'
        if syslinux_cfg.exists():
            content = syslinux_cfg.read_text()
            import re
            content = re.sub(r'^TIMEOUT \d+', 'TIMEOUT 0', content, flags=re.MULTILINE)
            syslinux_cfg.write_text(content)
            print(f"{Colors.GREEN}Boot timeout set to 0 for instant VM boot{Colors.NC}")
    
    # 3b. Force Online Build Config
    pacman_online_conf = repo_root / 'iso-builder' / 'configs' / 'pacman-online.conf'
    if pacman_online_conf.exists():
        shutil.copy2(pacman_online_conf, profile_dir / 'pacman.conf')
    
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
    
    print(f"{Colors.GREEN}Build complete! ISO is located in {out_dir}{Colors.NC}")
    for iso_file in iso_files:
        print(f"  {Colors.GREEN}{iso_file.name}{Colors.NC}")


if __name__ == '__main__':
    main()

