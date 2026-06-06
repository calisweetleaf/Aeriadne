#!/usr/bin/env bash
# CTMv3 Plugin Full Validation
# Runs unit tests, smoke test, and config syntax checks.
# Exit non-zero on any failure.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PLUGIN_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="$PLUGIN_ROOT/core:${PYTHONPATH:-}"

echo "[run-all] CTMv3 Plugin Validation Suite"
echo "[run-all] Plugin root: $PLUGIN_ROOT"
echo "[run-all] Python:      $($PYTHON_BIN --version)"
echo

# --- 1. Unit tests ---
echo "[run-all] === 1. Engine unit tests ==="
$PYTHON_BIN -m unittest discover -s core/ctmv3/tests -v 2>&1 | tail -5
echo

# --- 2. Smoke test ---
echo "[run-all] === 2. End-to-end smoke test ==="
bash tests/smoke.sh 2>&1 | tail -10
echo

# --- 3. JSON syntax ---
echo "[run-all] === 3. JSON syntax validation ==="
for f in \
    claude-code/.claude-plugin/plugin.json \
    claude-code/settings.json \
    claude-code/hooks/hooks.json \
    codex/config-fragments/hooks.json.fragment \
    gemini-cli/ctmv3/gemini-extension.json
do
    $PYTHON_BIN -c "import json; json.load(open('$f'))" && echo "  OK: $f"
done
echo

# --- 4. Bash script syntax ---
echo "[run-all] === 4. Bash script syntax ==="
SCRIPT_COUNT=0
for s in $(find . -type f -name "*.sh" -not -path "*/__pycache__*"); do
    bash -n "$s"
    SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
done
echo "  $SCRIPT_COUNT bash scripts: all syntactically valid"
echo

# --- 5. TOML structural check ---
echo "[run-all] === 5. Gemini CLI TOML command files ==="
TOML_COUNT=0
for f in $(find gemini-cli -name "*.toml"); do
    grep -q 'description = ' "$f" && grep -q 'prompt = ' "$f" || { echo "FAIL: $f"; exit 1; }
    TOML_COUNT=$((TOML_COUNT + 1))
done
echo "  $TOML_COUNT TOML command files: all have description and prompt"
echo

# --- 6. File inventory ---
echo "[run-all] === 6. Plugin inventory ==="
echo "  Total files:        $(find . -type f -not -path '*/__pycache__*' -not -name '*.pyc' | wc -l)"
echo "  Python engine LOC:  $(find core/ctmv3 -name '*.py' -not -path '*/__pycache__*' | xargs wc -l | tail -1 | awk '{print $1}')"
echo "  Doc files:          $(find docs -type f | wc -l)"
echo "  Adapter LOC total:  $(find claude-code codex gemini-cli opencode -type f -not -name '*.pyc' | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')"
echo

echo "[run-all] ALL CHECKS PASSED"
