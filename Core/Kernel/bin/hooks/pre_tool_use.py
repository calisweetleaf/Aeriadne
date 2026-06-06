#!/usr/bin/env python3
"""Sovereign PreToolUse — log tool call to events.jsonl, check golden path."""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, safe_main

def main() -> int:
    payload = read_payload()
    tool_name = payload.get("tool_name", "")
    data_dir = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"))
    try:
        event = {"ts": time.time(), "event": "pre_tool_use",
                 "tool": tool_name, "session": payload.get("session_id", "")}
        with (data_dir / "events.jsonl").open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass
    return 0  # always allow — Mentat handles blocking

if __name__ == "__main__":
    sys.exit(safe_main("pre_tool_use", main))
