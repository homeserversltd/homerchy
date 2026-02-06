"""
Logging helpers for Homerchy installation.
"""

import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path


# Global variables for log monitoring
_log_thread = None
_stop_event = None


def _monitor_log_file():
    """
    Background thread to monitor log file and display new lines to tty.
    """
    ansi_reset = '\033[0m'
    ansi_gray = '\033[90m'

    logo_width = int(os.environ.get('LOGO_WIDTH', '0'))
    max_line_width = logo_width - 4
    padding_left_spaces = os.environ.get('PADDING_LEFT_SPACES', '')

    last_position = 0
    last_inode = 0
    log_file = os.environ.get('HOMERCHY_INSTALL_LOG_FILE')

    if not log_file:
        return

    while not _stop_event.is_set():
        try:
            if Path(log_file).exists():
                # Get current file size and inode
                stat = os.stat(log_file)
                current_size = stat.st_size
                current_inode = stat.st_ino

                # Reset position if file was recreated
                if current_inode != last_inode and last_inode != 0:
                    last_position = 0
                last_inode = current_inode

                # Read new content
                if current_size > last_position:
                    with open(log_file, 'rb') as f:
                        f.seek(last_position)
                        new_content = f.read().decode('utf-8', errors='ignore')

                    if new_content:
                        lines = new_content.splitlines()
                        for line in lines:
                            if line.strip():  # Skip empty lines
                                # Truncate if needed
                                if len(line) > max_line_width:
                                    line = line[:max_line_width] + '...'

                                # Output to tty
                                output = f"{ansi_gray}{padding_left_spaces}  → {line}{ansi_reset}\n"
                                try:
                                    with open('/dev/tty', 'w') as tty:
                                        tty.write(output)
                                        tty.flush()
                                except Exception:
                                    print(output, end='', flush=True)

                    last_position = current_size

        except Exception:
            pass  # Ignore errors in monitoring thread

        time.sleep(0.2)


def start_install_log():
    """
    Start installation logging.

    Creates log directory and file, writes start message, starts background monitoring.
    """
    global _log_thread, _stop_event

    log_file = os.environ.get('HOMERCHY_INSTALL_LOG_FILE')
    if not log_file:
        return

    log_path = Path(log_file)
    log_dir = log_path.parent

    # Ensure log directory exists
    try:
        subprocess.run(['sudo', 'mkdir', '-p', str(log_dir)], check=True)
    except subprocess.CalledProcessError:
        print(f"ERROR: Failed to create log directory: {log_dir}", file=sys.stderr)
        return

    # Create log file
    try:
        subprocess.run(['sudo', 'touch', log_file], check=True)
        subprocess.run(['sudo', 'chmod', '666', log_file], check=False)
    except subprocess.CalledProcessError:
        print(f"ERROR: Failed to create log file: {log_file}", file=sys.stderr)
        return

    # Write start message
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os.environ['HOMERCHY_START_TIME'] = start_time

    try:
        with open(log_file, 'a') as f:
            f.write(f"=== Omarchy Installation Started: {start_time} ===\n")
    except Exception:
        print(f"ERROR: Failed to write to log file: {log_file}", file=sys.stderr)
        return

    # Start background monitoring
    _stop_event = threading.Event()
    _log_thread = threading.Thread(target=_monitor_log_file, daemon=True)
    _log_thread.start()


def stop_install_log():
    """
    Stop installation logging.

    Stops background monitoring, writes completion message and time summary.
    """
    global _log_thread, _stop_event

    # Stop monitoring thread
    if _stop_event:
        _stop_event.set()
    if _log_thread and _log_thread.is_alive():
        _log_thread.join(timeout=1.0)

    log_file = os.environ.get('HOMERCHY_INSTALL_LOG_FILE')
    if not log_file or not Path(log_file).exists():
        return

    # Write completion message
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os.environ['HOMERCHY_END_TIME'] = end_time

    try:
        with open(log_file, 'a') as f:
            f.write(f"=== Omarchy Installation Completed: {end_time} ===\n\n")
            f.write("=== Installation Time Summary ===\n")

            # Calculate duration
            start_time_str = os.environ.get('HOMERCHY_START_TIME')
            if start_time_str:
                try:
                    start_dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                    duration = end_dt - start_dt
                    total_seconds = int(duration.total_seconds())
                    mins = total_seconds // 60
                    secs = total_seconds % 60
                    f.write(f"Omarchy:     {mins}m {secs}s\n")
                except Exception:
                    pass

            f.write("=================================\n")
            f.write("Rebooting system...\n")

    except Exception:
        pass  # Ignore errors when writing completion