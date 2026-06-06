#!/usr/bin/env bash
# install.sh -- CTMv3 Codex adapter installer
# Copies the ctmv3 skill into ~/.codex/skills/ctmv3/ and prints merge
# instructions for config.toml and hooks.json. Does NOT auto-modify any
# Codex configuration files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="${SCRIPT_DIR}/skills/ctmv3"
CODEX_DIR="${HOME}/.codex"
SKILL_DEST="${CODEX_DIR}/skills/ctmv3"

# -----------------------------------------------------------------------
# Step 1: Verify ~/.codex/ exists
# -----------------------------------------------------------------------
if [ ! -d "${CODEX_DIR}" ]; then
    echo "ERROR: ${CODEX_DIR} does not exist." >&2
    echo "Codex CLI must be installed before running this installer." >&2
    echo "See: https://github.com/openai/codex" >&2
    exit 1
fi

echo "Found ~/.codex/ at ${CODEX_DIR}"

# -----------------------------------------------------------------------
# Step 2: Copy skill into ~/.codex/skills/ctmv3/
# -----------------------------------------------------------------------
if [ -d "${SKILL_DEST}" ]; then
    echo "WARNING: ${SKILL_DEST} already exists. Overwriting." >&2
fi

mkdir -p "${CODEX_DIR}/skills"
cp -r "${SKILL_SRC}" "${SKILL_DEST}"
echo "Copied skill to ${SKILL_DEST}"

# -----------------------------------------------------------------------
# Step 3: chmod +x all scripts
# -----------------------------------------------------------------------
find "${SKILL_DEST}/scripts" -name "*.sh" -exec chmod +x {} \;
echo "Set +x on all scripts in ${SKILL_DEST}/scripts/"

# -----------------------------------------------------------------------
# Step 4: Print config.toml merge instructions
# -----------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "MANUAL STEP REQUIRED: Merge into ~/.codex/config.toml"
echo "======================================================================"
echo "Open ~/.codex/config.toml and add the following lines:"
echo ""
cat "${SCRIPT_DIR}/config-fragments/config.toml.fragment"
echo ""
echo "======================================================================"

# -----------------------------------------------------------------------
# Step 5: Print hooks.json merge instructions
# -----------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "MANUAL STEP REQUIRED: Merge into ~/.codex/hooks.json"
echo "======================================================================"
echo "Open ~/.codex/hooks.json (create it if absent) and merge the"
echo "following JSON. If SessionStart already exists, add the hook entry"
echo "to the existing array rather than replacing it."
echo ""
cat "${SCRIPT_DIR}/config-fragments/hooks.json.fragment"
echo ""
echo "======================================================================"

# -----------------------------------------------------------------------
# Step 6: Verify python3 -c "import ctmv3" succeeds
# -----------------------------------------------------------------------
echo ""
echo "Checking ctmv3 Python package availability..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found in PATH." >&2
    echo "Install Python 3.8+ before using this skill." >&2
    exit 1
fi

if python3 -c "import ctmv3" 2>/dev/null; then
    echo "ctmv3 Python package: found"
else
    echo "WARNING: python3 -c \"import ctmv3\" failed." >&2
    echo "The CTMv3 core engine is not installed or not on PYTHONPATH." >&2
    echo "" >&2
    echo "To install the core engine, run one of:" >&2
    echo "  pip install -e /agent/workspace/ctmv3-plugin/  (development install)" >&2
    echo "  pip install ctmv3  (when published to PyPI)" >&2
    echo "" >&2
    echo "The skill files are installed, but commands will fail until the" >&2
    echo "core engine is available." >&2
fi

echo ""
echo "Installation complete."
echo "Skill installed at: ${SKILL_DEST}"
echo ""
echo "Test with:"
echo "  bash ${SKILL_DEST}/scripts/ctmv3-status.sh"
