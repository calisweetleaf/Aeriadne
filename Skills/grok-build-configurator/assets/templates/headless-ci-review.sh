#!/usr/bin/env bash
set -euo pipefail

: "${XAI_API_KEY:?Set XAI_API_KEY in your CI secret store}"

PROMPT=${1:-"Review this repository for likely bugs, regressions, and unsafe changes. Return concise findings."}

GROK_LOG_FILE=${GROK_LOG_FILE:-1} \
GROK_LOG_FILTER=${GROK_LOG_FILTER:-info} \
grok -p "$PROMPT" \
  --output-format json \
  --no-auto-update \
  --permission-mode dontAsk \
  --allow 'Read' \
  --allow 'Grep' \
  --allow 'Bash(git *)' \
  --allow 'Bash(gh *)' \
  --sandbox read-only
