#!/usr/bin/env python3
"""Non-blocking Codex notify relay for Sovereign staging.

Codex may invoke this on agent-turn-complete. The relay records a compact
JSONL event under SOVEREIGN_DATA_DIR and exits zero even if no receiver is up.
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

def main() -> int:
    data_dir = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    event = {"ts": time.time(), "event": "agent_turn_complete", "argv": sys.argv[1:]}
    try:
        with (data_dir / "notify_events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
