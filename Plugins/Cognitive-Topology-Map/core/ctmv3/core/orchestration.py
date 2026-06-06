"""
Production Module: CTMv3 Golden-Path Orchestration Layer
=========================================================
Source: CTMv3 Engine v1.1.0 — golden-path-architect
Integrated: 2026-05-23
Lines: ~340
Status: Production Stable

Capabilities:
- GoldenPathSignal dataclass: the atomic unit of orchestration emission
- pre_chain_rules: pure-function map of (command, exit_state) -> next_command
- memory_surface_tags: pure function emitting structured memory tags per command output
- emit_signal: serialize GoldenPathSignal as single-line JSON under sentinel prefix
- chain: walk the pre-chain spine from an initial command up to MAX_CHAIN_DEPTH steps

API Surface:
- GoldenPathSignal (dataclass)
- ChainTooLongError (exception)
- pre_chain_rules(command, exit_state) -> Optional[str]
- memory_surface_tags(command, exit_state, metadata) -> List[str]
- emit_signal(signal) -> None
- chain(initial_command, project_root) -> List[GoldenPathSignal]
- MAX_CHAIN_DEPTH (int, default 5)
- SIGNAL_SENTINEL (str)

Dependencies:
- Python stdlib only: dataclasses, json, logging, subprocess, sys, time, pathlib

Error Handling:
- ChainTooLongError: raised when chain exceeds MAX_CHAIN_DEPTH
- All subprocess invocations are bounded and never raise uncaught exceptions to callers
- Individual step failures are captured in GoldenPathSignal.command_status and
  GoldenPathSignal.payload["error"] without propagating to the chain caller

Design rationale:
  Pre-chain rules SUGGEST; they never FORCE. The orchestrator reads the signal envelope
  and MAY follow the suggestion. An agent runtime that ignores golden-path signals loses
  flow efficiency but never breaks. This decoupling is the key property that makes the
  system safe to deploy across heterogeneous runtimes (Claude Code, Codex, opencode,
  Gemini CLI, Cursor) without a guaranteed contract on how the outer host interprets signals.

  Memory tags are emitted at signal time so that memory systems operating outside the
  subprocess boundary can index command outputs without reading stdout. They are purely
  derived from the known command/exit-state pair — no file I/O, no model calls.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CHAIN_DEPTH: int = 5

SIGNAL_SENTINEL: str = "[CTMV3_GOLDEN_PATH]"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ChainTooLongError(Exception):
    """
    Raised when chain() has walked MAX_CHAIN_DEPTH steps without reaching a
    terminal state. Callers should treat this as a configuration signal that
    the pre-chain rules form a cycle or the depth limit is too low for this
    workflow.
    """

    def __init__(self, depth: int, last_command: str) -> None:
        self.depth = depth
        self.last_command = last_command
        super().__init__(
            f"Chain exceeded MAX_CHAIN_DEPTH={MAX_CHAIN_DEPTH} at step {depth} "
            f"(last command: '{last_command}'). "
            "Check pre_chain_rules for cycles or increase MAX_CHAIN_DEPTH."
        )


# ---------------------------------------------------------------------------
# GoldenPathSignal
# ---------------------------------------------------------------------------


@dataclass
class GoldenPathSignal:
    """
    The atomic unit of orchestration emission.

    Every subcommand that participates in the golden path emits one of these
    after it completes. External orchestrators grep stdout for SIGNAL_SENTINEL
    and parse the JSON envelope to decide whether to follow the chain suggestion.

    Fields:
        command_name: The CTMv3 subcommand that just completed (e.g. "boot").
        command_status: "success", "failure", or a domain-specific exit token
            like "COLD_START", "WARM_START", "PARTIAL", "drift_detected", "no_drift".
        next_command_suggested: Optional next command the orchestrator SHOULD consider.
            None means terminal — no further pre-chain suggestion.
        memory_relevance_tags: Structured tags for memory systems. Pure derived values;
            no I/O needed to produce them.
        payload: Dict carrying structured emission data from the command output.
            Shape varies by command. Always JSON-serializable.
        chain_depth: Step index within the chain (0 = initial command). Set by chain().
    """

    command_name: str
    command_status: str
    next_command_suggested: Optional[str]
    memory_relevance_tags: List[str]
    payload: Dict = field(default_factory=dict)
    chain_depth: int = 0

    def to_dict(self) -> dict:
        """Return JSON-serializable dict for signal envelope emission."""
        return {
            "command_name": self.command_name,
            "command_status": self.command_status,
            "next_command_suggested": self.next_command_suggested,
            "memory_relevance_tags": self.memory_relevance_tags,
            "payload": self.payload,
            "chain_depth": self.chain_depth,
        }


# ---------------------------------------------------------------------------
# Pre-chain rules
# ---------------------------------------------------------------------------

# The table encodes the domino spine: each (command, exit_state) pair maps to
# the next suggested command. None means terminal.
#
# Exit states used here must match what each command actually produces.
# boot produces: "COLD_START", "WARM_START", "PARTIAL"
# activate produces: "success", "failure"
# fingerprint produces: "drift_detected", "no_drift", "success"
# architecture-map produces: "success", "skipped", "failure"
# session-close produces: "success", "failure"
# warm produces: "success", "failure"
# sovereign-init produces: "success", "failure"
# dot-init produces: "success", "failure"
# status produces: "success", "failure"

_CHAIN_TABLE: dict[tuple[str, str], Optional[str]] = {
    # boot branch
    ("boot", "COLD_START"): "activate",
    ("boot", "WARM_START"): "warm",
    ("boot", "PARTIAL"): "activate",
    ("boot", "success"): "warm",     # generic success from boot → warm path
    ("boot", "failure"): None,       # boot failed: no safe suggestion
    # activate branch
    ("activate", "success"): "fingerprint",
    ("activate", "failure"): None,
    # warm branch
    ("warm", "success"): "fingerprint",
    ("warm", "failure"): None,
    # fingerprint branch
    ("fingerprint", "drift_detected"): "architecture-map",
    ("fingerprint", "no_drift"): "session-close",
    ("fingerprint", "success"): "session-close",   # legacy: success with no drift signal
    ("fingerprint", "failure"): None,
    # architecture-map branch
    ("architecture-map", "success"): "session-close",
    ("architecture-map", "skipped"): "session-close",
    ("architecture-map", "failure"): None,
    # session-close branch (terminal by design — closing is always the last step)
    ("session-close", "success"): None,
    ("session-close", "failure"): None,
    # sovereign-init and dot-init (utility; suggest next only if inline with activate)
    ("sovereign-init", "success"): "dot-init",
    ("sovereign-init", "failure"): None,
    ("dot-init", "success"): "fingerprint",
    ("dot-init", "failure"): None,
    # status (read-only diagnostic; never chains)
    ("status", "success"): None,
    ("status", "failure"): None,
}


def pre_chain_rules(command: str, exit_state: str) -> Optional[str]:
    """
    Pure function: given a command name and its exit state, return the next
    suggested command or None if this is a terminal state.

    Args:
        command: The completed CTMv3 subcommand name (e.g. "boot", "activate").
        exit_state: The command's exit state token. This is the semantic result,
            not the process exit code. Examples: "COLD_START", "success", "failure",
            "drift_detected".

    Returns:
        The next suggested command name, or None for terminal.
    """
    key = (command, exit_state)
    result = _CHAIN_TABLE.get(key)
    if key not in _CHAIN_TABLE:
        # Unknown combination: log and return None to avoid blind chaining
        logger.debug(
            "pre_chain_rules: no rule for (%r, %r) — returning None (terminal)",
            command,
            exit_state,
        )
        return None
    return result


# ---------------------------------------------------------------------------
# Memory surface tags
# ---------------------------------------------------------------------------

# Tags are structured strings for memory system indexing. They follow the
# convention: category_dimension_value. Pure function over known command/state.

_MEMORY_TAG_TABLE: dict[tuple[str, str], List[str]] = {
    ("boot", "COLD_START"): ["activation", "cold_start", "phase_0_required", "no_tier1_signals"],
    ("boot", "WARM_START"): ["activation", "warm_start", "tier1_signals_present", "provenance_valid"],
    ("boot", "PARTIAL"): ["activation", "partial_state", "tier1_incomplete", "archaeology_needed"],
    ("boot", "success"): ["activation", "boot_complete"],
    ("boot", "failure"): ["activation", "boot_failed", "diagnostic_needed"],
    ("activate", "success"): ["activation", "phase_0_5_complete", "all_artifacts_written", "repo_live"],
    ("activate", "failure"): ["activation", "activate_failed", "artifact_incomplete"],
    ("warm", "success"): ["warm_start", "topology_current", "session_resumed"],
    ("warm", "failure"): ["warm_start", "warm_invalid", "partial_archaeology_needed"],
    ("fingerprint", "drift_detected"): ["topology", "fingerprint_drift", "architecture_map_stale"],
    ("fingerprint", "no_drift"): ["topology", "fingerprint_stable", "no_drift"],
    ("fingerprint", "success"): ["topology", "fingerprint_written"],
    ("fingerprint", "failure"): ["topology", "fingerprint_failed"],
    ("architecture-map", "success"): ["architecture", "map_updated", "topology_traversal_ready"],
    ("architecture-map", "skipped"): ["architecture", "map_skipped", "existing_preserved"],
    ("architecture-map", "failure"): ["architecture", "map_failed"],
    ("session-close", "success"): ["session", "close_complete", "provenance_updated", "state_anchored"],
    ("session-close", "failure"): ["session", "close_failed", "state_potentially_stale"],
    ("sovereign-init", "success"): ["sovereign", "initialized", "session_anchor_ready"],
    ("sovereign-init", "failure"): ["sovereign", "init_failed"],
    ("dot-init", "success"): ["ecosystem", "dot_dirs_initialized", "adapters_ready"],
    ("dot-init", "failure"): ["ecosystem", "dot_init_failed"],
    ("status", "success"): ["diagnostic", "status_read", "signal_inventory_current"],
    ("status", "failure"): ["diagnostic", "status_failed"],
}


def memory_surface_tags(
    command: str, exit_state: str, metadata: Optional[dict] = None
) -> List[str]:
    """
    Pure function: return structured memory-relevance tags for the given command output.

    Tags enable downstream memory systems to index command outputs without reading
    stdout. They are emitted at signal time, before any memory write operation.

    Args:
        command: The completed subcommand name.
        exit_state: The command's exit state token.
        metadata: Optional dict of additional context from the command output.
            Not used in base tag derivation but reserved for future enrichment.

    Returns:
        List of tag strings. Empty list if no tags defined for this combination.
    """
    base_tags = list(_MEMORY_TAG_TABLE.get((command, exit_state), []))

    # Enrich with metadata-derived tags if provided
    if metadata:
        project_name = metadata.get("project_name")
        if project_name and isinstance(project_name, str):
            base_tags.append(f"project_{project_name.lower().replace(' ', '_')}")

        fingerprint = metadata.get("fingerprint")
        if fingerprint and isinstance(fingerprint, str):
            base_tags.append(f"fingerprint_{fingerprint[:16]}")

        errors = metadata.get("errors")
        if errors and isinstance(errors, list) and errors:
            base_tags.append("has_errors")

    return base_tags


# ---------------------------------------------------------------------------
# Signal emission
# ---------------------------------------------------------------------------


def emit_signal(signal: GoldenPathSignal) -> None:
    """
    Serialize signal as a single-line JSON envelope to stdout under SIGNAL_SENTINEL.

    Output format:
        [CTMV3_GOLDEN_PATH] {"command_name": "boot", "command_status": "COLD_START", ...}

    External orchestrators grep for "[CTMV3_GOLDEN_PATH]" to extract signals.
    Humans reading stdout see this as one additional line after human-readable output.
    The --no-golden-path flag in cli.py suppresses calls to this function.

    Serialization errors are logged but never propagate — emission is best-effort.
    """
    try:
        envelope = signal.to_dict()
        line = f"{SIGNAL_SENTINEL} {json.dumps(envelope, separators=(',', ':'))}"
        print(line, flush=True)
        logger.debug("emit_signal: emitted %s step=%d", signal.command_name, signal.chain_depth)
    except (TypeError, ValueError) as exc:
        logger.error("emit_signal: serialization error for command %r: %s", signal.command_name, exc)


# ---------------------------------------------------------------------------
# Command execution (subprocess bridge)
# ---------------------------------------------------------------------------


def _run_command(command: str, project_root: Path) -> tuple[int, str, str]:
    """
    Execute `python3 -m ctmv3 <command> --project-root <root> --json` as a subprocess.

    Returns (returncode, stdout, stderr).

    Never raises — all exceptions are caught and encoded in the return tuple
    with returncode=-1 and the exception message in stderr.
    """
    cmd = [
        sys.executable,
        "-m",
        "ctmv3",
        command,
        "--project-root",
        str(project_root),
        "--json",
        "--no-golden-path",  # suppress nested signal emission during chain runs
    ]
    logger.debug("_run_command: executing %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes maximum per command
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        logger.error("_run_command: timeout for command %r: %s", command, exc)
        return -1, "", f"TimeoutExpired: {exc}"
    except FileNotFoundError as exc:
        logger.error("_run_command: python3 not found: %s", exc)
        return -1, "", f"FileNotFoundError: {exc}"
    except OSError as exc:
        logger.error("_run_command: OS error for command %r: %s", command, exc)
        return -1, "", f"OSError: {exc}"


def _parse_exit_state(command: str, returncode: int, stdout: str, stderr: str) -> tuple[str, dict]:
    """
    Derive the semantic exit state and payload dict from a command's subprocess result.

    The exit state is the canonical token used by pre_chain_rules and memory_surface_tags.
    It is not the process exit code.

    Returns (exit_state, payload).
    """
    if returncode < 0:
        return "failure", {"error": stderr, "returncode": returncode}

    payload: dict = {"returncode": returncode}
    if stderr.strip():
        payload["stderr_excerpt"] = stderr.strip()[-512:]

    # Attempt to parse JSON from stdout
    stdout_data: dict = {}
    if stdout.strip():
        try:
            stdout_data = json.loads(stdout.strip())
            payload.update(stdout_data)
        except json.JSONDecodeError:
            payload["stdout_raw"] = stdout.strip()[-512:]

    # Command-specific exit state derivation
    if command == "boot":
        branch = stdout_data.get("branch", "")
        if branch in ("COLD_START", "WARM_START", "PARTIAL"):
            return branch, payload
        return ("success" if returncode == 0 else "failure"), payload

    if command == "fingerprint":
        if returncode != 0:
            return "failure", payload
        # Infer drift from whether stored fingerprint matched before this run
        # The fingerprint command always writes a fresh fingerprint; drift is
        # only detectable if we had a prior hash. We treat the payload conservatively:
        # if the payload explicitly carries a matches field from a prior verify call,
        # use it. Otherwise treat as success (no drift signal available).
        matches = stdout_data.get("matches")
        if matches is False:
            return "drift_detected", payload
        if matches is True:
            return "no_drift", payload
        return "success", payload

    if command == "architecture-map":
        if returncode != 0:
            return "failure", payload
        status_field = stdout_data.get("status", "")
        if status_field == "skipped":
            return "skipped", payload
        return "success", payload

    # Default: success/failure from returncode
    return ("success" if returncode == 0 else "failure"), payload


# ---------------------------------------------------------------------------
# Chain execution
# ---------------------------------------------------------------------------


def chain(initial_command: str, project_root: Path) -> List[GoldenPathSignal]:
    """
    Walk the pre-chain spine starting from initial_command.

    Executes each command as a subprocess, derives the exit state, looks up the
    next suggested command via pre_chain_rules, and continues until:
      - pre_chain_rules returns None (terminal state), or
      - MAX_CHAIN_DEPTH steps have been executed

    Each step produces a GoldenPathSignal. All signals are emitted to stdout
    via emit_signal as they are produced. The full list is also returned for
    programmatic consumers.

    Args:
        initial_command: The first CTMv3 subcommand to execute (e.g. "boot").
        project_root: Path to the project root directory. Must exist.

    Returns:
        List[GoldenPathSignal] with one entry per step executed.

    Raises:
        ValueError: If initial_command is empty or project_root does not exist.
        ChainTooLongError: If the chain exceeds MAX_CHAIN_DEPTH steps.
    """
    if not initial_command or not isinstance(initial_command, str):
        raise ValueError(
            f"initial_command must be a non-empty string, got {initial_command!r}"
        )

    root = Path(project_root).resolve()
    if not root.exists():
        raise ValueError(
            f"project_root does not exist: {root}. Pass an existing directory."
        )

    logger.info("chain: starting from %r at %s (max_depth=%d)", initial_command, root, MAX_CHAIN_DEPTH)

    signals: List[GoldenPathSignal] = []
    current_command: Optional[str] = initial_command
    depth: int = 0

    while current_command is not None:
        if depth >= MAX_CHAIN_DEPTH:
            logger.error(
                "chain: MAX_CHAIN_DEPTH=%d exceeded at step %d (command=%r)",
                MAX_CHAIN_DEPTH,
                depth,
                current_command,
            )
            raise ChainTooLongError(depth, current_command)

        logger.info("chain: step %d — executing %r", depth, current_command)
        returncode, stdout, stderr = _run_command(current_command, root)
        exit_state, payload = _parse_exit_state(current_command, returncode, stdout, stderr)
        next_cmd = pre_chain_rules(current_command, exit_state)
        tags = memory_surface_tags(current_command, exit_state, payload)

        signal = GoldenPathSignal(
            command_name=current_command,
            command_status=exit_state,
            next_command_suggested=next_cmd,
            memory_relevance_tags=tags,
            payload=payload,
            chain_depth=depth,
        )
        emit_signal(signal)
        signals.append(signal)

        logger.info(
            "chain: step %d complete — command=%r status=%r next=%r",
            depth,
            current_command,
            exit_state,
            next_cmd,
        )

        current_command = next_cmd
        depth += 1

    logger.info("chain: complete — %d steps executed", len(signals))
    return signals
