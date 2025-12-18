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
import time
from datetime import datetime
from pathlib import Path

# Import log viewer TUI
from .log_viewer import launch_log_viewer


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
            # NOTE: Future enhancement - we want to restart at the end of homerchy installation
            # For now, we dump logs and drop to TTY instead of rebooting
            f.write("Installation completed - dropping to TTY (no reboot yet)\n")
    
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


def dump_logs_to_root():
    """Dump useful logs to /root for debugging - one grep pattern per file."""
    root_logs = Path('/root')
    root_logs.mkdir(parents=True, exist_ok=True)
    
    print("Dumping logs to /root for debugging...", file=sys.stderr)
    
    # Get service journal output once
    journal_output = None
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'omarchy-first-boot-install.service', '--no-pager'],
            capture_output=True, text=True, check=False
        )
        journal_output = result.stdout
    except Exception:
        pass
    
    # Get installation log content
    install_log = os.environ.get('OMARCHY_INSTALL_LOG_FILE', '/var/log/omarchy-install.log')
    install_log_content = None
    if os.path.exists(install_log):
        try:
            with open(install_log, 'r') as f:
                install_log_content = f.read()
            subprocess.run(['cp', install_log, '/root/a.txt'], check=False)
            print("  Created: /root/a.txt (full installation log)", file=sys.stderr)
        except Exception:
            pass
    
    # Create focused log files with grep patterns
    log_patterns = [
        ('b.txt', 'ERROR|FAILED|Failed|Error|error|FAIL|fail'),
        ('c.txt', 'Permission denied|permission denied|EACCES|EAGAIN'),
        ('d.txt', 'timeout|Timeout|TIMEOUT|timed out'),
        ('e.txt', 'Traceback|traceback|Exception|exception'),
        ('f.txt', 'systemd|systemctl|service'),
        ('g.txt', 'getty|TTY|tty'),
        ('h.txt', 'plymouth|Plymouth|PLYMOUTH'),
        ('i.txt', 'lockout|Lock|lock|passwd'),
        ('j.txt', 'reboot|Reboot|REBOOT'),
        ('k.txt', 'marker|Marker|MARKER|omarchy-install-needed'),
        ('l.txt', 'orchestrator|Orchestrator|ORCHESTRATOR'),
        ('m.txt', 'module|Module|MODULE'),
    ]
    
    # Combine all log sources for grepping
    all_logs = ""
    if journal_output:
        all_logs += journal_output + "\n"
    if install_log_content:
        all_logs += install_log_content + "\n"
    
    # Create grep'd log files
    for filename, pattern in log_patterns:
        try:
            with open(f'/root/{filename}', 'w') as f:
                if all_logs:
                    # Use grep to filter
                    grep_proc = subprocess.Popen(
                        ['grep', '-i', '-E', pattern],
                        stdin=subprocess.PIPE,
                        stdout=f,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )
                    grep_proc.communicate(input=all_logs)
            print(f"  Created: /root/{filename} (grep: {pattern})", file=sys.stderr)
        except Exception:
            pass
    
    # Also dump full service journal
    if journal_output:
        try:
            with open('/root/z.txt', 'w') as f:
                f.write(journal_output)
            print("  Created: /root/z.txt (full service journal)", file=sys.stderr)
        except Exception:
            pass
    
    print("Logs dumped to /root/", file=sys.stderr)
    print("Files:", file=sys.stderr)
    try:
        subprocess.run(['ls', '-lh', '/root/[a-z].txt'], check=False, stderr=sys.stderr)
    except Exception:
        pass


def main(config: dict) -> dict:
    """
    Main function - displays completion screen and dumps logs to /root.
    
    NOTE: Future enhancement - we want to restart at the end of homerchy installation.
    For now, we dump logs and drop to TTY for debugging.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        # Stop install log
        stop_install_log()
        
        # Dump useful logs to /root for debugging
        dump_logs_to_root()
        
        # Remove sudoers file if it exists
        sudoers_file = Path('/etc/sudoers.d/99-omarchy-installer')
        if sudoers_file.exists():
            try:
                subprocess.run(['rm', '-f', str(sudoers_file)], 
                             check=False, capture_output=True)
            except Exception:
                pass
        
        # Launch pleasant completion screen
        # This will wait for Enter key, then reboot
        try:
            from .finishedDisplay import main as finished_display_main
            # Run finishedDisplay - shows completion screen and handles reboot
            finished_display_main()
        except ImportError:
            # Fallback if completion_tui not available
            print("Warning: completion_tui not available, using fallback", file=sys.stderr)
            try:
                # Switch to TTY1
                subprocess.run(['chvt', '1'], check=False, timeout=5)
                time.sleep(0.5)
                
                # Simple completion message
                completion_message = "\033[2J\033[H"
                completion_message += "\033[1m\033[32m"
                completion_message += "="*70 + "\n"
                completion_message += "HOMERCHY INSTALLATION COMPLETED\n"
                completion_message += "="*70 + "\n"
                completion_message += "\033[0m\n"
                completion_message += "Logs dumped to /root/\n"
                completion_message += "Press Enter to reboot (no automatic reboot)\n"
                
                with open('/dev/tty1', 'w') as tty1:
                    tty1.write(completion_message)
                    tty1.flush()
                
                # Wait for Enter - NO AUTO-REBOOT!
                try:
                    import select
                    import termios
                    import tty
                    
                    # Set stdin to raw mode
                    old_settings = termios.tcgetattr(sys.stdin)
                    tty.setraw(sys.stdin.fileno())
                    
                    # Wait for Enter
                    while True:
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1)
                            if key in ('\r', '\n'):
                                break
                    
                    # Restore terminal
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except Exception:
                    # Fallback: just wait for any input
                    input()
                
                subprocess.run(['reboot'], check=False)
            except Exception as e:
                print(f"Warning: Fallback completion failed: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Completion TUI failed: {e}", file=sys.stderr)
            # Still try to reboot
            try:
                subprocess.run(['reboot'], check=False)
            except Exception:
                pass
        
        # Drop to TTY (don't reboot)
        # The service will complete and TTY will be available for login
        return {"success": True, "message": "Installation completed - logs dumped to /root/, TTY enabled"}
    
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)










