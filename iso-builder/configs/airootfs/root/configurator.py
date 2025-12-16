#!/usr/bin/env python3
"""
HOMESERVER Homerchy Configurator
Copyright (C) 2024 HOMESERVER LLC

Interactive configuration script for Homerchy installation.
Collects keyboard layout, user credentials, system settings, and disk selection.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Set log file path early
LOG_FILE = Path(os.environ.get('OMARCHY_INSTALL_LOG_FILE', '/var/log/omarchy-install.log'))
STEP_COUNT = 0


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
    log_line = f"[{timestamp}] configurator: {message}"
    # Write to file
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{log_line}\n")
    except Exception:
        pass  # Best effort logging
    # Also print to console
    print(log_line, flush=True)


def get_helpers_path() -> Path:
    """Get path to helpers/all.sh file."""
    homerchy_path = Path('/root/homerchy')
    omarchy_path = Path('/root/omarchy')
    
    # Use symlink if it exists, otherwise check for direct path
    if omarchy_path.exists() or omarchy_path.is_symlink():
        os.environ['OMARCHY_PATH'] = str(omarchy_path)
    elif homerchy_path.exists():
        os.environ['OMARCHY_PATH'] = str(homerchy_path)
    else:
        os.environ['OMARCHY_PATH'] = '/root/omarchy'
    
    # VM test mode is auto-detected in main(), no need to source vm-env.sh
    
    omarchy_path = Path(os.environ['OMARCHY_PATH'])
    install_path = omarchy_path / 'install'
    
    os.environ['OMARCHY_INSTALL'] = str(install_path)
    os.environ['OMARCHY_INSTALL_LOG_FILE'] = str(LOG_FILE)
    
    helpers_file = install_path / 'helpers' / 'all.sh'
    if not helpers_file.exists():
        raise FileNotFoundError(f"Homerchy helpers not found: {helpers_file}")
    
    return helpers_file


def shell_cmd(cmd: str, check: bool = False, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Execute a shell command with helpers sourced."""
    helpers_file = get_helpers_path()
    full_cmd = f'source {helpers_file} && {cmd}'
    kwargs = {'check': check}
    if capture_output:
        kwargs['capture_output'] = True
        kwargs['text'] = True
    return subprocess.run(['bash', '-c', full_cmd], **kwargs)


def abort(message: str = "Aborted installation"):
    """Abort installation with message."""
    subprocess.run(['gum', 'style', message], check=False)
    print()
    subprocess.run(['gum', 'style', 'You can retry later by running: python3 ./.automated_script.py'], check=False)
    sys.exit(1)


def step(title: str):
    """Display step title with logo clearing on first call."""
    global STEP_COUNT
    if STEP_COUNT == 0:
        shell_cmd('clear_logo', check=False)
        STEP_COUNT = 1
    print()
    subprocess.run(['gum', 'style', title], check=False)
    print()


def notice(title: str, duration: int = 2):
    """Display notice with spinner."""
    print()
    subprocess.run(['gum', 'spin', '--spinner', 'pulse', '--title', title, '--', 'sleep', str(duration)], check=False)
    print()


