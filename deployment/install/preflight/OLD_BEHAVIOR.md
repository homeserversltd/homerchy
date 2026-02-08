# Old preflight behavior (from git history)

Reference: commit `b8922fd7` and related in homerchy repo. The old preflight had its own orchestrator and child modules. Below is what each piece did so we can choose what to reimplement.

## Execution order (index.json children)

1. **guard** – System checks (see below)
2. **begin** – Start message and log init
3. **show-env** – Show environment (debug)
4. **pacman** – Pacman preflight (e.g. refresh, config)
5. **migrations** – Data/config migrations
6. **first-run-mode** – First-run detection/setup
7. **disable-mkinitcpio** – Disable or adjust mkinitcpio for install

Note: **tty-control** existed as a separate module (TTYController). We no longer duplicate that: **install.py** is the single process that owns the display and state. It blocks TTY, runs a refresh loop, and uses the install-tree **reporting** tooling (`state.py` + `reporting.py`) so everything syncs and displays from one place. Phases (including preflight) only report into the shared state; they never draw or own TTY. See README “Display and state” section.

---

## guard.py

**Purpose:** Pre-install guard checks. Validates system requirements; during installation (chroot/first-boot) many checks are skipped.

- **is_installation()** – True if `OMARCHY_CHROOT_INSTALL` env set or running as root (installation context).
- **check_arch_release()** – Vanilla Arch: `/etc/arch-release` exists; no derivative markers (e.g. `/etc/manjaro-release`, `/etc/garuda-release`).
- **check_not_root()** – Must not be root unless in installation mode (then root is OK).
- **check_architecture()** – CPU must be x86_64.
- **check_secure_boot()** – `bootctl status` must not show “Secure Boot: enabled”.
- **check_desktop_environment()** – gnome-shell and plasma-desktop must not be installed (fresh system).
- **check_limine()** – Limine bootloader must be installed (skipped during installation).
- **check_btrfs()** – Root filesystem must be btrfs (`findmnt -o FSTYPE /`).

**Return:** `{"success": bool, "message": str}`. On failure, message describes what is required (e.g. “Vanilla Arch”, “Btrfs root filesystem”).

**What to steal:** Guard list and semantics; drop or relax checks we don’t care about (e.g. btrfs, Limine). Installation-mode skip is useful so first-boot doesn’t fail guard.

---

## begin.py

**Purpose:** Start installation log and show “Installing…” to the user.

- Clear logo (placeholder; depended on presentation helper).
- Run `gum style --foreground 3 --padding '1 0 0 4' 'Installing...'` if `gum` exists; else `print("Installing...")`.
- Return `{"success": True, "message": "Installation begun"}`.

**What to steal:** Optional “Installing…” or similar message. install.py already shows a status screen; we can keep begin minimal (e.g. write a log line or set state) or fold into a single “start” step.

---

## tty-control.py (TTYController)

**Purpose:** Take exclusive control of TTY1 for installation progress. Replaced Plymouth during install.

- **acquire()** – Stop/mask gettys 1–6, `chvt 1`, open `/dev/tty1`, lock file `/tmp/omarchy-tty-control.lock`, clear screen, show “HOMERCHY INSTALLATION IN PROGRESS”, start keep-alive thread (refresh every 5s).
- **release()** – Stop thread, close fd, remove lock, unmask gettys, start getty@tty1.
- **show_message()** / **update_progress(phase, message)** – Update TTY display.
- **get_controller()** – Global singleton. Env `OMARCHY_TTY_CONTROLLER` set to `'active'` when acquired.

**What to steal:** install.py already blocks gettys and shows a persistent status (display_persistent_message, journalctl hint). We can either (a) keep TTY entirely in install.py and have preflight only run checks, or (b) pass a TTY/display helper from install.py into the orchestrator so phases can update one shared display. If we want phase-level progress (e.g. “preflight: guard”), we need a single place that owns TTY (install.py or a shared helper), not a second TTY controller in preflight.

---

## show-env, pacman, migrations, first-run-mode, disable-mkinitcpio

From the file list these existed; exact behavior was not fully captured in the sampled commits. As we rebuild:

- **show-env** – Likely dump env for debug; optional.
- **pacman** – Preflight pacman (e.g. keyring, refresh, or config); we’ll define when we implement packaging.
- **migrations** – Config or data migrations before main install; define per migration.
- **first-run-mode** – Detect or set “first run” flag; useful for one-time setup.
- **disable-mkinitcpio** – Turn off or adjust mkinitcpio during install to avoid rebuilds at wrong time.

Document each in this file or in the module when we implement it.

---

## Summary

- **Guard:** Keep the idea; implement checks we care about; skip most in installation mode.
- **Begin:** Minimal (log/message); can be merged with “start” in orchestrator.
- **TTY:** Don’t duplicate; use install.py’s display or a single shared helper for phase progress.
- **Other preflight children:** Define and implement one at a time with a report-then-advance step after preflight.
