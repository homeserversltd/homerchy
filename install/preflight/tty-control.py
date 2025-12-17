#!/usr/bin/env python3
"""
HOMESERVER Homerchy Preflight TTY Control
Copyright (C) 2024 HOMESERVER LLC

Takes exclusive control of TTY1 to display installation progress.
Replaces Plymouth for visual control during installation.
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path


class TTYController:
    """Manages TTY1 display during installation."""
    
    def __init__(self, tty_device='/dev/tty1'):
        self.tty_device = tty_device
        self.tty_fd = None
        self.running = False
        self.current_message = ""
        self.keep_alive_thread = None
        self.lock_file = Path('/tmp/omarchy-tty-control.lock')
        
    def acquire(self) -> bool:
        """Take control of TTY1."""
        try:
            # Stop and mask getty services (service already does this, but ensure it's done)
            for tty_num in range(1, 7):
                subprocess.run(
                    ['systemctl', 'stop', f'getty@tty{tty_num}.service'],
                    check=False, capture_output=True
                )
                subprocess.run(
                    ['systemctl', 'mask', f'getty@tty{tty_num}.service'],
                    check=False, capture_output=True
                )
            
            # Switch to TTY1
            subprocess.run(['chvt', '1'], check=False, timeout=5)
            time.sleep(0.5)  # Give it a moment to switch
            
            # Open TTY1 for writing
            try:
                self.tty_fd = open(self.tty_device, 'w')
            except PermissionError:
                # Try with root privileges if we don't have direct access
                result = subprocess.run(
                    ['bash', '-c', f'exec 3>{self.tty_device}'],
                    check=False
                )
                if result.returncode != 0:
                    print("WARNING: Could not acquire TTY1 control", file=sys.stderr)
                    return False
            
            # Create lock file
            self.lock_file.write_text(str(os.getpid()))
            
            # Clear screen and show initial message
            self.clear()
            self.show_message("HOMERCHY INSTALLATION IN PROGRESS", centered=True)
            
            # Start keep-alive thread to maintain control
            self.running = True
            self.keep_alive_thread = threading.Thread(target=self._keep_alive, daemon=True)
            self.keep_alive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"WARNING: Failed to acquire TTY control: {e}", file=sys.stderr)
            return False
    
    def clear(self):
        """Clear the screen."""
        try:
            if self.tty_fd:
                self.tty_fd.write('\033[2J\033[H')  # Clear screen and move cursor home
                self.tty_fd.flush()
            else:
                # Fallback: use subprocess
                subprocess.run(['bash', '-c', f'echo -ne "\\033[2J\\033[H" > {self.tty_device}'],
                             check=False)
        except Exception:
            pass
    
    def show_message(self, message: str, centered: bool = False):
        """Display a message on TTY1."""
        try:
            self.current_message = message
            
            if centered:
                # Simple centering (assume 80 column width, adjust if needed)
                width = 80
                padding = (width - len(message)) // 2
                message = ' ' * padding + message
            
            if self.tty_fd:
                self.tty_fd.write(f'\033[H{message}\033[K\n')  # Move to top, write, clear line
                self.tty_fd.flush()
            else:
                # Fallback: use subprocess
                subprocess.run(['bash', '-c', f'echo -ne "\\033[H{message}\\033[K\\n" > {self.tty_device}'],
                             check=False)
        except Exception:
            pass
    
    def update_progress(self, phase: str, message: str = ""):
        """Update installation progress display."""
        try:
            if self.tty_fd:
                # Move cursor to line 3 (below header)
                self.tty_fd.write(f'\033[3;1H\033[K')  # Line 3, column 1, clear line
                self.tty_fd.write(f'Phase: {phase}')
                if message:
                    self.tty_fd.write(f' - {message}')
                self.tty_fd.write('\033[K')  # Clear to end of line
                self.tty_fd.flush()
            else:
                # Fallback
                display = f'Phase: {phase}'
                if message:
                    display += f' - {message}'
                subprocess.run(['bash', '-c', f'echo -ne "\\033[3;1H\\033[K{display}\\033[K" > {self.tty_device}'],
                             check=False)
        except Exception:
            pass
    
    def _keep_alive(self):
        """Keep TTY control alive by periodically refreshing display."""
        while self.running:
            try:
                time.sleep(5)  # Refresh every 5 seconds
                if self.current_message and self.tty_fd:
                    # Just re-write current message to maintain control
                    self.show_message(self.current_message, centered=True)
            except Exception:
                break
    
    def release(self):
        """Release control of TTY1 and restore getty."""
        try:
            self.running = False
            
            if self.keep_alive_thread:
                self.keep_alive_thread.join(timeout=2)
            
            if self.tty_fd:
                self.tty_fd.close()
                self.tty_fd = None
            
            # Remove lock file
            if self.lock_file.exists():
                self.lock_file.unlink()
            
            # Clear screen one last time
            try:
                subprocess.run(['bash', '-c', f'echo -ne "\\033[2J\\033[H" > {self.tty_device}'],
                             check=False)
            except Exception:
                pass
            
            # Unmask and start getty services (let service handle this, but ensure it happens)
            # Note: Service ExecStartPost will handle this, but we ensure it here too
            for tty_num in range(1, 7):
                subprocess.run(
                    ['systemctl', 'unmask', f'getty@tty{tty_num}.service'],
                    check=False, capture_output=True
                )
            subprocess.run(
                ['systemctl', 'start', 'getty@tty1.service'],
                check=False, capture_output=True
            )
            
        except Exception as e:
            print(f"WARNING: Error releasing TTY control: {e}", file=sys.stderr)


# Global controller instance
_controller = None


def get_controller() -> TTYController:
    """Get or create the global TTY controller instance."""
    global _controller
    if _controller is None:
        _controller = TTYController()
    return _controller


def main(config: dict) -> dict:
    """
    Main function - takes control of TTY1 for installation display.
    
    Args:
        config: Configuration dictionary (unused, but required by orchestrator)
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        controller = get_controller()
        
        # Store controller reference in environment for other modules to use
        # (Python modules can import and use get_controller())
        os.environ['OMARCHY_TTY_CONTROLLER'] = 'active'
        
        if controller.acquire():
            return {"success": True, "message": "TTY control acquired"}
        else:
            # Non-fatal - installation can continue without TTY control
            return {"success": True, "message": "TTY control not available (non-fatal)"}
    
    except Exception as e:
        # Non-fatal error - don't fail installation if TTY control fails
        print(f"WARNING: TTY control setup failed: {e}", file=sys.stderr)
        return {"success": True, "message": f"TTY control setup failed: {e} (non-fatal)"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)