def load_vm_settings() -> Optional[Dict]:
    """Load VM test settings from index.json."""
    vmtools_dir = Path('/root/vmtools')
    index_file = vmtools_dir / 'index.json'
    profile_name = os.environ.get('OMARCHY_VM_PROFILE')
    
    print(f"[LOAD_VM_SETTINGS] Called with OMARCHY_VM_TEST={os.environ.get('OMARCHY_VM_TEST')}", flush=True)
    
    if os.environ.get('OMARCHY_VM_TEST') != '1':
        print(f"[LOAD_VM_SETTINGS] ✗ VM test mode not enabled", flush=True)
        debug_log("load_vm_settings: VM test mode not enabled")
        return None
    
    # Load from index.json
    print(f"[LOAD_VM_SETTINGS] Checking for index.json at: {index_file}", flush=True)
    if not index_file.exists():
        print(f"[LOAD_VM_SETTINGS] ✗ index.json not found at {index_file}", flush=True)
        debug_log("load_vm_settings: index.json not found")
        return None
    
    print(f"[LOAD_VM_SETTINGS] ✓ index.json found, loading...", flush=True)
    debug_log("load_vm_settings: Loading from index.json")
    try:
        with open(index_file) as f:
            index_data = json.load(f)
        
        # Determine which profile to use
        if not profile_name:
            profile_name = index_data.get('default_profile', 'homerchy-test')
            print(f"[LOAD_VM_SETTINGS] Using default profile: {profile_name}", flush=True)
            debug_log(f"load_vm_settings: Using default profile: {profile_name}")
        else:
            print(f"[LOAD_VM_SETTINGS] Using specified profile: {profile_name}", flush=True)
            debug_log(f"load_vm_settings: Using specified profile: {profile_name}")
        
        # Validate profile exists
        profiles = index_data.get('profiles', {})
        print(f"[LOAD_VM_SETTINGS] Available profiles: {list(profiles.keys())}", flush=True)
        
        if profile_name not in profiles:
            print(f"[LOAD_VM_SETTINGS] ✗ Profile '{profile_name}' not found!", flush=True)
            log(f"load_vm_settings: WARNING: Profile '{profile_name}' not found in index.json, using defaults")
            return None
        
        profile = profiles[profile_name]
        settings = {
            'keyboard_choice': profile.get('keyboard', {}).get('choice', 'English (US)'),
            'keyboard_code': profile.get('keyboard', {}).get('code', 'us'),
            'username': profile.get('user', {}).get('username', 'testuser'),
            'password': profile.get('user', {}).get('password', 'testpass123'),
            'full_name': profile.get('user', {}).get('full_name', 'Test User'),
            'email_address': profile.get('user', {}).get('email_address', 'test@example.com'),
            'hostname': profile.get('system', {}).get('hostname', 'homerchy'),
            'timezone': profile.get('system', {}).get('timezone', 'America/New_York'),
        }
        print(f"[LOAD_VM_SETTINGS] ✓ Successfully loaded profile '{profile_name}'", flush=True)
        print(f"[LOAD_VM_SETTINGS]   Username: {settings['username']}, Hostname: {settings['hostname']}", flush=True)
        debug_log(f"load_vm_settings: Loaded profile '{profile_name}' from index.json successfully")
        return settings
    except Exception as e:
        print(f"[LOAD_VM_SETTINGS] ✗ ERROR loading index.json: {e}", flush=True)
        debug_log(f"load_vm_settings: Error loading index.json: {e}")
        import traceback
        traceback.print_exc()
        return None


