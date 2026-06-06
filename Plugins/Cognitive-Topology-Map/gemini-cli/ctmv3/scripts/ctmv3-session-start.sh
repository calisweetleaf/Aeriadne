#!/usr/bin/env bash
# Auto-invoked at session start to populate the CTMv3 signal inventory in
# Gemini's context. Errors are suppressed so a missing ctmv3 install does not
# break the session.
#
# Environment variables:
#   CTMV3_PROJECT_ROOT  Override the project root (defaults to $PWD)

set -euo pipefail

python3 -m ctmv3 boot --json --project-root "${CTMV3_PROJECT_ROOT:-$PWD}" 2>/dev/null || true
