#!/usr/bin/env python3
"""
HOMESERVER Homerchy Automated Installation Script
Copyright (C) 2024 HOMESERVER LLC

Runs during ISO boot to orchestrate Homerchy installation via archinstall.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


LOG_FILE = Path('/var/log/omarchy-install.log')


def debug_log(message: str):
    """Log debug messages if OMARCHY_DEBUG is set."""
    if os.environ.get('OMARCHY_DEBUG'):
        log(message)
    # Always print debug messages to console for visibility
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] DEBUG: {message}", flush=True)


def log(message: str):
    """Log important events to both file and console."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    # Write to file
    with open(LOG_FILE, 'a') as f:
        f.write(f"{log_line}\n")
    # Also print to console
    print(log_line, flush=True)


def get_helpers_path():
    """Get path to helpers/all.sh file."""
    # Default path (backward compatibility - installer expects /root/omarchy)
    homerchy_path = Path('/root/homerchy')
    omarchy_path = Path('/root/omarchy')
    
    # Use symlink if it exists, otherwise check for direct path
    if omarchy_path.exists() or omarchy_path.is_symlink():
        os.environ['OMARCHY_PATH'] = str(omarchy_path)
    elif homerchy_path.exists():
        os.environ['OMARCHY_PATH'] = str(homerchy_path)
    else:
        os.environ['OMARCHY_PATH'] = '/root/omarchy'
    
    # VM detection and path override handled by configurator
    # No longer using vm-env.sh, configurator auto-detects VM mode from index.json
    
    omarchy_path = Path(os.environ['OMARCHY_PATH'])
    install_path = omarchy_path / 'install'
    
    os.environ['OMARCHY_INSTALL'] = str(install_path)
    os.environ['OMARCHY_INSTALL_LOG_FILE'] = str(LOG_FILE)
    
    helpers_file = install_path / 'helpers' / 'all.sh'
    if not helpers_file.exists():
        raise FileNotFoundError(f"Homerchy helpers not found: {helpers_file}")
    
    return str(helpers_file)


def use_homerchy_helpers():
    """Load Homerchy installation helpers."""
    helpers_file = get_helpers_path()
    # Source helpers
    subprocess.run(['bash', '-c', f'source {helpers_file}'], check=True)


def shell_cmd(cmd: str, check: bool = False):
    """
    Execute a shell command with helpers sourced.
    
    Args:
        cmd: Shell command to execute
        check: Whether to raise exception on non-zero exit code
    """
    helpers_file = get_helpers_path()
    full_cmd = f'source {helpers_file} && {cmd}'
    return subprocess.run(['bash', '-c', full_cmd], check=check)


def set_tokyo_night_colors():
    """Set Tokyo Night color scheme for the terminal."""
    tty = os.ttyname(sys.stdout.fileno()) if hasattr(os, 'ttyname') else None
    if tty and '/dev/tty' in tty:
        # Tokyo Night color palette
        colors = [
            '\033]P01a1b26',  # black (background)
            '\033]P1f7768e',  # red
            '\033]P29ece6a',  # green
            '\033]P3e0af68',  # yellow
            '\033]P47aa2f7',  # blue
            '\033]P5bb9af7',  # magenta
            '\033]P67dcfff',  # cyan
            '\033]P7a9b1d6',  # white
            '\033]P8414868',  # bright black
            '\033]P9f7768e',  # bright red
            '\033]PA9ece6a',  # bright green
            '\033]PBe0af68',  # bright yellow
            '\033]PC7aa2f7',  # bright blue
            '\033]PDbb9af7',  # bright magenta
            '\033]PE7dcfff',  # bright cyan
            '\033]PFc0caf5',  # bright white (foreground)
        ]
        for color in colors:
            print(color, end='')
        print('\033[0m', end='')
        subprocess.run(['clear'], check=False)


