#!/usr/bin/env python3
"""Archivist — daily rotation of stale Mentat artifacts.

Three jobs, all idempotent and crash-safe:

1. Rotate insight JSONL files older than 7 days into
   ~/.mentat/insights.archive/<YYYY-MM>/<sid>.jsonl.gz. The compression
   ratio for line-delimited JSON is typically 8-15x, so a one-month-old
   insight log shrinks from ~2 MB to ~150 KB.

2. Same treatment for ~/.mentat/handoff/ and ~/.mentat/sessions/ when files
   are older than 30 days — those are larger windows because the handoff
   snapshot is the load-bearing artifact for any post-compaction replay.

3. Vacuum the persistent Q-table: DELETE rows whose last_updated is older
   than 90 days AND whose visits < 3. Low-confidence stale entries
   (especially ones learned during a one-off experiment) bloat the table
   and skew Thompson sampling. The 3-visit floor preserves anything that
   the model actually used repeatedly.

Every action is line-logged to ~/.mentat/log/archivist.log so the user can
audit weeks later. The script is invoked by Claude Code's monitor system
on a daily cadence — runs once and exits.
"""
from __future__ import annotations

import gzip
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make the plugin's state_machine package importable.
_HERE = Path(__file__).resolve().parent
_PLUGIN_ROOT = _HERE.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from state_machine.session import home_root  # noqa: E402


# Retention thresholds (in seconds)
INSIGHTS_RETENTION_S = 7 * 86400
HANDOFF_RETENTION_S = 30 * 86400
SESSIONS_RETENTION_S = 30 * 86400

# Q-table vacuum thresholds
QTABLE_STALE_S = 90 * 86400
QTABLE_MIN_VISITS = 3


def log_path() -> Path:
    d = home_root() / "log"
    d.mkdir(parents=True, exist_ok=True)
    return d / "archivist.log"


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}\n"
    with log_path().open("a", encoding="utf-8") as f:
        f.write(line)


def _month_bucket(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m")


def _archive_root() -> Path:
    a = home_root() / "insights.archive"
    a.mkdir(parents=True, exist_ok=True)
    return a


def _rotate_dir(
    src_dir: Path,
    glob_pattern: str,
    retention_s: float,
    now: float,
    archive_root: Path,
) -> tuple[int, int]:
    """Compress + relocate any file under src_dir older than retention_s.

    Returns (rotated_count, error_count).
    """
    if not src_dir.exists():
        return 0, 0

    rotated = 0
    errors = 0
    for src in src_dir.glob(glob_pattern):
        if not src.is_file():
            continue
        try:
            mtime = src.stat().st_mtime
        except FileNotFoundError:
            continue
        age = now - mtime
        if age < retention_s:
            continue

        bucket = archive_root / _month_bucket(mtime)
        bucket.mkdir(parents=True, exist_ok=True)
        dst = bucket / (src.name + ".gz")

        # If a stale archive happens to exist for this exact name, append a
        # numeric suffix rather than clobbering — preserves auditability.
        counter = 1
        while dst.exists():
            dst = bucket / f"{src.name}.{counter}.gz"
            counter += 1

        tmp = dst.with_suffix(dst.suffix + ".tmp")
        try:
            with src.open("rb") as fi, gzip.open(tmp, "wb", compresslevel=6) as fo:
                shutil.copyfileobj(fi, fo, length=1024 * 1024)
            # Atomic move into place, then delete original. fsync-light:
            # we don't fsync here because the monitor is idempotent and the
            # source survives a partial run (no rename happens if gzip raises).
            os.replace(tmp, dst)
            src.unlink()
            rotated += 1
            _log(f"rotated {src} -> {dst} ({src.name}, age={int(age)}s)")
        except Exception as exc:
            errors += 1
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            _log(f"ERROR rotating {src}: {exc!r}")
    return rotated, errors


def vacuum_qtable(now: float) -> tuple[int, int]:
    """Delete stale + low-confidence rows from the Q-table.

    Returns (deleted_count, error_count).
    """
    db = home_root() / "q_table.sqlite"
    if not db.exists():
        return 0, 0
    cutoff = now - QTABLE_STALE_S
    try:
        conn = sqlite3.connect(str(db))
        cur = conn.execute(
            "DELETE FROM q_values WHERE last_updated < ? AND visits < ?",
            (cutoff, QTABLE_MIN_VISITS),
        )
        deleted = cur.rowcount or 0
        conn.commit()
        if deleted:
            conn.execute("VACUUM")
            conn.commit()
        conn.close()
        _log(
            f"q_table vacuum: deleted={deleted} "
            f"(cutoff={int(cutoff)}, min_visits={QTABLE_MIN_VISITS})"
        )
        return deleted, 0
    except sqlite3.OperationalError as exc:
        # Most common cause: schema not yet created (no hook has fired). Treat
        # as a no-op rather than an error.
        _log(f"q_table vacuum skipped (schema missing): {exc!r}")
        return 0, 0
    except Exception as exc:
        _log(f"ERROR q_table vacuum: {exc!r}")
        return 0, 1


def run_once() -> dict:
    """Run all three jobs and return a summary dict."""
    root = home_root()
    archive_root = _archive_root()
    now = time.time()

    _log("archivist run started")

    insights_rot, insights_err = _rotate_dir(
        root / "insights", "*.jsonl", INSIGHTS_RETENTION_S, now, archive_root
    )
    handoff_rot, handoff_err = _rotate_dir(
        root / "handoff", "*.md", HANDOFF_RETENTION_S, now, archive_root
    )
    sessions_rot, sessions_err = _rotate_dir(
        root / "sessions", "*.json", SESSIONS_RETENTION_S, now, archive_root
    )
    qtable_deleted, qtable_err = vacuum_qtable(now)

    summary = {
        "insights_rotated": insights_rot,
        "insights_errors": insights_err,
        "handoff_rotated": handoff_rot,
        "handoff_errors": handoff_err,
        "sessions_rotated": sessions_rot,
        "sessions_errors": sessions_err,
        "qtable_deleted": qtable_deleted,
        "qtable_errors": qtable_err,
    }
    _log(f"archivist run finished: {summary}")
    return summary


def main() -> int:
    try:
        summary = run_once()
    except Exception as exc:
        _log(f"FATAL: {exc!r}")
        print(f"archivist: fatal {exc!r}", file=sys.stderr)
        return 1
    print(f"archivist: {summary}")
    errs = (
        summary["insights_errors"]
        + summary["handoff_errors"]
        + summary["sessions_errors"]
        + summary["qtable_errors"]
    )
    return 0 if errs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
