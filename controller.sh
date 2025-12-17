#!/bin/bash
# Thin wrapper for Python controller
# All logic has been moved to homerchy/controller/main.py

set -e

REPO_ROOT="$(dirname "$(realpath "$0")")"
CONTROLLER_PY="${REPO_ROOT}/controller/main.py"

# Execute Python controller with all arguments passed through
exec python3 "$CONTROLLER_PY" "$@"
