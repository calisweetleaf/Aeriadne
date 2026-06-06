#!/usr/bin/env python3
"""Sovereign PostCompact — capture what survived compaction to distillation."""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, safe_main

def main() -> int:
    payload = read_payload()
    data_dir = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"))
    try:
        event = {"ts": time.time(), "event": "post_compact",
                 "trigger": payload.get("trigger","auto"),
                 "session": payload.get("session_id","")}
        with (data_dir / "events.jsonl").open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(safe_main("post_compact", main))
