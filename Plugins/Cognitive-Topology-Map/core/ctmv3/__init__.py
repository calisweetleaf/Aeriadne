"""
CTMv3 — Cognitive Topology Map v3 Workspace Activation System.

This is the top-level package. The execution engine lives at ctmv3.core.
Host adapters (Claude Code, Codex, opencode, Gemini CLI) invoke the engine
via `python -m ctmv3 <command>` which dispatches through ctmv3.__main__.

Public API surface (re-exported for convenience):
    discover, classify_branch, is_warm_valid, SignalInventory
    compute_fingerprint, verify_fingerprint
    sovereign_init, write_session_state, update_session_log
    activate_run
"""

from ctmv3.core import (
    __version__,
    __ctmv3_protocol__,
    SignalInventory,
    discover,
    classify_branch,
    is_warm_valid,
    compute_fingerprint,
    verify_fingerprint,
    sovereign_init,
    write_session_state,
    update_session_log,
    activate_run,
)

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
