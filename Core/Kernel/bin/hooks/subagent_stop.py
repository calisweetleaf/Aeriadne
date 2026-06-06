#!/usr/bin/env python3
"""Sovereign SubagentStop — harvest final output to Q-table + insights."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, call_bb7, safe_main

def main() -> int:
    payload = read_payload()
    last_msg = payload.get("last_assistant_message","")
    if last_msg:
        try:
            call_bb7("bb7_lisan_distill", {
                "trajectory": [{"role": "assistant", "content": last_msg[:4000]}],
                "session_id": payload.get("session_id",""),
                "source_plane": "subagent_stop"
            }, timeout=3.0)
        except Exception:
            pass
    return 0

if __name__ == "__main__":
    sys.exit(safe_main("subagent_stop", main))
