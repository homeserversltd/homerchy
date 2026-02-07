# Old install tree (not run by current install.py)

Everything here was moved so the active first-boot path is minimal: **deployment/install.py** only (block TTY, status screen, sleep 5, unblock, remove marker). No orchestrator runs.

- **install/** — Full orchestrator tree (root index.json/index.py, preflight, packaging, config, login, post-install, first-run, display-test, utils, helpers). Sample folder-by-folder when you need something (e.g. menu system, package lists).
- **install.py.backup** — Full install.py that imported and ran the orchestrator.

Use this as the reference when building the new “naked” flow: browser + file explorer + minimal Libre + the bits you want to keep (e.g. menu system).
