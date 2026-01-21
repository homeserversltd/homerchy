#!/bin/bash
# Thin wrapper for Python controller
# All logic has been moved to homerchy/lib/controller/main.py

set -e

REPO_ROOT="$(dirname "$(realpath "$0")")"
CONTROLLER_DIR="${REPO_ROOT}/lib/controller"

# Add controller directory to Python path and execute main module
PYTHONPATH="${REPO_ROOT}:${PYTHONPATH}" exec python3 -m lib.controller.main "$@"