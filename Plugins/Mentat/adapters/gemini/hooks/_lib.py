"""Gemini-flavored hook helper for Mentat.

Gemini CLI invokes hook scripts as independent subprocesses, same shape as
Claude Code and Codex (stdin JSON → side effects → stdout JSON / exit code),
but with eleven event types instead of six and slightly different field
names. This module is the Gemini translation layer.

Gemini stdin payload (per https://geminicli.com/docs/hooks):

    {
      "session_id":      "<uuid>",
      "hook_event_name": "BeforeTool" | "AfterTool" | "BeforeAgent" | ...
      "cwd":             "<abs path>",
      # Event-specific extras:
      "tool_name":       "<name>",            # BeforeTool / AfterTool / BeforeToolSelection
      "tool_input":      {...},               # BeforeTool / AfterTool
      "tool_response":   {...},               # AfterTool
      "prompt":          "<text>",            # BeforeAgent (most reliable for prompt text)
      "model":           "<slug>",            # BeforeModel / AfterModel
      "matcher":         "<string>"           # SessionStart / SessionEnd
    }

Gemini exit-code semantics:
    0 → success; stdout MUST be a single JSON object or empty
    2 → System Block — target action aborted; stderr shown as reason
    other → non-fatal warning; interaction proceeds

The Q-table and insight bus live at the same on-disk path as Claude Code
and Codex (~/.mentat/q_table.sqlite and ~/.mentat/insights/<sid>.jsonl).
Cross-runtime accumulation is the design goal.

Per-hook latency budget: < 50 ms. Gemini's default timeout is 60 s; Mentat
caps each hook at 5 s in hooks.json (5000 ms). Errors land in
~/.mentat/log/hook-errors.log and on stderr — never silent.

Per Gemini's docs: stdout MUST be silent except for the final JSON object.
A stray print() before the JSON corrupts parsing; the CLI then defaults to
"Allow" and shows your entire output as a systemMessage. Use stderr for
debugging, never stdout.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


def _resolve_plugin_root() -> Path:
    for env_var in ("GEMINI_PLUGIN_ROOT", "MENTAT_PLUGIN_ROOT",
                    "CODEX_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
        val = os.environ.get(env_var)
        if val:
            return Path(val)
    # adapters/gemini/hooks/_lib.py → adapters/gemini/hooks → adapters/gemini → adapters → plugin
    return Path(__file__).resolve().parents[3]


_PLUGIN_ROOT = _resolve_plugin_root()
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from state_machine import (  # noqa: E402
    Event,
    EventClass,
    Insight,
    InsightBus,
    InsightType,
    QTable,
    Reward,
    State,
    StateMachine,
)
from state_machine.session import (  # noqa: E402
    Session,
    home_root,
    load_session,
    save_session,
    set_active_session,
)
from state_machine.drift import detect_drift, parse_scope  # noqa: E402


# Gemini's built-in tool names. The CLI uses snake_case for built-ins and
# slash-separated MCP tool ids. Keep both shapes in the classifier.
_READ_TOOLS = {
    "read_file", "read_many_files", "search_file_content",
    "list_directory", "glob", "web_fetch", "web_search",
    "Read", "Grep", "Glob", "LS", "WebFetch", "WebSearch",
}
_WRITE_TOOLS = {
    "write_file", "replace", "edit",
    "Edit", "MultiEdit", "Write",
}
_EXEC_TOOLS = {
    "run_shell_command", "shell", "bash",
    "Bash",
}
_AGENT_TOOLS = {
    "task", "agent", "subagent",
    "Task", "Agent",
}


def classify_tool(tool_name: str, tool_input: dict) -> EventClass:
    """Map a Gemini tool name into Mentat's coarse event class."""
    if tool_name in _READ_TOOLS:
        return EventClass.READ_TOOL
    if tool_name in _WRITE_TOOLS:
        return EventClass.WRITE_TOOL
    if tool_name in _AGENT_TOOLS:
        return EventClass.AGENT_TOOL
    if tool_name in _EXEC_TOOLS:
        return EventClass.EXEC_TOOL
    n = tool_name.lower()
    # MCP tool naming in Gemini is "<server>/<tool>" (slash separator).
    # Claude-style "mcp__server__tool" also accepted for portability.
    if "/" in tool_name or tool_name.startswith("mcp__"):
        if any(k in n for k in ("write", "create", "update", "delete", "send",
                                "publish", "replace", "edit", "patch")):
            return EventClass.WRITE_TOOL
        return EventClass.READ_TOOL
    return EventClass.READ_TOOL


