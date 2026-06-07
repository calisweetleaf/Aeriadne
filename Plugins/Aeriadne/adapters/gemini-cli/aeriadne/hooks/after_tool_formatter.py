#!/usr/bin/env python3
"""
after_tool_formatter.py
─────────────────────────────────────────────────────────────────────────────
Gemini-CLI AfterTool hook that applies the intelligent tool output formatter
before the tool response enters the model context.

Wiring: referenced from hooks/hooks.json in the Aeriadne Gemini-CLI extension.

The hook reads the Gemini-CLI tool event payload from stdin, applies
tool_output_formatter.format_tool_output(), and writes the modified payload
to stdout. Suppressed tools get an empty "output" to minimize token cost.

EXIT CODES (Gemini-CLI hook protocol):
  0  — proceed (formatted or passthrough output)
  1  — internal error (logged to stderr, Gemini CLI falls back to raw output)

FAIL LOUD contract: exceptions are printed to stderr before exit(1).
No silent swallowing.

IMPORT NOTE: tool_output_formatter.py must be importable from this file's
directory. The hook copies or symlinks it alongside this file at install time.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ── Import formatter ──────────────────────────────────────────────────────────
# Allow running from any cwd by adding the hook's own directory to sys.path.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

try:
    from tool_output_formatter import format_tool_output
except ImportError as _imp_err:
    print(
        f"[aeriadne-hook] FATAL: cannot import tool_output_formatter: {_imp_err}\n"
        f"  Expected it at: {_HERE / 'tool_output_formatter.py'}",
        file=sys.stderr,
    )
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# HOOK MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    debug = os.getenv("AERIADNE_FORMATTER_DEBUG", "").lower() in ("1", "true", "yes")

    # Read Gemini-CLI hook payload from stdin
    try:
        raw_stdin = sys.stdin.read()
        payload: dict = json.loads(raw_stdin)
    except json.JSONDecodeError as exc:
        print(f"[aeriadne-hook] ERROR: invalid JSON payload from Gemini-CLI: {exc}", file=sys.stderr)
        return 1

    # Extract tool identification
    # Gemini-CLI AfterTool payload shape (v0.4+):
    #   { "tool_name": str, "tool_input": dict, "tool_response": any, ... }
    tool_name: str = payload.get("tool_name", "")
    tool_response = payload.get("tool_response")

    if not tool_name:
        # Malformed payload — pass through unchanged
        print(json.dumps(payload), end="")
        return 0

    # Reconstruct the tool invocation string for command-style tools (ctmv3)
    # Gemini-CLI fires shell commands with tool_name="run_shell_command" and
    # the actual command in tool_input["command"].
    effective_name = tool_name
    if tool_name == "run_shell_command":
        command = (payload.get("tool_input") or {}).get("command", "")
        if command:
            effective_name = command.strip()

    # Apply formatter
    try:
        formatted = format_tool_output(effective_name, tool_response, debug=debug)
    except Exception as exc:
        print(
            f"[aeriadne-hook] ERROR: formatter failed for tool={effective_name!r}: {exc}",
            file=sys.stderr,
        )
        # Fail loud but do not block the hook chain — pass through raw
        print(json.dumps(payload), end="")
        return 0  # exit 0 so Gemini CLI continues

    if formatted is None:
        # Suppressed: replace tool_response with a minimal acknowledgment
        # so the model knows the tool ran but doesn't see the bulk content.
        payload["tool_response"] = {
            "_suppressed_by": "aeriadne-formatter",
            "_tool": effective_name,
            "status": "ok",
        }
        if debug:
            print(
                f"[aeriadne-hook] suppressed output for tool={effective_name!r}",
                file=sys.stderr,
            )
    else:
        payload["tool_response"] = formatted

    print(json.dumps(payload), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
