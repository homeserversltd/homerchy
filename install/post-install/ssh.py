#!/usr/bin/env python3
"""
HOMESERVER Homerchy SSH Configuration
Copyright (C) 2024 HOMESERVER LLC

Enable and start SSH service for VM access (only in VM environments).
Detects VM environment and configures SSH service appropriately.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_log_file() -> Path:
    """Determine log file path for SSH installation."""
    # Use phase log file if set, otherwise create script-specific log file
    phase_log = os.environ.get('OMARCHY_PHASE_LOG_FILE')
    if phase_log:
        return Path(phase_log)
    
    # Fallback: create script-specific log file
    main_log = os.environ.get('OMARCHY_INSTALL_LOG_FILE', '/var/log/omarchy-install.log')
    log_dir = Path(main_log).parent
    ssh_log_file = log_dir / 'omarchy-ssh-install.log'
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    ssh_log_file.touch(mode=0o666, exist_ok=True)
    
    return ssh_log_file


def timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log(message: str, log_file: Path):
    """Log message to file and stdout."""
    msg = f"[{timestamp()}] post-install/ssh.py: {message}"
    # Write to log file
    try:
        with open(log_file, 'a') as f:
            f.write(f"{msg}\n")
    except Exception:
        pass  # Best effort logging
    # Also output to stdout
    print(msg, flush=True)


def log_error(message: str, log_file: Path):
    """Log error message to file, stdout, and stderr."""
    msg = f"[{timestamp()}] post-install/ssh.py: ERROR: {message}"
    # Write to log file
    try:
        with open(log_file, 'a') as f:
            f.write(f"{msg}\n")
    except Exception:
        pass
    # Output to both stdout and stderr
    print(msg, flush=True)
    print(msg, file=sys.stderr, flush=True)


def detect_vm_environment() -> bool:
    """Detect if running in VM environment."""
    # Check for VM test environment signal
    vm_test = os.environ.get('OMARCHY_VM_TEST')
    index_json = Path('/root/vmtools/index.json')
    
    if vm_test == '1' or index_json.exists():
        return True
    
    # Fallback: check systemd-detect-virt
    try:
        result = subprocess.run(
            ['systemd-detect-virt'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            virt_type = result.stdout.strip()
            return virt_type != 'none'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False


def find_ssh_service() -> Optional[str]:
    """Find which SSH service exists (ssh.service or sshd.service)."""
    try:
        result = subprocess.run(
            ['systemctl', 'list-unit-files', '--no-pager'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check for ssh.service first (Arch Linux standard)
        if 'ssh.service' in result.stdout:
            return 'ssh.service'
        
        # Check for sshd.service (non-standard)
        if 'sshd.service' in result.stdout:
            return 'sshd.service'
        
        # Log available SSH-related services for debugging
        for line in result.stdout.split('\n'):
            if 'ssh' in line.lower():
                log_error(f"Available SSH service: {line.strip()}", get_log_file())
        
        return None
    except Exception as e:
        log_error(f"Failed to list systemd unit files: {e}", get_log_file())
        return None


def enable_ssh_service(service_name: str, log_file: Path) -> bool:
    """Enable SSH service to start on boot."""
    log(f"Enabling {service_name} to start on boot...", log_file)
    
    try:
        result = subprocess.run(
            ['systemctl', 'enable', service_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            log(f"SSH service enabled successfully", log_file)
            return True
        else:
            log_error(f"Failed to enable SSH service (exit code: {result.returncode})", log_file)
            log_error(f"Enable output: {result.stdout}{result.stderr}", log_file)
            # Continue anyway - might be in chroot where enable doesn't work
            return False
    except Exception as e:
        log_error(f"Exception enabling SSH service: {e}", log_file)
        return False


def start_ssh_service(service_name: str, log_file: Path) -> bool:
    """Start SSH service immediately."""
    log(f"Starting {service_name}...", log_file)
    
    try:
        result = subprocess.run(
            ['systemctl', 'start', service_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            log(f"SSH service started successfully", log_file)
            return True
        else:
            log_error(f"Failed to start SSH service (exit code: {result.returncode})", log_file)
            log_error(f"Start output: {result.stdout}{result.stderr}", log_file)
            
            # Check if we're in chroot (start command ignored)
            if 'Running in chroot' in result.stderr or 'Running in chroot' in result.stdout:
                log("Running in chroot - start command ignored (expected)", log_file)
            
            return False
    except Exception as e:
        log_error(f"Exception starting SSH service: {e}", log_file)
        return False


def check_ssh_status(service_name: str, log_file: Path):
    """Check and log SSH service status."""
    log("Checking SSH service status...", log_file)
    
    try:
        result = subprocess.run(
            ['systemctl', 'status', service_name, '--no-pager'],
            capture_output=True,
            text=True,
            check=False
        )
        
        for line in result.stdout.split('\n'):
            if line.strip():
                log(f"STATUS: {line}", log_file)
    except Exception as e:
        log_error(f"Failed to check SSH status: {e}", log_file)


def main():
    """Main SSH configuration flow."""
    log_file = get_log_file()
    
    log("=== SSH.PY STARTED ===", log_file)
    log(f"Detailed log file: {log_file}", log_file)
    log(f"Main install log: {os.environ.get('OMARCHY_INSTALL_LOG_FILE', '/var/log/omarchy-install.log')}", log_file)
    log(f"OMARCHY_VM_TEST: {os.environ.get('OMARCHY_VM_TEST', 'NOT SET')}", log_file)
    log(f"Current directory: {os.getcwd()}", log_file)
    log(f"User: {os.getenv('USER', 'unknown')}", log_file)
    log("SSH log file created successfully", log_file)
    
    # Check if we're in a VM
    log("Checking if running in VM...", log_file)
    log(f"OMARCHY_VM_TEST: {os.environ.get('OMARCHY_VM_TEST', 'not set')}", log_file)
    
    index_json = Path('/root/vmtools/index.json')
    log(f"/root/vmtools/index.json exists: {'YES' if index_json.exists() else 'NO'}", log_file)
    
    if not detect_vm_environment():
        log("Not in VM, skipping SSH enablement", log_file)
        return {"success": True, "message": "Not in VM environment, SSH setup skipped"}
    
    log("VM environment detected, proceeding with SSH setup", log_file)
    
    # Find SSH service
    log("Checking for SSH service...", log_file)
    ssh_service = find_ssh_service()
    
    if not ssh_service:
        log_error("No SSH service found (neither ssh.service nor sshd.service)", log_file)
        return {"success": False, "message": "No SSH service found"}
    
    log(f"Found {ssh_service}", log_file)
    log(f"Using SSH service: {ssh_service}", log_file)
    
    # Enable SSH service
    enable_ssh_service(ssh_service, log_file)
    
    # Start SSH service
    start_ssh_service(ssh_service, log_file)
    
    # Check status
    check_ssh_status(ssh_service, log_file)
    
    log("=== SSH.PY COMPLETED ===", log_file)
    log(f"SSH service: {ssh_service}", log_file)
    log("SSH available at: ssh -p 2222 owner@localhost (password: from index.json profile)", log_file)
    
    return {"success": True, "message": f"SSH service {ssh_service} configured successfully"}


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result.get('success') else 1)




