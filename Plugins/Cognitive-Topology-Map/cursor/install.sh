#!/usr/bin/env bash
# CTMv3 Cursor adapter installer
#
# Usage:
#   bash install.sh            # project scope: installs to .cursor/ in $PWD
#   bash install.sh global     # global scope: installs to ~/.cursor/
#
# The adapter installs:
#   .cursor/rules/ctmv3.mdc       -- Cursor Rules: CTMv3 cognitive doctrine
#   .cursor/commands/ctmv3-*.md   -- Cursor Commands: one per CTMv3 subcommand
#   .cursor/scripts/ctmv3/        -- Bash wrappers that shell out to python3 -m ctmv3
#
# Idempotent: running the installer twice overwrites existing files but does not
# corrupt any non-CTMv3 .cursor/ content.
#
# After installing, restart Cursor for rules and commands to take effect.

set -euo pipefail

SCOPE="${1:-project}"

if [ "$SCOPE" = "global" ]; then
    TARGET="$HOME/.cursor"
else
    TARGET="$PWD/.cursor"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_SRC="${SCRIPT_DIR}/.cursor"

echo "Installing CTMv3 Cursor adapter to: $TARGET (scope: $SCOPE)"

# -----------------------------------------------------------------------
# Create target directories
# -----------------------------------------------------------------------
mkdir -p "$TARGET/rules"
mkdir -p "$TARGET/commands"
mkdir -p "$TARGET/scripts/ctmv3"

# -----------------------------------------------------------------------
# Install Cursor Rule
# -----------------------------------------------------------------------
echo "  -> rules/ctmv3.mdc"
cp "$CURSOR_SRC/rules/ctmv3.mdc" "$TARGET/rules/"

# -----------------------------------------------------------------------
# Install Cursor Commands
# -----------------------------------------------------------------------
echo "  -> commands/ctmv3-*.md"
for cmd_file in "$CURSOR_SRC/commands"/ctmv3-*.md; do
    filename="$(basename "$cmd_file")"
    echo "     $filename"
    cp "$cmd_file" "$TARGET/commands/"
done

# -----------------------------------------------------------------------
# Install bash wrappers
# -----------------------------------------------------------------------
echo "  -> scripts/ctmv3/"
for script_file in "$SCRIPT_DIR/scripts"/ctmv3-*.sh; do
    filename="$(basename "$script_file")"
    echo "     $filename"
    cp "$script_file" "$TARGET/scripts/ctmv3/"
    chmod +x "$TARGET/scripts/ctmv3/$filename"
done

echo ""
echo "Installation complete."
echo ""
echo "Restart Cursor for rules and commands to take effect."
echo ""
echo "Verify Python engine is installed:"
if python3 -m ctmv3 version 2>/dev/null; then
    echo "  ctmv3 engine: OK"
else
    echo "  ctmv3 engine: NOT FOUND"
    echo "  Install the engine before using CTMv3 commands."
    echo "  pip install -e /path/to/ctmv3-plugin/core/"
fi
echo ""
echo "Test with:"
echo "  bash $TARGET/scripts/ctmv3/ctmv3-status.sh"
