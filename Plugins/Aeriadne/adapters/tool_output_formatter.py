#!/usr/bin/env python3
"""
tool_output_formatter.py
─────────────────────────────────────────────────────────────────────────────
Intelligent tool output formatter for the Aeriadne adapter layer.

WHAT THIS DOES
  Sits between a tool's raw stdout/JSON and the model context window. Applies
  tool-specific and class-based rules to decide what to keep, compress, redact,
  or suppress entirely before the response reaches the model.

WHY THIS EXISTS
  CTMv3 and Mentat tools emit verbose JSON, progress traces, and internal state
  that is useful for debugging but is pure token waste in the model context.
  Not all tool outputs need to be shown to the model. Some should be silenced
  entirely. Others need structural compression — keep the signal, drop the noise.

DESIGN RULES
  1. FAIL LOUD — every exception bubbles with full context. No silent swallowing.
  2. Passthrough-safe — unknown tools pass through unmodified. No suppression
     of unrecognized output.
  3. Deterministic — same input always produces same output. No randomness.
  4. Auditable — every transformation is logged to stderr at DEBUG level.
  5. Configurable — per-tool rules live in FORMATTER_RULES dict. Add entries
     without touching core logic.

USAGE
  As a library:
      from tool_output_formatter import format_tool_output
      clean = format_tool_output(tool_name="ctmv3_boot", raw=json_blob)

  As a CLI filter (pipe mode):
      echo '{"tool":"ctmv3_boot","output":{...}}' | python3 tool_output_formatter.py

  In a Gemini-CLI hook (after_tool.py):
      from tool_output_formatter import format_tool_output
      payload["tool_response"] = format_tool_output(tool_name, payload["tool_response"])
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

log = logging.getLogger("tool_output_formatter")

# ─────────────────────────────────────────────────────────────────────────────
# RULE DEFINITIONS
# Each entry in FORMATTER_RULES maps a tool name prefix to a dict of options:
#
#   mode:
#     "passthrough"  — emit as-is (default for unknown tools)
#     "suppress"     — emit nothing (tool output never reaches model)
#     "summary"      — emit a compressed summary instead of raw output
#     "keys"         — emit only the listed top-level keys from a JSON object
#     "redact"       — pass through but redact listed key paths
#
#   keep_keys: list[str]
#     For mode="keys" — which top-level keys to keep. All others are dropped.
#
#   redact_paths: list[str]
#     For mode="redact" — dot-notation paths to zero out (e.g. "result.token").
#
#   max_chars: int | None
#     Truncate the final output string to this many characters before sending
#     to the model. None = no limit.
#
#   summary_template: str | None
#     For mode="summary" — a Python .format_map() template applied to the
#     parsed JSON dict. Use {key} to reference top-level keys.
#     Falls back to a generic summary if the template fails.
#
#   note: str
#     Human-readable rationale shown in DEBUG logs.
# ─────────────────────────────────────────────────────────────────────────────

FORMATTER_RULES: dict[str, dict[str, Any]] = {
    # ── CTMv3 ────────────────────────────────────────────────────────────────
    # boot: only the branch + signal counts matter. Full JSON is ~2–4KB of noise.
    "python3 -m ctmv3 boot": {
        "mode": "keys",
        "keep_keys": [
            "branch",
            "tier1_signals",
            "tier2_signals",
            "warm_start_valid",
            "last_session",
            "provenance_present",
        ],
        "max_chars": 1200,
        "note": "CTMv3 boot emits full signal inventory. Model only needs branch + tier1.",
    },
    # activate: suppress raw phase traces. Model gets a final state summary.
    "python3 -m ctmv3 activate": {
        "mode": "summary",
        "summary_template": "CTMv3 activate complete. Phase outputs written. "
        "Artifacts: {artifacts_written}. "
        "Status: {status}. "
        "Errors: {errors}.",
        "max_chars": 600,
        "note": "Activate emits verbose per-phase traces. Model only needs final state.",
    },
    # warm: keep the validity check result + delta summary only.
    "python3 -m ctmv3 warm": {
        "mode": "keys",
        "keep_keys": [
            "warm_valid",
            "topology_drift",
            "session_delta",
            "recommended_action",
            "status",
        ],
        "max_chars": 800,
        "note": "Warm emits full topology diff. Model only needs validity + delta.",
    },
    # architecture-map: just the status — artifact path and completion state.
    "python3 -m ctmv3 architecture-map": {
        "mode": "keys",
        "keep_keys": ["status", "output_path", "sections_built", "errors"],
        "max_chars": 500,
        "note": "Architecture-map emits full MD content. Model doesn't need the artifact echo.",
    },
    # sovereign-init, dot-init, session-close: operational housekeeping.
    # Model only needs success/fail + what was created.
    "python3 -m ctmv3 sovereign-init": {
        "mode": "keys",
        "keep_keys": ["status", "paths_created", "errors"],
        "max_chars": 400,
        "note": "Sovereign-init output is verbose path listing. Model needs status only.",
    },
    "python3 -m ctmv3 dot-init": {
        "mode": "keys",
        "keep_keys": ["status", "dirs_created", "errors"],
        "max_chars": 400,
        "note": "Dot-init output is verbose dir listing. Model needs status only.",
    },
    "python3 -m ctmv3 session-close": {
        "mode": "keys",
        "keep_keys": [
            "status",
            "provenance_updated",
            "session_state_flushed",
            "errors",
        ],
        "max_chars": 400,
        "note": "Session-close is bookkeeping. Model needs confirmation only.",
    },
    # status: keep as-is — it is short and directly actionable.
    "python3 -m ctmv3 status": {
        "mode": "passthrough",
        "note": "Status output is already concise and actionable.",
    },
    # ── Mentat FSA / Q-table tools ───────────────────────────────────────────
    # These tools are internal substrate ops. Model should never see raw Q-table
    # dumps or full insight bus payloads — those are for mentat tail, not context.
    # mentat_state_get: keep state + last_transition only.
    "mentat_state_get": {
        "mode": "keys",
        "keep_keys": ["state", "last_transition", "drift_count", "chain_depth"],
        "max_chars": 300,
        "note": "Full state payload includes Q-scores. Model only needs current state.",
    },
    # mentat_insight_query / tail: suppress. These are for operator monitoring
    # via `mentat tail`, not for model context. Feeding them to the model
    # creates reward-hacking risk and wastes tokens on internal bookkeeping.
    "mentat_insight_query": {
        "mode": "suppress",
        "note": "Insight bus is operator monitoring. Model should not read internal Q-signals.",
    },
    "mentat_insight_tail": {
        "mode": "suppress",
        "note": "Insight tail is operator monitoring. Suppress from model context.",
    },
    # mentat_q_table: suppress entirely. The Q-table dump is for analysis tooling.
    "mentat_q_table": {
        "mode": "suppress",
        "note": "Q-table dump is for mentat q-table CLI, not model context.",
    },
    # mentat_q_route: compress to just the recommended tool.
    "mentat_q_route": {
        "mode": "summary",
        "summary_template": "Q-route recommendation: {best_tool} (Q={best_q:.3f}, state={state}).",
        "max_chars": 200,
        "note": "Q-route emits full tool probability distribution. Model needs only the top pick.",
    },
    # mentat_handoff_read/write: keep just the status + session summary.
    "mentat_handoff_read": {
        "mode": "keys",
        "keep_keys": ["found", "session_id", "state", "last_action", "open_tasks"],
        "max_chars": 600,
        "note": "Handoff payload can be multi-KB. Model needs session summary only.",
    },
    "mentat_handoff_write": {
        "mode": "keys",
        "keep_keys": ["status", "path", "session_id"],
        "max_chars": 200,
        "note": "Handoff write confirmation. Model needs path + status only.",
    },
    # mentat_drift_check: keep the result clearly.
    "mentat_drift_check": {
        "mode": "keys",
        "keep_keys": ["drift_detected", "matched_topic", "matched_phrase", "state"],
        "max_chars": 300,
        "note": "Drift check — result is actionable; internal matching debug is not.",
    },
    # mentat_state_set: confirmation only.
    "mentat_state_set": {
        "mode": "keys",
        "keep_keys": ["prev_state", "new_state", "transition"],
        "max_chars": 200,
        "note": "State set confirmation. Model needs prev/new state only.",
    },
    # mentat_insight_emit: suppress. Self-referential cognitive substrate op.
    "mentat_insight_emit": {
        "mode": "suppress",
        "note": "Insight emit is a substrate write. Model should not echo its own substrate ops.",
    },
    # ── BB7 / Sovereign MCP tools ─────────────────────────────────────────────
    # Memory and session tools can emit large blobs. Compress aggressively.
    # bb7_memory_store: suppress verbose confirmation. Model knows it worked if no error.
    "bb7_memory_store": {
        "mode": "keys",
        "keep_keys": ["key", "status", "importance"],
        "max_chars": 200,
        "note": "Memory store confirmation is verbose. Model needs key + status only.",
    },
    # bb7_memory_retrieve: passthrough — the whole point is the retrieved content.
    "bb7_memory_retrieve": {
        "mode": "passthrough",
        "note": "Retrieve result is the payload — pass through.",
    },
    # bb7_memory_search / intelligent_search: cap result list to avoid context floods.
    "bb7_memory_search": {
        "mode": "redact",
        "max_chars": 4000,
        "note": "Memory search can return large result sets. Cap to prevent context flood.",
    },
    "bb7_memory_intelligent_search": {
        "mode": "redact",
        "max_chars": 4000,
        "note": "Intelligent search can return large result sets with embeddings. Cap.",
    },
    # bb7_memory_stats / insights: suppress. Operator monitoring, not model context.
    "bb7_memory_stats": {
        "mode": "suppress",
        "note": "Memory stats is operator telemetry. Not useful in model context.",
    },
    # bb7_journal_* trace ops: suppress. Journal is substrate, not model input.
    "bb7_journal_record_thought": {
        "mode": "suppress",
        "note": "Journal write ops are substrate. Model should not echo substrate writes.",
    },
    "bb7_journal_capture_decision": {
        "mode": "suppress",
        "note": "Journal write op — suppress.",
    },
    # bb7_session_* telemetry: suppress most. Keep session start/end summaries.
    "bb7_log_event": {
        "mode": "suppress",
        "note": "Session log event is substrate bookkeeping. Suppress from model context.",
    },
    "bb7_capture_insight": {
        "mode": "suppress",
        "note": "Insight capture is substrate write. Suppress.",
    },
    "bb7_get_session_summary": {
        "mode": "passthrough",
        "note": "Session summary is useful context for the model — pass through.",
    },
    # bb7_run_command: passthrough — the output IS the point.
    "bb7_run_command": {
        "mode": "passthrough",
        "note": "Shell command output is the purpose of the call — pass through.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# CORE FORMATTER
# ─────────────────────────────────────────────────────────────────────────────


def format_tool_output(
    tool_name: str,
    raw: Any,
    *,
    debug: bool = False,
) -> Any:
    """
    Apply formatting rules to a tool's output.

    Args:
        tool_name: The exact tool name or invocation string (e.g. "mentat_state_get"
                   or "python3 -m ctmv3 boot --json --project-root /repo").
        raw: The raw tool output — dict, list, str, or any JSON-serializable type.
        debug: If True, emit transformation notes to stderr.

    Returns:
        The formatted output. May be the original, a compressed dict, a summary
        string, or None (for suppressed tools).

    Raises:
        ValueError: If the rule configuration is invalid (load-time programming error).
        Exception: Any other exception propagates — this function does not swallow errors.
    """
    rule = _match_rule(tool_name)
    if rule is None:
        _dbg(debug, tool_name, "passthrough", "no rule — passing through unmodified")
        return raw

    mode = rule.get("mode", "passthrough")
    note = rule.get("note", "")
    max_chars = rule.get("max_chars")

    _dbg(debug, tool_name, mode, note)

    if mode == "passthrough":
        result = raw

    elif mode == "suppress":
        return None  # caller must handle None → do not inject into context

    elif mode == "keys":
        keep_keys = rule.get("keep_keys")
        if not keep_keys:
            raise ValueError(
                f"Rule for '{tool_name}' uses mode='keys' but has no keep_keys"
            )
        if isinstance(raw, dict):
            result = {k: raw[k] for k in keep_keys if k in raw}
        elif isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                result = {k: parsed[k] for k in keep_keys if k in parsed}
            except json.JSONDecodeError:
                _dbg(
                    debug,
                    tool_name,
                    "keys-fallback",
                    "raw is non-JSON string — passthrough",
                )
                result = raw
        else:
            _dbg(
                debug,
                tool_name,
                "keys-type-mismatch",
                f"raw type={type(raw).__name__} — passthrough",
            )
            result = raw

    elif mode == "summary":
        template = rule.get("summary_template")
        if not template:
            raise ValueError(
                f"Rule for '{tool_name}' uses mode='summary' but has no summary_template"
            )
        try:
            if isinstance(raw, dict):
                data = raw
            elif isinstance(raw, str):
                data = json.loads(raw)
            else:
                data = {}
            result = template.format_map(_SafeFormatMap(data))
        except Exception as exc:  # noqa: BLE001
            _dbg(
                debug,
                tool_name,
                "summary-fallback",
                f"template failed ({exc}) — using generic",
            )
            result = f"[{tool_name}] completed. Raw output suppressed by formatter."

    elif mode == "redact":
        redact_paths = rule.get("redact_paths", [])
        if isinstance(raw, dict):
            result = _redact_paths(raw, redact_paths)
        else:
            result = raw  # cannot redact non-dict

    else:
        raise ValueError(f"Unknown formatter mode '{mode}' for tool '{tool_name}'")

    # Apply max_chars cap on string output
    if max_chars is not None:
        if isinstance(result, (dict, list)):
            serialized = json.dumps(result, ensure_ascii=False)
            if len(serialized) > max_chars:
                suffix = (
                    f"... [truncated by formatter, original={len(serialized)} chars]"
                )
                available = max_chars - len(suffix)
                if available < 0:
                    result = suffix[:max_chars]
                else:
                    result = serialized[:available] + suffix
        elif isinstance(result, str) and len(result) > max_chars:
            suffix = f"... [truncated by formatter, original={len(result)} chars]"
            available = max_chars - len(suffix)
            if available < 0:
                result = suffix[:max_chars]
            else:
                result = result[:available] + suffix

    return result


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _match_rule(tool_name: str) -> dict[str, Any] | None:
    """
    Find the best matching rule for tool_name.
    Matching is prefix-based: the longest matching rule prefix wins.
    Exact match beats any prefix.
    Returns None if no rule matches (passthrough).
    """
    best: dict[str, Any] | None = None
    best_len = -1
    for prefix, rule in FORMATTER_RULES.items():
        if (
            tool_name == prefix
            or tool_name.startswith(prefix + " ")
            or tool_name.startswith(prefix)
        ):
            if len(prefix) > best_len:
                best = rule
                best_len = len(prefix)
    return best


def _redact_paths(data: dict, paths: list[str]) -> dict:
    """Zero out dot-notation paths in a nested dict. Non-destructive (deep copy)."""
    import copy

    result = copy.deepcopy(data)
    for path in paths:
        parts = path.split(".")
        obj = result
        for part in parts[:-1]:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                break
        else:
            last = parts[-1]
            if isinstance(obj, dict) and last in obj:
                obj[last] = "[REDACTED]"
    return result


def _dbg(debug: bool, tool: str, mode: str, note: str) -> None:
    if debug:
        print(f"[formatter] tool={tool!r} mode={mode} note={note}", file=sys.stderr)


class _SafeFormatMap(dict):
    """format_map that returns '{key}' for missing keys instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


