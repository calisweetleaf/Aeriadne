#!/usr/bin/env python3
"""
Intelligent Output Hook — PostToolUse layered enrichment for Claude Code.

Runs after each tool call. Reads PostToolUse JSON from stdin.
Cleans and structures tool output FOR Claude Code's benefit.
Raw data in the distillation pipeline is never modified — this hook reads only.
Codex uses jsonrpc2 stdio directly and does not go through this hook.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"))
TWIN_DIR = DATA_DIR / "digital_twin"

_PRIMARY_KEYS = ("result", "data", "output", "response", "content", "value", "results")
_NOISE_KEYS = ("_telemetry", "_raw", "_debug", "trace", "meta", "metadata")
_MAX_STR = 3000
_MAX_LIST = 10


def _read_json(path: Path) -> Optional[Any]:
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _extract_primary(payload: Dict) -> Tuple[Any, bool]:
    """Pull the high-signal payload key if present, return (value, was_extracted)."""
    for k in _PRIMARY_KEYS:
        if k in payload:
            return payload[k], True
    return payload, False


def clean_output(output: Any, depth: int = 0) -> Any:
    """Semantically clean output for Claude Code consumption — surface signal, suppress noise."""
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
            return clean_output(parsed, depth)
        except json.JSONDecodeError:
            if len(output) > _MAX_STR:
                return output[:_MAX_STR // 2] + f"\n…[{len(output) - _MAX_STR} chars omitted]…\n" + output[-(_MAX_STR // 2):]
            return output

    elif isinstance(output, dict):
        # At top level, try to extract primary payload key
        if depth == 0:
            primary, extracted = _extract_primary(output)
            if extracted:
                cleaned_primary = clean_output(primary, depth + 1)
                # Keep status/error fields alongside
                extras = {k: output[k] for k in ("status", "error", "code", "success", "session_id")
                          if k in output and k not in _PRIMARY_KEYS}
                if extras:
                    if isinstance(cleaned_primary, dict):
                        return {**extras, **cleaned_primary}
                    return {"_status": extras, "payload": cleaned_primary}
                return cleaned_primary

        cleaned = {}
        for k, v in output.items():
            if k in _NOISE_KEYS:
                cleaned[k] = f"[omitted — {len(str(v))} chars]"
                continue
            cleaned[k] = clean_output(v, depth + 1)
        return cleaned

    elif isinstance(output, list):
        if len(output) > _MAX_LIST:
            cleaned = [clean_output(item, depth + 1) for item in output[:_MAX_LIST]]
            cleaned.append(f"…[{len(output) - _MAX_LIST} more items]")
            return cleaned
        return [clean_output(item, depth + 1) for item in output]

    return output


def get_muaddib_context(tool_name: str) -> Optional[str]:
    qtable = _read_json(TWIN_DIR / "qtable.json")
    if not qtable or not isinstance(qtable, dict):
        return None

    high_reward = []
    for state, actions in qtable.items():
        if isinstance(actions, dict) and tool_name in actions and actions[tool_name] > 0.5:
            high_reward.append(actions[tool_name])

    if not high_reward:
        return None

    best_q = round(max(high_reward), 3)
    return f"Muad'dib Q={best_q} ({len(high_reward)} high-reward states)"


def get_session_momentum(tool_name: str) -> Optional[str]:
    for fname in ("session_momentum.json", "lisan_context.json", "distillation_state.json"):
        data = _read_json(DATA_DIR / fname)
        if not data:
            continue
        momentum = (data.get("momentum") or data.get("current_tools")
                    or data.get("recent_tools") or data.get("trajectory"))
        if momentum:
            if isinstance(momentum, list):
                recent = [str(m) for m in momentum[-3:]]
                return f"Trajectory: {' → '.join(recent)}"
            return f"Session: {str(momentum)[:80]}"
    return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        input_data = {}

    tool_name = input_data.get("tool_name", "unknown")
    raw_output = input_data.get("output") or input_data.get("result") or input_data

    try:
        cleaned = clean_output(raw_output)
        layers = [f"<!-- Sovereign Layer: {tool_name} -->"]

        # Layer 1 — cleaned result
        if isinstance(cleaned, (dict, list)):
            layers.append(json.dumps(cleaned, indent=2))
        else:
            layers.append(str(cleaned))

        # Layer 2 — Muad'dib Q-table
        q_insight = get_muaddib_context(tool_name)
        if q_insight:
            layers.append(f"[{q_insight}]")

        # Layer 3 — session momentum / trajectory
        momentum = get_session_momentum(tool_name)
        if momentum:
            layers.append(f"[{momentum}]")

        enriched = "\n".join(layers)

        # Write the full cleaned + intelligent state to the dedicated volatile tail (bottom of payload).
        # This isolates volatility. The tail file is the place for dynamic per-turn state.
        tail_path = DATA_DIR / "current_volatile_tail.md"
        try:
            with open(tail_path, "w", encoding="utf-8") as tf:
                tf.write(f"# Sovereign Volatile Tail (tool: {tool_name}, updated {time.strftime('%Y-%m-%d %H:%M:%S')})\n\n")
                tf.write(enriched)
                tf.write("\n\n--- Full raw tool events also in intelligent_tool_outputs.log for distillation ---\n")
        except Exception:
            pass

        # Persist to the log (append for history of cleaned events).
        try:
            log_path = DATA_DIR / "intelligent_tool_outputs.log"
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"[{tool_name}] {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                lf.write(enriched + "\n\n")
        except Exception:
            pass

        # Emit *minimal* systemMessage to the host.
        # Carrying the full enriched (which can contain large cleaned payloads or changing Q/momentum)
        # on every PostToolUse would bloat the per-turn injection and risk cache effects on the foundation.
        # The full details live in current_volatile_tail.md (read explicitly or via memory when needed).
        small_injection = f"<!-- Sovereign PostToolUse cleaned for {tool_name}. Full intelligent output in data/current_volatile_tail.md. Raw in intelligent_tool_outputs.log. -->"
        print(json.dumps({"systemMessage": small_injection}))

        # Print the full enriched for hook annotations / visibility in the TUI when the operator wants to see it.
        print("\n" + "=" * 60)
        print(small_injection)
        print("Full cleaned + layers written to data/current_volatile_tail.md")
        print("=" * 60 + "\n")

    except Exception:
        print(json.dumps({}))

    sys.exit(0)


if __name__ == "__main__":
    main()
