#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CAP = 2200


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def emit_context(msg: str) -> None:
    if not msg:
        return
    if len(msg) > CAP:
        msg = msg[: CAP - 80] + "\n…[ctmv3: truncated]"
    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }
    sys.stdout.write(json.dumps(out))
    sys.stdout.flush()


def main() -> int:
    payload = read_payload()
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    try:
        root_path = Path(root).expanduser().resolve()
    except Exception:
        root_path = Path.cwd()
    cmd = [sys.executable, "-m", "ctmv3", "boot", "--json", "--project-root", str(root_path)]
    try:
        cp = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=4,
            cwd=str(root_path) if root_path.exists() else None,
        )
    except Exception:
        return 0
    text = (cp.stdout or "").strip()
    if not text:
        return 0
    emit_context("<ctmv3:boot>\n" + text + "\n</ctmv3:boot>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
