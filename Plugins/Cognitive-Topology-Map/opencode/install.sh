#!/usr/bin/env bash
# CTMv3 opencode adapter installer
#
# Usage:
#   bash install.sh            # project scope: installs to .opencode/ in $PWD
#   bash install.sh global     # global scope: installs to ~/.config/opencode/
#
# The adapter consists of:
#   - agent/ctmv3-architect.md      -> <target>/agents/
#   - command/ctmv3-*.md            -> <target>/commands/
#   - plugin/ctmv3.ts               -> <target>/plugins/
#
# Note: opencode uses 'agents/' and 'commands/' and 'plugins/' (plural) as the
# directory names under both .opencode/ and ~/.config/opencode/.
# See: https://opencode.ai/docs/agents, /docs/commands, /docs/plugins

set -euo pipefail

SCOPE="${1:-project}"

if [ "$SCOPE" = "global" ]; then
  TARGET="$HOME/.config/opencode"
else
  TARGET="$PWD/.opencode"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing CTMv3 opencode adapter to: $TARGET (scope: $SCOPE)"

# Create target directories
mkdir -p "$TARGET/agents"
mkdir -p "$TARGET/commands"
mkdir -p "$TARGET/plugins"

# Install agent
echo "  -> agents/ctmv3-architect.md"
cp "$SCRIPT_DIR/agent/ctmv3-architect.md" "$TARGET/agents/"

# Install commands
echo "  -> commands/ctmv3-*.md"
for cmd_file in "$SCRIPT_DIR/command"/ctmv3-*.md; do
  filename="$(basename "$cmd_file")"
  echo "     $filename"
  cp "$cmd_file" "$TARGET/commands/"
done

# Install plugin
echo "  -> plugins/ctmv3.ts"
cp "$SCRIPT_DIR/plugin/ctmv3.ts" "$TARGET/plugins/"

echo ""
echo "Installation complete."
echo ""
echo "Verify opencode recognizes the adapter by running opencode and checking:"
echo "  - /ctmv3-boot is available as a command"
echo "  - @ctmv3-architect is available as a subagent"
echo ""
echo "Verify Python engine is installed:"
if python3 -m ctmv3 version 2>/dev/null; then
  echo "  ctmv3 engine: OK"
else
  echo "  ctmv3 engine: NOT FOUND"
  echo "  Install the engine before using CTMv3 commands."
  echo "  See: /agent/workspace/ctmv3-plugin/core/ for the Python engine source."
fi
