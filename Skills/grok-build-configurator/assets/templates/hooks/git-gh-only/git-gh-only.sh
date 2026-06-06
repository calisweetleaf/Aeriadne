#!/bin/sh
# Allow only shell commands whose first word is git or gh.
# Requires jq. Returns explicit deny on parse issues to avoid accidental fail-open behavior.

set -eu

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.toolInput.command // empty' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

if [ -z "$CMD" ]; then
  echo '{"decision":"deny","reason":"Empty command is not allowed"}'
  exit 2
fi

FIRST_WORD=$(printf '%s' "$CMD" | awk '{print $1}')

case "$FIRST_WORD" in
  git|gh)
    echo '{"decision":"allow"}'
    exit 0
    ;;
  *)
    SAFE_REASON=$(printf 'Only git and gh commands are permitted. Blocked first word: %s' "$FIRST_WORD" | sed 's/"/\\"/g')
    printf '{"decision":"deny","reason":"%s"}\n' "$SAFE_REASON"
    exit 2
    ;;
esac
