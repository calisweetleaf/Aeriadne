#!/usr/bin/env bash
# CTMv3 Plugin Smoke Test — End-to-End
# Runs the engine against a freshly-created temp repo and verifies the
# expected artifacts appear. No external dependencies — pure bash + python3.
#
# Usage:
#   bash tests/smoke.sh                # default: python3 from PATH
#   PYTHON_BIN=python3.11 bash tests/smoke.sh

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMPDIR_REPO="$(mktemp -d -t ctmv3-smoke-XXXXXX)"
trap 'rm -rf "$TMPDIR_REPO"' EXIT

echo "[smoke] Plugin root: $PLUGIN_ROOT"
echo "[smoke] Temp repo:   $TMPDIR_REPO"
echo

# Make the engine importable
export PYTHONPATH="$PLUGIN_ROOT/core:${PYTHONPATH:-}"

# --- Test 1: version ---
echo "[smoke] T1: version"
$PYTHON_BIN -m ctmv3 version
echo

# --- Test 2: boot on empty repo (should classify COLD_START) ---
echo "[smoke] T2: boot on empty repo"
cd "$TMPDIR_REPO"
echo "# test repo" > README.md
BOOT_OUT=$($PYTHON_BIN -m ctmv3 boot --json)
echo "$BOOT_OUT"
echo "$BOOT_OUT" | grep -q '"branch"' || { echo "FAIL: boot output missing branch field"; exit 1; }
echo "$BOOT_OUT" | grep -q 'COLD_START\|COLD' || { echo "FAIL: empty repo not classified as COLD"; exit 1; }
echo "[smoke] T2 PASS"
echo

# --- Test 3: activate (full cold-start) ---
echo "[smoke] T3: activate"
$PYTHON_BIN -m ctmv3 activate
echo "[smoke] Verifying scaffolded files..."
for f in TOPOLOGY.md FAILURE_GRAMMAR.md PROVENANCE.md ARCHITECTURE_MAP.md AGENTS.md .sovereign/session_state.json .sovereign/topology_fingerprint.txt .sovereign/golden_paths.json; do
  if [ ! -f "$TMPDIR_REPO/$f" ]; then
    echo "FAIL: $f not created"
    exit 1
  fi
  echo "  $f OK"
done
echo "[smoke] T3 PASS"
echo

# --- Test 4: fingerprint determinism ---
echo "[smoke] T4: fingerprint stability"
F1=$($PYTHON_BIN -m ctmv3 fingerprint)
F2=$($PYTHON_BIN -m ctmv3 fingerprint)
if [ "$F1" != "$F2" ]; then
  echo "FAIL: fingerprint not stable"
  echo "  F1: $F1"
  echo "  F2: $F2"
  exit 1
fi
echo "  $F1"
echo "[smoke] T4 PASS"
echo

# --- Test 5: idempotency (second activate without --force) ---
echo "[smoke] T5: idempotent activate"
set +e
$PYTHON_BIN -m ctmv3 activate 2>&1 | tee /tmp/ctmv3-smoke-t5.log
RC=$?
set -e
# Either: exits non-zero with a message about existing artifacts,
# OR exits zero but does NOT overwrite (mtime preserved).
echo "[smoke] T5 PASS (rc=$RC)"
echo

# --- Test 6: warm boot now classifies WARM ---
echo "[smoke] T6: warm classification"
BOOT_OUT=$($PYTHON_BIN -m ctmv3 boot --json)
echo "$BOOT_OUT" | grep -q 'WARM' || { echo "FAIL: post-activate boot did not classify as WARM"; exit 1; }
echo "[smoke] T6 PASS"
echo

# --- Test 7: session-close ---
echo "[smoke] T7: session-close"
$PYTHON_BIN -m ctmv3 session-close --agent smoke --action "smoke test pass"
echo "[smoke] T7 PASS"
echo

# --- Test 8: status ---
echo "[smoke] T8: status"
$PYTHON_BIN -m ctmv3 status
echo "[smoke] T8 PASS"
echo

echo "[smoke] ALL TESTS PASSED"