def keyboard_form() -> Tuple[str, str]:
    """Collect keyboard layout selection."""
    # CRITICAL: Check for index.json FIRST, before ANYTHING else
    index_check = Path('/root/vmtools/index.json')
    vm_test = os.environ.get('OMARCHY_VM_TEST')
    
    print(f"[KEYBOARD_FORM] ENTERED - VM_TEST={vm_test}, index.json exists={index_check.exists()}", flush=True)
    
    # Force enable VM mode if index.json exists
    if index_check.exists():
        os.environ['OMARCHY_VM_TEST'] = '1'
        vm_test = '1'
        print(f"[KEYBOARD_FORM] ✓✓✓ FORCE ENABLED VM MODE ✓✓✓", flush=True)
    else:
        print(f"[KEYBOARD_FORM] ✗ index.json NOT FOUND at {index_check}", flush=True)
    
    # ONLY show step UI if NOT in VM mode
    if vm_test != '1':
        print(f"[KEYBOARD_FORM] Showing interactive step (VM mode disabled)", flush=True)
        step("Let's setup your machine... WE'RE SEEING IF THERE ARE ACTUALLY CHANGES HERE")
    else:
        print(f"[KEYBOARD_FORM] ✓✓✓ SKIPPING INTERACTIVE STEP - VM MODE ACTIVE ✓✓✓", flush=True)
        # DO NOT CALL step() - it shows the UI
    
    keyboards = [
        ('Azerbaijani', 'azerty'), ('Belarusian', 'by'), ('Belgian', 'be-latin1'),
        ('Bosnian', 'ba'), ('Bulgarian', 'bg-cp1251'), ('Croatian', 'croat'),
        ('Czech', 'cz'), ('Danish', 'dk-latin1'), ('Dutch', 'nl'),
        ('English (UK)', 'uk'), ('English (US)', 'us'), ('English (US, Dvorak)', 'dvorak'),
        ('Estonian', 'et'), ('Finnish', 'fi'), ('French', 'fr'),
        ('French (Canada)', 'cf'), ('French (Switzerland)', 'fr_CH'), ('Georgian', 'ge'),
        ('German', 'de'), ('German (Switzerland)', 'de_CH-latin1'), ('Greek', 'gr'),
        ('Hebrew', 'il'), ('Hungarian', 'hu'), ('Icelandic', 'is-latin1'),
        ('Irish', 'ie'), ('Italian', 'it'), ('Japanese', 'jp106'),
        ('Kazakh', 'kazakh'), ('Khmer (Cambodia)', 'khmer'), ('Kyrgyz', 'kyrgyz'),
        ('Lao', 'la-latin1'), ('Latvian', 'lv'), ('Lithuanian', 'lt'),
        ('Macedonian', 'mk-utf'), ('Norwegian', 'no-latin1'), ('Polish', 'pl'),
        ('Portuguese', 'pt-latin1'), ('Portuguese (Brazil)', 'br-abnt2'), ('Romanian', 'ro'),
        ('Russian', 'ru'), ('Serbian', 'sr-latin'), ('Slovak', 'sk-qwertz'),
        ('Slovenian', 'slovene'), ('Spanish', 'es'), ('Spanish (Latin American)', 'la-latin1'),
        ('Swedish', 'sv-latin1'), ('Tajik', 'tj_alt-UTF8'), ('Turkish', 'trq'),
        ('Ukrainian', 'ua'),
    ]
    
    # Use the vm_test we already determined above
    # (no need to check again, we already forced it if index.json exists)
    if vm_test == '1':
        print(f"[KEYBOARD_FORM] VM mode detected, loading profile settings...", flush=True)
        settings = load_vm_settings()
        if settings:
            choice = settings['keyboard_choice']
            keyboard = settings['keyboard_code']
            debug_log(f"keyboard_form: VM Test Mode - using settings from profile")
            print(f"[KEYBOARD_FORM] ✓ Using profile: {choice} ({keyboard})", flush=True)
        else:
            # Fallback to defaults if settings file not found
            choice = "English (US)"
            keyboard = "us"
            debug_log("keyboard_form: VM Test Mode - using fallback defaults (English US)")
            print(f"[KEYBOARD_FORM] WARNING: Profile not loaded, using defaults: {choice} ({keyboard})", flush=True)
    else:
        # Interactive selection
        keyboard_choices = [name for name, _ in keyboards]
        choice_proc = subprocess.run(
            ['gum', 'choose', '--height', '10', '--selected', 'English (US)', '--header', 'Select keyboard layout'],
            input='\n'.join(keyboard_choices),
            text=True,
            capture_output=True
        )
        if choice_proc.returncode != 0:
            abort()
        choice = choice_proc.stdout.strip()
        
        # Find corresponding code
        keyboard = next((code for name, code in keyboards if name == choice), 'us')
        debug_log(f"keyboard_form: Selected {choice} ({keyboard})")
    
    # Only attempt to load keyboard layout if we're on a real console
    # loadkeys only works on Linux virtual consoles (tty), not in terminal emulators
    try:
        tty_name = os.ttyname(sys.stdout.fileno()) if hasattr(os, 'ttyname') else None
        if tty_name and '/dev/tty' in tty_name:
            subprocess.run(['loadkeys', keyboard], capture_output=True, check=False)
            debug_log("keyboard_form: Loaded keyboard layout")
    except Exception:
        pass  # Not a real console, skip
    
    debug_log("keyboard_form: Completed")
    return choice, keyboard


