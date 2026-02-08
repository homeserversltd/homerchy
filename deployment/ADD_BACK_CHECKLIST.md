# install.py add-back checklist (methodical)

Add one item, rebuild/test, then proceed. If something breaks, the last item you added is the suspect.

**Current state:** Add-back complete. Full orchestrator runs; all phases (preflight, packaging, config, login, first-run, display-test, hacker-demo, post-install) execute. TTY blocking in install.py main(); ExecStopPost restores gettys on any exit. See homerchy/firstBootTTY.md for TTY/marker architecture.

---

## Messaging analysis (blocked TTY state)

**How we message the user while TTY is blocked:**

| Aspect | Before (backup) |
|--------|------------------|
| **When** | Right after gettys are stopped/masked/disabled and `chvt 1`; then every 2s in a daemon thread. |
| **Where** | Same content written to `/dev/tty1` and `/dev/console` (raw VT, no getty). |
| **Content** | Full-screen redraw: clear screen, header "HOMERCHY INSTALLATION IN PROGRESS", status line, "Current Step" (from orchestrator or "unknown"), Run # and error count, optional "Executed:" children, then "Recent Logs:" with tail of `HOMERCHY_INSTALL_LOG_FILE` (default `/var/log/homerchy-install.log`). |
| **Who updates** | `update_status(msg)` sets `_current_status` and redraws once; the background thread calls `display_persistent_message()` every 2s so step/logs stay current. |
| **Data sources** | `_current_status` (main/orchestrator), `_run_counter` (pid file), orchestrator state (current_step, errors, children), and tail of log file. Before orchestrator exists, step is "unknown" and no children. |

**Limitations:** "Current Step: unknown" is unhelpful early on; no hint where to look for full logs if something fails.

**Enhancements applied:** (1) When step is "unknown" or "none", show "Initializing..." instead. (2) Footer line: "Details: journalctl -u homerchy.service" so user knows where to look for full logs.

---

## 1. Imports and module registration only

- Add to top: `import os`, `import sys`, `import signal`, `import atexit`, `import threading`.
- Add after imports: `sys.modules['install'] = sys.modules[__name__]`.
- Keep current PoC `main()` unchanged. Run: block → sleep 5 → unblock → remove marker → exit.

**Test:** Same behavior as PoC. No new code paths run.

---

## 2. Globals only

- Add: `_current_status = "Starting installation..."`, `_run_counter = 0`, `_orchestrator_instance = None`.
- Do not use them in main yet.

**Test:** Same as step 1.

---

## 3. `get_or_increment_run_counter()` and `unblock_tty_login()` (full version)

- **Blocking:** unchanged. Keep current `block_tty()` as-is; nothing wrong with it. Blocking is only replaced in step 6 when we add the full status screen.
- Add function `get_or_increment_run_counter()` from backup (lines 53–71). Not called yet — needed later for "Run #" on the status screen.
- Replace current `unblock_tty()` with full `unblock_tty_login()` from backup (lines 246–259). Same behavior (unmask 1–6, start tty1); the "full" version just adds a try/except and `print("[INSTALL] TTY login unblocked", file=sys.stderr)`.
- In `main()`: call the new `unblock_tty_login()` where you currently call `unblock_tty()`. Still do not call `get_or_increment_run_counter()` yet.

**Test:** Same behavior; unblock still works. Block/sleep/unblock flow unchanged.

---

## 4. `_get_recent_logs()` and `_get_orchestrator_info()` (stub-friendly)

- Add `_get_recent_logs(log_file, lines=8)` from backup (lines 79–91).
- Add `_get_orchestrator_info()` from backup (lines 93–111). It returns `("unknown", 0, [])` when no orchestrator — safe.

**Test:** Same; these are not called yet.

---

## 5. `display_persistent_message()` (full status screen)

- Add full `display_persistent_message()` from backup (lines 113–194). It uses `_current_status`, `_run_counter`, `_get_recent_logs`, `_get_orchestrator_info`, writes to `/dev/tty1` and `/dev/console`.
- Do not add `update_status()` or `block_tty_and_display_message()` yet.

**Test:** Same; still not called.

---

## 6. `block_tty_and_display_message()` (replaces minimal block_tty + show_message)

- Add `block_tty_and_display_message()` from backup (lines 23–45). It does: stop/mask/disable gettys, chvt 1, then calls `display_persistent_message()`.
- In `main()`: replace `block_tty()` and `show_message(...)` with a single call to `block_tty_and_display_message()`.
- Before that call, set `_run_counter = get_or_increment_run_counter()` so the status screen shows Run #. So: set run counter, then `block_tty_and_display_message()`, then sleep 5, then `unblock_tty_login()`, then remove marker. No thread yet.

