#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

WRITE_TOOL_NAMES = {
    "Write",
    "Edit",
    "MultiEdit",
    "Bash",
    "apply_patch",
    "exec_command",
    "functions.apply_patch",
    "functions.exec_command",
}


def tool_name(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    return str(item.get("tool_name") or item.get("name") or "")


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            return 0
    except Exception:
        return 0
    tool_uses = data.get("tool_uses") or []
    if not isinstance(tool_uses, list):
        return 0
    write_tools = [t for t in tool_uses if tool_name(t) in WRITE_TOOL_NAMES]
    if len(write_tools) >= 3:
        out = {
            "decision": "block",
            "reason": (
                "Session had substantive edits. Run /ctmv3:session-close to "
                "update PROVENANCE.md and session state before closing."
            ),
        }
        sys.stdout.write(json.dumps(out))
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
