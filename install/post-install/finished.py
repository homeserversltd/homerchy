#!/usr/bin/env python3
"""
HOMESERVER Homerchy Post-Install Finished
Copyright (C) 2024 HOMESERVER LLC

Displays completion screen and handles reboot prompt.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def stop_install_log():
    """Stop log monitoring and write final summary to log file."""
    log_file = os.environ.get('OMARCHY_INSTALL_LOG_FILE', '/var/log/omarchy-install.log')
    
    if not log_file:
        return
    
    try:
        # Stop log output monitoring (kill background process if running)
        # This is handled by the shell environment, but we ensure it's stopped
        
        # Write completion summary
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a') as f:
            f.write(f"=== Omarchy Installation Completed: {end_time} ===\n")
            f.write("\n")
            f.write("=== Installation Time Summary ===\n")
            
            # Try to get archinstall times
            archinstall_log = Path('/var/log/archinstall/install.log')
            if archinstall_log.exists():
                try:
                    with open(archinstall_log, 'r') as af:
                        content = af.read()
                        # Find first timestamp
                        start_match = re.search(r'^\[([^\]]+)\]', content, re.MULTILINE)
                        end_match = re.search(r'Installation completed without any errors', content)
                        
                        if start_match and end_match:
                            arch_start_str = start_match.group(1)
                            # Find timestamp near end_match
                            end_context = content[max(0, end_match.start()-200):end_match.end()]
                            end_timestamp_match = re.search(r'\[([^\]]+)\]', end_context)
                            
                            if end_timestamp_match:
                                arch_end_str = end_timestamp_match.group(1)
                                
                                try:
                                    arch_start = datetime.strptime(arch_start_str, '%Y-%m-%d %H:%M:%S')
                                    arch_end = datetime.strptime(arch_end_str, '%Y-%m-%d %H:%M:%S')
                                    arch_duration = (arch_end - arch_start).total_seconds()
                                    arch_mins = int(arch_duration // 60)
                                    arch_secs = int(arch_duration % 60)
                                    f.write(f"Archinstall: {arch_mins}m {arch_secs}s\n")
                                except ValueError:
                                    pass
                except Exception:
                    pass
            
            # Calculate Omarchy duration
            start_time_str = os.environ.get('OMARCHY_START_TIME')
            if start_time_str:
                try:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    end_time_obj = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                    omarchy_duration = (end_time_obj - start_time).total_seconds()
                    omarchy_mins = int(omarchy_duration // 60)
                    omarchy_secs = int(omarchy_duration % 60)
                    f.write(f"Omarchy:     {omarchy_mins}m {omarchy_secs}s\n")
                    
                    # Try to calculate total if we have archinstall duration
                    # (This would require storing archinstall duration, simplified here)
                except ValueError:
                    pass
            
            f.write("=================================\n")
            f.write("Rebooting system...\n")
    
    except Exception as e:
        # Don't fail installation if log writing fails
        print(f"Warning: Failed to write log summary: {e}", file=sys.stderr)


def get_terminal_width():
    """Get terminal width, fallback to 80."""
    try:
        result = subprocess.run(
            ['stty', 'size'],
            capture_output=True,
            text=True,
            stdin=sys.stdin
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                return int(parts[1])
    except Exception:
        pass
    return 80


def get_logo_width():
    """Get logo width from logo.txt file."""
    omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy'))
    logo_path = omarchy_path / 'logo.txt'
    
    if not logo_path.exists():
        return 0
    
    try:
        max_width = 0
        with open(logo_path, 'r') as f:
            for line in f:
                max_width = max(max_width, len(line.rstrip()))
        return max_width
    except Exception:
        return 0


def echo_in_style(text):
    """Print text with tte styling."""
    try:
        subprocess.run(
            ['tte', '--canvas-width', '0', '--anchor-text', 'c', '--frame-rate', '640', 'print'],
            input=text,
            text=True,
            check=False
        )
    except Exception:
        # Fallback to regular echo if tte fails
        print(text)


def main(config: dict) -> dict:
    """
    Main function - displays completion screen and handles reboot.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        # Stop install log
        stop_install_log()
        
        # Clear screen
        subprocess.run(['clear'], check=False)
        print()
        
        # Display logo
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy'))
        logo_path = omarchy_path / 'logo.txt'
        
        if logo_path.exists():
            try:
                subprocess.run(
                    ['tte', '-i', str(logo_path), '--canvas-width', '0', '--anchor-text', 'c', '--frame-rate', '920', 'laseretch'],
                    check=False
                )
            except Exception:
                # Fallback: just print logo text
                with open(logo_path, 'r') as f:
                    print(f.read())
        print()
        
        # Display installation time if available
        log_file = os.environ.get('OMARCHY_INSTALL_LOG_FILE', '/var/log/omarchy-install.log')
        total_time = None
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    # Read last 20 lines
                    lines = f.readlines()
                    for line in reversed(lines[-20:]):
                        if 'Total:' in line:
                            match = re.search(r'Total:\s*(.+)', line)
                            if match:
                                total_time = match.group(1).strip()
                                break
            except Exception:
                pass
        
        if total_time:
            echo_in_style(f"Installed in {total_time}")
        else:
            echo_in_style("Finished installing")
        
        # Remove sudoers file if it exists
        sudoers_file = Path('/etc/sudoers.d/99-omarchy-installer')
        if sudoers_file.exists():
            try:
                subprocess.run(['sudo', 'rm', '-f', str(sudoers_file)], 
                             capture_output=True, check=False)
            except Exception:
                pass
        
        # Prompt for reboot
        term_width = get_terminal_width()
        logo_width = get_logo_width()
        padding_left = max(0, (term_width - logo_width) // 2)
        
        # Calculate padding for gum confirm (original: PADDING_LEFT + 32)
        confirm_padding = padding_left + 32
        
        try:
            result = subprocess.run(
                ['gum', 'confirm',
                 '--padding', f'0 0 0 {confirm_padding}',
                 '--show-help=false',
                 '--default',
                 '--affirmative', 'Reboot Now',
                 '--negative', '', ''],
                check=False
            )
            
            if result.returncode == 0:
                # User chose to reboot
                subprocess.run(['clear'], check=False)
                
                if os.environ.get('OMARCHY_CHROOT_INSTALL'):
                    # In chroot mode, just create completion marker
                    completion_marker = Path('/var/tmp/omarchy-install-completed')
                    completion_marker.touch()
                    return {"success": True, "message": "Installation completed (chroot mode)"}
                else:
                    # Reboot system
                    subprocess.run(['sudo', 'reboot'], check=False, 
                                 capture_output=True, stderr=subprocess.DEVNULL)
                    return {"success": True, "message": "Rebooting system"}
            else:
                # User chose not to reboot
                return {"success": True, "message": "Installation completed (user chose not to reboot)"}
        
        except FileNotFoundError:
            # gum not available, skip prompt
            return {"success": True, "message": "Installation completed (gum not available, skipping reboot prompt)"}
        except Exception as e:
            return {"success": False, "message": f"Failed to prompt for reboot: {e}"}
    
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)








