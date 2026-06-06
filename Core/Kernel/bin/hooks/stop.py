#!/usr/bin/env python3
"""Sovereign Stop — final exo_reflect + memory_store + golden path update."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, call_bb7, safe_main

def main() -> int:
    read_payload()  # consume stdin
    # Final reflection pass — golden paths update internally if threshold met
    try:
        call_bb7("bb7_exo_reflect", {
            "plan_id": "hook::session_stop",
            "tools_used": ["Stop"],
            "success": True,
            "intent": "codex_stop_hook",
        }, timeout=5.0)
    except Exception:
        pass
    # Store session close event
    try:
        call_bb7("bb7_journal_capture_decision", {
            "decision": "session_close",
            "rationale": "sovereign stop hook fired",
            "constraints": "non-blocking Codex Stop hook",
            "success_criteria": "hook exits zero without polluting stdout",
        }, timeout=3.0)
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(safe_main("stop", main))
