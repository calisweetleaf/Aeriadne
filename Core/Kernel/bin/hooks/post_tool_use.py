#!/usr/bin/env python3
"""Sovereign PostToolUse — distill trajectory + auto bb7_exo_reflect."""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _lib import read_payload, call_bb7, safe_main

def main() -> int:
    payload = read_payload()
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    tool_response = payload.get("tool_response", {})
    is_error = bool(
        tool_response.get("error") or payload.get("error")
        or (tool_response.get("exit_code", 0) not in (0, None))
    )
    data_dir = Path(os.environ.get("SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"))

    # 1. Async distillation — fire-and-forget to DistillationSubsystem
    if os.environ.get("SOVEREIGN_DISTILLATION_ENABLED") == "1":
        try:
            traj = {"ts": time.time(), "tool": tool_name, "input": tool_input,
                    "success": not is_error, "session": payload.get("session_id","")}
            dist_dir = data_dir / "distillation"
            dist_dir.mkdir(exist_ok=True)
            today = time.strftime("%Y-%m-%d")
            with (dist_dir / f"trajectories_{today}.jsonl").open("a") as f:
                f.write(json.dumps(traj) + "\n")
        except Exception:
            pass

    # 2. Auto-reflect after execution tools (no model turn consumed)
    exec_tools = {"Bash", "bash", "apply_patch", "shell", "exec_command"}
    if tool_name in exec_tools and not is_error:
        try:
            call_bb7("bb7_exo_reflect", {
                "plan_id": f"hook::{payload.get('session_id','unknown')}",
                "tools_used": [tool_name],
                "success": not is_error,
                "intent": "codex_post_tool_use_hook",
            }, timeout=3.0)
        except Exception:
            pass

    return 0

if __name__ == "__main__":
    sys.exit(safe_main("post_tool_use", main))
