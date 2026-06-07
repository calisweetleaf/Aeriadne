#!/usr/bin/env bash
# Aeriadne Gemini-CLI adapter installer
#
# Usage:
#   bash install.sh            # install to ~/.gemini/extensions/aeriadne/
#   bash install.sh uninstall  # remove extension
#
# What this installs:
#   ~/.gemini/extensions/aeriadne/
#   ├── gemini-extension.json
#   ├── GEMINI.md
#   ├── commands/aeriadne/*.toml   (5 slash commands)
#   └── skills/
#       ├── cpf/SKILL.md
#       └── mop/SKILL.md
#
# Canonical source:
#   /home/daeron/Repositories/Somnus-Intellligence-Stack/Plugins/Aeriadne
#
# After install: restart Gemini-CLI and run /extensions list to confirm.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOME/.gemini/extensions/aeriadne"
ACTION="${1:-install}"

if [ "$ACTION" = "uninstall" ]; then
    echo "Removing $TARGET ..."
    rm -rf "$TARGET"
    echo "Aeriadne Gemini-CLI extension uninstalled."
    echo "Restart Gemini-CLI to apply."
    exit 0
fi

echo "Aeriadne Gemini-CLI adapter install"
echo "  target : $TARGET"
echo "  source : $SCRIPT_DIR/aeriadne"
echo ""

# Remove stale install before copy
if [ -d "$TARGET" ]; then
    echo "  Removing existing installation at $TARGET"
    rm -rf "$TARGET"
fi

# Copy extension tree
mkdir -p "$TARGET"
cp -r "$SCRIPT_DIR/aeriadne/." "$TARGET/"

# Copy formatter module into hooks/ so the hook import path resolves
FORMATTER_SRC="$SCRIPT_DIR/../tool_output_formatter.py"
if [ -f "$FORMATTER_SRC" ]; then
    cp "$FORMATTER_SRC" "$TARGET/hooks/tool_output_formatter.py"
    echo "  -> hooks/tool_output_formatter.py (formatter module)"
else
    echo "  WARNING: tool_output_formatter.py not found at $FORMATTER_SRC"
    echo "           after_tool_formatter.py hook will fail to import it."
fi


echo "  -> gemini-extension.json"
echo "  -> GEMINI.md"
echo "  -> commands/aeriadne/*.toml"
echo "  -> skills/cpf/SKILL.md"
echo "  -> skills/mop/SKILL.md"

# Verify
if [ ! -f "$TARGET/gemini-extension.json" ]; then
    echo "ERROR: gemini-extension.json not found after copy." >&2
    exit 1
fi

echo ""
echo "Installation complete."
echo ""
echo "Next steps:"
echo "  1. Restart Gemini-CLI"
echo "  2. Run: /extensions list"
echo "     Confirm 'aeriadne' appears in the list."
echo "  3. Run: /aeriadne:cpf"
echo "     Should invoke the Constitutional Prompt Framework."
echo ""
echo "To update: pull the latest source and re-run install.sh"
echo "To remove:  bash install.sh uninstall"