def run_configurator():
    """Run the Homerchy configurator."""
    # Check for VM mode BEFORE clearing screen
    vmtools_dir = Path('/root/vmtools')
    index_file = vmtools_dir / 'index.json'
    is_vm_test = index_file.exists()
    
    if is_vm_test:
        print("\n" + "="*70, flush=True)
        print("[AUTOMATED_SCRIPT] VM TEST MODE DETECTED", flush=True)
        print(f"[AUTOMATED_SCRIPT] Profile: {index_file}", flush=True)
        try:
            with open(index_file) as f:
                index_data = json.load(f)
                default_profile = index_data.get('default_profile', 'homerchy-test')
                print(f"[AUTOMATED_SCRIPT] Using profile: {default_profile}", flush=True)
        except Exception:
            print(f"[AUTOMATED_SCRIPT] Using default profile: homerchy-test", flush=True)
        print("="*70 + "\n", flush=True)
    
    debug_log("run_configurator: Setting Tokyo Night colors")
    set_tokyo_night_colors()
    
    # Print again AFTER clear so it's visible
    if is_vm_test:
        print("[AUTOMATED_SCRIPT] VM TEST MODE - Profile will be auto-loaded", flush=True)
        print("", flush=True)
    
    log("run_configurator: Executing configurator script")
    # Use Python configurator only
    configurator_py = Path('./configurator.py')
    
    if not configurator_py.exists():
        raise FileNotFoundError(f"configurator.py not found at {configurator_py.absolute()}")
    
    cmd = ['python3', str(configurator_py)]
    print(f"[AUTOMATED_SCRIPT] Executing: python3 {configurator_py}", flush=True)
    print(f"[AUTOMATED_SCRIPT] Configurator exists: {configurator_py.exists()}", flush=True)
    print(f"[AUTOMATED_SCRIPT] Configurator path: {configurator_py.absolute()}", flush=True)
    
    # Always show configurator output to console (critical for VM profile debugging)
    log(f"run_configurator: Executing Python configurator")
    result = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    
    if result.returncode != 0:
        log(f"run_configurator: Configurator exited with code {result.returncode}")
        return False
    
    debug_log("run_configurator: Reading username from credentials")
    creds_file = Path('user_credentials.json')
    if creds_file.exists():
        with open(creds_file) as f:
            creds = json.load(f)
            os.environ['OMARCHY_USER'] = creds['users'][0]['username']
            log(f"run_configurator: Username set to: {os.environ['OMARCHY_USER']}")
    else:
        log("run_configurator: ERROR: user_credentials.json not found!")
        return False
    
    return True


def chroot_bash(*args, stdout=None, stderr=None):
    """Execute command in chroot with proper environment."""
    omarchy_user = os.environ.get('OMARCHY_USER')
    if not omarchy_user:
        raise ValueError("OMARCHY_USER not set")
    
    user_full_name_file = Path('user_full_name.txt')
    user_email_file = Path('user_email_address.txt')
    
    user_full_name = user_full_name_file.read_text().strip() if user_full_name_file.exists() else ''
    user_email = user_email_file.read_text().strip() if user_email_file.exists() else ''
    
    env = os.environ.copy()
    env.update({
        'OMARCHY_CHROOT_INSTALL': '1',
        'OMARCHY_USER_NAME': user_full_name,
        'OMARCHY_USER_EMAIL': user_email,
        'USER': omarchy_user,
        'HOME': f'/home/{omarchy_user}',
    })
    
    cmd = ['arch-chroot', '-u', omarchy_user, '/mnt'] + list(args)
    return subprocess.run(cmd, env=env, stdout=stdout, stderr=stderr)


