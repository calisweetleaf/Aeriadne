"""
CTMv3 Boot Protocol — Discovery Sequence and Branch Classification
==================================================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Implements BOOT_PROTOCOL.md Section 1 (signal taxonomy) and Section 2
         (discovery sequence). Returns a SignalInventory dataclass used by all
         downstream phases to determine cold vs warm entry.

No writes occur in this module. All operations are read-only scans.

Hardening notes (v1.1.0):
  - Structured logging via stdlib logging at module level.
  - Discovery scan bounded by MAX_SCAN_DEPTH and MAX_FILE_COUNT to prevent
    runaway on large repositories. Both bounds are enforced during the file-count
    scan that underlies any future depth-aware traversal; signal-tier checks are
    direct path lookups and are not affected by the bounds.
  - Input validation: project_root must be an existing directory.
  - File reads wrapped with specific OSError / UnicodeDecodeError handling.
  - Fixed operator-precedence ambiguity in _extract_last_session condition.
  - is_warm_valid age comparison now timezone-safe.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Discovery bounds — prevents runaway scan on huge repos
# ---------------------------------------------------------------------------

MAX_SCAN_DEPTH: int = 5
MAX_FILE_COUNT: int = 10_000


# ---------------------------------------------------------------------------
# Signal taxonomy (BOOT_PROTOCOL.md Section 1)
# ---------------------------------------------------------------------------

TIER1_PATHS: list[str] = [
    ".sovereign",
    "ARCHITECTURE_MAP.md",
    ".claude/CLAUDE.md",
    "AGENTS.md",
]

TIER2_PATHS: list[str] = [
    ".github/copilot-instructions.md",
    ".codex/skills",
    "PROVENANCE.md",
    "manifest.json",
    "golden_paths.json",
]

TIER3_PATHS: list[str] = [
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "package.json",
    ".env.example",
]


@dataclass
class SignalInventory:
    """
    Output of discover(). Encodes all CTM presence signals found in the repo.
    Used by classify_branch() and is_warm_valid() to determine the execution path.
    """

    project_root: Path
    tier1_signals: list[str] = field(default_factory=list)
    tier2_signals: list[str] = field(default_factory=list)
    tier3_signals: list[str] = field(default_factory=list)
    provenance_present: bool = False
    manifest_present: bool = False
    last_session: Optional[str] = None
    branch: Literal["COLD_START", "WARM_START", "PARTIAL"] = "COLD_START"
    config_spine: dict[str, bool] = field(default_factory=dict)
    session_state_valid: bool = False
    session_timestamp: Optional[datetime] = None
    file_count: int = 0  # total files scanned during discovery (bounded by MAX_FILE_COUNT)

    def to_dict(self) -> dict:
        """Return JSON-serializable representation."""
        return {
            "project_root": str(self.project_root),
            "tier1_signals": self.tier1_signals,
            "tier2_signals": self.tier2_signals,
            "tier3_signals": self.tier3_signals,
            "provenance_present": self.provenance_present,
            "manifest_present": self.manifest_present,
            "last_session": self.last_session,
            "branch": self.branch,
            "config_spine": self.config_spine,
            "session_state_valid": self.session_state_valid,
            "session_timestamp": (
                self.session_timestamp.isoformat() if self.session_timestamp else None
            ),
            "file_count": self.file_count,
        }


# ---------------------------------------------------------------------------
# Discovery sequence
# ---------------------------------------------------------------------------


def discover(project_root: Path) -> SignalInventory:
    """
    Run the BOOT_PROTOCOL.md Section 2 discovery sequence (read-only).

    Steps performed:
      1. Root scan for Tier 1 signals
      2. .xyz directory inventory for Tier 2 signals
      3. Config spine scan for Tier 3 signals
      4. AGENTS.md / CLAUDE.md presence check
      5. PROVENANCE.md check (Session Log extraction)
      6. manifest.json check
      7. session_state.json read (if present)
      8. Bounded file count scan (enforces MAX_SCAN_DEPTH and MAX_FILE_COUNT)

    Args:
        project_root: Path to the project root directory. Must exist and be a directory.

    Returns:
        SignalInventory with all findings and branch classification.

    Raises:
        ValueError: If project_root does not exist or is not a directory.
        OSError: If the root directory cannot be read (permissions).
    """
    root = Path(project_root).resolve()

    if not root.exists():
        raise ValueError(
            f"project_root does not exist: {root}. "
            "Pass an existing directory path."
        )
    if not root.is_dir():
        raise ValueError(
            f"project_root is not a directory: {root}. "
            "Pass a directory, not a file."
        )

    logger.debug("discover: scanning %s", root)
    inv = SignalInventory(project_root=root)

    # Step 1 + 2 — Tier 1 and Tier 2 signals (direct path lookups, not a tree walk)
    for rel in TIER1_PATHS:
        p = root / rel
        if p.exists():
            inv.tier1_signals.append(rel)
            logger.debug("discover: Tier 1 signal found: %s", rel)

    for rel in TIER2_PATHS:
        p = root / rel
        if p.exists():
            inv.tier2_signals.append(rel)
            logger.debug("discover: Tier 2 signal found: %s", rel)

    # Step 3 — Tier 3 config spine
    for rel in TIER3_PATHS:
        p = root / rel
        present = p.exists()
        if present:
            inv.tier3_signals.append(rel)
        inv.config_spine[rel] = present
        if present:
            logger.debug("discover: Tier 3 config spine: %s", rel)

    # Step 4 — AGENTS.md / CLAUDE.md (subset of Tier 1, already captured above)

    # Step 5 — PROVENANCE.md
    prov_path = root / "PROVENANCE.md"
    if prov_path.exists():
        inv.provenance_present = True
        inv.last_session = _extract_last_session(prov_path)
        logger.debug(
            "discover: PROVENANCE.md present; last_session=%r", inv.last_session
        )

    # Step 6 — manifest.json
    if (root / "manifest.json").exists():
        inv.manifest_present = True
        logger.debug("discover: manifest.json present")

    # Step 7 — session_state.json
    ss_path = root / ".sovereign" / "session_state.json"
    if ss_path.exists():
        inv.session_state_valid, inv.session_timestamp = _read_session_state_meta(
            ss_path
        )
        logger.debug(
            "discover: session_state valid=%s timestamp=%s",
            inv.session_state_valid,
            inv.session_timestamp,
        )

    # Step 8 — bounded file count scan
    inv.file_count = _count_files_bounded(root, MAX_SCAN_DEPTH, MAX_FILE_COUNT)
    logger.debug("discover: file_count=%d (cap=%d)", inv.file_count, MAX_FILE_COUNT)
    if inv.file_count >= MAX_FILE_COUNT:
        logger.warning(
            "discover: file count hit cap of %d at depth %d in %s. "
            "Some files may not have been counted.",
            MAX_FILE_COUNT,
            MAX_SCAN_DEPTH,
            root,
        )

    # Final classification
    inv.branch = classify_branch(inv)
    logger.info(
        "discover: complete; branch=%s tier1=%s file_count=%d",
        inv.branch,
        inv.tier1_signals,
        inv.file_count,
    )
    return inv


def _count_files_bounded(root: Path, max_depth: int, max_count: int) -> int:
    """
    Count files under root up to max_depth directory levels and max_count files.

    Returns the count found (which may be max_count if the tree is larger).
    Uses os.scandir for efficiency instead of Path.rglob to respect bounds.
    """
    count = 0

    def _walk(directory: Path, depth: int) -> None:
        nonlocal count
        if depth > max_depth or count >= max_count:
            return
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if count >= max_count:
                        return
                    if entry.is_file(follow_symlinks=False):
                        count += 1
                    elif entry.is_dir(follow_symlinks=False):
                        _walk(Path(entry.path), depth + 1)
        except OSError as exc:
            logger.debug("_count_files_bounded: cannot scan %s: %s", directory, exc)

    _walk(root, 0)
    return count


def _extract_last_session(prov_path: Path) -> Optional[str]:
    """
    Scan PROVENANCE.md for the last Session Log row.
    Returns a string like "2026-05-20 | Claude Code | ..." or None.
    """
    try:
        text = prov_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning(
            "_extract_last_session: cannot read %s: %s", prov_path, exc
        )
        return None

    in_session_log = False
    last_row: Optional[str] = None
    for line in text.splitlines():
        stripped = line.strip()
        # Detect Session Log heading robustly: handle both "## Session Log" and
        # other heading levels that mention "Session Log".
        if "## Session Log" in stripped or (
            "Session Log" in stripped and stripped.startswith("#")
        ):
            in_session_log = True
            continue
        if in_session_log and stripped.startswith("#"):
            # Moved to a new section — stop scanning
            break
        if (
            in_session_log
            and stripped.startswith("|")
            and not stripped.startswith("| Date")
        ):
            # Skip separator rows where every cell consists solely of dashes and spaces
            cols = [c.strip() for c in stripped.split("|") if c.strip()]
            if cols and cols[0] not in ("---", "Date"):
                # Exclude separator rows: a cell that is all dashes (like "------")
                is_separator = all(set(c.replace("-", "")) == set() or c == "" for c in cols)
                if not is_separator:
                    last_row = stripped
    return last_row


def _read_session_state_meta(ss_path: Path) -> tuple[bool, Optional[datetime]]:
    """
    Read session_state.json and return (is_valid, timestamp).
    Returns (False, None) on any parse error per BOOT_PROTOCOL.md Section 6 Failure 4.
    """
    try:
        raw = ss_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("_read_session_state_meta: cannot read %s: %s", ss_path, exc)
        return False, None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning(
            "_read_session_state_meta: malformed JSON in %s: %s", ss_path, exc
        )
        return False, None

    if not isinstance(data, dict):
        logger.warning(
            "_read_session_state_meta: session_state.json is not a JSON object in %s",
            ss_path,
        )
        return False, None

    ts_str = data.get("last_timestamp")
    ts: Optional[datetime] = None
    if ts_str and isinstance(ts_str, str):
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            logger.debug(
                "_read_session_state_meta: unparseable timestamp %r in %s",
                ts_str,
                ss_path,
            )

    return True, ts


# ---------------------------------------------------------------------------
# Branch classification
# ---------------------------------------------------------------------------


def classify_branch(
    inv: SignalInventory,
) -> Literal["COLD_START", "WARM_START", "PARTIAL"]:
    """
    Classify the repo's boot state based on the signal inventory.

    WARM_START:  at least one Tier 1 signal AND PROVENANCE.md present AND
                 Session Log has at least one entry.
    PARTIAL:     at least one Tier 1 signal but missing PROVENANCE.md or
                 empty Session Log (BOOT_PROTOCOL.md Section 6 Failure 2).
    COLD_START:  no Tier 1 signals.
    """
    has_tier1 = bool(inv.tier1_signals)

    if not has_tier1:
        return "COLD_START"

    if inv.provenance_present and inv.last_session:
        return "WARM_START"

    # Tier 1 signals present but provenance missing or empty Session Log
    return "PARTIAL"


def is_warm_valid(inv: SignalInventory, age_days_threshold: int = 30) -> bool:
    """
    Warm validity check per BOOT_PROTOCOL.md Section 3.1.

    Returns True only if:
    1. Branch is WARM_START
    2. session_state.json is readable and not older than age_days_threshold days

    Note: This engine cannot answer "topology still valid?" programmatically —
    that question requires agent judgement. This function covers the mechanical
    checks only (presence + age).

    Args:
        inv: SignalInventory from discover().
        age_days_threshold: Maximum age in days for a warm state to be considered
                            valid. Defaults to 30 per BOOT_PROTOCOL.md Section 3.

    Raises:
        ValueError: If age_days_threshold is negative.
    """
    if age_days_threshold < 0:
        raise ValueError(
            f"age_days_threshold must be non-negative, got {age_days_threshold}"
        )

    if inv.branch != "WARM_START":
        return False

    if not inv.session_state_valid:
        return False

    if inv.session_timestamp is not None:
        # Normalize to naive UTC. Timestamps from this engine are always naive UTC.
        # If a timezone-aware timestamp arrives (e.g., from external tooling), strip
        # the tzinfo by converting to UTC first.
        stored_ts = inv.session_timestamp
        if stored_ts.tzinfo is not None:
            offset = stored_ts.utcoffset() or timedelta(0)
            stored_ts = stored_ts.replace(tzinfo=None) - offset
        age = datetime.now(timezone.utc).replace(tzinfo=None) - stored_ts
        if age > timedelta(days=age_days_threshold):
            logger.debug(
                "is_warm_valid: session is stale (%s days > threshold %s)",
                age.days,
                age_days_threshold,
            )
            return False

    return True


def discover_all(project_root: Path, max_depth: int = 3) -> list[SignalInventory]:
    """
    Discover all CTM-activated subdirectories within project_root.

    Scans subdirectories up to max_depth levels deep. Returns one SignalInventory
    for each subdirectory that contains at least one Tier 1 signal. The root
    itself is not included — use discover(project_root) for the root inventory.

    This implements monorepo awareness per BOOT_PROTOCOL.md Section 7 (OQ1).

    Args:
        project_root: The monorepo root to scan. Must exist and be a directory.
        max_depth: Maximum directory depth to scan beneath project_root. Default 3.

    Returns:
        List of SignalInventory objects sorted by project_root path string,
        one per CTM-activated subdirectory. Empty list if none found.

    Raises:
        ValueError: If project_root does not exist or is not a directory.
    """
    root = Path(project_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(
            f"project_root must be an existing directory: {root}"
        )

    logger.debug("discover_all: scanning %s (max_depth=%d)", root, max_depth)
    results: list[SignalInventory] = []
    _tier1_set = set(TIER1_PATHS)

    def _scan(directory: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    sub = Path(entry.path)
                    # Check if this subdir has any Tier 1 signals
                    has_tier1 = any((sub / rel).exists() for rel in TIER1_PATHS)
                    if has_tier1:
                        try:
                            inv = discover(sub)
                            results.append(inv)
                            logger.debug(
                                "discover_all: found activated subdir %s (branch=%s)",
                                sub,
                                inv.branch,
                            )
                        except (ValueError, OSError) as exc:
                            logger.warning(
                                "discover_all: skipping %s: %s", sub, exc
                            )
                    # Continue scanning even if this subdir is activated
                    _scan(sub, depth + 1)
        except OSError as exc:
            logger.debug("discover_all: cannot scan %s: %s", directory, exc)

    _scan(root, 1)  # Start at depth 1 (immediate children of root)
    results.sort(key=lambda inv: str(inv.project_root))
    logger.info("discover_all: found %d activated subdirectories", len(results))
    return results
