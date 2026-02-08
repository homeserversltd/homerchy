#!/usr/bin/env python3
"""
HOMESERVER Homerchy Installation Entry Point
Copyright (C) 2024 HOMESERVER LLC

Main Python entry point for Homerchy installation system.
Blocks TTY, runs root orchestrator (install/index.py), displays state via reporting.
"""

import os
import sys
import subprocess
import signal
import atexit
import threading
import time
from pathlib import Path

# Register this module in sys.modules so index.py can find it
sys.modules['install'] = sys.modules[__name__]

# Global status for persistent message
_current_status = "Starting installation..."
_run_counter = 0  # Set by get_or_increment_run_counter()
_orchestrator_instance = None  # Global reference for state access
_install_state = None  # Shared state for display; set after we import from install tree
_reporting_redraw = None  # reporting.redraw; set in main after sys.path includes install


def get_or_increment_run_counter() -> int:
    """Get or increment the run counter from /tmp/work/homerchy.pid.
    Resets on reboot (tmp cleared). Returns current counter value."""
    pid_file = Path('/tmp/work/homerchy.pid')
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        if pid_file.exists():
            counter = int(pid_file.read_text().strip()) + 1
        else:
            counter = 1
        pid_file.write_text(str(counter))
        return counter
    except Exception as e:
        print(f"[INSTALL] WARNING: Failed to read/increment run counter: {e}", file=sys.stderr)
        return 1


def _get_recent_logs(log_file: str, lines: int = 8) -> list:
    """Return last N lines from log file."""
    try:
        if not Path(log_file).exists():
            return ["[Log file not created yet]"]
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        recent = [line.rstrip() for line in all_lines[-lines:] if line.strip()]
        return recent if recent else ["[Log file is empty]"]
    except Exception as e:
        return [f"[Error reading log: {e}]"]


def _get_orchestrator_info() -> tuple:
    """Current step, error count, and executed children from orchestrator if available."""
    global _orchestrator_instance
    current_step = "unknown"
    error_count = 0
    child_info = []
    try:
        if _orchestrator_instance and hasattr(_orchestrator_instance, 'state'):
            state = _orchestrator_instance.state
            current_step = state.current_step or "none"
            error_count = len(state.errors) if hasattr(state, 'errors') else 0
            if hasattr(state, 'children') and state.children:
                child_info = list(state.children.keys())
    except Exception:
        pass
    return current_step, error_count, child_info


def display_persistent_message():
    """Draw full-screen status on TTY1 and console. Uses install-tree reporting when state is set."""
    global _current_status, _run_counter, _install_state, _reporting_redraw

    try:
        if _install_state is not None and _reporting_redraw is not None:
            _reporting_redraw(_install_state, _run_counter, _current_status, None)
            return
    except Exception:
        pass

    # Fallback when orchestrator not yet run (no state)
    log_file = os.environ.get('HOMERCHY_INSTALL_LOG_FILE', '/var/log/homerchy-install.log')
    recent_logs = _get_recent_logs(log_file, lines=8)
    current_step, error_count, child_info = _get_orchestrator_info()
    step_display = current_step if current_step not in ("unknown", "none") else "Initializing..."

    colors = [
        "\033[1m\033[31m", "\033[1m\033[32m", "\033[1m\033[33m",
        "\033[1m\033[34m", "\033[1m\033[35m", "\033[1m\033[36m",
    ]
    header_color = colors[_run_counter % len(colors)]

    try:
        msg = "\033[2J\033[H"
        msg += header_color
        msg += "=" * 70 + "\n"
        msg += "HOMERCHY INSTALLATION IN PROGRESS\n"
        msg += "=" * 70 + "\n\033[0m\n"
        msg += "\033[33m"
        msg += f"Status: {_current_status}\n"
        msg += "\033[0m\033[36m"
        msg += f"Current Step: {step_display}\n"
        msg += f"Run #: {_run_counter} | Errors: {error_count}\n"
        msg += "\033[0m"
        if child_info:
            msg += "\033[35m"
            msg += f"Executed: {', '.join(child_info[-5:])}\n"
            msg += "\033[0m"
        msg += "\n\033[32mRecent Logs:\033[0m\n"
        msg += "-" * 70 + "\n"
        for line in recent_logs[-6:]:
            if len(line) > 68:
                line = line[:65] + "..."
            msg += line + "\n"
        msg += "-" * 70 + "\n"
        msg += "\033[2mDetails: journalctl -u homerchy-first-boot-install.service\033[0m\n"

        for dev in ('/dev/tty1', '/dev/console'):
            try:
                with open(dev, 'w') as f:
                    f.write(msg)
                    f.flush()
            except Exception:
                pass
    except Exception as e:
        print(f"WARNING: Failed to display message: {e}", file=sys.stderr)


