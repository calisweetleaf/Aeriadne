#!/usr/bin/env bash
# ctmv3-session-close.sh -- Codex-side wrapper for python3 -m ctmv3 session-close
# Closes the current session cleanly: updates PROVENANCE.md Session Log and
# session_state.json. Every CTM-active session must close cleanly.
# Usage: ctmv3-session-close.sh [PROJECT_ROOT] [additional args...]
set -euo pipefail

ROOT="${1:-$PWD}"
shift || true

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found in PATH" >&2
    exit 1
fi

if ! python3 -c "import ctmv3" 2>/dev/null; then
    echo "ERROR: ctmv3 Python package not found." >&2
    echo "Install the core engine first. See the plugin README.md for install path." >&2
    exit 1
fi

exec python3 -m ctmv3 session-close --project-root "$ROOT" "$@"
