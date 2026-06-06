#!/usr/bin/env bash
# CTMv3 Gemini CLI extension installer.
# Copies ctmv3/ into ~/.gemini/extensions/ctmv3/ and enables the extension.
#
# Usage:
#   bash install.sh
#
# After install, restart Gemini CLI for the extension to take effect.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/ctmv3"
DEST_DIR="${HOME}/.gemini/extensions/ctmv3"

# Validate source exists
if [ ! -d "${SOURCE_DIR}" ]; then
  echo "ERROR: Source directory not found: ${SOURCE_DIR}"
  echo "Run this installer from the gemini-cli/ directory of the ctmv3-plugin repo."
  exit 1
fi

# Create extensions directory if absent
mkdir -p "${HOME}/.gemini/extensions"

# Remove stale install if present
if [ -d "${DEST_DIR}" ]; then
  echo "Removing existing installation at ${DEST_DIR}"
  rm -rf "${DEST_DIR}"
fi

# Copy extension
echo "Installing ctmv3 extension to ${DEST_DIR}"
cp -r "${SOURCE_DIR}" "${DEST_DIR}"

# Make scripts executable
chmod +x "${DEST_DIR}/scripts/ctmv3-wrap.sh"
chmod +x "${DEST_DIR}/scripts/ctmv3-session-start.sh"

echo ""
echo "Extension installed at: ${DEST_DIR}"
echo ""
echo "Files installed:"
find "${DEST_DIR}" -type f | sort | sed "s|${DEST_DIR}|  ctmv3|"
echo ""

# Check that python3 -m ctmv3 is reachable
if python3 -m ctmv3 --help >/dev/null 2>&1; then
  echo "python3 -m ctmv3: found"
else
  echo "WARNING: python3 -m ctmv3 not found."
  echo "Install the CTMv3 engine before using the extension:"
  echo "  pip install ctmv3   (or install from /agent/workspace/ctmv3-plugin/core/)"
  echo ""
fi

echo "Next steps:"
echo "  1. Restart Gemini CLI (extensions load on startup)."
echo "  2. Verify the extension is active: /extensions list"
echo "  3. To disable the extension:"
echo "       gemini extensions disable ctmv3"
echo "  4. To enable in a specific workspace only:"
echo "       gemini extensions disable ctmv3"
echo "       gemini extensions enable ctmv3 --scope workspace"
echo ""
echo "Slash commands available after restart:"
echo "  /ctmv3:boot              discover signal inventory"
echo "  /ctmv3:activate          full cold-start activation"
echo "  /ctmv3:warm              warm-start diff check"
echo "  /ctmv3:architecture-map  build/update ARCHITECTURE_MAP.md"
echo "  /ctmv3:sovereign-init    initialize .sovereign/"
echo "  /ctmv3:dot-init          scaffold .claude/, .codex/, .github/"
echo "  /ctmv3:session-close     close session cleanly"
echo "  /ctmv3:status            print activation status"
