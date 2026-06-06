#!/usr/bin/env python3
"""
Sovereign Context Hook — UserPromptSubmit bridge between Somnus-MCP state and Claude Code context.

Runs on every user prompt. Reads MCP state files directly (no RPC).
Returns systemMessage with enriched context, injected by Claude Code before processing.
This IS the golden path auto-trigger — the environment enriches itself.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"))


def _read_json(path: Path) -> Optional[Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _read_jsonl_tail(path: Path, n: int = 5) -> List[Dict]:
    """Read last n lines from a JSONL file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        results = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(results) >= n:
                break
        return list(reversed(results))
    except Exception:
        return []


def get_recent_memories(n: int = 5) -> List[Dict]:
    """Pull recent memories from memory_store.json sorted by timestamp."""
    store = _read_json(DATA_DIR / "memory_store.json")
    if not store or not isinstance(store, dict):
        return []

    entries = store.get("memories", store) if "memories" in store else store
    if not isinstance(entries, dict):
        return []

    # Sort by timestamp descending
    items = []
    for key, val in entries.items():
        if isinstance(val, dict):
            val["_key"] = key
            items.append(val)

    items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return items[:n]


def get_active_session() -> Optional[Dict]:
    """Get the most recent active session."""
    sessions = _read_jsonl_tail(DATA_DIR / "events.jsonl", n=20)
    for event in reversed(sessions):
        if event.get("event_type") == "session_start":
            return {
                "session_id": event.get("payload", {}).get("session_id") or event.get("session_id"),
                "tool_count": event.get("payload", {}).get("tool_count"),
                "timestamp": event.get("timestamp"),
            }
    return None


def get_golden_path_hint() -> Optional[str]:
    """Read latest golden path plan if available."""
    plan_file = DATA_DIR / "active_plan.json"
    plan = _read_json(plan_file)
    if plan:
        intent = plan.get("intent", "")
        steps = plan.get("steps", [])
        if intent:
            step_summary = ", ".join(s.get("tool", str(s)) for s in steps[:4]) if steps else "none"
            return f"Active plan: '{intent}' → [{step_summary}]"
    return None


def get_lisan_context() -> Optional[str]:
    """Read latest lisan/distillation context."""
    for fname in ["lisan_context.json", "distillation_state.json", "session_momentum.json"]:
        data = _read_json(DATA_DIR / fname)
        if data:
            momentum = data.get("momentum") or data.get("current_tools") or data.get("recent_tools")
            if momentum:
                if isinstance(momentum, list):
                    return f"Session momentum: {', '.join(str(m) for m in momentum[:5])}"
                return f"Session context: {str(momentum)[:120]}"
    return None


def build_system_message(input_data: Dict) -> Optional[str]:
    """Build enriched system context from MCP state."""
    parts = []

    # Session context
    session = get_active_session()
    if session:
        session_id = session.get("session_id", "?")
        parts.append(f"**SovereignMCP Session**: `{session_id}` | {session.get('tool_count', '?')} tools loaded")

    # Recent memories
    memories = get_recent_memories(3)
    if memories:
        mem_lines = []
        for m in memories:
            key = m.get("_key", "?")
            content = m.get("content") or m.get("value") or ""
            if isinstance(content, dict):
                content = json.dumps(content)[:100]
            elif isinstance(content, str):
                content = content[:120]
            imp = m.get("importance", m.get("score", "?"))
            mem_lines.append(f"  • `{key}` (imp={imp}): {content}")
        if mem_lines:
            parts.append("**Recent MCP Memories**:\n" + "\n".join(mem_lines))

    # Golden path hint
    gp = get_golden_path_hint()
    if gp:
        parts.append(f"**Golden Path**: {gp}")

    # Lisan context
    lisan = get_lisan_context()
    if lisan:
        parts.append(f"**Lisan**: {lisan}")

    if not parts:
        return None

    return "<!-- SovereignMCP Auto-Context -->\n" + "\n\n".join(parts)


def main():
    """Hook entrypoint — reads stdin JSON, writes systemMessage to stdout."""
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        input_data = {}

    try:
        msg = build_system_message(input_data)
        if msg:
            # Write full enriched state to a dedicated small "tail" file.
            # This is the volatility tail — appended strictly after the static foundation and history.
            # The main session prompt should treat this as low-priority trailing context (read explicitly when needed).
            tail_path = DATA_DIR / "current_volatile_tail.md"
            with open(tail_path, "w", encoding="utf-8") as tf:
                tf.write(f"# Sovereign Volatile Tail (updated {time.strftime('%Y-%m-%d %H:%M:%S')})\n\n")
                tf.write(msg)
                tf.write("\n\n--- Raw event data logged to intelligent_tool_outputs.log for distillation ---\n")

            # Append to the persistent log for distillation / RL / later recall (raw + cleaned).
            try:
                log_path = DATA_DIR / "intelligent_tool_outputs.log"
                with open(log_path, "a", encoding="utf-8") as lf:
                    lf.write(f"[UserPromptSubmit context] {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    lf.write(msg + "\n\n")
            except Exception:
                pass

            # Emit *minimal* systemMessage / output to the host.
            # Do not carry the full dynamic memories/golden-path/Lisan in the per-turn injection.
            # This prevents cache invalidation of the large static foundation (AGENTS + base system).
            # The full state lives in the tail file at the "bottom".
            small_injection = "<!-- Sovereign volatile context updated. Full state in data/current_volatile_tail.md (read on demand for memories, golden paths, Lisan, session). Raw in intelligent_tool_outputs.log. -->"
            print(json.dumps({"systemMessage": small_injection}))

            # Still print the full for visibility in hook annotations / scrollback when desired.
            print("\n" + "=" * 60)
            print(small_injection)
            print("Full tail written to data/current_volatile_tail.md")
            print("=" * 60 + "\n")
        else:
            print(json.dumps({}))
    except Exception as e:
        # Never crash — just pass through silently
        print(json.dumps({}))

    sys.exit(0)


if __name__ == "__main__":
    main()
