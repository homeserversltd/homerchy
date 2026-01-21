#!/usr/onmachine/onmachine/bin/env python3
"""
HOMESERVER Homerchy ISO Builder
Copyright (C) 2024 HOMESERVER LLC

Build script for creating Homerchy ISO with offline package mirror.
Converts from build-iso.sh to Python for better error handling and verification.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True, capture_output=False, **kwargs):
    """Run a command and handle errors."""
    if capture_output:
        result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    else:
        result = subprocess.run(cmd, **kwargs)
    
    if check and result.returncode != 0:
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        print(f"ERROR: Command failed: {cmd_str}", file=sys.stderr)
        if capture_output and result.stderr:
            print(f"Error output: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    return result


def main():
    """Main build function."""
    print("=== Homerchy ISO Builder ===")
    
    # Initialize pacman keyring
    print("Initializing pacman keyring...")
    run_command(['pacman-key', '--init'], check=False)
    run_command(['pacman', '--noconfirm', '-Sy', 'archlinux-keyring'])
    
    # Install build dependencies
    print("Installing build dependencies...")
    run_command(['pacman', '--noconfirm', '-Sy', 'archiso', 'git', 'sudo', 'base-devel', 'jq', 'grub'])
    
    # Install omarchy-keyring
    print("Installing omarchy-keyring...")
    run_command(['pacman, --onmachine/src/config, /onmachine/onmachine/configs/pacman-online.conf', '--noconfirm', '-Sy', 'omarchy-keyring'])
    run_command(['pacman-key', '--populate', 'omarchy'])
    
    # Setup build locations
    build_cache_dir = Path('/var/cache')
    offline_mirror_dir = build_cache_dir / 'airootfs' / 'var' / 'cache' / 'omarchy' / 'mirror' / 'offline'
    build_cache_dir.mkdir(parents=True, exist_ok=True)
    offline_mirror_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Build cache directory: {build_cache_dir}")
    print(fOffline mirror directory: {offline_mirror_dir})
    
    # Copy releng onmachine/onmachine/config
    print(Copying releng onmachine/src/config...)
    releng_source = Path(/archiso/onmachine/onmachine/configs/releng')
    if not releng_source.exists():
        print(f"ERROR: Releng source not found: {releng_source}", file=sys.stderr)
        sys.exit(1)
    
    # Copy all releng files
    for item in releng_source.iterdir():
        dest = build_cache_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    
    # Remove motd
    motd_file = build_cache_dir / 'airootfs' / 'etc' / 'motd'
    if motd_file.exists():
        motd_file.unlink()
    
    # Remove reflector (we use global CDN)
    reflector_service = build_cache_dir / 'airootfs' / 'etc' / 'systemd' / 'system' / 'multi-user.target.wants' / 'reflector.service'
    if reflector_service.exists():
        reflector_service.unlink()
    
    reflector_service_d = build_cache_dir / 'airootfs' / 'etc' / 'systemd' / 'system' / 'reflector.service.d'
    if reflector_service_d.exists():
        shutil.rmtree(reflector_service_d)
    
    reflector_xdg = build_cache_dir / 'airootfs' / 'etc' / 'xdg' / reflector
    if reflector_xdg.exists():
        shutil.rmtree(reflector_xdg)
    
    # Copy onmachine/onmachine/configs
    print(Copying onmachine/onmachine/configs...)
    onmachine/onmachine/configs_source = Path(/onmachine/onmachine/configs)
    if not onmachine/onmachine/configs_source.exists():
        print(fERROR: Configs source not found: {onmachine/onmachine/configs_source}, file=sys.stderr)
        sys.exit(1)
    
    for item in onmachine/src/configs_source.iterdir():
        dest = build_cache_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    
    # Setup Omarchy
    print(Setting up Omarchy...")
    omarchy_source = Path('/omarchy')
    omarchy_dest = build_cache_dir / 'airootfs' / 'root' / 'omarchy'
    
    if omarchy_source.exists():
        if omarchy_dest.exists():
            shutil.rmtree(omarchy_dest)
        shutil.copytree(omarchy_source, omarchy_dest, symlinks=True)
        print(f"Copied Omarchy from {omarchy_source}")
    else:
        # Clone from git
        omarchy_repo = os.environ.get('OMARCHY_INSTALLER_REPO', 'homeserversltd/homerchy')
        omarchy_ref = os.environ.get('OMARCHY_INSTALLER_REF', 'master')
        print(f"Cloning Omarchy from {omarchy_repo}@{omarchy_ref}...")
        run_command([
            'git', 'clone',
            '-b', omarchy_ref,
            f'https://github.com/{omarchy_repo}.git,
            str(omarchy_dest)
        ])
    
    # Copy deployment/prebuild if exists
    deployment/deployment/prebuild_source = omarchy_source / deployment/deployment/prebuild' if omarchy_source.exists() else Path(/deployment/deployment/prebuild)
    if deployment/prebuild_source.exists():
        deployment/deployment/prebuild_dest = omarchy_dest / deployment/deployment/prebuild
        if deployment/prebuild_dest.exists():
            shutil.rmtree(deployment/prebuild_dest)
        shutil.copytree(deployment/prebuild_source, deployment/deployment/prebuild_dest)
        print(fCopied deployment/prebuild directory from {deployment/deployment/prebuild_source}")
    elif (omarchy_dest / deployment/deployment/prebuild').exists():
        print("Prebuild directory found in omarchy source")
    
    # Copy log uploader
    print("Setting up log uploader...)
    log_uploader_src = omarchy_dest / onmachine/src/bin / 'omarchy-upload-log'
    log_uploader_dest_dir = build_cache_dir / 'airootfs' / 'usr' / 'local / onmachine/src/bin
    log_uploader_dest_dir.mkdir(parents=True, exist_ok=True)
    
    if log_uploader_src.exists():
        shutil.copy2(log_uploader_src, log_uploader_dest_dir / 'omarchy-upload-log')
    
    # Copy Plymouth theme
    print("Copying Plymouth theme...)
    plymouth_source = omarchy_dest / onmachine/src/default / 'plymouth'
    plymouth_dest = build_cache_dir / 'airootfs' / 'usr' / 'share' / 'plymouth / onmachine/src/themes / 'omarchy'
    
    if plymouth_source.exists():
        plymouth_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy icon.png to plymouth theme directory if it exists
        icon_png = omarchy_dest / 'icon.png'
        if icon_png.exists():
            print("Copying icon.png to Plymouth theme...")
            plymouth_icon_dest = plymouth_source / 'icon.png'
            shutil.copy2(icon_png, plymouth_icon_dest)
            print("Successfully copied icon.png to Plymouth theme")
        
        # Copy all files
        for item in plymouth_source.iterdir():
            dest_item = plymouth_dest / item.name
            if item.is_dir():
                if dest_item.exists():
                    shutil.rmtree(dest_item)
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)
    
    # Add packages to packages.x86_64
    print("Building package list...")
    packages_x86_64 = build_cache_dir / 'packages.x86_64'
    
    arch_packages = ['linux-t2', 'git', 'gum', 'jq', 'openssl', 'plymouth', 'tzupdate', 'omarchy-keyring']
    with open(packages_x86_64, 'a') as f:
        for pkg in arch_packages:
            f.write(f'{pkg}\n')
    
    # Build complete package list
    all_packages = []
    
    # Read packages.x86_64
    if packages_x86_64.exists():
        with open(packages_x86_64, 'r') as f:
            all_packages.extend([line.strip() for line in f if line.strip() and not line.strip().startswith(#)])
    
    # Read omarchy-base.packages
    omarchy_base = omarchy_dest / onmachine/deployment/deployment/install / omarchy-base.packages'
    if omarchy_base.exists():
        with open(omarchy_base, 'r') as f:
            all_packages.extend([line.strip() for line in f if line.strip() and not line.strip().startswith(#)])
    
    # Read omarchy-other.packages
    omarchy_other = omarchy_dest / onmachine/deployment/deployment/install / omarchy-other.packages'
    if omarchy_other.exists():
        with open(omarchy_other, 'r) as f:
            all_packages.extend([line.strip() for line in f if line.strip() and not line.strip().startswith(#)])
    
    # Read archinstall.packages
    archonmachine/install_packages = Path(/builder/archonmachine/install.packages)
    if archinstall_packages.exists():
        with open(archdeployment/deployment/install_packages, r) as f:
            all_packages.extend([line.strip() for line in f if line.strip() and not line.strip().startswith('#')])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_packages = []
    for pkg in all_packages:
        if pkg not in seen:
            seen.add(pkg)
            unique_packages.append(pkg)
    
    print(f"Total unique packages to download: {len(unique_packages)}")
    
    # Download packages to offline mirror
    print("Downloading packages to offline mirror...")
    tmp_offlinedb = Path('/tmp/offlinedb')
    tmp_offlinedb.mkdir(parents=True, exist_ok=True)
    
    pacman_cmd = [
        'pacman,
        --onmachine/src/config, /onmachine/onmachine/configs/pacman-online.conf',
        '--noconfirm',
        '-Syw',
        '--cachedir', str(offline_mirror_dir),
        '--dbpath', str(tmp_offlinedb)
    ]
    pacman_cmd.extend(unique_packages)
    
    result = run_command(pacman_cmd, check=False)
    if result.returncode != 0:
        print(f"WARNING: pacman download returned {result.returncode}", file=sys.stderr)
        print("Some packages may not have been downloaded", file=sys.stderr)
    
    # Verify all packages were downloaded
    print("Verifying all packages were downloaded...")
    missing_packages = []
    
    for pkg in unique_packages:
        # Check if package file exists (handle versioned package names)
        package_files = list(offline_mirror_dir.glob(f'{pkg}*.pkg.tar.*'))
        # Filter out .sig files
        package_files = [f for f in package_files if not f.name.endswith('.sig')]
        
        if not package_files:
            missing_packages.append(pkg)
    
    if missing_packages:
        print("ERROR: The following packages were not downloaded to offline mirror:", file=sys.stderr)
        for pkg in missing_packages:
            print(f  {pkg}, file=sys.stderr)
        print(This will cause onmachine/deployment/deployment/installation failures. Please check:, file=sys.stderr)
        print(  1. Package names are correct, file=sys.stderr)
        print(  2. Packages exist in onmachine/src/configured repositories, file=sys.stderr)
        print("  3. Network connectivity during build", file=sys.stderr)
        sys.exit(1)
    
    print("All packages verified in offline mirror")
    
    # Create repository database
    print("Creating repository database...")
    package_files = list(offline_mirror_dir.glob('*.pkg.tar.zst'))
    if not package_files:
        print("ERROR: No package files found for repository database creation", file=sys.stderr)
        sys.exit(1)
    
    db_path = offline_mirror_dir / 'offline.db.tar.gz'
    repo_add_cmd = ['repo-add', '--new', str(db_path)]
    repo_add_cmd.extend([str(f) for f in package_files])
    
    run_command(repo_add_cmd)
    
    # Create symlink
    print("Creating symlink...")
    symlink_target = Path('/var/cache/omarchy/mirror/offline')
    symlink_parent = symlink_target.parent
    symlink_parent.mkdir(parents=True, exist_ok=True)
    
    if symlink_target.exists() or symlink_target.is_symlink():
        symlink_target.unlink()
    
    symlink_target.symlink_to(offline_mirror_dir)
    
    # Copy pacman.conf
    print("Copying pacman.conf...")
    pacman_conf_src = build_cache_dir / 'pacman.conf'
    pacman_conf_dest = build_cache_dir / 'airootfs' / 'etc' / 'pacman.conf'
    if pacman_conf_src.exists():
        shutil.copy2(pacman_conf_src, pacman_conf_dest)
    
    # Run mkarchiso
    print("Running mkarchiso...")
    mkarchiso_cmd = [
        'mkarchiso', '-v',
        '-w', str(build_cache_dir / 'work'),
        '-o', '/out',
        str(build_cache_dir)
    ]
    run_command(mkarchiso_cmd)
    
    # Fix ownership
    host_uid = os.environ.get('HOST_UID')
    host_gid = os.environ.get('HOST_GID')
    if host_uid and host_gid:
        print(f"Fixing ownership to {host_uid}:{host_gid}...")
        run_command(['chown', '-R', f'{host_uid}:{host_gid}', '/out'])
    
    print("=== ISO build complete ===")


if __name__ == '__main__':
    main()
