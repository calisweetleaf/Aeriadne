#!/usr/bin/env bash
# Generic wrapper invoked by Gemini CLI extension to call CTMv3 engine.
# Usage: ctmv3-wrap.sh <subcommand> [args...]
#
# Environment variables:
#   CTMV3_PROJECT_ROOT  Override the project root (defaults to $PWD)
#
# The wrapper forwards all arguments to python3 -m ctmv3 with --project-root
# set to CTMV3_PROJECT_ROOT or the current working directory.

set -euo pipefail

CMD="${1:?Usage: ctmv3-wrap.sh <subcommand> [args...]}"
shift
ROOT="${CTMV3_PROJECT_ROOT:-$PWD}"

exec python3 -m ctmv3 "$CMD" --project-root "$ROOT" "$@"
