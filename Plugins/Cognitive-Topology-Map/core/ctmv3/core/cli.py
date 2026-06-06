"""
CTMv3 CLI — Command-Line Entry Point
=====================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: python -m ctmv3 <command> [args] entry point. Every host adapter
         (Claude Code, Codex, opencode, Gemini CLI, Cursor) shells out to this CLI.

Exit codes:
  0 -- success
  1 -- user error (bad args, missing required input)
  2 -- corrupt state (malformed artifacts, unreadable files)
  3 -- missing prerequisite (required file absent, dependency missing)

All human-readable messages go to stderr.
Machine-readable (--json) payloads go to stdout.

Golden-path signal emission:
  After each subcommand completes, a GoldenPathSignal is emitted to stdout
  under the sentinel prefix "[CTMV3_GOLDEN_PATH] {...json...}".
  External orchestrators grep for the sentinel. Humans see it as one extra
  line after the command output.
  Use --no-golden-path to suppress signal emission entirely.

Subcommands:
  boot                 -- run BOOT_PROTOCOL discovery, print signal inventory
  activate             -- full cold-start build (Phase 0-5)
  warm                 -- warm-start protocol (Section 3 of BOOT_PROTOCOL)
  architecture-map     -- scaffold ARCHITECTURE_MAP.md
  sovereign-init       -- create .sovereign/ directory and seed files
  dot-init             -- create the .xyz dirs
  fingerprint          -- recompute topology_fingerprint.txt
  session-close        -- update PROVENANCE Session Log and session_state.json
  status               -- print current CTMv3 state
  version              -- print version
  chain                -- walk the golden-path domino chain from an initial command
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from ctmv3.core import __version__
from ctmv3.core import boot as boot_module
from ctmv3.core import fingerprint as fp_module
from ctmv3.core import sovereign as sov_module
from ctmv3.core import dot_init as dot_module
from ctmv3.core import architecture_map as arch_module
from ctmv3.core import activate as activate_module
from ctmv3.core.boot import SignalInventory
from ctmv3.core.orchestration import (
    GoldenPathSignal,
    ChainTooLongError,
    emit_signal,
    pre_chain_rules,
    memory_surface_tags,
    chain as orchestration_chain,
)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _emit_json(payload: Any) -> None:
    """Write JSON to stdout."""
    print(json.dumps(payload, indent=2))


def _emit_human(msg: str) -> None:
    """Write a human-readable message to stderr."""
    print(msg, file=sys.stderr)


def _fail(msg: str, exit_code: int = 1) -> None:
    """Print error to stderr and exit with the given code."""
    _emit_human(f"ERROR: {msg}")
    sys.exit(exit_code)


def _maybe_emit_signal(
    args: argparse.Namespace,
    command: str,
    exit_state: str,
    payload: Optional[dict] = None,
) -> None:
    """
    Emit a GoldenPathSignal for the completed command unless --no-golden-path is set.

    This is called at the end of every subcommand handler. The signal goes to stdout
    after all human-readable output (which goes to stderr). External orchestrators
    grep for SIGNAL_SENTINEL; human output on stderr is unaffected.
    """
    if getattr(args, "no_golden_path", False):
        return

    p = payload or {}
    tags = memory_surface_tags(command, exit_state, p)
    next_cmd = pre_chain_rules(command, exit_state)

    signal = GoldenPathSignal(
        command_name=command,
        command_status=exit_state,
        next_command_suggested=next_cmd,
        memory_relevance_tags=tags,
        payload=p,
        chain_depth=0,  # single-command invocation; chain() sets its own depths
    )
    emit_signal(signal)


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------


def cmd_boot(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    inv = boot_module.discover(root)

    if args.json:
        _emit_json(inv.to_dict())
    else:
        _emit_human("CTMv3 Boot Discovery")
        _emit_human(f"  Project root: {root}")
        _emit_human(f"  Branch:       {inv.branch}")
        _emit_human(f"  Tier 1 signals: {inv.tier1_signals or 'none'}")
        _emit_human(f"  Tier 2 signals: {inv.tier2_signals or 'none'}")
        _emit_human(f"  Tier 3 signals: {inv.tier3_signals or 'none'}")
        _emit_human(f"  PROVENANCE present: {inv.provenance_present}")
        _emit_human(f"  manifest.json present: {inv.manifest_present}")
        _emit_human(f"  Last session: {inv.last_session or 'none'}")

    _maybe_emit_signal(
        args,
        "boot",
        inv.branch,  # COLD_START | WARM_START | PARTIAL
        inv.to_dict(),
    )


def cmd_activate(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    force = getattr(args, "force", False)
    dot_targets = getattr(args, "dot_targets", "all") or "all"

    report = activate_module.run(root, force=force, dot_targets=dot_targets)

    if report.get("aborted"):
        if args.json:
            _emit_json(report)
        else:
            _emit_human(f"ABORTED: {report['abort_reason']}")
        _maybe_emit_signal(args, "activate", "failure", report)
        abort_reason = report.get("abort_reason", "")
        if "malformed" in abort_reason.lower() or "corrupt" in abort_reason.lower():
            sys.exit(2)  # exit 2: corrupt state
        sys.exit(1)  # exit 1: user error (existing artifacts without --force)

    if args.json:
        _emit_json(report)
    else:
        _emit_human("CTMv3 Activation Complete")
        _emit_human(f"  Project: {report.get('project_name', '')}")
        _emit_human(f"  Phase:   {report.get('phase', '')}")
        _emit_human(f"  Fingerprint: {report.get('fingerprint', '')}")
        _emit_human("")
        _emit_human("Files:")
        for path, status in sorted(report.get("files_written", {}).items()):
            _emit_human(f"  [{status}] {path}")
        if report.get("errors"):
            _emit_human("")
            _emit_human("Errors encountered:")
            for err in report["errors"]:
                _emit_human(f"  - {err}")

    _maybe_emit_signal(args, "activate", "success", report)


def cmd_warm(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    inv = boot_module.discover(root)

    if inv.branch == "COLD_START":
        msg = "Repo has no CTM artifacts — this is a cold start. Run 'ctmv3 activate' first."
        if args.json:
            _emit_json({"error": msg, "branch": inv.branch})
        else:
            _emit_human(msg)
        _maybe_emit_signal(args, "warm", "failure", {"error": msg, "branch": inv.branch})
        sys.exit(3)  # exit 3: missing prerequisite (no artifacts to warm)

    warm_valid = boot_module.is_warm_valid(inv)
    state = sov_module.read_session_state(root)
    matches, current_hash = fp_module.verify(root)

    result: dict[str, Any] = {
        "branch": inv.branch,
        "warm_valid": warm_valid,
        "fingerprint_matches": matches,
        "current_hash": current_hash,
        "last_session": inv.last_session,
        "session_state": state,
        "signal_inventory": inv.to_dict(),
    }

    if args.json:
        _emit_json(result)
    else:
        _emit_human("CTMv3 Warm-Start Check")
        _emit_human(f"  Branch:             {inv.branch}")
        _emit_human(f"  Warm valid:         {warm_valid}")
        _emit_human(f"  Fingerprint match:  {matches}")
        _emit_human(f"  Current hash:       {current_hash}")
        _emit_human(f"  Last session:       {inv.last_session or 'none'}")
        _emit_human(f"  Last agent:         {state.get('last_agent', 'unknown')}")
        _emit_human(f"  Last action:        {state.get('last_action', 'unknown')}")
        if not warm_valid:
            _emit_human("")
            _emit_human(
                "Warm state is not valid. Run partial archaeology per BOOT_PROTOCOL.md Section 3.2."
            )
        if not matches:
            _emit_human("")
            _emit_human(
                "Topology fingerprint does not match — topology may have drifted. "
                "Run 'ctmv3 fingerprint' to update."
            )

    exit_state = "success" if warm_valid else "failure"
    _maybe_emit_signal(args, "warm", exit_state, result)


def cmd_architecture_map(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    force = getattr(args, "force", False)
    from_topo = getattr(args, "from_topology", False)

    if from_topo:
        path, status = arch_module.from_topology(root, force=force)
    else:
        project_name = getattr(args, "project_name", None) or arch_module._infer_project_name(root)
        path, status = arch_module.scaffold(root, project_name=project_name, force=force)

    result = {"path": str(path), "status": status}

    if args.json:
        _emit_json(result)
    else:
        _emit_human(f"ARCHITECTURE_MAP.md [{status}]: {path}")
        if status == "skipped":
            _emit_human("  Existing file preserved. Use --force to overwrite.")

    # status field from arch_module: "written" | "skipped" | error
    if status in ("written", "skipped"):
        exit_state = status  # pre_chain_rules handles both
    else:
        exit_state = "failure"
    _maybe_emit_signal(args, "architecture-map", exit_state, result)


def cmd_sovereign_init(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    sov_module.init(root)
    result = {
        "sovereign_dir": str(root / ".sovereign"),
        "status": "initialized",
    }

    if args.json:
        _emit_json(result)
    else:
        _emit_human(f".sovereign/ initialized at: {root / '.sovereign'}")

    _maybe_emit_signal(args, "sovereign-init", "success", result)


def cmd_dot_init(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    target = getattr(args, "target", "all") or "all"
    force = getattr(args, "force", False)
    project_name = getattr(args, "project_name", None) or arch_module._infer_project_name(root)

    try:
        results = dot_module.init_target(
            target,  # type: ignore[arg-type]
            root,
            project_name,
            force=force,
        )
    except ValueError as exc:
        _fail(str(exc), exit_code=1)
        return  # unreachable, satisfies type checker

    if args.json:
        _emit_json({"target": target, "files": results})
    else:
        _emit_human(f"dot-init [{target}]:")
        for path, status in sorted(results.items()):
            _emit_human(f"  [{status}] {path}")

    _maybe_emit_signal(args, "dot-init", "success", {"target": target, "files": results})


def cmd_fingerprint(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    # If no topology artifacts exist at all, warn and exit 3
    has_topology = (root / "TOPOLOGY.md").exists()
    has_arch_map = (root / "ARCHITECTURE_MAP.md").exists()
    if not has_topology and not has_arch_map:
        msg = (
            "No TOPOLOGY.md or ARCHITECTURE_MAP.md found at the project root. "
            "Run 'ctmv3 activate' first to create the topology artifacts before "
            "computing a fingerprint."
        )
        if args.json:
            _emit_json({"error": msg, "hint": "Run ctmv3 activate --project-root <path>"})
        else:
            _emit_human(f"WARNING: {msg}")
        _maybe_emit_signal(args, "fingerprint", "failure", {"error": msg})
        sys.exit(3)  # exit 3: missing prerequisite

    # Capture pre-write verification so we can report drift
    pre_matches, _ = fp_module.verify(root)

    fp_path = fp_module.write(root)
    current_hash = fp_module.compute(root)
    matches, _ = fp_module.verify(root)

    result = {
        "fingerprint_path": str(fp_path),
        "hash": current_hash,
        "matches": matches,
        "drift_detected": not pre_matches,
    }

    if args.json:
        _emit_json(result)
    else:
        _emit_human(f"Fingerprint written: {fp_path}")
        _emit_human(f"Hash: {current_hash}")

    # Derive exit state from pre-write drift detection
    if not pre_matches:
        exit_state = "drift_detected"
    else:
        exit_state = "no_drift"

    _maybe_emit_signal(args, "fingerprint", exit_state, result)


def cmd_session_close(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    agent = getattr(args, "agent", None) or "unknown"
    action = getattr(args, "action", None) or "session close"
    next_action = getattr(args, "next_action", None) or "review open tasks"
    topology_drift = getattr(args, "topology_drift", False)

    # Recompute fingerprint at close
    try:
        fp_path = fp_module.write(root)
        current_hash = fp_module.compute(root)
    except OSError as exc:
        current_hash = ""
        _emit_human(f"WARNING: Could not update fingerprint: {exc}")

    # Update session_state.json
    state = sov_module.read_session_state(root)
    open_tasks = state.get("open_tasks", [])

    sov_module.write_session_state(
        root,
        last_agent=agent,
        last_action=action,
        open_tasks=open_tasks,
        topology_hash=current_hash,
        warm_start_valid=True,
    )

    # Append to PROVENANCE.md Session Log
    sov_module.update_session_log(
        root,
        agent=agent,
        action=action,
        topology_drift=topology_drift,
        next_action=next_action,
    )

    result = {
        "agent": agent,
        "action": action,
        "topology_drift": topology_drift,
        "fingerprint": current_hash,
        "provenance_updated": True,
        "session_state_updated": True,
    }

    if args.json:
        _emit_json(result)
    else:
        _emit_human("Session closed.")
        _emit_human(f"  Agent:          {agent}")
        _emit_human(f"  Action:         {action}")
        _emit_human(f"  Topology drift: {topology_drift}")
        _emit_human(f"  Fingerprint:    {current_hash}")
        _emit_human("  PROVENANCE.md Session Log updated.")
        _emit_human("  session_state.json updated.")

    _maybe_emit_signal(args, "session-close", "success", result)


def cmd_status(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    inv = boot_module.discover(root)
    warm_valid = boot_module.is_warm_valid(inv) if inv.branch != "COLD_START" else False
    matches, current_hash = fp_module.verify(root)
    state = sov_module.read_session_state(root)

    status: dict[str, Any] = {
        "project_root": str(root),
        "branch": inv.branch,
        "warm_valid": warm_valid,
        "tier1_signals": inv.tier1_signals,
        "tier2_signals": inv.tier2_signals,
        "tier3_signals": inv.tier3_signals,
        "fingerprint_matches": matches,
        "current_hash": current_hash,
        "last_agent": state.get("last_agent", ""),
        "last_action": state.get("last_action", ""),
        "last_timestamp": state.get("last_timestamp", ""),
        "open_tasks": state.get("open_tasks", []),
    }

    if args.json:
        _emit_json(status)
    else:
        _emit_human("CTMv3 Status")
        _emit_human(f"  Project root:      {root}")
        _emit_human(f"  Branch:            {inv.branch}")
        _emit_human(f"  Warm valid:        {warm_valid}")
        _emit_human(f"  Fingerprint match: {matches}")
        _emit_human(f"  Hash:              {current_hash}")
        _emit_human(f"  Tier 1 signals:    {inv.tier1_signals or 'none'}")
        _emit_human(f"  Last agent:        {state.get('last_agent', 'none')}")
        _emit_human(f"  Last action:       {state.get('last_action', 'none')}")
        _emit_human(f"  Last timestamp:    {state.get('last_timestamp', 'none')}")
        if state.get("open_tasks"):
            _emit_human("  Open tasks:")
            for task in state["open_tasks"]:
                _emit_human(f"    - {task}")

    _maybe_emit_signal(args, "status", "success", status)


def cmd_version(args: argparse.Namespace) -> None:
    result = {"version": __version__, "protocol": "CTMv3"}
    if args.json:
        _emit_json(result)
    else:
        _emit_human(f"CTMv3 Engine v{__version__} (protocol CTMv3)")
    # version does not participate in the golden-path chain


def cmd_chain(args: argparse.Namespace) -> None:
    """
    Walk the golden-path domino chain from --initial <command>.

    Executes initial_command as a subprocess, derives its exit state, looks up
    the next suggestion via pre_chain_rules, and continues until terminal or
    MAX_CHAIN_DEPTH steps. Emits one GoldenPathSignal per step to stdout under
    the CTMV3_GOLDEN_PATH sentinel as steps complete.

    Final output to stdout is a JSON array of all signals.
    """
    initial = args.initial
    root = Path(args.project_root).resolve()

    if not root.exists():
        _fail(f"Project root does not exist: {root}", exit_code=1)

    try:
        signals = orchestration_chain(initial, root)
    except ValueError as exc:
        _fail(str(exc), exit_code=1)
        return
    except ChainTooLongError as exc:
        _emit_human(f"ERROR: {exc}")
        sys.exit(2)

    # Output the JSON array of all signals
    output = [s.to_dict() for s in signals]
    _emit_json(output)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add --project-root, --json, and --no-golden-path to a subcommand parser."""
    parser.add_argument(
        "--project-root",
        default=".",
        metavar="PATH",
        help="Path to the project root directory (default: current working directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output machine-readable JSON to stdout",
    )
    parser.add_argument(
        "--no-golden-path",
        action="store_true",
        default=False,
        dest="no_golden_path",
        help=(
            "Suppress golden-path signal emission. Use in environments that do not "
            "consume the [CTMV3_GOLDEN_PATH] sentinel (e.g. nested chain subprocess calls)."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ctmv3",
        description=(
            "CTMv3 — Codebase Activation and Workspace Onboarding Engine. "
            "Turns a repository into a living, agent-operable workspace."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"CTMv3 {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", title="subcommands")
    subparsers.required = True

    # boot
    p_boot = subparsers.add_parser(
        "boot",
        help="Run BOOT_PROTOCOL discovery sequence and print signal inventory",
    )
    _add_common_args(p_boot)
    p_boot.set_defaults(func=cmd_boot)

    # activate
    p_activate = subparsers.add_parser(
        "activate",
        help="Full cold-start build: Phase 0-5, all artifacts",
    )
    _add_common_args(p_activate)
    p_activate.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing protected files (AGENTS.md, CLAUDE.md, etc.)",
    )
    p_activate.add_argument(
        "--dot-targets",
        default="all",
        choices=["all", "claude", "codex", "github"],
        help="Which .xyz directories to initialize (default: all)",
    )
    p_activate.set_defaults(func=cmd_activate)

    # warm
    p_warm = subparsers.add_parser(
        "warm",
        help="Warm-start protocol: check state validity and fingerprint",
    )
    _add_common_args(p_warm)
    p_warm.set_defaults(func=cmd_warm)

    # architecture-map
    p_arch = subparsers.add_parser(
        "architecture-map",
        help="Scaffold ARCHITECTURE_MAP.md",
    )
    _add_common_args(p_arch)
    p_arch.add_argument(
        "--from-topology",
        action="store_true",
        default=False,
        help="Extract project name from TOPOLOGY.md header",
    )
    p_arch.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing ARCHITECTURE_MAP.md",
    )
    p_arch.add_argument(
        "--project-name",
        default=None,
        metavar="NAME",
        help="Override the project name used in the template",
    )
    p_arch.set_defaults(func=cmd_architecture_map)

    # sovereign-init
    p_sov = subparsers.add_parser(
        "sovereign-init",
        help="Create .sovereign/ directory and seed files",
    )
    _add_common_args(p_sov)
    p_sov.set_defaults(func=cmd_sovereign_init)

    # dot-init
    p_dot = subparsers.add_parser(
        "dot-init",
        help="Create .xyz directories (claude, codex, github, or all)",
    )
    _add_common_args(p_dot)
    p_dot.add_argument(
        "--target",
        default="all",
        choices=["claude", "codex", "github", "all"],
        help="Which .xyz directory to initialize (default: all)",
    )
    p_dot.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing files in .xyz directories",
    )
    p_dot.add_argument(
        "--project-name",
        default=None,
        metavar="NAME",
        help="Override the project name used in templates",
    )
    p_dot.set_defaults(func=cmd_dot_init)

    # fingerprint
    p_fp = subparsers.add_parser(
        "fingerprint",
        help="Recompute and write .sovereign/topology_fingerprint.txt",
    )
    _add_common_args(p_fp)
    p_fp.set_defaults(func=cmd_fingerprint)

    # session-close
    p_close = subparsers.add_parser(
        "session-close",
        help="Update PROVENANCE.md Session Log and session_state.json",
    )
    _add_common_args(p_close)
    p_close.add_argument(
        "--agent",
        default="unknown",
        metavar="NAME",
        help="Agent name (e.g. 'Claude Code', 'Codex')",
    )
    p_close.add_argument(
        "--action",
        default="session close",
        metavar="DESC",
        help="Description of what was done this session",
    )
    p_close.add_argument(
        "--next-action",
        default="review open tasks",
        metavar="DESC",
        help="Recommended next action for the next agent session",
    )
    p_close.add_argument(
        "--topology-drift",
        action="store_true",
        default=False,
        help="Flag that topology drifted this session (triggers fingerprint update)",
    )
    p_close.set_defaults(func=cmd_session_close)

    # status
    p_status = subparsers.add_parser(
        "status",
        help="Print current CTMv3 state: branch, signals, fingerprint match",
    )
    _add_common_args(p_status)
    p_status.set_defaults(func=cmd_status)

    # version
    p_ver = subparsers.add_parser(
        "version",
        help="Print CTMv3 engine version",
    )
    _add_common_args(p_ver)
    p_ver.set_defaults(func=cmd_version)

    # chain (golden-path entry point)
    p_chain = subparsers.add_parser(
        "chain",
        help=(
            "Walk the golden-path domino chain from an initial command. "
            "Executes commands in sequence per pre-chain rules until terminal. "
            "Output is a JSON array of GoldenPathSignal envelopes."
        ),
    )
    _add_common_args(p_chain)
    p_chain.add_argument(
        "--initial",
        default="boot",
        metavar="COMMAND",
        help=(
            "Starting command for the chain (default: boot). "
            "Valid values: boot, activate, warm, fingerprint, architecture-map, "
            "sovereign-init, dot-init, session-close, status."
        ),
    )
    p_chain.set_defaults(func=cmd_chain)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
