#!/usr/bin/env bash
# ctmv3-chain.sh -- Cursor-side wrapper for python3 -m ctmv3 chain
# Walks the golden-path domino chain from an initial command.
# Usage: ctmv3-chain.sh [PROJECT_ROOT] [--initial COMMAND] [additional args...]
#
# Default initial command is 'boot'. The chain runs until terminal or MAX_CHAIN_DEPTH=5.
# Output is a JSON array of GoldenPathSignal envelopes.
#
# Examples:
#   ctmv3-chain.sh                         # chain from boot at $PWD
#   ctmv3-chain.sh /path/to/repo           # chain from boot at specified path
#   ctmv3-chain.sh /path/to/repo --initial warm  # chain from warm
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

exec python3 -m ctmv3 chain --project-root "$ROOT" "$@"
