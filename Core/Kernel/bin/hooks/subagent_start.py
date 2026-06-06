#!/usr/bin/env python3
"""Sovereign SubagentStart — inject per-subagent context."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, write_additional_context, call_bb7, safe_main

def main() -> int:
    payload = read_payload()
    try:
        task = payload.get("task") or payload.get("prompt") or "subagent_start"
        result = call_bb7("bb7_exo_briefing", {"intent": str(task), "max_recommendations": 5}, timeout=3.0)
        if result and result.get("briefing"):
            write_additional_context(
                "<sovereign:subagent-briefing>\n"
                f"{result['briefing'][:1024]}\n"
                "</sovereign:subagent-briefing>"
            )
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(safe_main("subagent_start", main))