def user_form() -> Dict[str, str]:
    """Collect user account information."""
    debug_log("user_form: Starting")
    
    # Check VM mode BEFORE calling step() which shows UI
    index_check = Path('/root/vmtools/index.json')
    vm_test = os.environ.get('OMARCHY_VM_TEST')
    if index_check.exists() and vm_test != '1':
        os.environ['OMARCHY_VM_TEST'] = '1'
        vm_test = '1'
        print(f"[USER_FORM] Force-enabled VM mode before step()", flush=True)
    
    print(f"[USER_FORM] VM mode check: OMARCHY_VM_TEST={vm_test}, index.json exists={index_check.exists()}", flush=True)
    
    # Only show step UI if NOT in VM mode
    if vm_test != '1':
        step("Let's setup your user account...")
    else:
        print(f"[USER_FORM] VM mode active - skipping interactive step", flush=True)
    
    if vm_test == '1':
        print(f"[USER_FORM] VM mode detected, loading profile settings...", flush=True)
        settings = load_vm_settings()
        if settings:
            username = settings['username']
            password = settings['password']
            password_confirmation = settings['password']
            full_name = settings['full_name']
            email_address = settings['email_address']
            hostname = settings['hostname']
            timezone = settings['timezone']
            debug_log("user_form: VM Test Mode - using settings from profile")
            debug_log(f"user_form: Username={username}, Hostname={hostname}, Timezone={timezone}")
            print("[USER_FORM] ✓ Using profile values:", flush=True)
            print(f"  Username: {username}", flush=True)
            print(f"  Hostname: {hostname}", flush=True)
            print(f"  Timezone: {timezone}", flush=True)
        else:
            # Fallback to defaults if settings file not found
            username = "testuser"
            password = "testpass123"
            password_confirmation = "testpass123"
            full_name = "Test User"
            email_address = "test@example.com"
            hostname = "homerchy"
            timezone = "America/New_York"
            debug_log("user_form: VM Test Mode - using fallback defaults")
            debug_log(f"user_form: Username={username}, Hostname={hostname}, Timezone={timezone}")
            print("VM Test Mode: Using default values")
            print(f"  Username: {username}")
            print(f"  Hostname: {hostname}")
            print(f"  Timezone: {timezone}")
    else:
        # Interactive mode
        while True:
            username_proc = subprocess.run(
                ['gum', 'input', '--placeholder', 'Alphanumeric without spaces (like dhh)',
                 '--prompt.foreground', '#845DF9', '--prompt', 'Username> '],
                capture_output=True, text=True
            )
            if username_proc.returncode != 0:
                abort()
            username = username_proc.stdout.strip()
            
            if re.match(r'^[a-z_][a-z0-9_-]*[$]?$', username):
                break
            else:
                notice("Username must be alphanumeric with no spaces", 1)
        
        while True:
            password_proc = subprocess.run(
                ['gum', 'input', '--placeholder', 'Used for user + root + encryption',
                 '--prompt.foreground', '#845DF9', '--password', '--prompt', 'Password> '],
                capture_output=True, text=True
            )
            if password_proc.returncode != 0:
                abort()
            password = password_proc.stdout.strip()
            
            password_conf_proc = subprocess.run(
                ['gum', 'input', '--placeholder', 'Must match the password you just typed',
                 '--prompt.foreground', '#845DF9', '--password', '--prompt', 'Confirm> '],
                capture_output=True, text=True
            )
            if password_conf_proc.returncode != 0:
                abort()
            password_confirmation = password_conf_proc.stdout.strip()
            
            if password and password == password_confirmation:
                break
            elif not password:
                notice("Your password can't be blank!", 1)
            else:
                notice("Passwords didn't match!", 1)
        
        full_name_proc = subprocess.run(
            ['gum', 'input', '--placeholder', 'Used for git authentication (hit return to skip)',
             '--prompt.foreground', '#845DF9', '--prompt', 'Full name> '],
            capture_output=True, text=True
        )
        full_name = full_name_proc.stdout.strip() if full_name_proc.returncode == 0 else ''
        
        email_proc = subprocess.run(
            ['gum', 'input', '--placeholder', 'Used for git authentication (hit return to skip)',
             '--prompt.foreground', '#845DF9', '--prompt', 'Email address> '],
            capture_output=True, text=True
        )
        email_address = email_proc.stdout.strip() if email_proc.returncode == 0 else ''
        
        while True:
            hostname_proc = subprocess.run(
                ['gum', 'input', '--placeholder', "Alphanumeric without spaces (or return for 'homerchy')",
                 '--prompt.foreground', '#845DF9', '--prompt', 'Hostname> '],
                capture_output=True, text=True
            )
            if hostname_proc.returncode != 0:
                abort()
            hostname = hostname_proc.stdout.strip()
            
            if re.match(r'^[A-Za-z_][A-Za-z0-9_-]*\$?$', hostname):
                break
            elif not hostname:
                hostname = "homerchy"
                break
            else:
                notice("Hostname must be alphanumeric using dashes or underscores but no spaces", 1)
        
        # Pick timezone
        geo_guessed_timezone = None
        try:
            tzupdate_proc = subprocess.run(['tzupdate', '-p'], capture_output=True, text=True, timeout=5)
            if tzupdate_proc.returncode == 0:
                geo_guessed_timezone = tzupdate_proc.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        timezones_proc = subprocess.run(['timedatectl', 'list-timezones'], capture_output=True, text=True, check=True)
        timezones = timezones_proc.stdout.strip().split('\n')
        
        if geo_guessed_timezone and geo_guessed_timezone in timezones:
            tz_proc = subprocess.run(
                ['gum', 'choose', '--height', '10', '--selected', geo_guessed_timezone, '--header', 'Timezone'],
                input='\n'.join(timezones),
                text=True,
                capture_output=True
            )
        else:
            tz_proc = subprocess.run(
                ['gum', 'filter', '--height', '10', '--header', 'Timezone'],
                input='\n'.join(timezones),
                text=True,
                capture_output=True
            )
        
        if tz_proc.returncode != 0:
            abort()
        timezone = tz_proc.stdout.strip()
    
    # Hash the password using yescrypt (via openssl)
    password_hash_proc = subprocess.run(
        ['openssl', 'passwd', '-6', '-stdin'],
        input=password,
        text=True,
        capture_output=True,
        check=True
    )
    password_hash = password_hash_proc.stdout.strip()
    
    debug_log("user_form: Completed")
    return {
        'username': username,
        'password': password,
        'password_hash': password_hash,
        'full_name': full_name,
        'email_address': email_address,
        'hostname': hostname,
        'timezone': timezone,
    }


