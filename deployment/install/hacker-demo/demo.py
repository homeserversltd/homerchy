#!/usr/bin/env python3
"""
HOMESERVER Homerchy first-boot install – hacker-demo phase.
Copyright (C) 2024 HOMESERVER LLC

Fake installation with ultimate hacker meme vibes for demo/recording.
Spams silly log lines so the status screen looks impressive.
"""

import random
import sys
import time
from pathlib import Path
from typing import Any

from helpers.logging import append_log

MESSAGES = [
    "Initializing quantum encryption protocols...",
    "Downloading internet...",
    "Bypassing mainframe firewall...",
    "Decrypting neural network weights...",
    "Installing blockchain into kernel...",
    "Synthesizing AI consciousness...",
    "Calibrating flux capacitor...",
    "Routing packets through the matrix...",
    "Compiling zero-day exploits...",
    "Mounting /dev/null to /dev/awesome...",
    "Injecting sudo into sudo...",
    "Unlocking government backdoors...",
    "Patching reality.exe...",
    "Optimizing entropy generation...",
    "Loading cybernetic enhancements...",
    "Establishing Skynet handshake...",
    "Defragmenting the cloud...",
    "Installing more RAM...",
    "Caching the entire internet...",
    "Recompiling the universe...",
    "Extracting pure caffeine from /dev/urandom...",
    "Initializing hackerman mode...",
    "Spoofing MAC address to 00:11:22:33:44:55...",
    "Deploying neural implants...",
    "Configuring warp drive...",
    "Booting the mainframe...",
    "Encrypting the decryptor...",
    "Installing hacker license...",
    "Downloading more cores...",
    "Syncing with the mothership...",
    "Bypassing CAPTCHA with pure skill...",
    "Overclocking the CPU to 11...",
    "Installing the internet (standalone package)...",
    "Running make world in background...",
    "Grepping /dev/zero for vulnerabilities...",
    "chmod 777 on everything (for speed)...",
    "Enabling turbo mode...",
    "Loading nanobots...",
    "Installing hacker fonts...",
    "Compressing the uncompressed...",
]


def run(install_path: Path, state: Any) -> None:
    """Run the fake hacker-style install demo."""
    append_log("[HACKER-DEMO] Ultimate installer engaged.", state)
    print("[HACKER-DEMO] Ultimate installer engaged.", file=sys.stderr, flush=True)

    msgs = MESSAGES.copy()
    random.shuffle(msgs)

    total = len(msgs)
    for i, msg in enumerate(msgs):
        pct = ((i + 1) * 100) // total
        line = f"  [{pct:3d}%] {msg}"
        append_log(line, state)
        print(line, file=sys.stderr, flush=True)
        time.sleep(random.uniform(0.4, 1.2))

    append_log("[HACKER-DEMO] Installation complete. You are now one with the machine.", state)
    print("[HACKER-DEMO] Installation complete.", file=sys.stderr, flush=True)
