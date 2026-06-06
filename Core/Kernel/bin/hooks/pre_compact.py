#!/usr/bin/env python3
"""Sovereign PreCompact — persist key facts to memory before Codex compacts."""
from __future__ import annotations
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, write_additional_context, call_bb7, safe_main

def main() -> int:
    payload = read_payload()
    trigger = payload.get("trigger", "auto")
    # Ask lisan to recall current session state before it's lost
    try:
        result = call_bb7("bb7_lisan_recall", {"context": "compact_pre_trigger"}, timeout=5.0)
        summary = ""
        if result:
            summary = result.get("summary") or result.get("context_blob") or ""
        if summary:
            call_bb7("bb7_memory_store", {
                "key": f"compact_snapshot::{payload.get('session_id','unknown')}::{int(time.time())}",
                "value": summary,
                "category": "compact_snapshot",
                "importance": 0.7,
                "tags": [f"compact:{trigger}"],
            }, timeout=3.0)
            write_additional_context(
                "<sovereign:pre-compact-summary>\n"
                f"{summary}\n"
                "</sovereign:pre-compact-summary>"
            )
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(safe_main("pre_compact", main))