def get_disk_info(device: str) -> str:
    """Get formatted disk information."""
    try:
        size_proc = subprocess.run(['lsblk', '-dno', 'SIZE', device], capture_output=True, text=True, check=True)
        size = size_proc.stdout.strip()
        model_proc = subprocess.run(['lsblk', '-dno', 'MODEL', device], capture_output=True, text=True, check=True)
        model = model_proc.stdout.strip()
        
        display = device
        if size:
            display = f"{display} ({size})"
        if model:
            display = f"{display} - {model}"
        return display
    except Exception:
        return device


def disk_form() -> str:
    """Collect disk selection."""
    log("disk_form: Starting")
    step("Let's select where to install Homerchy...")
    
    # Don't offer the install media as an option (Arch ISO mounts it here)
    exclude_disk = None
    try:
        findmnt_proc = subprocess.run(['findmnt', '-no', 'SOURCE', '/run/archiso/bootmnt'],
                                     capture_output=True, text=True, check=False)
        if findmnt_proc.returncode == 0:
            exclude_disk = findmnt_proc.stdout.strip()
    except Exception:
        pass
    
    debug_log(f"disk_form: Excluding boot disk: {exclude_disk or 'none'}")
    
    # List all installable disks
    lsblk_proc = subprocess.run(['lsblk', '-dpno', 'NAME,TYPE'], capture_output=True, text=True, check=True)
    available_disks = []
    for line in lsblk_proc.stdout.strip().split('\n'):
        parts = line.split()
        if len(parts) >= 2 and parts[1] == 'disk':
            disk = parts[0]
            if re.match(r'/dev/(sd|hd|vd|nvme|mmcblk|xv)', disk):
                if not exclude_disk or disk != exclude_disk:
                    available_disks.append(disk)
    
    debug_log(f"disk_form: Available disks: {' '.join(available_disks)}")
    
    # Non-interactive mode for VM testing - use first available disk
    # Force check: if index.json exists, we're in VM mode
    index_check = Path('/root/vmtools/index.json')
    vm_test = os.environ.get('OMARCHY_VM_TEST')
    if index_check.exists() and vm_test != '1':
        os.environ['OMARCHY_VM_TEST'] = '1'
        vm_test = '1'
    
    if vm_test == '1':
        if not available_disks:
            log("disk_form: ERROR: No disk found!")
            print("Error: No disk found for installation")
            sys.exit(1)
        disk = available_disks[0]
        debug_log(f"disk_form: VM Test Mode - selected disk: {disk}")
        print(f"VM Test Mode: Using disk {disk}")
    else:
        # Interactive selection
        disk_options = [get_disk_info(disk) for disk in available_disks]
        selected_proc = subprocess.run(
            ['gum', 'choose', '--header', 'Select install disk'],
            input='\n'.join(disk_options),
            text=True,
            capture_output=True
        )
        if selected_proc.returncode != 0:
            abort()
        selected_display = selected_proc.stdout.strip()
        # Extract device name (first word)
        disk = selected_display.split()[0]
        debug_log(f"disk_form: Selected disk: {disk}")
    
    debug_log("disk_form: Completed")
    return disk


