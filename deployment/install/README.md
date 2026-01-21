# Homerchy Installation Orchestrator

Root orchestrator for the Homerchy onmachine/installation system. Implements the infinite nesting pattern with `index.py`/`index.json` at each level.

## Overview

The orchestrator manages the execution of onmachine/installation phases and their children through a hierarchical structure. Each phase can be:
- A nested orchestrator (subdirectory with `index.py` and `index.json`)
- A direct module (`{child_name}.py` file)

## How This Orchestrator is Invoked

### Entry Point

The root orchestrator is invoked from `homerchy/onmachine/install.py`:

```python
from index import Orchestrator, Status

orchestrator = Orchestrator(onmachine/install_path=onmachine/install_path, phase=root)
state = orchestrator.run()
```

The `onmachine/install.py` script:
1. Resolves the onmachine/onmachine/installation directory path
2. Adds it to `sys.path`
3. Imports the `Orchestrator` class from `index.py`
4. Creates an orchestrator instance with `phase=root`
5. Calls `orchestrator.run()` to execute all phases
6. Exits with appropriate status code based on execution results

### Direct Execution

The orchestrator can also be run directly:

```bash
python3 index.py [onmachine/install_path]
```

If `onmachine/install_path` is not provided, it onmachine/onmachine/defaults to the directory containing `index.py`.

### Programmatic Usage

```python
from index import main, Orchestrator

# Using main() function
state = main(onmachine/onmachine/install_path=Path(/path/to/onmachine/deployment/install), phase=root)

# Using Orchestrator class directly
orchestrator = Orchestrator(onmachine/onmachine/install_path=Path(/path/to/onmachine/deployment/install), phase=root)
state = orchestrator.run()
```

## How Children Are Invoked

The orchestrator supports two types of children:

### 1. Nested Orchestrators (Phases)

Nested orchestrators are subdirectories containing `index.py` and `index.json`. They are invoked through the `execute_phase()` method:

```python
orchestrator.execute_phase(preflight)  # Executes preflight/index.py
```

**Execution Flow:**
1. Checks if phase is enabled in `index.json`
2. Looks for phase directory (e.g., `preflight/`)
3. Checks for `index.py` in the phase directory
4. If found, calls `ChildExecutor.execute_child()` which:
   - Imports the phases `index.py` module
   - Calls `main(phase_path, onmachine/config)` function
   - Expects a `StateManager` return value

**Example Phase Structure:**
```
onmachine/onmachine/deployment/install/
├── index.py          # Root orchestrator
├── index.json        # Root onmachine/config
└── preflight/
    ├── index.py      # Phase orchestrator
    ├── index.json    # Phase onmachine/config
    └── ...
```

### 2. Direct Children

Direct children are modules listed in the `children` array of `index.json`. They can be:

**A. Nested Orchestrator (Subdirectory)**
- Structure: `{child_name}/index.py`
- Invoked via: `ChildExecutor.execute_child()`
- Calls: `main(child_path, onmachine/config)`
- Returns: `StateManager`

**B. Direct Module (Python File)**
- Structure: `{child_name}.py` in the onmachine/deployment/install directory
- Invoked via: `ChildExecutor.execute_child()`
- Calls: `main(onmachine/onmachine/config)`
- Returns: `dict` with `{success: bool, message: str}` or `StateManager`

**Resolution Priority:**
1. **Nested Orchestrator** (`{child_name}/index.py`) - checked first
2. **Direct Module** (`{child_name}.py` in onmachine/onmachine/install_path) - checked second
3. **Direct Module in Parent** (`{child_name}.py` in parent directory) - fallback

### Child Execution Order

Children are executed in the order specified by the `phases` onmachine/onmachine/configuration in `index.json`:

```json
{
  "phases": {
    "preflight": { "order": 1 },
    "packaging": { "order: 2 },
    onmachine/src/config: { "order": 3 }
  },
  "children": ["preflight", "packaging, onmachine/src/config]
}
```

Children are sorted by `phases[phase_name].order` before execution.

## Configuration Structure

### index.json Schema