def install_base_system():
    """Install base Arch Linux system via archinstall."""
    # Ensure OMARCHY_PATH is set before we need it
    if 'OMARCHY_PATH' not in os.environ:
        get_helpers_path()
    
    debug_log("install_base_system: Initializing pacman keyring")
    
    # Initialize keyring if needed
    gnupg_dir = Path('/etc/pacman.d/gnupg')
    if not gnupg_dir.exists() or not (gnupg_dir / 'pubring.gpg').exists():
        debug = os.environ.get('OMARCHY_DEBUG')
        if debug:
            subprocess.run(['pacman-key', '--init'],
                         stdout=open(LOG_FILE, 'a'), stderr=subprocess.STDOUT, check=False)
        else:
            subprocess.run(['pacman-key', '--init'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        debug_log("install_base_system: Keyring already initialized")
    
    # Populate keyrings
    debug = os.environ.get('OMARCHY_DEBUG')
    if debug:
        subprocess.run(['pacman-key', '--populate', 'archlinux'],
                     stdout=open(LOG_FILE, 'a'), stderr=subprocess.STDOUT, check=False)
        subprocess.run(['pacman-key', '--populate', 'omarchy'],
                     stdout=open(LOG_FILE, 'a'), stderr=subprocess.STDOUT, check=False)
    else:
        subprocess.run(['pacman-key', '--populate', 'archlinux'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        subprocess.run(['pacman-key', '--populate', 'omarchy'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    
    # Verify offline mirror exists (packages should be pre-downloaded in ISO)
    offline_mirror_path = Path('/var/cache/omarchy/mirror/offline')
    if not offline_mirror_path.exists():
        log("install_base_system: WARNING: Offline mirror directory not found!")
    else:
        package_count = len(list(offline_mirror_path.glob('*.pkg.tar.*')))
        log(f"install_base_system: Offline mirror contains {package_count} package files")
        if package_count == 0:
            log("install_base_system: WARNING: Offline mirror is empty!")
    
    # CRITICAL: Configure pacman.conf to use offline mirror BEFORE archinstall runs
    # archinstall syncs the package database before reading the config, so pacman.conf must be correct
    pacman_conf_path = Path('/etc/pacman.conf')
    if pacman_conf_path.exists():
        pacman_conf_content = pacman_conf_path.read_text()
        if 'file:///var/cache/omarchy/mirror/offline' not in pacman_conf_content:
            log("install_base_system: Configuring pacman.conf for offline mirror...")
            # Read the offline pacman.conf template
            # Use OMARCHY_PATH if set, otherwise try common paths
            omarchy_path = Path(os.environ.get('OMARCHY_PATH', '/root/omarchy'))
            offline_pacman_conf = omarchy_path / 'iso-builder' / 'configs' / 'pacman.conf'
            if not offline_pacman_conf.exists():
                # Try alternative path structure
                offline_pacman_conf = omarchy_path / 'configs' / 'pacman.conf'
            if offline_pacman_conf.exists():
                offline_content = offline_pacman_conf.read_text()
                # Backup original
                backup_path = pacman_conf_path.with_suffix('.conf.backup')
                pacman_conf_path.rename(backup_path)
                # Write offline configuration
                pacman_conf_path.write_text(offline_content)
                log("install_base_system: ✓ Configured pacman.conf for offline mirror")
            else:
                log(f"install_base_system: WARNING: Offline pacman.conf template not found at {offline_pacman_conf}")
                log("install_base_system: WARNING: Offline pacman.conf template not found, trying to modify existing...")
                # Fallback: Modify existing pacman.conf to add offline repos
                import re
                # Remove all existing repo sections
                modified_content = re.sub(r'\[.*?\].*?(?=\n\[|\Z)', '', pacman_conf_content, flags=re.DOTALL)
                # Keep only the [options] section
                options_match = re.search(r'\[options\].*?(?=\n\[|\Z)', pacman_conf_content, re.DOTALL)
                if options_match:
                    modified_content = options_match.group() + "\n\n"
                # Add offline repos
                offline_repos = """
[offline]
SigLevel = Optional TrustAll
Server = file:///var/cache/omarchy/mirror/offline/

[omarchy]
SigLevel = Optional TrustAll
Server = file:///var/cache/omarchy/mirror/offline/
"""
                modified_content += offline_repos
                # Backup and write
                backup_path = pacman_conf_path.with_suffix('.conf.backup')
                pacman_conf_path.rename(backup_path)
                pacman_conf_path.write_text(modified_content)
                log("install_base_system: ✓ Modified pacman.conf for offline mirror")
        else:
            log("install_base_system: ✓ pacman.conf already configured for offline mirror")
    else:
        log("install_base_system: ERROR: pacman.conf not found!")
        return False
    
    debug_log("install_base_system: Cleaning up old mounts")
    # Unmount any existing mounts
    subprocess.run(['findmnt', '-R', '/mnt'], capture_output=True)
    subprocess.run(['umount', '-R', '/mnt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    
    log("install_base_system: Starting archinstall")
    log("install_base_system: Using offline mirror - network connectivity not required")
    
    # Run archinstall - show output to console
    log("install_base_system: Running archinstall (this may take a while)...")
    archinstall_result = subprocess.run([
        'archinstall',
        '--config', 'user_configuration.json',
        '--creds', 'user_credentials.json',
        '--silent',
        '--skip-ntp',
        '--skip-wkd',
        '--skip-wifi-check'
    ], stdout=sys.stdout, stderr=sys.stderr)
    
    if archinstall_result.returncode != 0:
        log(f"install_base_system: ERROR: archinstall failed with return code {archinstall_result.returncode}")
        raise RuntimeError(f"archinstall failed with return code {archinstall_result.returncode}")
    
    log("install_base_system: Archinstall completed, verifying installation...")
    log("install_base_system: [VERIFICATION] Starting post-archinstall verification checks...")
    
    # Check archinstall log for success indicators
    archinstall_log = Path('/var/log/archinstall/install.log')
    installation_successful = False
    if archinstall_log.exists():
        try:
            with open(archinstall_log, 'r') as f:
                log_content = f.read()
                # Check for success indicators
                if 'Installation completed without any errors' in log_content:
                    installation_successful = True
                    log("install_base_system: Archinstall log indicates successful installation")
                elif 'Failed to sync Arch Linux package database' in log_content:
                    log("install_base_system: ERROR: Archinstall log shows database sync failure")
                    log("install_base_system: This indicates network connectivity issues prevented installation")
                    log("install_base_system: Last 20 lines of archinstall log:")
                    lines = log_content.split('\n')
                    for line in lines[-20:]:
                        log(f"  {line}")
                    raise RuntimeError("archinstall failed to sync package database (network connectivity issue)")
                elif 'error' in log_content.lower() or 'failed' in log_content.lower():
                    log("install_base_system: WARNING: Archinstall log contains errors")
                    # Show last few error lines
                    lines = log_content.split('\n')
                    error_lines = [line for line in lines if 'error' in line.lower() or 'failed' in line.lower()]
                    if error_lines:
                        log("install_base_system: Recent errors from archinstall log:")
                        for line in error_lines[-5:]:
                            log(f"  {line}")
        except RuntimeError:
            # Re-raise RuntimeError (database sync failure)
            raise
        except Exception as e:
            log(f"install_base_system: Could not read archinstall log: {e}")
    
    # Verify that archinstall actually installed a system
    # archinstall can return 0 even when network failures prevent installation
    mnt_etc = Path('/mnt/etc')
    if not mnt_etc.exists():
        log("install_base_system: ERROR: /mnt/etc does not exist - archinstall did not install base system")
        log("install_base_system: This is likely due to network connectivity issues")
        log("install_base_system: Check archinstall log at /var/log/archinstall/install.log for details")
        
        # Show last 20 lines of log for debugging
        if archinstall_log.exists():
            log("install_base_system: Last 20 lines of archinstall log:")
            try:
                with open(archinstall_log, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        log(f"  {line.rstrip()}")
            except Exception as e:
                log(f"install_base_system: Could not read archinstall log: {e}")
        
        raise RuntimeError("archinstall completed but did not install base system (likely network failure)")
    
    # Verify critical files exist
    pacman_conf_target = Path('/mnt/etc/pacman.conf')
    if not pacman_conf_target.exists():
        # Check if archinstall created pacman.conf in a different location
        log("install_base_system: /mnt/etc/pacman.conf does not exist, checking if archinstall created it...")
        # archinstall should have created this, but if not, we'll create it
        if not mnt_etc.exists():
            raise RuntimeError("/mnt/etc directory does not exist - installation incomplete")
    
    log("install_base_system: Installation verified, setting up chroot environment")
    
    # Configure installed system to use offline mirror
    # Copy pacman config from ISO (which is already configured for offline mirror)
    if not pacman_conf_target.exists():
        log("install_base_system: Copying pacman.conf to installed system")
        shutil.copy2('/etc/pacman.conf', str(pacman_conf_target))
        log("install_base_system: ✓ Installed system pacman.conf configured for offline mirror")
    else:
        debug_log("install_base_system: pacman.conf already exists in installed system")
        # Check if it's already configured for offline mirror
        pacman_conf_content = pacman_conf_target.read_text()
        if 'file:///var/cache/omarchy/mirror/offline' not in pacman_conf_content:
            debug_log("install_base_system: Updating installed system pacman.conf to use offline mirror")
            # Replace with ISO's pacman.conf which is already configured for offline
            shutil.copy2('/etc/pacman.conf', str(pacman_conf_target))
            log("install_base_system: ✓ Updated installed system pacman.conf to use offline mirror")
        else:
            log("install_base_system: Installed system pacman.conf already configured for offline mirror")
    
    debug_log("install_base_system: Mounting offline mirror")
    # Mount offline mirror from ISO to installed system
    offline_mirror_source = Path('/var/cache/omarchy/mirror/offline')
    cache_target = Path('/mnt/var/cache/omarchy/mirror/offline')
    
    # Verify source exists and has packages
    if not offline_mirror_source.exists():
        log("install_base_system: ERROR: Offline mirror source not found at /var/cache/omarchy/mirror/offline")
        raise RuntimeError("Offline mirror not found in ISO")
    
    package_files = list(offline_mirror_source.glob('*.pkg.tar.*'))
    if not package_files:
        log("install_base_system: WARNING: Offline mirror appears to be empty!")
    else:
        log(f"install_base_system: Offline mirror contains {len(package_files)} package files")
    
    # Create target directory
    cache_target.mkdir(parents=True, exist_ok=True)
    
    # Mount the offline mirror
    mount_result = subprocess.run(
        ['mount', '--bind', str(offline_mirror_source), str(cache_target)],
        capture_output=True,
        text=True
    )
    
    if mount_result.returncode != 0:
        log(f"install_base_system: ERROR: Failed to mount offline mirror: {mount_result.stderr}")
        raise RuntimeError(f"Failed to mount offline mirror: {mount_result.stderr}")
    
    log("install_base_system: ✓ Offline mirror mounted successfully")
    
    debug_log("install_base_system: Mounting packages directory")
    # Mount packages dir
    packages_target = Path('/mnt/opt/packages')
    packages_target.mkdir(parents=True, exist_ok=True)
    subprocess.run(['mount', '--bind', '/opt/packages', str(packages_target)], check=True)
    
    debug_log("install_base_system: Setting up sudoers")
    # Setup sudoers
    sudoers_dir = Path('/mnt/etc/sudoers.d')
    sudoers_dir.mkdir(parents=True, exist_ok=True)
    
    omarchy_user = os.environ.get('OMARCHY_USER')
    sudoers_content = f"""root ALL=(ALL:ALL) NOPASSWD: ALL
%wheel ALL=(ALL:ALL) NOPASSWD: ALL
{omarchy_user} ALL=(ALL:ALL) NOPASSWD: ALL
"""
    (sudoers_dir / '99-omarchy-installer').write_text(sudoers_content)
    (sudoers_dir / '99-omarchy-installer').chmod(0o440)
    
    log("install_base_system: Ensuring user home directory exists")
    # Ensure user home exists
    user_home = Path(f'/mnt/home/{omarchy_user}')
    if not user_home.exists():
        debug_log("install_base_system: Home directory doesn't exist, creating it")
        user_home.mkdir(parents=True, exist_ok=True)
        
        skel = Path('/mnt/etc/skel')
        if skel.exists():
            subprocess.run(['cp', '-r'] + [str(skel / '.')] + [str(user_home)],
                         check=False)
        
        user_home.chmod(0o755)
        subprocess.run(['chown', '-R', '1000:1000', str(user_home)], check=True)
    
    log("install_base_system: Copying Homerchy repository to user home")
    # Copy Homerchy repo
    omarchy_path = Path(os.environ['OMARCHY_PATH'])
    local_share = Path(f'/mnt/home/{omarchy_user}/.local/share')
    local_share.mkdir(parents=True, exist_ok=True)
    
    target_omarchy = local_share / 'omarchy'
    if target_omarchy.exists():
        shutil.rmtree(target_omarchy)
    shutil.copytree(omarchy_path, target_omarchy)
    
    subprocess.run(['chown', '-R', '1000:1000', str(local_share)], check=True)
    
    debug_log("install_base_system: Setting executable permissions")
    # Set executable permissions
    for bin_file in target_omarchy.rglob('bin/*'):
        if bin_file.is_file():
            bin_file.chmod(0o755)
    
    boot_sh = target_omarchy / 'boot.sh'
    if boot_sh.exists():
        boot_sh.chmod(0o755)
    
    waybar_script = target_omarchy / 'default' / 'waybar' / 'indicators' / 'screen-recording.sh'
    if waybar_script.exists():
        waybar_script.chmod(0o755)
    
    log("install_base_system: Completed successfully")


def install_arch():
    """Install base Arch Linux system."""
    # Call clear_logo from helpers (shell function)
    shell_cmd('clear_logo', check=False)
    
    # Use gum to display message (from helpers)
    shell_cmd('gum style --foreground 3 --padding "1 0 0 $PADDING_LEFT" "Installing..."', check=False)
    print()
    
    os.environ['CURRENT_SCRIPT'] = 'install_base_system'
    
    try:
        install_base_system()
        return True
    except Exception as e:
        log(f"install_arch: ERROR: {e}")
        return False
    finally:
        if 'CURRENT_SCRIPT' in os.environ:
            del os.environ['CURRENT_SCRIPT']


def install_homerchy():
    """Install Homerchy on top of base Arch."""
    omarchy_user = os.environ.get('OMARCHY_USER')
    if not omarchy_user:
        log("install_homerchy: ERROR: OMARCHY_USER not set")
        return False
    
    debug = os.environ.get('OMARCHY_DEBUG')
    
    # Install gum in chroot
    debug_log("install_homerchy: Installing gum in chroot")
    cmd = ['bash', '-lc', 'sudo pacman -S --noconfirm --needed gum']
    if debug:
        result = chroot_bash(*cmd)
        if result.returncode != 0:
            log(f"install_homerchy: WARNING: gum installation returned {result.returncode}")
    else:
        result = chroot_bash(*cmd)
        if result.returncode != 0:
            debug_log(f"install_homerchy: WARNING: gum installation returned {result.returncode}")
    
    # Run Homerchy installer in chroot
    log("install_homerchy: Running Homerchy installer in chroot")
    install_cmd = ['bash', '-lc', f'source /home/{omarchy_user}/.local/share/omarchy/install.sh || bash']
    if debug:
        result = chroot_bash(*install_cmd)
        if result.returncode != 0:
            log(f"install_homerchy: ERROR: installer returned {result.returncode}")
            return False
    else:
        # Pass stdout/stderr through so we can see Python orchestrator output
        # The Python orchestrator uses Logger with console=True, so it will print to stdout
        result = chroot_bash(*install_cmd, stdout=sys.stdout, stderr=sys.stderr)
        if result.returncode != 0:
            log(f"install_homerchy: ERROR: installer returned {result.returncode}")
            return False
    
    # Reboot if requested by installer
    completion_marker = Path('/mnt/var/tmp/omarchy-install-completed')
    if completion_marker.exists():
        subprocess.run(['reboot'], check=False)
    
    return True


def main():
    """Main installation orchestration."""
    # Only run on tty1
    tty = os.ttyname(sys.stdout.fileno()) if hasattr(os, 'ttyname') else None
    if tty != '/dev/tty1':
        return
    
    # Initialize log
    LOG_FILE.touch()
    LOG_FILE.chmod(0o666)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"=== Homerchy Installation Started: {timestamp} ===\n")
        f.write(f"[{timestamp}] Starting automated_script.py\n")
        f.write(f"[{timestamp}] TTY: {tty}\n")
        f.write(f"[{timestamp}] User: {os.getenv('USER', 'unknown')}\n")
        f.write(f"[{timestamp}] PWD: {os.getcwd()}\n")
    
    os.environ['OMARCHY_INSTALL_LOG_FILE'] = str(LOG_FILE)
    
    try:
        use_homerchy_helpers()
    except Exception as e:
        log(f"ERROR: Failed to load Homerchy helpers: {e}")
        sys.exit(1)
    
    # Start proper logging (shell function)
    shell_cmd('start_install_log', check=False)
    
    # Run configurator
    log("Starting configurator...")
    if not run_configurator():
        log("ERROR: Configurator failed")
        sys.exit(1)
    log("Configurator completed successfully")
    
    # Install Arch
    log("Starting Arch installation...")
    if not install_arch():
        log("ERROR: Arch installation failed")
        sys.exit(1)
    log("Arch installation completed")
    
    # Install Homerchy
    log("Starting Homerchy installation...")
    if not install_homerchy():
        log("ERROR: Homerchy installation failed")
        sys.exit(1)
    log("Homerchy installation completed")
    
    # Check if reboot was requested
    completion_marker = Path('/mnt/var/tmp/omarchy-install-completed')
    if not completion_marker.exists():
        print("\nInstallation complete! Please reboot your system:")
        print("  sudo reboot\n")


if __name__ == '__main__':
    main()

