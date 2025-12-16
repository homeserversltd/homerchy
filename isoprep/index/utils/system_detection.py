#!/usr/bin/env python3
"""
HOMESERVER Homerchy ISO Builder - System Detection Utility
Copyright (C) 2024 HOMESERVER LLC

System environment detection and dependency checking.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


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

