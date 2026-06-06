"""
CTMv3 Sovereign — .sovereign/ Directory Management
===================================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Creates and manages the .sovereign/ directory, session_state.json,
         golden_paths.json, and appends to the PROVENANCE.md Session Log.
         Implements the .sovereign/ encoding from DOT_TOPOLOGY.md.

The .sovereign/ directory is the session continuity anchor. Its presence is a
Tier 1 CTM signal (BOOT_PROTOCOL.md Section 1). It must be initialized after
the topology artifacts are complete, not before (BOOT_PROTOCOL.md Section 4.2).

Hardening notes (v1.1.0):
  - Structured logging via stdlib logging.
  - All file writes are atomic (write to .tmp then os.replace).
  - Input validation: last_agent and last_action must be non-empty strings.
  - update_session_log now atomic; OSError on read is logged and returned early
    rather than silently dropped.
  - golden_paths.json seed write is atomic.
  - _write_session_state_seed is atomic.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger(__name__)

SOVEREIGN_DIR: str = ".sovereign"
SESSION_STATE_FILE: str = "session_state.json"
GOLDEN_PATHS_FILE: str = "golden_paths.json"
FINGERPRINT_FILE: str = "topology_fingerprint.txt"

# Session Log rotation thresholds (PR1 — prevents unbounded PROVENANCE.md growth)
MAX_SESSION_LOG_ROWS: int = 500
SESSION_LOG_RETAIN_ROWS: int = 50  # rows to retain in PROVENANCE.md after rotation

# Seed content from DOT_TOPOLOGY.md .sovereign/ section
GOLDEN_PATHS_SEED: dict[str, Any] = {
    "ctm_session_bootstrap": {
        "chain": ["bb7_exo_bootstrap", "bb7_lisan_intend", "bb7_exo_route"],
        "priors": {"alpha": 7.0, "beta": 1.0},
        "use_cases": ["CTM session start", "skill-guided repo entry"],
        "tags": ["ctm", "session", "bootstrap"],
    }
}

SESSION_STATE_INITIAL: dict[str, Any] = {
    "session_id": "",
    "last_agent": "",
    "last_timestamp": "",
    "last_action": "Initial CTMv3 activation",
    "open_tasks": [
        "Fill TOPOLOGY.md LBC sections",
        "Fill ARCHITECTURE_MAP.md branches with file:line anchors",
        "Fill AGENTS.md with project-specific content",
    ],
    "topology_hash": "",
    "warm_start_valid": False,
}


def _sovereign_dir(project_root: Path) -> Path:
    return Path(project_root).resolve() / SOVEREIGN_DIR


def init(project_root: Path) -> None:
    """
    Create .sovereign/ directory and seed all initial files.

    Files created:
      .sovereign/session_state.json  -- initial session state
      .sovereign/golden_paths.json   -- seeded with ctm_session_bootstrap chain
      .sovereign/topology_fingerprint.txt -- placeholder (overwritten by fingerprint.write)

    Idempotent: existing files are not overwritten (unless they are malformed).
    Per BOOT_PROTOCOL.md Section 6 Failure 4: malformed session_state.json is
    silently replaced with a fresh seed.

    Raises:
        OSError: If the .sovereign/ directory cannot be created or files cannot be written.
    """
    root = Path(project_root).resolve()
    sov = _sovereign_dir(root)
    sov.mkdir(parents=True, exist_ok=True)
    logger.debug("init: .sovereign/ created or confirmed at %s", sov)

    # session_state.json — seed or repair if malformed
    ss_path = sov / SESSION_STATE_FILE
    if ss_path.exists():
        try:
            existing = json.loads(ss_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                raise ValueError("session_state.json is not a JSON object")
            logger.debug("init: session_state.json already valid; preserving")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.warning(
                "init: session_state.json malformed or unreadable (%s); reseeding", exc
            )
            _write_session_state_seed(ss_path)
    else:
        _write_session_state_seed(ss_path)
        logger.info("init: session_state.json seeded at %s", ss_path)

    # golden_paths.json — seed if absent, do not overwrite existing
    gp_path = sov / GOLDEN_PATHS_FILE
    if not gp_path.exists():
        _atomic_write_json(gp_path, GOLDEN_PATHS_SEED)
        logger.info("init: golden_paths.json seeded at %s", gp_path)
    else:
        logger.debug("init: golden_paths.json already present; preserving")

    # topology_fingerprint.txt placeholder — only write if absent
    fp_path = sov / FINGERPRINT_FILE
    if not fp_path.exists():
        placeholder = (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
            "\nPlaceholder — run: python -m ctmv3 fingerprint to compute real hash.\n"
        )
        _atomic_write(fp_path, placeholder)
        logger.info("init: topology_fingerprint.txt placeholder written at %s", fp_path)
    else:
        logger.debug("init: topology_fingerprint.txt already present; preserving")


def _write_session_state_seed(ss_path: Path) -> None:
    """Write a fresh session_state.json seed atomically."""
    state = dict(SESSION_STATE_INITIAL)
    state["session_id"] = str(uuid.uuid4())
    state["last_timestamp"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    _atomic_write_json(ss_path, state)


def read_session_state(project_root: Path) -> dict:
    """
    Read .sovereign/session_state.json and return its contents as a dict.

    Returns a fresh seed dict if the file is absent or malformed.
    Never raises — per BOOT_PROTOCOL.md Section 6 Failure 4, malformed state
    is treated as a seed signal, not an error.
    """
    ss_path = _sovereign_dir(project_root) / SESSION_STATE_FILE
    if not ss_path.exists():
        logger.debug("read_session_state: file absent; returning seed")
        return dict(SESSION_STATE_INITIAL)

    try:
        raw = ss_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        logger.warning(
            "read_session_state: session_state.json is not a dict in %s; returning seed",
            ss_path,
        )
        return dict(SESSION_STATE_INITIAL)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "read_session_state: cannot parse %s (%s); returning seed", ss_path, exc
        )
        return dict(SESSION_STATE_INITIAL)


def write_session_state(
    project_root: Path,
    *,
    last_agent: str,
    last_action: str,
    open_tasks: list[str],
    topology_hash: str = "",
    warm_start_valid: bool = True,
) -> None:
    """
    Update .sovereign/session_state.json with current session information.

    Used by session-close (BOOT_PROTOCOL.md Section 5). Creates .sovereign/ if absent.
    Reads existing state and updates only the provided fields, preserving session_id.
    Write is atomic.

    Args:
        project_root: Path to the project root directory.
        last_agent: Name of the agent closing the session. Must be non-empty.
        last_action: Description of the last action performed. Must be non-empty.
        open_tasks: List of tasks left open for the next session.
        topology_hash: Current topology fingerprint hash.
        warm_start_valid: Whether the session state is valid for warm start.

    Raises:
        ValueError: If last_agent or last_action is empty.
        OSError: If .sovereign/ cannot be created or session_state.json cannot be written.
    """
    if not last_agent or not last_agent.strip():
        raise ValueError(
            "last_agent must be a non-empty string. "
            "Received empty or whitespace-only value."
        )
    if not last_action or not last_action.strip():
        raise ValueError(
            "last_action must be a non-empty string. "
            "Received empty or whitespace-only value."
        )

    root = Path(project_root).resolve()
    sov = _sovereign_dir(root)
    sov.mkdir(parents=True, exist_ok=True)
    ss_path = sov / SESSION_STATE_FILE

    # Load existing state or seed fresh
    try:
        raw = ss_path.read_text(encoding="utf-8")
        existing: dict = json.loads(raw)
        if not isinstance(existing, dict):
            existing = {}
    except (json.JSONDecodeError, OSError) as exc:
        logger.debug(
            "write_session_state: cannot load existing state (%s); starting fresh", exc
        )
        existing = {}

    session_id = existing.get("session_id") or str(uuid.uuid4())

    state: dict[str, Any] = {
        "session_id": session_id,
        "last_agent": last_agent.strip(),
        "last_timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "last_action": last_action.strip(),
        "open_tasks": open_tasks,
        "topology_hash": topology_hash,
        "warm_start_valid": warm_start_valid,
    }

    _atomic_write_json(ss_path, state)
    logger.info(
        "write_session_state: written; agent=%s action=%s",
        last_agent,
        last_action[:60],
    )


def update_session_log(
    project_root: Path,
    *,
    agent: str,
    action: str,
    topology_drift: bool,
    next_action: str,
) -> None:
    """
    Append a row to the PROVENANCE.md Session Log table.

    Per BOOT_PROTOCOL.md Section 5: every CTM-active session must close cleanly
    by logging to PROVENANCE.md. This function handles the append-only write.

    Format: | Date | Agent | Action | Topology Drift? | Next Recommended Action |

    If PROVENANCE.md does not exist or has no Session Log section, a minimal
    Session Log section is appended. Existing content is never overwritten.
    Write is atomic.

    Args:
        project_root: Path to the project root directory.
        agent: Agent name for the session log row. Must be non-empty.
        action: Action description for the session log row. Must be non-empty.
        topology_drift: Whether topology drifted during this session.
        next_action: Recommended next action for the next session.

    Raises:
        ValueError: If agent or action is empty.
    """
    if not agent or not agent.strip():
        raise ValueError(
            "agent must be a non-empty string."
        )
    if not action or not action.strip():
        raise ValueError(
            "action must be a non-empty string."
        )

    root = Path(project_root).resolve()
    prov_path = root / "PROVENANCE.md"

    today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
    drift_str = "yes" if topology_drift else "no"
    new_row = (
        f"| {today} | {agent.strip()} | {action.strip()} "
        f"| {drift_str} | {next_action.strip()} |"
    )

    if not prov_path.exists():
        content = _minimal_provenance(new_row)
        _atomic_write(prov_path, content)
        logger.info("update_session_log: created PROVENANCE.md at %s", prov_path)
        return

    try:
        text = prov_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error(
            "update_session_log: cannot read PROVENANCE.md at %s: %s", prov_path, exc
        )
        return

    if "## Session Log" in text:
        updated = _append_to_session_log(text, new_row)
        _atomic_write(prov_path, updated)
    else:
        section = _session_log_section(new_row)
        _atomic_write(prov_path, text.rstrip() + "\n\n" + section)

    # Check if rotation is needed after append
    try:
        current_text = prov_path.read_text(encoding="utf-8")
        rotated_text = _rotate_session_log_if_needed(root, prov_path, current_text)
        if rotated_text is not current_text:  # identity check: rotation occurred
            _atomic_write(prov_path, rotated_text)
    except OSError as exc:
        logger.warning("update_session_log: rotation check failed: %s", exc)

    logger.info(
        "update_session_log: appended row; agent=%s drift=%s", agent, topology_drift
    )


def _rotate_session_log_if_needed(
    project_root: Path,
    prov_path: Path,
    text: str,
) -> str:
    """
    If the Session Log section exceeds MAX_SESSION_LOG_ROWS data rows,
    archive the older rows to .sovereign/provenance_archive_{date}.md
    and retain only the last SESSION_LOG_RETAIN_ROWS rows in PROVENANCE.md.

    Returns the (potentially modified) PROVENANCE.md text. If rotation does not
    occur, returns the exact same object (identity check: ``is not`` returns False
    only on actual rotation).

    Archive write is atomic via _atomic_write. If archive write fails, rotation is
    skipped (better to have an oversized log than lose history).
    """
    lines = text.splitlines(keepends=True)
    session_log_start: Optional[int] = None
    table_rows: list[tuple[int, str]] = []  # (line_index, row_text)

    for i, line in enumerate(lines):
        if "## Session Log" in line:
            session_log_start = i
            continue
        if session_log_start is not None and i > session_log_start:
            stripped = line.strip()
            if stripped.startswith("|"):
                # Skip the header row and separator rows
                cols = [c.strip() for c in stripped.split("|") if c.strip()]
                if not cols:
                    continue
                # Skip header row (starts with "Date")
                if cols[0] == "Date":
                    continue
                # Skip separator rows (cells are all dashes)
                is_sep = all(set(c.replace("-", "")) == set() for c in cols)
                if is_sep:
                    continue
                table_rows.append((i, line))
            elif stripped.startswith("#") and i > session_log_start:
                # Reached next section — stop
                break

    if len(table_rows) <= MAX_SESSION_LOG_ROWS:
        return text  # no rotation needed — return same object

    # Rotation needed
    archive_rows = table_rows[:-SESSION_LOG_RETAIN_ROWS]
    retain_rows = table_rows[-SESSION_LOG_RETAIN_ROWS:]

    # Write archive
    sov_dir = _sovereign_dir(project_root)
    sov_dir.mkdir(parents=True, exist_ok=True)
    archive_date = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y%m%d_%H")
    archive_path = sov_dir / f"provenance_archive_{archive_date}.md"

    archive_header = (
        "# PROVENANCE Session Log Archive\n\n"
        f"Archived: {archive_date}\n"
        f"Rows archived: {len(archive_rows)}\n\n"
        "## Session Log\n\n"
        "| Date | Agent | Action | Topology Drift? | Next Recommended Action |\n"
        "|------|-------|--------|----------------|------------------------|\n"
    )
    archive_content = archive_header + "".join(row for _, row in archive_rows)

    try:
        _atomic_write(archive_path, archive_content)
        logger.info(
            "_rotate_session_log_if_needed: archived %d rows to %s",
            len(archive_rows),
            archive_path,
        )
    except OSError as exc:
        logger.error(
            "_rotate_session_log_if_needed: archive write failed (%s); skipping rotation",
            exc,
        )
        return text  # Better an oversized log than lost history

    # Rebuild the text with only retained rows (archive rows removed)
    archive_line_indices = {idx for idx, _ in archive_rows}
    new_lines = [line for i, line in enumerate(lines) if i not in archive_line_indices]

    logger.info(
        "_rotate_session_log_if_needed: rotated; retained %d rows, archived %d rows",
        len(retain_rows),
        len(archive_rows),
    )
    return "".join(new_lines)


def _append_to_session_log(text: str, new_row: str) -> str:
    """
    Insert new_row after the last data row in the Session Log table.
    If the table has no data rows yet, append after the header row.
    """
    lines = text.splitlines(keepends=True)
    session_log_idx: Optional[int] = None
    last_table_row_idx: Optional[int] = None

    for i, line in enumerate(lines):
        if "## Session Log" in line:
            session_log_idx = i
        if session_log_idx is not None and i > session_log_idx:
            stripped = line.strip()
            # Detect table rows: start with | and not the separator ---
            if stripped.startswith("|") and "---" not in stripped:
                last_table_row_idx = i
            elif stripped.startswith("#"):
                # Reached next section — stop
                break

    if last_table_row_idx is not None:
        lines.insert(last_table_row_idx + 1, new_row + "\n")
    elif session_log_idx is not None:
        # Append after the Session Log heading
        header = "| Date | Agent | Action | Topology Drift? | Next Recommended Action |\n"
        sep = "|------|-------|--------|----------------|------------------------|\n"
        lines.insert(session_log_idx + 1, "\n")
        lines.insert(session_log_idx + 2, header)
        lines.insert(session_log_idx + 3, sep)
        lines.insert(session_log_idx + 4, new_row + "\n")

    return "".join(lines)


def _session_log_section(first_row: str) -> str:
    return (
        "## Session Log\n\n"
        "| Date | Agent | Action | Topology Drift? | Next Recommended Action |\n"
        "|------|-------|--------|----------------|------------------------|\n"
        f"{first_row}\n"
    )


def _minimal_provenance(first_row: str) -> str:
    return (
        "# PROVENANCE\n\n"
        "This file was created automatically by CTMv3. "
        "Fill the template sections as work progresses.\n\n"
        + _session_log_section(first_row)
    )


def _atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write a text string to path atomically via a .tmp intermediate file.

    Raises:
        OSError: If the write or rename fails.
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding=encoding)
        os.replace(str(tmp_path), str(path))
    except OSError:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _atomic_write_json(path: Path, data: Any, indent: int = 2) -> None:
    """
    Serialize data to JSON and write to path atomically.

    Raises:
        OSError: If the write or rename fails.
    """
    content = json.dumps(data, indent=indent) + "\n"
    _atomic_write(path, content)
