"""
CTMv3 Core Engine — Workspace Activation System
================================================
Provenance: CTMv3 Engine v1.2.0 — 2026-05-24
Author: Forge (activation engine builder)
Purpose: Python activation engine for CTMv3 plugin. Entry point for all host
         adapter integrations (Claude Code, Codex, opencode, Gemini CLI).

This package implements the BOOT_PROTOCOL.md state machine, artifact scaffolding,
fingerprint management, and session close protocol described in the CTMv3 source docs.

Public API surface:
    boot.discover()          -- run discovery sequence, return SignalInventory
    boot.classify_branch()   -- classify as COLD_START / WARM_START / PARTIAL
    activate.run()           -- full cold-start Phase 0-5 build
    fingerprint.compute()    -- SHA-256 of TOPOLOGY.md + ARCHITECTURE_MAP.md
    fingerprint.verify()     -- check stored fingerprint against current
    sovereign.init()         -- scaffold .sovereign/ directory
    sovereign.write_session_state()  -- update session_state.json
    sovereign.update_session_log()   -- append to PROVENANCE.md Session Log

Changes in v1.1.0:
    - Structured logging added to all core modules (stdlib logging).
    - Atomic file writes throughout (write to .tmp then os.replace).
    - Input validation at all public boundaries.
    - SHA-256 computation is now streaming (8 KiB chunks).
    - boot.discover() enforces MAX_SCAN_DEPTH and MAX_FILE_COUNT bounds.
    - Fixed status-logic bug in _scaffold_protected and _write_if_absent.
    - _detect_language falls back to "unknown" instead of returning a TODO string.
    - sovereign.write_session_state / update_session_log validate agent/action args.
"""

__version__ = "1.2.0"
__ctmv3_protocol__ = "3.0"

from pathlib import Path

# Re-export the most commonly used public symbols so adapter code can do:
#   from ctmv3.core import discover, classify_branch
from ctmv3.core.boot import discover, classify_branch, is_warm_valid, SignalInventory
from ctmv3.core.fingerprint import compute as compute_fingerprint
from ctmv3.core.fingerprint import verify as verify_fingerprint
from ctmv3.core.sovereign import init as sovereign_init
from ctmv3.core.sovereign import write_session_state, update_session_log
from ctmv3.core.activate import run as activate_run

__all__ = [
    "__version__",
    "__ctmv3_protocol__",
    "SignalInventory",
    "discover",
    "classify_branch",
    "is_warm_valid",
    "compute_fingerprint",
    "verify_fingerprint",
    "sovereign_init",
    "write_session_state",
    "update_session_log",
    "activate_run",
]