def update_status(status: str):
    """Set status and redraw the persistent message once."""
    global _current_status
    _current_status = status
    print(f"[STATUS UPDATE] {status}", file=sys.stderr)
    display_persistent_message()


def persistent_message_loop():
    """Background thread: refresh the status screen every 2 seconds."""
    while True:
        try:
            display_persistent_message()
            time.sleep(2)
        except Exception:
            break


def block_tty_and_display_message():
    """Stop/mask/disable gettys, switch to tty1, show persistent status screen."""
    try:
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'stop', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
            subprocess.run(['systemctl', 'mask', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
            subprocess.run(['systemctl', 'disable', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
        subprocess.run(['chvt', '1'], check=False, capture_output=True)
        time.sleep(0.2)
        display_persistent_message()
        print("[INSTALL] TTY blocked, status displayed", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to block TTY: {e}", file=sys.stderr)


def unblock_tty_login():
    """Unmask gettys and start getty on tty1."""
    try:
        for tty_num in range(1, 7):
            subprocess.run(['systemctl', 'unmask', f'getty@tty{tty_num}.service'],
                          check=False, capture_output=True)
        subprocess.run(['systemctl', 'start', 'getty@tty1.service'],
                      check=False, capture_output=True)
        print("[INSTALL] TTY login unblocked", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to unblock TTY: {e}", file=sys.stderr)


def setup_environment():
    """Set up environment variables for installation."""
    if 'HOMERCHY_PATH' not in os.environ:
        homerchy_path = None
        candidate = Path.home() / '.local' / 'share' / 'homerchy'
        if (candidate / 'install').exists() or (candidate / 'deployment' / 'install').exists():
            homerchy_path = candidate
        elif (Path('/root/homerchy') / 'install').exists() or (Path('/root/homerchy') / 'deployment' / 'install').exists():
            homerchy_path = Path('/root/homerchy')
        else:
            script_dir = Path(__file__).resolve().parent  # homerchy/ (flat) or homerchy/deployment/ (repo)
            if script_dir.name == 'deployment' and (script_dir / 'install').exists():
                homerchy_path = script_dir.parent  # repo: homerchy/deployment/install.py -> homerchy/
            elif (script_dir / 'install').exists():
                homerchy_path = script_dir  # flat: homerchy/install.py
            elif script_dir.parent and (script_dir.parent / 'install').exists():
                homerchy_path = script_dir.parent
            elif script_dir.parent and (script_dir.parent / 'deployment' / 'install').exists():
                homerchy_path = script_dir.parent
        if homerchy_path is None:
            homerchy_path = Path.home() / '.local' / 'share' / 'homerchy'
        os.environ['HOMERCHY_PATH'] = str(homerchy_path)

    homerchy_path = Path(os.environ['HOMERCHY_PATH'])
    # Installed: homerchy/install/ (flat, source_injection copies deployment contents).
    # Dev: homerchy/deployment/install/ (repo structure).
    install_tree = homerchy_path / 'install' if (homerchy_path / 'install').exists() else homerchy_path / 'deployment' / 'install'
    os.environ['HOMERCHY_INSTALL'] = str(install_tree)
    if 'HOMERCHY_INSTALL_LOG_FILE' not in os.environ:
        os.environ['HOMERCHY_INSTALL_LOG_FILE'] = '/var/log/homerchy-install.log'
    homerchy_bin = homerchy_path / 'src' / 'bin'
    if homerchy_bin.exists():
        os.environ['PATH'] = f"{homerchy_bin}:{os.environ.get('PATH', '')}"


def unlock_account():
    """Unlock user account on successful installation."""
    try:
        username = os.environ.get('HOMERCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        subprocess.run(['passwd', '-u', username], check=False, capture_output=True)
    except Exception as e:
        print(f"WARNING: Failed to unlock account: {e}", file=sys.stderr)


def lockout_and_reboot():
    """Lock out login and force reboot on installation failure."""
    print("INSTALLATION FAILED - Locking out login and rebooting...", file=sys.stderr)
    try:
        marker_file = Path('/var/lib/homerchy-install-needed')
        if marker_file.exists():
            marker_file.unlink(missing_ok=True)
        subprocess.run(['systemctl', 'disable', 'sddm.service'], check=False, capture_output=True)
        subprocess.run(['systemctl', 'stop', 'sddm.service'], check=False, capture_output=True)
        username = os.environ.get('HOMERCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        subprocess.run(['passwd', '-l', username], check=False, capture_output=True)
        print("Login locked. Rebooting in 5 seconds...", file=sys.stderr)
        subprocess.run(['sleep', '5'], check=False)
        subprocess.run(['reboot', '-f'], check=False)
    except Exception as e:
        print(f"WARNING: Lockout failed: {e}", file=sys.stderr)
        try:
            Path('/var/lib/homerchy-install-needed').unlink(missing_ok=True)
            subprocess.run(['reboot', '-f'], check=False)
        except Exception:
            pass


def cleanup_on_exit():
    """Restore TTY and clear marker on any exit."""
    try:
        unblock_tty_login()
    except Exception as e:
        print(f"[INSTALL] WARNING: Failed to unblock TTY in cleanup: {e}", file=sys.stderr)
    try:
        Path('/var/lib/homerchy-install-needed').unlink(missing_ok=True)
    except Exception as e:
        print(f"[INSTALL] WARNING: Failed to clear marker: {e}", file=sys.stderr)


def _signal_handler(signum, frame):
    cleanup_on_exit()
    sys.exit(1)


def main():
    """Block TTY, run root orchestrator, display state; on success unblock and exit; on failure lockout and reboot."""
    global _run_counter, _orchestrator_instance, _install_state, _reporting_redraw

    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    _run_counter = get_or_increment_run_counter()
    print(f"[INSTALL] Run # {_run_counter}", file=sys.stderr)

    setup_environment()

    block_tty_and_display_message()
    threading.Thread(target=persistent_message_loop, daemon=True).start()

    try:
        username = os.environ.get('HOMERCHY_INSTALL_USER') or os.environ.get('USER', 'owner')
        subprocess.run(['passwd', '-u', username], check=False, capture_output=True)
    except Exception:
        pass

    install_path = Path(os.environ.get('HOMERCHY_INSTALL', Path(__file__).resolve().parent / 'install'))
    if not install_path.exists():
        print("ERROR: Installation directory not found!", file=sys.stderr)
        print(f"ERROR: HOMERCHY_INSTALL={install_path}", file=sys.stderr)
        lockout_and_reboot()
        sys.exit(1)

    sys.path.insert(0, str(install_path))

    try:
        from state import State, Status  # noqa: E402
        from index import Orchestrator  # noqa: E402
        import reporting  # noqa: E402

        _reporting_redraw = reporting.redraw
        _install_state = State()
        _orchestrator_instance = Orchestrator(install_path=install_path, phase="root", state=_install_state)

        update_status("Initializing orchestrator...")
        update_status("Running installation phases...")

        state = _orchestrator_instance.run()

        if state.status == Status.COMPLETED:
            update_status("Installation completed successfully!")
            unlock_account()
            unblock_tty_login()
            Path('/var/lib/homerchy-install-needed').unlink(missing_ok=True)
            sys.exit(0)
        else:
            update_status(f"Installation failed: {state.status}")
            lockout_and_reboot()
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: Failed to run orchestrator: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        lockout_and_reboot()
        sys.exit(1)


if __name__ == "__main__":
    main()
