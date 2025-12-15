#!/usr/bin/env python3
"""
HOMESERVER Homerchy Post-Install Prebuild
Copyright (C) 2024 HOMESERVER LLC

Deploys prebuild configuration files based on index.json manifest.
Uses Python's built-in json module (no jq dependency).
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def expand_path(path: str, user_home: str) -> str:
    """Expand ~ in paths to actual home directory."""
    return path.replace('~', user_home)


def main(config: dict) -> dict:
    """
    Main function - deploys prebuild configuration files.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    """
    try:
        omarchy_path = Path(os.environ.get('OMARCHY_PATH', Path.home() / '.local' / 'share' / 'omarchy'))
        prebuild_dir = omarchy_path / 'prebuild'
        index_file = prebuild_dir / 'index.json'
        
        # Check if prebuild directory exists
        if not prebuild_dir.exists():
            return {"success": True, "message": f"Prebuild directory not found: {prebuild_dir}, skipping"}
        
        # Check if index.json exists
        if not index_file.exists():
            return {"success": True, "message": f"index.json not found: {index_file}, skipping"}
        
        # Load and validate JSON
        try:
            with open(index_file, 'r') as f:
                prebuild_config = json.load(f)
        except json.JSONDecodeError as e:
            return {"success": False, "message": f"Invalid JSON syntax in {index_file}: {e}"}
        
        # Determine user home directory
        if os.environ.get('OMARCHY_USER'):
            user_home = f"/home/{os.environ['OMARCHY_USER']}"
            username = os.environ['OMARCHY_USER']
        else:
            user_home = str(Path.home())
            username = os.environ.get('USER', 'user')
        
        # Install packages if specified
        packages = prebuild_config.get('packages', [])
        if packages:
            print(f"Installing {len(packages)} prerequisite packages...")
            try:
                result = subprocess.run(
                    ['sudo', 'pacman', '-S', '--noconfirm', '--needed'] + packages,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result.returncode != 0:
                    print(f"WARNING: Some packages failed to install (exit code: {result.returncode})")
                    print(f"Output: {result.stderr}")
                else:
                    print(f"All {len(packages)} packages installed successfully")
            except subprocess.TimeoutExpired:
                return {"success": False, "message": "Package installation timed out"}
            except Exception as e:
                return {"success": False, "message": f"Package installation failed: {e}"}
        
        # Deploy files
        deployments = prebuild_config.get('deployments', [])
        if not deployments:
            return {"success": True, "message": "No deployments found in index.json"}
        
        print(f"Deploying {len(deployments)} configuration files...")
        
        deployed = 0
        failed = 0
        
        for i, deployment in enumerate(deployments):
            source_file = deployment.get('source')
            dest_path_raw = deployment.get('destination')
            permissions = deployment.get('permissions', '644')
            
            if not source_file or not dest_path_raw:
                print(f"WARNING: Deployment {i+1} missing source or destination, skipping")
                failed += 1
                continue
            
            # Expand destination path
            dest_path = expand_path(dest_path_raw, user_home)
            dest_path_obj = Path(dest_path)
            
            # Build full source path
            source_path = prebuild_dir / source_file
            
            print(f"Processing [{i+1}/{len(deployments)}]: {source_file} -> {dest_path}")
            
            # Check if source file exists
            if not source_path.exists():
                print(f"ERROR: Source file not found: {source_path}")
                failed += 1
                continue
            
            # Create destination directory if needed
            dest_dir = dest_path_obj.parent
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"ERROR: Failed to create directory {dest_dir}: {e}")
                failed += 1
                continue
            
            # Backup existing file if it exists
            if dest_path_obj.exists():
                backup_path = Path(f"{dest_path}.backup")
                try:
                    shutil.copy2(dest_path_obj, backup_path)
                    print(f"Backed up existing file: {backup_path}")
                except Exception as e:
                    print(f"WARNING: Failed to create backup: {e}")
            
            # Copy file
            try:
                shutil.copy2(source_path, dest_path_obj)
                
                # Set permissions
                try:
                    os.chmod(dest_path_obj, int(permissions, 8))
                except Exception as e:
                    print(f"WARNING: Failed to set permissions: {e}")
                
                # Set ownership if in chroot context
                if os.environ.get('OMARCHY_USER'):
                    try:
                        import pwd
                        user_info = pwd.getpwnam(username)
                        os.chown(dest_path_obj, user_info.pw_uid, user_info.pw_gid)
                    except Exception as e:
                        print(f"WARNING: Failed to set ownership: {e}")
                
                print(f"Deployed successfully: {source_file} -> {dest_path} (perms: {permissions})")
                deployed += 1
                
            except Exception as e:
                print(f"ERROR: Failed to deploy {source_file}: {e}")
                failed += 1
        
        if failed > 0:
            return {
                "success": False,
                "message": f"Deployment completed with errors: {deployed} deployed, {failed} failed"
            }
        
        return {
            "success": True,
            "message": f"All deployments completed successfully: {deployed} files deployed"
        }
    
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)