@dataclass
class HookContext:
    """Bundled state for a single Gemini hook invocation."""
    payload: dict
    session_id: str
    session: Session
    machine: StateMachine
    q_table: QTable
    bus: InsightBus

    def step(self, event: Event) -> tuple[State, State, bool]:
        prev, nxt, transitioned = self.machine.step(event)
        self.session.state = nxt
        self.session.transition_count = self.machine.transition_count
        self.session.last_event_at = time.time()
        if event.tool_name:
            self.session.last_tool = event.tool_name
        if transitioned:
            trigger = f"{event.event_class.value}:{event.tool_name or '-'}"
            self.bus.emit_state_transition(prev.value, nxt.value, trigger)
        return prev, nxt, transitioned

    def update_chain(self, success: bool) -> None:
        if success:
            self.session.chain_depth += 1
            self.session.last_tool_success = True
        else:
            self.session.chain_depth = 0
            self.session.last_tool_success = False

    def reward(self, tool: str, success: bool, latency_ms: float = 0.0,
               next_state: Optional[State] = None) -> Reward:
        r = Reward(success=success, latency_ms=latency_ms,
                   chain_depth=self.session.chain_depth)
        self.q_table.update(self.session.state, tool, r,
                            next_state or self.session.state)
        self.bus.emit_reward(self.session.state.value, tool, r.value, success)
        return r

    def save(self) -> None:
        save_session(self.session)


def _session_id_from_payload(payload: dict) -> str:
    return (
        payload.get("session_id")
        or os.environ.get("GEMINI_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or "default"
    )


def open_context(payload: dict) -> HookContext:
    """Reconstruct the per-invocation context from disk."""
    sid = _session_id_from_payload(payload)
    set_active_session(sid)
    session = load_session(sid)
    machine = StateMachine(state=session.state,
                           transition_count=session.transition_count)
    q_table = QTable(home_root() / "q_table.sqlite")
    bus = InsightBus(home_root(), sid)
    return HookContext(
        payload=payload,
        session_id=sid,
        session=session,
        machine=machine,
        q_table=q_table,
        bus=bus,
    )


def read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


CONTEXT_INJECTION_BYTE_CAP = 2048


def write_additional_context(msg: str) -> None:
    """Emit a Gemini additionalContext JSON object on stdout.

    Gemini's BeforeAgent / SessionStart hooks expose context injection via
    `hookSpecificOutput.additionalContext`. Capped to avoid burning the
    model's working context on every turn.

    NOTE: Per Gemini docs, stdout MUST be either empty or a single valid
    JSON object. Do not write anything else before or after.
    """
    if len(msg) > CONTEXT_INJECTION_BYTE_CAP:
        msg = msg[:CONTEXT_INJECTION_BYTE_CAP - 60] + "\n…[mentat: truncated to fit context cap]"
    out = {"hookSpecificOutput": {"additionalContext": msg}}
    sys.stdout.write(json.dumps(out))
    sys.stdout.flush()


def write_decision(decision: str, reason: str) -> None:
    """Emit a tool-gate decision JSON for BeforeTool.

    Gemini accepts `{"decision": "deny"}` with exit 0 as the preferred path
    for intentional blocks. Reason is surfaced in the rejection message.
    """
    out = {
        "decision": decision,
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "BeforeTool",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        },
    }
    sys.stdout.write(json.dumps(out))
    sys.stdout.flush()


def deny_and_exit(reason: str) -> None:
    """Hard System Block via exit 2 + stderr (Gemini's canonical block path)."""
    sys.stderr.write(reason)
    sys.stderr.flush()
    sys.exit(2)


def log_error(prefix: str, exc: BaseException) -> None:
    """Fail loud. Gemini's exit-2-on-script-failure semantics would otherwise
    block work on a Mentat bug; we use safe_main() to swallow exceptions and
    return 0 instead, but still record the traceback."""
    try:
        log_dir = Path(os.environ.get("MENTAT_HOME", Path.home() / ".mentat")) / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        line = (
            f"{time.strftime('%Y-%m-%dT%H:%M:%S')} [gemini/{prefix}] "
            f"{type(exc).__name__}: {exc}\n"
            f"{traceback.format_exc()}\n---\n"
        )
        with (log_dir / "hook-errors.log").open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(f"mentat:gemini/{prefix}: {type(exc).__name__}: {exc}", file=sys.stderr)


def safe_main(prefix: str, fn) -> int:
    """Wrap a hook entry-point. Errors log loudly and return 0 so the agent
    loop continues — Mentat must never block work on its own bug."""
    try:
        return fn()
    except SystemExit:
        raise
    except BaseException as e:
        log_error(prefix, e)
        return 0


def scope_path() -> Optional[Path]:
    """Locate scope.md. Gemini exports GEMINI_PROJECT_DIR; we also honor the
    CLAUDE_PROJECT_DIR alias that Gemini ships for compatibility, plus a
    cwd fallback."""
    proj = (
        os.environ.get("GEMINI_PROJECT_DIR")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    if not proj:
        return None
    p = Path(proj) / ".mentat" / "scope.md"
    # Synthesize CLAUDE_PROJECT_DIR for session.py's project_root() so the
    # active-session pointer lands in the right place regardless of runtime.
    os.environ.setdefault("CLAUDE_PROJECT_DIR", proj)
    return p
