#!/usr/bin/env python3
"""Sovereign UserPromptSubmit — bb7_lisan_intend + bb7_journal_surface_relevant."""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, write_additional_context, call_bb7, safe_main

def main() -> int:
    payload = read_payload()
    prompt = payload.get("prompt") or payload.get("user_prompt") or ""
    if not prompt:
        return 0

    context_parts = []

    # 1. lisan intent classification
    try:
        result = call_bb7("bb7_lisan_intend", {"user_message": prompt, "verbosity": "minimal"}, timeout=3.0)
        if result and result.get("golden_path_match"):
            gp = result["golden_path_match"]
            if isinstance(gp, dict):
                gp_text = f"{gp.get('name','?')} (score={gp.get('score',0):.2f})"
            else:
                gp_text = str(gp)
            context_parts.append(
                f"<sovereign:lisan-intent>\n"
                f"Golden path match: {gp_text}\n"
                f"</sovereign:lisan-intent>"
            )
    except Exception:
        pass

    # 2. surface relevant journal entries
    try:
        result = call_bb7("bb7_journal_surface_relevant", {"context_text": prompt[:200], "max_results": 3}, timeout=2.0)
        if result and result.get("relevant_entries"):
            entries = result["relevant_entries"][:3]
            lines = [f"  - {e.get('summary', str(e))}" for e in entries]
            context_parts.append(
                "<sovereign:journal-context>\n"
                + "\n".join(lines) +
                "\n</sovereign:journal-context>"
            )
    except Exception:
        pass

    if context_parts:
        write_additional_context("\n".join(context_parts))
    return 0

if __name__ == "__main__":
    sys.exit(safe_main("user_prompt_submit", main))
