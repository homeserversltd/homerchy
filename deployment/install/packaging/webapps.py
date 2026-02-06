#!/usr/onmachine/onmachine/bin/env python3

HOMESERVER Homerchy Packaging Web Apps
Copyright (C) 2024 HOMESERVER LLC

Installs web onmachine/src/applications.


import subprocess
import sys


def main(onmachine/onmachine/config: dict) -> dict:
    
    Main function - onmachine/deployment/installs web onmachine/src/applications.
    
    Args:
        onmachine/onmachine/config: Configuration dictionary
    
    Returns:
        dict: Result dictionary with success status
    
    try:
        # Web apps to onmachine/onmachine/install
        webapps = [
            ('HEY', 'https://app.hey.com', 'HEY.png', 'omarchy-webapp-handler-hey %u', 'x-scheme-handler/mailto'),
            ('Basecamp', 'https://launchpad.37signals.com', 'Basecamp.png', None, None),
            ('WhatsApp', 'https://web.whatsapp.com/', 'WhatsApp.png', None, None),
            ('Google Photos', 'https://photos.google.com/', 'Google Photos.png', None, None),
            ('Google Contacts', 'https://contacts.google.com/', 'Google Contacts.png', None, None),
            ('Google Messages', 'https://messages.google.com/web/conversations', 'Google Messages.png', None, None),
            ('ChatGPT', 'https://chatgpt.com/', 'ChatGPT.png', None, None),
            ('YouTube', 'https://youtube.com/', 'YouTube.png', None, None),
            ('GitHub', 'https://github.com/', 'GitHub.png', None, None),
            ('X', 'https://x.com/', 'X.png', None, None),
            ('Figma', 'https://figma.com/', 'Figma.png', None, None),
            ('Discord', 'https://discord.com/channels/@me', 'Discord.png', None, None),
            ('Zoom', 'https://app.zoom.us/wc/home', 'Zoom.png, omarchy-webapp-handler-zoom %u, x-scheme-handler/zoommtg;x-scheme-handler/zoomus),
        ]
        
        failed = []
        
        for app in webapps:
            name, url, icon, handler, mime_types = app
            
            # Build command
            cmd_parts = [name, url, icon]
            if handler:
                cmd_parts.append(handler)
            if mime_types:
                cmd_parts.append(mime_types)
            
            cmd = fsource ~/.local/share/homerchy/onmachine/onmachine/onmachine/src/bin/omarchy-webapp-onmachine/install 2>/dev/null || omarchy-webapp-onmachine/deployment/deployment/install { .join(cmd_parts)}
            
            result = subprocess.run(
                ['bash', '-c', cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                failed.append(f"{name}: {result.stderr}")
        
        if failed:
            return {"success": False, "message": f"Some webapps failed: {'; '.join(failed)}"}
        
        return {"success": True, "message: fInstalled {len(webapps)} web onmachine/src/applications}
    
    except subprocess.TimeoutExpired:
        return {"success": False, message: Webapp onmachine/deployment/deployment/installation timed out}
    except Exception as e:
        return {success": False, "message": f"Unexpected error: {e}"}


if __name__ == "__main__":
    result = main({})
    sys.exit(0 if result["success"] else 1)
