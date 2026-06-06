#!/usr/bin/env bash
# ctmv3-sovereign-init.sh -- Cursor-side wrapper for python3 -m ctmv3 sovereign-init
# Initializes or reinitializes the .sovereign/ session continuity anchor.
# Usage: ctmv3-sovereign-init.sh [PROJECT_ROOT] [additional args...]
set -euo pipefail

ROOT="${1:-$PWD}"
shift || true

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found in PATH" >&2
    exit 1
fi

if ! python3 -c "import ctmv3" 2>/dev/null; then
    echo "ERROR: ctmv3 Python package not found." >&2
    echo "Install the core engine first. See cursor/README.md for install path." >&2
    exit 1
fi

exec python3 -m ctmv3 sovereign-init --project-root "$ROOT" "$@"
