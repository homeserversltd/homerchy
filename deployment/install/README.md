# Homerchy first-boot install tree

First-boot orchestrator run by `deployment/install.py`. Infinite-index pattern: root `index.json` / `index.py` and nested phases (preflight, packaging, config, login, first-run, display-test, post-install). All code is Python; no shell scripts.

## What we're doing

We are rebuilding this tree **module by module, very slowly**. We have infinite patience. We will:

1. **Go file-by-file** – Recreate or determine the value of each piece from the old tree. Decide what we actually want before adding it. The stubbed placeholders are the scaffold; we fill only what we need.
2. **Know precisely where it breaks** – When something fails, we know exactly which module or step failed. We brute-force the path into existence by fixing one boundary at a time.
3. **Report then advance** – Each cluster (e.g. preflight) runs to a defined stop point and produces a **report** of what happened. We stop, read the report, then move to the next cluster. No silent failures.

## Target flow (first milestone)

1. **`deployment/install.py`** – Entry point. Sets env, blocks TTY, shows status, runs root orchestrator (see ADD_BACK_CHECKLIST in `deployment/`).
2. **`deployment/install/index.py`** – Root orchestrator. Loads `index.json`, runs children in order (preflight → packaging → …). Exposes `Orchestrator`, `Status`, `State` for install.py.
3. **`deployment/install/preflight`** – First phase. Runs its steps, then **stops** and reports:
   - What ran (which submodules)
   - Success / failure
   - Any errors or context needed for the next step

So: **install.py → index.py → preflight → stop + report**. Once that works reliably, we add the next phase (e.g. packaging) and again run to a clean stop with a report.

## Old behavior reference

We are not re-adding the old tree blindly. For each phase we document what the **old** code did and steal only what we care about.

- **Preflight:** See [preflight/OLD_BEHAVIOR.md](preflight/OLD_BEHAVIOR.md) for what the old preflight did (from git history). Use it to decide what to reimplement and what to drop.

Other phases will get similar OLD_BEHAVIOR or design notes as we reach them.

## Display and state: one process, main owns both

We run one Python process (install.py). That process holds a bit of RAM and **owns the display and state** until it exits. Everything else reports into it.

- **Main (install.py):** Starts the process, blocks TTY, owns the refresh loop. Creates or receives the single **State** object. Calls the install-tree **reporting** API to redraw the screen from state (e.g. every 2s and on status change). Never hands off TTY or display to phases.
- **Tooling in this tree:**
  - **`state.py`** – Defines `State` (current_step, errors, children, status, recent_logs) and `Status` enum. Single source of truth for “what’s happening.” `recent_logs` is a live buffer phases can append to via `helpers.logging.append_log`; reporting uses it when non-empty, else the log file tail.
  - **`reporting.py`** – Builds the status message from state + log file (or state.recent_logs) and writes to `/dev/tty1` and `/dev/console`. Main imports `redraw(state, run_counter, status_str, log_file)` and calls it; phases never call it.
  - **`helpers/`** – `errors.record_error(state, step, message)` and `logging.append_log(message, state=None)`. Phases use these to report into shared state. No display helpers (presentation.py removed; main + reporting own display).
- **Orchestrator and phases:** Receive the same `State` instance (main creates it, passes to Orchestrator; Orchestrator passes it to each phase). They only **mutate** state (e.g. `state.current_step = "guard"`, `state.errors.append(...)`). They do not open TTY, draw, or own any display. Syncing and displaying correctly is achieved by: everyone touches the same state; main refreshes the display from that state via `reporting.redraw`.

So: **main controls display and state; tooling in install/ is the contract; phases only report into state.**

## Structure (current)

- **Root:** `index.py` (Orchestrator; imports State, Status from `state.py`), `index.json` (children: preflight, packaging, config, login, first-run, display-test, post-install), `state.py`, `reporting.py`.
- **Phases:** Each has `index.json` + `index.py` and optional child modules. Config has a nested `hardware` sub-phase. **Preflight** is a sub-orchestrator: its `index.json` lists children (guard, begin, show_env, pacman, migrations, first_run_mode, disable_mkinitcpio) and `index.py` runs them in order, updating state and using `helpers.errors.record_error` on failure.
- **Helpers:** `errors.record_error`, `logging.append_log`; no TTY/display (removed).
- **Removed (redundant with shared state/display):** `preflight/tty_control.py` (main owns TTY), `helpers/presentation.py` (reporting owns display).
- **Placeholders:** Step modules (e.g. `preflight/guard.py`) are stubs until we implement them.

## State machine and report

- **State** is the single mutable object: current_step, errors, children, status, recent_logs. Phases only mutate it; main redraws from it.
- **Report** after a phase (e.g. preflight) is derived from state: `state.children` (step → "ok" or error message), `state.errors` (list of "step: message"). No separate report file; main can surface state on TTY or in logs. To “stop after preflight and report,” run the root orchestrator (which runs preflight first); then read state.children and state.errors and exit or continue.
