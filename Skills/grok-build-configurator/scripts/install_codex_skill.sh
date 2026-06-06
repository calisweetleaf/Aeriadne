#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
DEST_ROOT=${CODEX_SKILLS_DIR:-"$HOME/.agents/skills"}
DEST="$DEST_ROOT/$(basename "$SKILL_DIR")"

mkdir -p "$DEST_ROOT"

if [ -e "$DEST" ]; then
  echo "Destination already exists: $DEST" >&2
  echo "Remove it first or set CODEX_SKILLS_DIR to another destination." >&2
  exit 1
fi

cp -R "$SKILL_DIR" "$DEST"

echo "Installed Codex skill to: $DEST"
echo "Restart Codex if it does not appear immediately."