# ─────────────────────────────────────────────────────────────────────────────
# CLI PIPE MODE
# ─────────────────────────────────────────────────────────────────────────────


def _cli_main() -> None:
    """
    Pipe mode: read JSON from stdin, format, write to stdout.

    Input shape: {"tool": "<tool_name>", "output": <any>}
    Output shape: {"tool": "<tool_name>", "output": <formatted>}
                  or nothing if suppressed.

    Errors: always printed to stderr, exit 1.
    """
    try:
        raw_input = sys.stdin.read()
        envelope = json.loads(raw_input)
        tool_name = envelope["tool"]
        tool_output = envelope["output"]
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"[formatter] ERROR: invalid input envelope: {exc}", file=sys.stderr)
        sys.exit(1)

    debug = "--debug" in sys.argv

    try:
        result = format_tool_output(tool_name, tool_output, debug=debug)
    except Exception as exc:
        print(
            f"[formatter] ERROR: formatting failed for tool={tool_name!r}: {exc}",
            file=sys.stderr,
        )
        raise  # fail loud

    if result is None:
        # Suppressed — emit nothing to stdout (caller treats empty stdout as no output)
        sys.exit(0)

    out_envelope = {"tool": tool_name, "output": result}
    print(json.dumps(out_envelope, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG if "--debug" in sys.argv else logging.WARNING
    )
    _cli_main()
