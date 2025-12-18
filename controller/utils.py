"""
Utility functions for controller operations.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List


def run_command(cmd: List[str], check: bool = True, capture_output: bool = False, 
                sudo: bool = False) -> subprocess.CompletedProcess:
    """
    Run a command and handle errors.
    
    Args:
        cmd: Command as list of strings
        check: Whether to raise exception on non-zero exit code
        capture_output: Whether to capture stdout/stderr
        sudo: Whether to prefix command with sudo
    
    Returns:
        CompletedProcess result
    """
    if sudo:
        cmd = ['sudo'] + cmd
    
    kwargs = {}
    if capture_output:
        kwargs['capture_output'] = True
        kwargs['text'] = True
    
    result = subprocess.run(cmd, **kwargs)
    
    if check and result.returncode != 0:
        cmd_str = ' '.join(cmd)
        print(f"ERROR: Command failed: {cmd_str}", file=sys.stderr)
        if capture_output and result.stderr:
            print(f"Error output: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    return result


def run_shell_command(cmd: str, check: bool = True, capture_output: bool = False,
                     sudo: bool = False) -> subprocess.CompletedProcess:
    """
    Run a shell command (single string) and handle errors.
    
    Args:
        cmd: Shell command as single string
        check: Whether to raise exception on non-zero exit code
        capture_output: Whether to capture stdout/stderr
        sudo: Whether to prefix command with sudo
    
    Returns:
        CompletedProcess result
    """
    if sudo:
        cmd = f'sudo {cmd}'
    
    kwargs = {}
    if capture_output:
        kwargs['capture_output'] = True
        kwargs['text'] = True
    
    result = subprocess.run(['bash', '-c', cmd], **kwargs)
    
    if check and result.returncode != 0:
        print(f"ERROR: Command failed: {cmd}", file=sys.stderr)
        if capture_output and result.stderr:
            print(f"Error output: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    return result




