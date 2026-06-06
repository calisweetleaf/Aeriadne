#!/usr/bin/env python3
"""Sovereign SessionStart — inject precomputed_briefing.json from Muaddib daemon."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, write_additional_context, safe_main

def main() -> int:
    read_payload()  # consume stdin
    data_dir = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"))
    briefing_path = data_dir / "exoskeleton" / "precomputed_briefing.json"
    if not briefing_path.exists():
        return 0
    try:
        briefing = json.loads(briefing_path.read_text(encoding="utf-8"))
        summary = briefing.get("summary") or briefing.get("context") or ""
        if not summary:
            return 0
        write_additional_context(
            "<sovereign:briefing>\n"
            f"{summary}\n"
            "</sovereign:briefing>"
        )
    except Exception:
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(safe_main("session_start", main))
