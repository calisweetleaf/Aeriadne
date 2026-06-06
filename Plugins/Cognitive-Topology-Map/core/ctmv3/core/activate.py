"""
CTMv3 Activate — Cold-Start Build Orchestrator
===============================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Orchestrates the full cold-start build (Phase 0-5) as defined in
         BOOT_PROTOCOL.md Section 4 and SKILL.md Phase Protocols.

Phase ordering per BOOT_PROTOCOL.md Section 4.2 (Why This Order):
  Phase 0: discovery + signal inventory dump
  Phase 1: write TOPOLOGY.md skeleton
  Phase 2: write FAILURE_GRAMMAR.md skeleton
  Phase 3: write PROVENANCE.md (initialized with first session log entry)
  Phase 4: write ARCHITECTURE_MAP.md skeleton
  Phase 5: sovereign.init, dot_init, write AGENTS.md + CLAUDE.md, compute fingerprint

The --force flag must be passed explicitly to overwrite any of:
  AGENTS.md, CLAUDE.md, ARCHITECTURE_MAP.md, TOPOLOGY.md,
  FAILURE_GRAMMAR.md, PROVENANCE.md

Returns a structured report dict that is JSON-serializable for CLI --json output.

Hardening notes (v1.1.0):
  - Structured logging via stdlib logging.
  - Input validation: project_root must be a non-empty path and must be a directory
    (or creatable as one).
  - Atomic file writes via _atomic_write() helper (write to .tmp, then os.replace).
  - Fixed _scaffold_protected status logic: status is set BEFORE writing, not after.
  - _detect_language no longer returns a TODO string; falls back to "unknown".
  - All OSError paths log with context and re-raise or record in report.errors.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ctmv3.core import boot as boot_module
from ctmv3.core import fingerprint as fp_module
from ctmv3.core import sovereign as sov_module
from ctmv3.core import dot_init as dot_module
from ctmv3.core import architecture_map as arch_module
from ctmv3.core import templates as tmpl
from ctmv3.core.boot import SignalInventory


logger = logging.getLogger(__name__)

PROTECTED_FILES: list[str] = [
    "AGENTS.md",
    "CLAUDE.md",
    "ARCHITECTURE_MAP.md",
    "TOPOLOGY.md",
    "FAILURE_GRAMMAR.md",
    "PROVENANCE.md",
]


def run(
    project_root: Path,
    force: bool = False,
    dot_targets: str = "all",
) -> dict[str, Any]:
    """
    Execute the full CTMv3 cold-start activation sequence.

    Args:
        project_root: Absolute path to the target repository root. Must be an
                      existing directory or one that can be created.
        force: If True, overwrite existing protected files (AGENTS.md, CLAUDE.md, etc.)
        dot_targets: Which .xyz dirs to initialize: "all", "claude", "codex", "github"

    Returns:
        Structured report dict with keys:
          phase: str ("cold_start" | "partial" | "warm_aborted")
          signal_inventory: dict (from SignalInventory.to_dict())
          files_written: dict[str, str] (path -> status)
          fingerprint: str
          errors: list[str]
          aborted: bool
          abort_reason: str | None
          project_name: str
          today: str

    Raises:
        ValueError: If project_root is empty or not a directory (and not creatable).
    """
    if not project_root:
        raise ValueError(
            "project_root must be a non-empty path. Received empty value."
        )

    root = Path(project_root).resolve()
    logger.info("activate.run: starting; root=%s force=%s dot_targets=%s", root, force, dot_targets)

    today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
    report: dict[str, Any] = {
        "phase": "cold_start",
        "signal_inventory": {},
        "files_written": {},
        "fingerprint": "",
        "errors": [],
        "aborted": False,
        "abort_reason": None,
        "project_name": "",
        "today": today,
    }

    # Validate dot_targets early to avoid discovering the error deep in Phase 5
    _valid_dot_targets = {"all", "claude", "codex", "github"}
    if dot_targets not in _valid_dot_targets:
        raise ValueError(
            f"dot_targets must be one of {sorted(_valid_dot_targets)}, got '{dot_targets}'."
        )

    # Phase 0: Discovery
    try:
        inv = boot_module.discover(root)
    except ValueError as exc:
        # project_root does not exist or is not a directory
        logger.error("activate.run: discovery failed: %s", exc)
        raise

    report["signal_inventory"] = inv.to_dict()

    # Check for conflicts on warm/partial repos without --force
    if inv.branch in ("WARM_START", "PARTIAL"):
        protected_present = [
            f for f in PROTECTED_FILES if (root / f).exists()
        ]
        if protected_present and not force:
            abort_reason = (
                f"Repo has existing CTM artifacts: {protected_present}. "
                "Pass --force to overwrite, or use 'ctmv3 warm' for a warm-start continuation."
            )
            logger.warning("activate.run: aborting; %s", abort_reason)
            report["aborted"] = True
            report["abort_reason"] = abort_reason
            report["phase"] = "aborted_existing_artifacts"
            return report

    report["phase"] = inv.branch.lower()

    # Derive project name
    project_name = arch_module._infer_project_name(root)
    report["project_name"] = project_name
    logger.debug("activate.run: project_name=%s", project_name)

    # Detect language from config spine
    language = _detect_language(inv)
    logger.debug("activate.run: detected language=%s", language)

    # Build config flags for TOPOLOGY template
    config_flags = {
        "HAS_PYPROJECT": "yes" if (root / "pyproject.toml").exists() else "no",
        "HAS_GOMOD": "yes" if (root / "go.mod").exists() else "no",
        "HAS_CARGO": "yes" if (root / "Cargo.toml").exists() else "no",
        "HAS_PACKAGEJSON": "yes" if (root / "package.json").exists() else "no",
        "HAS_MANIFEST": "yes" if (root / "manifest.json").exists() else "no",
        "HAS_AGENTS": "yes" if (root / "AGENTS.md").exists() else "no",
        "HAS_CLAUDE": "yes" if (root / "CLAUDE.md").exists() else "no",
        "HAS_SOVEREIGN": "yes" if (root / ".sovereign").exists() else "no",
        "HAS_GITHUB": "yes" if (root / ".github").exists() else "no",
    }

    # Phase 1: TOPOLOGY.md
    _scaffold_protected(
        root / "TOPOLOGY.md",
        tmpl.render_topology(project_name, today, language, **config_flags),
        force=force,
        results=report["files_written"],
    )

    # Phase 2: FAILURE_GRAMMAR.md
    _scaffold_protected(
        root / "FAILURE_GRAMMAR.md",
        tmpl.render_failure_grammar(project_name, today),
        force=force,
        results=report["files_written"],
    )

    # Phase 3: PROVENANCE.md
    _scaffold_protected(
        root / "PROVENANCE.md",
        tmpl.render_provenance(project_name, today),
        force=force,
        results=report["files_written"],
    )

    # Phase 4: ARCHITECTURE_MAP.md
    _scaffold_protected(
        root / "ARCHITECTURE_MAP.md",
        tmpl.render_architecture_map(project_name),
        force=force,
        results=report["files_written"],
    )

    # Phase 5: Ecosystem artifacts

    # 5a: AGENTS.md
    _scaffold_protected(
        root / "AGENTS.md",
        tmpl.render_agents_md(project_name),
        force=force,
        results=report["files_written"],
    )

    # 5b: CLAUDE.md at root (not in .claude/ — that is handled by dot_init)
    _scaffold_protected(
        root / "CLAUDE.md",
        tmpl.render_claude_md(project_name),
        force=force,
        results=report["files_written"],
    )

    # 5c: .sovereign/ initialization
    try:
        sov_module.init(root)
        report["files_written"][str(root / ".sovereign")] = "initialized"
        logger.info("activate.run: .sovereign/ initialized")
    except OSError as exc:
        msg = f".sovereign/ init failed: {exc}"
        logger.error("activate.run: %s", msg)
        report["errors"].append(msg)

    # 5d: .xyz directory initialization
    try:
        dot_results = dot_module.init_target(
            dot_targets,  # type: ignore[arg-type]
            root,
            project_name,
            force=force,
        )
        report["files_written"].update(dot_results)
        logger.info("activate.run: dot_init completed; target=%s files=%d", dot_targets, len(dot_results))
    except ValueError as exc:
        msg = f"dot_init target error: {exc}"
        logger.error("activate.run: %s", msg)
        report["errors"].append(msg)
    except OSError as exc:
        msg = f"dot_init OSError: {exc}"
        logger.error("activate.run: %s", msg)
        report["errors"].append(msg)

    # 5e: Compute and write fingerprint
    try:
        fp_path = fp_module.write(root)
        current_hash = fp_module.compute(root)
        report["fingerprint"] = current_hash
        report["files_written"][str(fp_path)] = "written"
        logger.info("activate.run: fingerprint written; hash=%s", current_hash[:20])
    except OSError as exc:
        msg = f"fingerprint write failed: {exc}"
        logger.error("activate.run: %s", msg)
        report["errors"].append(msg)
        report["fingerprint"] = ""

    # 5f: Write initial session state
    try:
        sov_module.write_session_state(
            root,
            last_agent="CTMv3 Engine",
            last_action="Initial cold-start activation",
            open_tasks=[
                "Fill TOPOLOGY.md LBC sections",
                "Fill ARCHITECTURE_MAP.md branches with file:line anchors",
                "Fill AGENTS.md with project-specific content",
                "Fill FAILURE_GRAMMAR.md with domain-specific patterns",
            ],
            topology_hash=report["fingerprint"],
            warm_start_valid=False,
        )
        logger.info("activate.run: session state written")
    except OSError as exc:
        msg = f"session_state write failed: {exc}"
        logger.error("activate.run: %s", msg)
        report["errors"].append(msg)

    logger.info(
        "activate.run: complete; phase=%s files_written=%d errors=%d",
        report["phase"],
        len(report["files_written"]),
        len(report["errors"]),
    )
    return report


def _scaffold_protected(
    path: Path,
    content: str,
    force: bool,
    results: dict[str, str],
) -> None:
    """
    Write content to path respecting the --force semantics for protected files.

    Uses atomic write (write to .tmp then os.replace) so a crash mid-write
    cannot leave a partially-written file.

    Status semantics:
      "skipped"          -- file exists and force=False
      "force-overwritten" -- file existed and force=True
      "created"          -- file did not exist

    Raises:
        OSError: If the directory cannot be created or the file cannot be written.
    """
    if path.exists() and not force:
        results[str(path)] = "skipped"
        logger.debug("_scaffold_protected: skipped (exists, no force) path=%s", path)
        return

    # Determine status BEFORE writing (path.exists() is accurate here)
    status = "force-overwritten" if path.exists() else "created"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(path, content)
    except OSError as exc:
        logger.error("_scaffold_protected: write failed path=%s: %s", path, exc)
        raise

    results[str(path)] = status
    logger.debug("_scaffold_protected: %s path=%s", status, path)


def _atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write content to path atomically: write to path.tmp, then os.replace to path.

    This ensures that a crash or KeyboardInterrupt mid-write cannot leave a
    partially-written target file. The .tmp file may be left behind on crash,
    but the target is always either the old version or the complete new version.

    Raises:
        OSError: If the write or rename fails.
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding=encoding)
        os.replace(str(tmp_path), str(path))
    except OSError:
        # Best-effort cleanup of the .tmp file; if this fails, ignore it
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _detect_language(inv: SignalInventory) -> str:
    """
    Detect the primary language from the config spine signals in the inventory.
    Returns a human-readable string like "python", "go", "rust", "javascript", or "mixed".
    Falls back to "unknown" when no config spine signals are present.
    """
    found: list[str] = []
    spine = inv.config_spine

    if spine.get("pyproject.toml") or spine.get("setup.py") or spine.get("setup.cfg"):
        found.append("python")
    if spine.get("go.mod"):
        found.append("go")
    if spine.get("Cargo.toml"):
        found.append("rust")
    if spine.get("package.json"):
        found.append("javascript")

    if len(found) == 0:
        return "unknown"
    if len(found) == 1:
        return found[0]
    return "mixed (" + ", ".join(found) + ")"
