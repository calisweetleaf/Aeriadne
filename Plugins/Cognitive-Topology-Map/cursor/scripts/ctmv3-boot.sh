#!/usr/bin/env bash
# ctmv3-boot.sh -- Cursor-side wrapper for python3 -m ctmv3 boot
# Runs the BOOT_PROTOCOL.md discovery sequence and determines cold vs warm entry branch.
# Usage: ctmv3-boot.sh [PROJECT_ROOT] [additional args...]
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

exec python3 -m ctmv3 boot --project-root "$ROOT" "$@"