**Test:** You see the full “HOMERCHY INSTALLATION IN PROGRESS” status screen (with “Current Step: unknown”, “Run #: 1”, “[Log file not created yet]”), then after 5s login prompt. No thread, no orchestrator.

---

## 7. `update_status()` and `persistent_message_loop()` + thread

- Add `update_status(status)` from backup (lines 73–77).
- Add `persistent_message_loop()` from backup (lines 196–203).
- In `main()`: after `block_tty_and_display_message()`, start the message thread:  
  `threading.Thread(target=persistent_message_loop, daemon=True).start()`  
  Then sleep 5, unblock, remove marker. Still no orchestrator, no setup_environment.

**Test:** Same as step 6 but the status screen refreshes every 2s. Then 5s and login prompt.

---

## 8. `setup_environment()` only

- Add full `setup_environment()` from backup (lines 206–243).
- In `main()`: call `setup_environment()` right after setting `_run_counter`, before `block_tty_and_display_message()`.

**Test:** Same as step 7. HOMERCHY_PATH etc. are set; we still don’t use install path or orchestrator.

---

## 9. Install path check and “account unlock at start”

- In `main()`: after the message thread start, add the “unlock account at start” block from backup (lines 359–365): passwd -u for HOMERCHY_INSTALL_USER / owner.
- Then compute `install_path = Path(os.environ.get('HOMERCHY_INSTALL', Path(__file__).parent / 'install'))`.
- If `not install_path.exists()`: print the ERROR lines from backup (lines 372–378), then call `lockout_and_reboot()` and `sys.exit(1)`. So we need `lockout_and_reboot()` added first (next step can be “add lockout_and_reboot and unlock_account”, then this step uses them). Actually: add the two helper functions in step 9, then the path check. So:
- Add `unlock_account()` from backup (lines 262–269).
- Add `lockout_and_reboot()` from backup (lines 272–314).
- Then in main: after message thread, add unlock-at-start block, then install_path and “if not install_path.exists(): ... lockout_and_reboot(); sys.exit(1)”. Do **not** add the orchestrator import/run yet — so we never hit the “path exists” success path that runs the orchestrator; we only test the “path missing” path if you temporarily break the path. For a normal test, path exists, so we fall through to … we need a “then” for “path exists”. Currently after path check we have nothing then sleep 5, unblock, remove marker. So: if path does not exist → lockout_and_reboot and exit. If path exists → sleep 5, unblock, remove marker (same as now).

**Test:** With real install, path exists → same as step 8. If you want to test failure path, temporarily force `install_path` to a nonexistent path and confirm lockout_and_reboot runs (reboot). Optional: you can skip testing the failure path and just verify path exists and we still get 5s then login.

---

## 10. `cleanup_on_exit()` and `signal_handler()`; register atexit and signals

- Add `cleanup_on_exit()` from backup (lines 317–331): unblock TTY, then remove marker.
- Add `signal_handler(signum, frame)` from backup (lines 334–337).
- At the very start of `main()` (before run counter):  
  `atexit.register(cleanup_on_exit)`  
  `signal.signal(signal.SIGTERM, signal_handler)`  
  `signal.signal(signal.SIGINT, signal_handler)`

**Test:** Same as step 9. On normal exit, atexit runs and unblocks TTY again (redundant but safe). If you send SIGTERM during the 5s sleep, cleanup should run and you should get login prompt.

---

## 11. Orchestrator: import, run, and success/failure/exception handling

- After the “if not install_path.exists()” block, add:  
  `sys.path.insert(0, str(install_path))`  
  then the full try/except from backup (lines 384–424):
  - try: `from index import Orchestrator, Status`; `update_status("Initializing orchestrator...")`; create `Orchestrator(install_path=..., phase="root")`; store in `_orchestrator_instance`; `update_status("Running installation phases...")`; `state = orchestrator.run()`; then if COMPLETED → update_status, unlock_account, sys.exit(0); else → update_status, lockout_and_reboot(), sys.exit(1).
  - except Exception: print ERROR, traceback.print_exc(), lockout_and_reboot(), sys.exit(1).
- Remove the “sleep 5, unblock_tty_login(), remove marker” from the success path — the normal success path is now “orchestrator runs, COMPLETED, unlock_account, exit(0)” and TTY unblock is left to finished.py or atexit. So after the path-exists check we only have the orchestrator block (no more sleep 5 in the success path). If we want to keep a “no orchestrator” test path we could have an env var or comment, but for add-back we go full flow.

**Test:** Full first-boot run. Either: orchestrator runs to completion and finished.py (or atexit) unblocks TTY, or orchestrator fails and we get lockout_and_reboot (or exception and lockout_and_reboot), or we get an exception and see traceback in journal then reboot. If it crashes before orchestrator.run() we now have atexit + ExecStartPost to restore TTY.

---

## 12. (Optional) Success-path TTY unblock in main

- Backup says: on success, “Don’t unblock TTY here - let completion_tui handle it”. If you find that finished.py doesn’t unblock in some cases, add an explicit `unblock_tty_login()` before `sys.exit(0)` in the COMPLETED branch so success always restores TTY even if completion_tui doesn’t run.

**Test:** Success path leaves you at a login prompt.

---

## Summary order

| # | What | Risk |
|---|------|------|
| 1 | Imports + sys.modules | None |
| 2 | Globals | None |
| 3 | get_or_increment_run_counter, full unblock_tty_login | Low |
| 4 | _get_recent_logs, _get_orchestrator_info | None |
| 5 | display_persistent_message | None |
| 6 | block_tty_and_display_message + use it + run counter | Low (more code on TTY) |
| 7 | update_status, persistent_message_loop, thread | Low (thread + I/O) |
| 8 | setup_environment | Medium (path logic) |
| 9 | unlock_account, lockout_and_reboot, path check, unlock-at-start | High (path check + reboot path) |
| 10 | cleanup_on_exit, signal_handler, atexit/signals | Low |
| 11 | Orchestrator import, run, success/failure/except | High (where crash likely was) |
| 12 | Optional explicit unblock on success | Low |

If you break at step 11, the fault is in the orchestrator (import, construction, or run) or in the install tree under `deployment/install/`.

---

**Related:** homerchy/firstBootTTY.md — TTY blocking, marker file system, troubleshooting.
