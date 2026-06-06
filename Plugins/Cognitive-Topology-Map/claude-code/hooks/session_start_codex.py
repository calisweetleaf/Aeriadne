#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CAP = 900


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _parse_boot(stdout: str) -> tuple[dict, dict]:
    boot: dict = {}
    golden: dict = {}
    marker = "[CTMV3_GOLDEN_PATH]"
    marker_idx = stdout.find(marker)
    boot_text = stdout[:marker_idx].strip() if marker_idx >= 0 else stdout.strip()
    if boot_text:
        try:
            parsed = json.loads(boot_text)
            if isinstance(parsed, dict):
                boot = parsed
        except Exception:
            pass
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith(marker):
            continue
        payload = line.removeprefix(marker).strip()
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                golden = parsed
        except Exception:
            pass
    return boot, golden


def _compact_context(stdout: str, root_path: Path) -> str:
    boot, golden = _parse_boot(stdout)
    if not boot and not golden:
        first = " ".join(stdout.strip().split())[:500]
        return f"<ctmv3:boot> status=unparsed project={root_path} note={first}</ctmv3:boot>"

    branch = boot.get("branch") or boot.get("command_status") or "unknown"
    file_count = boot.get("file_count", "unknown")
    tier1 = ",".join(boot.get("tier1_signals") or []) or "none"
    tier2 = ",".join(boot.get("tier2_signals") or []) or "none"
    tier3 = ",".join(boot.get("tier3_signals") or []) or "none"
    provenance = bool(boot.get("provenance_present"))
    manifest = bool(boot.get("manifest_present"))
    session_valid = bool(boot.get("session_state_valid"))
    next_cmd = golden.get("next_command_suggested") or "none"
    tags = ",".join(golden.get("memory_relevance_tags") or []) or "none"
    depth = golden.get("chain_depth", 0)

    lines = [
        "<ctmv3:boot compact=true>",
        f"project={root_path}",
        f"branch={branch} files={file_count} provenance={provenance} manifest={manifest} session_valid={session_valid}",
        f"signals=tier1:{tier1} tier2:{tier2} tier3:{tier3}",
        f"golden_next={next_cmd} chain_depth={depth} tags={tags}",
        "raw_json=suppressed_for_prompt; ctmv3 command still ran for hook telemetry/provenance",
        "</ctmv3:boot>",
    ]
    return "\n".join(lines)


def emit_context(msg: str) -> None:
    if not msg:
        return
    if len(msg) > CAP:
        msg = msg[: CAP - 80] + "\n…[ctmv3:compact-truncated]"
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
    emit_context(_compact_context(text, root_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
