#!/usr/bin/env python3
"""
HOMESERVER Homerchy Login Limine-Snapper Setup
Copyright (C) 2024 HOMESERVER LLC

Configures Limine bootloader and Snapper snapshot management.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def check_command(command: str) -> bool:
    """Check if a command exists."""
    result = subprocess.run(
        ['command', '-v', command],
        shell=True,
        capture_output=True
    )
    return result.returncode == 0


def chrootable_systemctl_enable(service: str) -> bool:
    """Enable systemd service, handling chroot mode."""
    try:
        if os.environ.get('OMARCHY_CHROOT_INSTALL'):
            # In chroot, just enable (don't start)
            subprocess.run(['sudo', 'systemctl', 'enable', service], check=True)
        else:
            # Not in chroot, enable and start
            subprocess.run(['sudo', 'systemctl', 'enable', '--now', service], check=True)
        return True
    except subprocess.CalledProcessError as e:
        return False


def disable_limine_update_hooks() -> bool:
    """Disable hooks that call limine-update (command doesn't exist)."""
    hooks_to_disable = [
        '/usr/share/libalpm/hooks/limine-mkinitcpio.hook',
        '/etc/pacman.d/hooks/limine-mkinitcpio.hook'
    ]
    
    disabled_count = 0
    
    for hook_path in hooks_to_disable:
        hook_file = Path(hook_path)
        if hook_file.exists():
            disabled_path = Path(f"{hook_path}.disabled")
            try:
                subprocess.run(['sudo', 'mv', str(hook_file), str(disabled_path)], check=True)
                disabled_count += 1
            except subprocess.CalledProcessError:
                pass  # Ignore errors, continue
    
    # Check mkinitcpio hooks directory
    mkinitcpio_hooks_dir = Path('/usr/lib/mkinitcpio/hooks')
    if mkinitcpio_hooks_dir.exists():
        for hook_file in mkinitcpio_hooks_dir.glob('limine*'):
            if hook_file.is_file():
                try:
                    with open(hook_file, 'r') as f:
                        content = f.read()
                    if 'limine-update' in content:
                        disabled_path = Path(f"{hook_file}.disabled")
                        subprocess.run(['sudo', 'mv', str(hook_file), str(disabled_path)], check=True)
                        disabled_count += 1
                except Exception:
                    pass
    
    return disabled_count > 0


def detect_efi() -> bool:
    """Detect if system is EFI or BIOS."""
    efi_paths = [
        Path('/boot/EFI/limine/limine.conf'),
        Path('/boot/EFI/BOOT/limine.conf')
    ]
    return any(path.exists() for path in efi_paths)


def find_limine_config(efi: bool) -> Path:
    """Find Limine config file location."""
    if efi:
        # Check USB location first, then regular EFI location
        if Path('/boot/EFI/BOOT/limine.conf').exists():
            return Path('/boot/EFI/BOOT/limine.conf')
        else:
            return Path('/boot/EFI/limine/limine.conf')
    else:
        return Path('/boot/limine/limine.conf')


def extract_cmdline(config_path: Path) -> str:
    """Extract cmdline from existing Limine config."""
    if not config_path.exists():
        return ""
    
    try:
        with open(config_path, 'r') as f:
            for line in f:
                match = re.match(r'^\s*cmdline:\s*(.+)$', line)
                if match:
                    return match.group(1).strip()
    except Exception:
        pass
    
    return ""


def get_root_uuid() -> str:
    """Get root filesystem UUID."""
    try:
        result = subprocess.run(
            ['findmnt', '-n', '-o', 'UUID', '/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def create_mkinitcpio_hooks_config() -> bool:
    """Create mkinitcpio hooks configuration."""
    # Check if btrfs-overlayfs hook exists (it's optional)
    hooks_dir = Path('/usr/lib/mkinitcpio/hooks')
    btrfs_overlayfs_hook = hooks_dir / 'btrfs-overlayfs' if hooks_dir.exists() else None
    
    # Build hooks list - include btrfs-overlayfs only if hook exists
    hooks_list = [
        'base', 'udev', 'plymouth', 'keyboard', 'autodetect', 'microcode',
        'modconf', 'kms', 'keymap', 'consolefont', 'block', 'encrypt',
        'filesystems', 'fsck'
    ]
    
    if btrfs_overlayfs_hook and btrfs_overlayfs_hook.exists():
        hooks_list.append('btrfs-overlayfs')
    
    hooks_content = f"HOOKS=({' '.join(hooks_list)})\n"
    
    config_dir = Path('/etc/mkinitcpio.conf.d')
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / 'omarchy_hooks.conf'
    
    try:
        process = subprocess.Popen(
            ['sudo', 'tee', str(config_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=hooks_content)
        return process.returncode == 0
    except Exception:
        return False


def create_limine_default_config(cmdline: str, efi: bool) -> bool:
    """Create /etc/default/limine configuration."""
    config_content = f'''TARGET_OS_NAME="Homerchy"

ESP_PATH="/boot"

KERNEL_CMDLINE[default]="{cmdline}"
KERNEL_CMDLINE[default]+="quiet splash"

ENABLE_UKI=yes
CUSTOM_UKI_NAME="homerchy"

ENABLE_LIMINE_FALLBACK=yes

# Find and add other bootloaders
FIND_BOOTLOADERS=yes

BOOT_ORDER="*, *fallback, Snapshots"

MAX_SNAPSHOT_ENTRIES=5

SNAPSHOT_FORMAT_CHOICE=5
'''
    
    # UKI and EFI fallback are EFI only
    if not efi:
        lines = config_content.split('\n')
        filtered_lines = [line for line in lines if not line.startswith('ENABLE_UKI=') and not line.startswith('ENABLE_LIMINE_FALLBACK=')]
        config_content = '\n'.join(filtered_lines)
    
    try:
        process = subprocess.Popen(
            ['sudo', 'tee', '/etc/default/limine'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=config_content)
        return process.returncode == 0
    except Exception:
        return False


def create_limine_base_config() -> bool:
    """Create base Limine bootloader configuration."""
    config_content = '''### Read more at config document: https://codeberg.org/Limine/Limine/src/branch/v10.x/CONFIG.md
#timeout: 3
default_entry: 0
interface_branding: Homerchy Bootloader
interface_branding_color: 2
hash_mismatch_panic: no

term_background: 1a1b26
backdrop: 1a1b26

# Terminal colors (Tokyo Night palette)
term_palette: 15161e;f7768e;9ece6a;e0af68;7aa2f7;bb9af7;7dcfff;a9b1d6
term_palette_bright: 414868;f7768e;9ece6a;e0af68;7aa2f7;bb9af7;7dcfff;c0caf5

# Text colors
term_foreground: c0caf5
term_foreground_bright: c0caf5
term_background_bright: 24283b

'''
    
    try:
        process = subprocess.Popen(
            ['sudo', 'tee', '/boot/limine.conf'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=config_content)
        return process.returncode == 0
    except Exception:
        return False


def setup_snapper_configs() -> bool:
    """Set up Snapper configurations for root and home."""
    # Only run if not in chroot install
    if os.environ.get('OMARCHY_CHROOT_INSTALL'):
        return True
    
    try:
        # Check if root config exists
        result = subprocess.run(
            ['sudo', 'snapper', 'list-configs'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        configs = result.stdout
        
        # Create root config if needed
        if 'root' not in configs:
            subprocess.run(['sudo', 'snapper', '-c', 'root', 'create-config', '/'], check=True)
        
        # Create home config if needed
        if 'home' not in configs:
            subprocess.run(['sudo', 'snapper', '-c', 'home', 'create-config', '/home'], check=True)
        
        # Tweak default Snapper configs
        config_files = ['/etc/snapper/configs/root', '/etc/snapper/configs/home']
        for config_file in config_files:
            if Path(config_file).exists():
                # Read file
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Apply replacements
                content = re.sub(r'^TIMELINE_CREATE="yes"', 'TIMELINE_CREATE="no"', content, flags=re.MULTILINE)
                content = re.sub(r'^NUMBER_LIMIT="50"', 'NUMBER_LIMIT="5"', content, flags=re.MULTILINE)
                content = re.sub(r'^NUMBER_LIMIT_IMPORTANT="10"', 'NUMBER_LIMIT_IMPORTANT="5"', content, flags=re.MULTILINE)
                
                # Write back
                process = subprocess.Popen(
                    ['sudo', 'tee', config_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=content)
        
        return True
    except Exception:
        return False


def reenable_mkinitcpio_hooks() -> bool:
    """Re-enable mkinitcpio hooks that were disabled earlier."""
    hooks_to_reenable = [
        '/usr/share/libalpm/hooks/90-mkinitcpio-install.hook.disabled',
        '/usr/share/libalpm/hooks/60-mkinitcpio-remove.hook.disabled'
    ]
    
    reenabled_count = 0
    
    for disabled_path in hooks_to_reenable:
        disabled_file = Path(disabled_path)
        if disabled_file.exists():
            enabled_path = disabled_path.replace('.disabled', '')
            try:
                subprocess.run(['sudo', 'mv', str(disabled_file), enabled_path], check=True)
                reenabled_count += 1
            except subprocess.CalledProcessError:
                pass
    
    return reenabled_count > 0


def generate_initramfs() -> bool:
    """Generate initramfs."""
    try:
        if check_command('limine-mkinitcpio'):
            # Try limine-mkinitcpio first, fallback to mkinitcpio -P
            result = subprocess.run(['sudo', 'limine-mkinitcpio'], capture_output=True, timeout=600)
            if result.returncode != 0:
                subprocess.run(['sudo', 'mkinitcpio', '-P'], check=True, timeout=600)
        else:
            subprocess.run(['sudo', 'mkinitcpio', '-P'], check=True, timeout=600)
        return True
    except Exception:
        return False


def create_limine_entries(cmdline: str) -> int:
    """Create Limine bootloader entries for all available kernels."""
    boot_dir = Path('/boot')
    kernels = sorted(boot_dir.glob('vmlinuz-*'), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not kernels:
        return 0
    
    entries = []
    entry_count = 0
    
    for kernel_path in kernels:
        kernel_name = kernel_path.name.replace('vmlinuz-', '')
        initrd_path = boot_dir / f'initramfs-{kernel_name}.img'
        
        if initrd_path.exists():
            entry = f'''
Homerchy ({kernel_name})
    PROTOCOL: linux
    KERNEL_PATH: boot():/vmlinuz-{kernel_name}
    MODULE_PATH: boot():/initramfs-{kernel_name}.img
    CMDLINE: {cmdline} quiet splash
'''
            entries.append(entry)
            entry_count += 1
    
    if entry_count > 0:
        # Append entries to config
        try:
            with open('/boot/limine.conf', 'a') as f:
                f.write(''.join(entries))
            
            # Update default_entry to 0
            with open('/boot/limine.conf', 'r') as f:
                content = f.read()
            
            content = re.sub(r'^default_entry:.*', 'default_entry: 0', content, flags=re.MULTILINE)
            
            process = subprocess.Popen(
                ['sudo', 'tee', '/boot/limine.conf'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            process.communicate(input=content)
            
        except Exception:
            pass
    
    return entry_count


def install_limine_to_efi() -> bool:
    """Install Limine EFI files to EFI partition and create boot entry."""
    try:
        # Find Limine EFI binary
        limine_efi_paths = [
            Path('/usr/share/limine/limine-uefi-x64.efi'),
            Path('/usr/lib/limine/limine-uefi-x64.efi'),
            Path('/usr/share/limine/BOOTX64.EFI'),
        ]
        
        limine_efi = None
        for path in limine_efi_paths:
            if path.exists():
                limine_efi = path
                break
        
        if not limine_efi:
            print("WARNING: Limine EFI binary not found, skipping EFI installation")
            return True  # Not fatal if Limine EFI not found
        
        # Determine EFI partition mount point
        boot_mount = subprocess.run(
            ['findmnt', '-n', '-o', 'TARGET', '/boot'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if boot_mount.returncode != 0:
            print("WARNING: Could not determine /boot mount point")
            return True
        
        boot_path = boot_mount.stdout.strip()
        
        # EFI directories to try
        efi_dirs = [
            Path(boot_path) / 'EFI' / 'BOOT',
            Path(boot_path) / 'EFI' / 'limine',
        ]
        
        efi_dir = None
        for dir_path in efi_dirs:
            if dir_path.exists():
                efi_dir = dir_path
                break
        
        if not efi_dir:
            # Create EFI/BOOT directory
            efi_dir = Path(boot_path) / 'EFI' / 'BOOT'
            efi_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy Limine EFI binary
        target_efi = efi_dir / 'BOOTX64.EFI'
        try:
            import shutil
            shutil.copy2(limine_efi, target_efi)
            print(f"Copied Limine EFI to {target_efi}")
        except Exception as e:
            print(f"WARNING: Failed to copy Limine EFI: {e}")
            return True
        
        # Copy limine.conf to EFI partition
        limine_conf_source = Path('/boot/limine.conf')
        if limine_conf_source.exists():
            limine_conf_target = efi_dir / 'limine.conf'
            try:
                shutil.copy2(limine_conf_source, limine_conf_target)
                print(f"Copied limine.conf to {limine_conf_target}")
            except Exception as e:
                print(f"WARNING: Failed to copy limine.conf: {e}")
        
        # Create EFI boot entry if efibootmgr is available
        if check_command('efibootmgr'):
            try:
                # Find boot device and partition
                boot_source = subprocess.run(
                    ['findmnt', '-n', '-o', 'SOURCE', '/boot'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if boot_source.returncode == 0:
                    boot_device = boot_source.stdout.strip()
                    
                    # Extract disk and partition number
                    # Format is usually /dev/sda1 or /dev/nvme0n1p1
                    import re
                    match = re.match(r'(.+?)(p?\d+)$', boot_device)
                    if match:
                        disk = match.group(1)
                        part = match.group(2).lstrip('p')
                        
                        # Create EFI boot entry
                        result = subprocess.run(
                            [
                                'sudo', 'efibootmgr', '--create',
                                '--disk', disk,
                                '--part', part,
                                '--label', 'Homerchy',
                                '--loader', f'\\EFI\\BOOT\\BOOTX64.EFI'
                            ],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode == 0:
                            print("Created EFI boot entry for Homerchy")
                        else:
                            print(f"WARNING: Failed to create EFI boot entry: {result.stderr}")
            except Exception as e:
                print(f"WARNING: Failed to create EFI boot entry: {e}")
        
        return True
    except Exception as e:
        print(f"WARNING: EFI installation failed: {e}")
        return True  # Don't fail installation if EFI setup fails


def cleanup_efi_boot_entries() -> bool:
    """Remove archinstall-created Limine entries from EFI."""
    if not check_command('efibootmgr'):
        return True  # Not an error if efibootmgr not available
    
    try:
        result = subprocess.run(
            ['efibootmgr'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return True
        
        # Find boot entries matching "Arch Linux Limine"
        boot_entries = []
        for line in result.stdout.split('\n'):
            match = re.match(r'^Boot([0-9]{4})\*?\s+Arch Linux Limine', line)
            if match:
                boot_entries.append(match.group(1))
        
        # Remove each entry
        for bootnum in boot_entries:
            subprocess.run(
                ['sudo', 'efibootmgr', '-b', bootnum, '-B'],
                capture_output=True,
                timeout=10
            )
        
        return True
    except Exception:
        return True  # Don't fail if cleanup fails


def main(config: dict) -> dict:
    """
    Main function - configures Limine and Snapper.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    if not check_command('limine'):
        return {"success": True, "message": "Limine not found, skipping"}
    
    try:
        # Install required packages
        subprocess.run(
            ['sudo', 'pacman', '-S', '--noconfirm', '--needed', 'limine-snapper-sync', 'limine-mkinitcpio-hook'],
            check=True,
            timeout=300
        )
        
        # Disable limine-update hooks
        disable_limine_update_hooks()
        
        # Create mkinitcpio hooks config
        if not create_mkinitcpio_hooks_config():
            return {"success": False, "message": "Failed to create mkinitcpio hooks config"}
        
        # Detect EFI vs BIOS
        efi = detect_efi()
        
        # Find Limine config
        limine_config = find_limine_config(efi)
        
        if not limine_config.exists():
            return {"success": False, "message": f"Limine config not found at {limine_config}"}
        
        # Extract cmdline
        cmdline = extract_cmdline(limine_config)
        if not cmdline:
            root_uuid = get_root_uuid()
            if root_uuid:
                cmdline = f"root=UUID={root_uuid} rw"
            else:
                cmdline = "root=UUID=unknown rw"
        
        # Create /etc/default/limine
        if not create_limine_default_config(cmdline, efi):
            return {"success": False, "message": "Failed to create /etc/default/limine"}
        
        # Create base Limine config
        if not create_limine_base_config():
            return {"success": False, "message": "Failed to create base Limine config"}
        
        # Copy limine.conf to EFI partition if EFI system
        if efi:
            efi_config_locations = [
                Path('/boot/EFI/BOOT/limine.conf'),
                Path('/boot/EFI/limine/limine.conf')
            ]
            for efi_config in efi_config_locations:
                efi_config.parent.mkdir(parents=True, exist_ok=True)
                try:
                    import shutil
                    shutil.copy2(Path('/boot/limine.conf'), efi_config)
                    print(f"Copied limine.conf to {efi_config}")
                except Exception as e:
                    print(f"WARNING: Failed to copy limine.conf to {efi_config}: {e}")
        
        # Remove original config if different location (but keep EFI copies)
        if limine_config != Path('/boot/limine.conf') and limine_config.exists():
            # Only remove if it's not one of the EFI locations we just created
            if limine_config not in [Path('/boot/EFI/BOOT/limine.conf'), Path('/boot/EFI/limine/limine.conf')]:
                subprocess.run(['sudo', 'rm', str(limine_config)], check=False)
        
        # Setup Snapper configs
        if not setup_snapper_configs():
            return {"success": False, "message": "Failed to setup Snapper configs"}
        
        # Enable limine-snapper-sync service
        if not chrootable_systemctl_enable('limine-snapper-sync.service'):
            return {"success": False, "message": "Failed to enable limine-snapper-sync.service"}
        
        # Re-enable mkinitcpio hooks
        reenable_mkinitcpio_hooks()
        
        # Generate initramfs
        if not generate_initramfs():
            return {"success": False, "message": "Failed to generate initramfs"}
        
        # Create Limine boot entries
        entry_count = create_limine_entries(cmdline)
        if entry_count == 0:
            return {"success": False, "message": "No valid kernel/initramfs pairs found"}
        
        # Cleanup old EFI boot entries
        if efi:
            cleanup_efi_boot_entries()
            # Install Limine to EFI partition and create boot entry
            install_limine_to_efi()
        
        return {"success": True, "message": f"Limine and Snapper configured successfully ({entry_count} boot entries created)"}
    
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Command failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
