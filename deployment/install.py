#!/usr/bin/env python3
"""
HOMERCHY install.py - MINIMAL PROOF OF CONCEPT
Block TTY -> sleep 5 -> unblock TTY. No orchestrator, no reboot, no lockout.
Restore full version from install.py.backup when done testing.
"""

import subprocess
import time
from pathlib import Path


def block_tty():
    """Stop and mask gettys, switch to tty1."""
    for tty_num in range(1, 7):
        subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'],
                      check=False, capture_output=True)
        subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'],
                      check=False, capture_output=True)
        subprocess.run(['systemctl', 'disable', f'getty@tty{tty_num}.service'],
                      check=False, capture_output=True)
    subprocess.run(['chvt', '1'], check=False, capture_output=True)
    time.sleep(0.2)


def show_message(text: str):
    """Write one line to tty1 and console."""
    msg = text + "\n"
    for dev in ('/dev/tty1', '/dev/console'):
        try:
            with open(dev, 'w') as f:
                f.write(msg)
                f.flush()
        except Exception:
            pass


def unblock_tty():
    """Unmask gettys and start tty1."""
    for tty_num in range(1, 7):
        subprocess.run(['systemctl', 'unmask', f'getty@tty{tty_num}.service'],
                       check=False, capture_output=True)
    subprocess.run(['systemctl', 'start', 'getty@tty1.service'],
                  check=False, capture_output=True)


def main():
    block_tty()
    show_message("HOMERCHY PoC: TTY blocked. Sleeping 5s then unblock...")
    time.sleep(5)
    unblock_tty()
    # Remove marker so service doesn't run again on next boot
    marker = Path('/var/lib/homerchy-install-needed')
    if marker.exists():
        marker.unlink(missing_ok=True)
    show_message("PoC done. You should see login prompt.")


if __name__ == "__main__":
    main()