def main():
    """Main configurator flow."""
    # CRITICAL: Check for index.json IMMEDIATELY and enable VM mode
    # Do this BEFORE anything else, even before printing
    vmtools_dir = Path('/root/vmtools')
    index_file = vmtools_dir / 'index.json'
    
    if index_file.exists():
        os.environ['OMARCHY_VM_TEST'] = '1'
        # Read profile immediately
        try:
            with open(index_file) as f:
                index_data = json.load(f)
                default_profile = index_data.get('default_profile', 'homerchy-test')
                os.environ['OMARCHY_VM_PROFILE'] = default_profile
        except Exception:
            os.environ['OMARCHY_VM_PROFILE'] = 'homerchy-test'
    
    # CRITICAL: Print immediately to console (before any screen clearing)
    # This proves the Python configurator is running
    print("\n\n" + "█"*70, flush=True)
    print("█" + " "*68 + "█", flush=True)
    print("█" + "  PYTHON CONFIGURATOR RUNNING (configurator.py)".center(68) + "█", flush=True)
    print("█" + " "*68 + "█", flush=True)
    print("█"*70 + "\n", flush=True)
    
    print(f"[CONFIGURATOR] Checking for VM profile: {index_file}", flush=True)
    
    # VM mode was already set above if index.json exists
    if os.environ.get('OMARCHY_VM_TEST') == '1':
        print(f"[CONFIGURATOR] ✓✓✓ VM TEST MODE ENABLED ✓✓✓", flush=True)
        print(f"[CONFIGURATOR] Found: {index_file}", flush=True)
        print(f"[CONFIGURATOR] ✓✓✓ Using profile: {os.environ.get('OMARCHY_VM_PROFILE', 'homerchy-test')} ✓✓✓", flush=True)
        print("", flush=True)
    else:
        print(f"[CONFIGURATOR] ✗✗✗ VM test mode DISABLED ✗✗✗", flush=True)
        print(f"[CONFIGURATOR] NOT FOUND: {index_file}", flush=True)
        print("", flush=True)
    
    # Print to console FIRST for immediate visibility (before logging setup)
    vm_test_status = os.environ.get('OMARCHY_VM_TEST', 'NOT SET')
    vm_profile_status = os.environ.get('OMARCHY_VM_PROFILE', 'NOT SET')
    print(f"[CONFIGURATOR] Status: VM_TEST={vm_test_status}", flush=True)
    print(f"[CONFIGURATOR] Status: VM_PROFILE={vm_profile_status}", flush=True)
    print("", flush=True)
    
    # Initialize logging
    log("Script started")
    debug_log(f"OMARCHY_PATH={os.environ.get('OMARCHY_PATH', 'not set')}")
    debug_log(f"OMARCHY_INSTALL={os.environ.get('OMARCHY_INSTALL', 'not set')}")
    debug_log(f"OMARCHY_VM_TEST={vm_test_status}")
    debug_log(f"OMARCHY_DEBUG={os.environ.get('OMARCHY_DEBUG', 'not set')}")
    debug_log(f"OMARCHY_VM_PROFILE={vm_profile_status}")
    
    # Load helpers (required for clear_logo, PADDING_LEFT, etc.)
    try:
        get_helpers_path()
        # Source helpers to make functions available
        shell_cmd('true', check=False)  # Just verify helpers are accessible
    except Exception as e:
        log(f"ERROR: Failed to load helpers: {e}")
        sys.exit(1)
    
    # Ensure tzupdate is available for guessing timezone (optional, AUR package)
    if not shutil.which('tzupdate'):
        debug_log("tzupdate not available (AUR package), timezone guessing will be skipped")
    
    # Step 1: Keyboard
    keyboard_choice, keyboard_code = keyboard_form()
    
    # Step 2: User
    user_info = user_form()
    
    # Skip confirmation in VM test mode
    if os.environ.get('OMARCHY_VM_TEST') != '1':
        while True:
            # Display summary table
            summary_data = f"""Field,Value
Username,{user_info['username']}
Password,{'*' * len(user_info['password'])}
Full name,{user_info['full_name'] or '[Skipped]'}
Email address,{user_info['email_address'] or '[Skipped]'}
Hostname,{user_info['hostname']}
Timezone,{user_info['timezone']}
Keyboard,{keyboard_code}"""
            
            # Get padding from environment (set by helpers)
            padding_left = int(os.environ.get('PADDING_LEFT', '0'))
            padding_spaces = ' ' * padding_left
            
            table_proc = subprocess.run(
                ['gum', 'table', '-s', ',', '-p'],
                input=summary_data,
                text=True,
                capture_output=True
            )
            if table_proc.returncode == 0:
                # Add padding manually since gum table -p doesn't always respect it
                for line in table_proc.stdout.split('\n'):
                    print(f"{padding_spaces}{line}")
            
            print()
            confirm_proc = subprocess.run(
                ['gum', 'confirm', '--negative', 'No, change it', 'Does this look right?'],
                capture_output=True
            )
            if confirm_proc.returncode == 0:
                break
            else:
                # Re-run forms
                keyboard_choice, keyboard_code = keyboard_form()
                user_info = user_form()
    
    # Step 3: Disk
    disk = disk_form()
    
    # Skip confirmation in VM test mode
    if os.environ.get('OMARCHY_VM_TEST') != '1':
        while True:
            subprocess.run(['gum', 'style', 'Everything will be overwritten. There is no recovery possible.'], check=False)
            print()
            confirm_proc = subprocess.run(
                ['gum', 'confirm', '--affirmative', 'Yes, format disk', '--negative', 'No, change it',
                 f'Confirm overwriting {disk}'],
                capture_output=True
            )
            if confirm_proc.returncode == 0:
                break
            else:
                disk = disk_form()
    
    # Clear screen
    subprocess.run(['clear'], check=False)
    
    log("Saving user configuration files")
    
    # Save user full name and email address
    Path('user_full_name.txt').write_text(user_info['full_name'])
    Path('user_email_address.txt').write_text(user_info['email_address'])
    debug_log("Created user_full_name.txt and user_email_address.txt")
    
    # Generate user_credentials.json
    password_escaped = json.dumps(user_info['password'])
    password_hash_escaped = json.dumps(user_info['password_hash'])
    username_escaped = json.dumps(user_info['username'])
    
    credentials = {
        "encryption_password": user_info['password'],
        "root_enc_password": user_info['password_hash'],
        "users": [
            {
                "enc_password": user_info['password_hash'],
                "groups": [],
                "sudo": True,
                "username": user_info['username']
            }
        ]
    }
    
    with open('user_credentials.json', 'w') as f:
        json.dump(credentials, f, indent=4)
    
    # Setup partition layout
    log(f"Calculating partition layout for disk: {disk}")
    lsblk_size_proc = subprocess.run(['lsblk', '-bdno', 'SIZE', disk], capture_output=True, text=True, check=True)
    disk_size = int(lsblk_size_proc.stdout.strip())
    log(f"Disk size: {disk_size} bytes")
    
    mib = 1024 * 1024
    gib = mib * 1024
    disk_size_in_mib = (disk_size // mib) * mib  # Rounds to nearest MiB
    
    gpt_backup_reserve = mib
    boot_partition_start = mib
    boot_partition_size = 2 * gib
    
    main_partition_start = boot_partition_size + boot_partition_start
    main_partition_size = disk_size_in_mib - main_partition_start - gpt_backup_reserve
    
    debug_log(f"Boot partition: {boot_partition_size} bytes, Main partition: {main_partition_size} bytes")
    
    # Detect T2 Mac and set appropriate kernel
    kernel_choice = "linux"
    try:
        lspci_proc = subprocess.run(['lspci', '-nn'], capture_output=True, text=True, check=False)
        if '106b:180' in lspci_proc.stdout or '106b:1801' in lspci_proc.stdout or '106b:1802' in lspci_proc.stdout:
            kernel_choice = "linux-t2"
            debug_log("Detected T2 Mac, using linux-t2 kernel")
    except Exception:
        pass
    
    if kernel_choice == "linux":
        debug_log("Using standard linux kernel")
    
    # Generate user_configuration.json
    configuration = {
        "app_config": None,
        "archinstall-language": "English",
        "auth_config": {},
        "audio_config": {"audio": "pipewire"},
        "bootloader": "Limine",
        "custom_commands": [],
        "disk_config": {
            "btrfs_options": {
                "snapshot_config": {
                    "type": "Snapper"
                }
            },
            "config_type": "default_layout",
            "device_modifications": [
                {
                    "device": disk,
                    "partitions": [
                        {
                            "btrfs": [],
                            "dev_path": None,
                            "flags": ["boot", "esp"],
                            "fs_type": "fat32",
                            "mount_options": [],
                            "mountpoint": "/boot",
                            "obj_id": "ea21d3f2-82bb-49cc-ab5d-6f81ae94e18d",
                            "size": {
                                "sector_size": {"unit": "B", "value": 512},
                                "unit": "B",
                                "value": boot_partition_size
                            },
                            "start": {
                                "sector_size": {"unit": "B", "value": 512},
                                "unit": "B",
                                "value": boot_partition_start
                            },
                            "status": "create",
                            "type": "primary"
                        },
                        {
                            "btrfs": [
                                {"mountpoint": "/", "name": "@"},
                                {"mountpoint": "/home", "name": "@home"},
                                {"mountpoint": "/var/log", "name": "@log"},
                                {"mountpoint": "/var/cache/pacman/pkg", "name": "@pkg"}
                            ],
                            "dev_path": None,
                            "flags": [],
                            "fs_type": "btrfs",
                            "mount_options": ["compress=zstd"],
                            "mountpoint": None,
                            "obj_id": "8c2c2b92-1070-455d-b76a-56263bab24aa",
                            "size": {
                                "sector_size": {"unit": "B", "value": 512},
                                "unit": "B",
                                "value": main_partition_size
                            },
                            "start": {
                                "sector_size": {"unit": "B", "value": 512},
                                "unit": "B",
                                "value": main_partition_start
                            },
                            "status": "create",
                            "type": "primary"
                        }
                    ],
                    "wipe": True
                }
            ],
            "disk_encryption": {
                "encryption_type": "luks",
                "lvm_volumes": [],
                "iter_time": 2000,
                "partitions": ["8c2c2b92-1070-455d-b76a-56263bab24aa"],
                "encryption_password": user_info['password']
            }
        },
        "hostname": user_info['hostname'],
        "kernels": [kernel_choice],
        "network_config": {"type": "iso"},
        "ntp": True,
        "parallel_downloads": 8,
        "script": None,
        "services": [],
        "swap": True,
        "timezone": user_info['timezone'],
        "locale_config": {
            "kb_layout": keyboard_code,
            "sys_enc": "UTF-8",
            "sys_lang": "en_US.UTF-8"
        },
        "mirror_config": {
            "custom_repositories": [],
            "custom_servers": [
                {"url": "file:///var/cache/omarchy/mirror/offline/"}
            ],
            "mirror_regions": {},
            "optional_repositories": []
        },
        "packages": [
            "base-devel",
            "git"
        ],
        "profile_config": {
            "gfx_driver": None,
            "greeter": None,
            "profile": {}
        },
        "version": "3.0.9"
    }
    
    with open('user_configuration.json', 'w') as f:
        json.dump(configuration, f, indent=4)
    
    log("Created user_configuration.json and user_credentials.json")
    log("Configuration complete!")
    
    # Dry run mode (for testing)
    if len(sys.argv) > 1 and sys.argv[1] == "dry":
        print("\nUser Configuration:")
        print(json.dumps(configuration, indent=2))
        print("\n\nUser Credentials:")
        print(json.dumps(credentials, indent=2))
        print("\n\nUser Full Name:")
        print(user_info['full_name'])
        print("\nUser Email Address:")
        print(user_info['email_address'])
        
        Path('user_configuration.json').unlink(missing_ok=True)
        Path('user_credentials.json').unlink(missing_ok=True)
        Path('user_full_name.txt').unlink(missing_ok=True)
        Path('user_email_address.txt').unlink(missing_ok=True)


if __name__ == '__main__':
    main()