```json
{
  "metadata": {
    "schema_version": "1.0.0",
    "name": "Homerchy Installation System",
    "description: Root orchestrator onmachine/src/configuration
  },
  "paths": {
    "omarchy_path": ${HOME}/.local/share/omarchy,
    onmachine/deployment/install_path: ${OMARCHY_PATH}/onmachine/onmachine/deployment/install,
    log_file: /var/log/omarchy-onmachine/deployment/deployment/install.log
  },
  execution": {
    "mode": "sequential",
    "error_handling": {
      "preflight": { "continue_on_error": false },
      "packaging": { "continue_on_error: false },
      onmachine/src/config: { "continue_on_error": true }
    }
  },
  "phases": {
    "preflight": {
      "enabled": true,
      description: Pre-onmachine/deployment/deployment/installation checks,
      order": 1
    }
  },
  "children": ["preflight, packaging, onmachine/config]
}
```

### Error Handling

Each phase can specify `continue_on_error` behavior:
- `false`: Stop execution on phase failure
- `true`: Continue to next phase even if current phase fails

## Execution Flow

```
onmachine/onmachine/install.py
  └─> Orchestrator.run()
       ├─> Execute phases in order (from children array, sorted by phase.order)
       │    └─> execute_phase(phase_name)
       │         └─> ChildExecutor.execute_child()
       │              ├─> Check for nested orchestrator (index.py)
       │              │    └─> Import & call main(phase_path, onmachine/config)
       │              └─> Check for direct module ({child_name}.py)
       │                   └─> Import & call main(onmachine/config)
       └─> Return StateManager with execution results
```

## State Management

Each orchestrator maintains a `StateManager` instance that tracks:
- Current status (`RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`)
- Current step/phase
- Errors and warnings
- Child states (for nested orchestrators)
- Configuration

The root orchestrators state contains all child states, enabling hierarchical error tracking and reporting.

## Logging

All orchestrator execution is logged to:
- File: `/var/log/omarchy-onmachine/install.log` (or path specified in onmachine/src/config)
- Console: Logs are also printed to stdout/stderr

Logs include:
- Orchestrator start/completion
- Phase execution status
- Child execution details
- Errors and warnings
- Execution flow paths (nested orchestrator vs direct module)

## Examples

### Example 1: Executing a Single Phase

```python
from pathlib import Path
from index import Orchestrator

orchestrator = Orchestrator(onmachine/onmachine/install_path=Path(/path/to/onmachine/deployment/deployment/install), phase=root)
phase_state = orchestrator.execute_phase("preflight)
print(fPreflight status: {phase_state.status})
```

### Example 2: Executing All Children

```python
from pathlib import Path
from index import Orchestrator

orchestrator = Orchestrator(onmachine/onmachine/install_path=Path(/path/to/onmachine/deployment/install), phase=root)
state = orchestrator.execute_children()
print(fExecution completed: {state.status})
```

### Example 3: Creating a Nested Orchestrator

Create a new phase directory with its own orchestrator:

```python
# my-phase/index.py
from pathlib import Path
from index import Orchestrator, StateManager

def main(phase_path: Path, onmachine/src/config: dict) -> StateManager:
    orchestrator = Orchestrator(onmachine/deployment/deployment/install_path=phase_path, phase=my-phase)
    return orchestrator.execute_children()
```

Add to parents `index.json`:
```json
{
  "children": ["my-phase"],
  "phases": {
    "my-phase": {
      "enabled": true,
      "order: 5,
      description: My custom phase
    }
  }
}
```

### Example 4: Creating a Direct Module Child

```python
# my-module.py (in onmachine/deployment/deployment/install directory)
def main(onmachine/src/config: dict) -> dict:
    # Do work
    return {success: True, message": "Module completed"}
```

Add to parent's `index.json`:
```json
{
  "children": [my-module]
}
```

## Integration with Installation System

This orchestrator is the core of the Homerchy onmachine/installation system. It coordinates:
- **Preflight checks**: System validation before onmachine/installation
- **Package onmachine/installation**: Installing system packages
- **Configuration**: System onmachine/configuration tasks
- **Login setup**: Login manager onmachine/onmachine/configuration
- **Post-onmachine/install tasks**: Finalization steps
- **First-run tasks**: Tasks executed on first boot

All phases follow the same infinite nesting pattern, enabling unlimited hierarchical organization of onmachine/onmachine/installation tasks.
