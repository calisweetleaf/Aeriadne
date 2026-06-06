#!/usr/bin/env python3
"""Smoke test for the archivist + watchers.

Runs against an isolated $MENTAT_HOME (TemporaryDirectory) so it never touches
a real user's ~/.mentat tree. Pure stdlib — gzip, sqlite3, tempfile, json.

Three slices:

1. archivist rotation
   - Synthesize fake old insight JSONL, handoff .md, and session .json files
     with mtimes nudged into the past via os.utime.
   - Drop a few fresh files that should NOT be rotated.
   - Run archivist.run_once(); assert old files are gone, archive files exist,
     and the gzipped contents round-trip byte-for-byte.

2. q_table vacuum
   - Build a tiny q_table.sqlite with one stale-low-visit row, one stale-high-
     visit row, one fresh-low-visit row.
   - Run archivist.run_once(); assert only the stale-low-visit row was deleted.

3. entropy_watcher idempotency
   - Synthesize a session in EXECUTING with chain_depth=12 and last_event_at
     6 minutes ago. Run the watcher twice; assert exactly one ENTROPY_SPIKE
     insight was emitted across both runs.
"""
from __future__ import annotations

import gzip
import importlib
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLUGIN_ROOT = _HERE.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))


def _set_home(tmpdir: Path) -> None:
    """Point MENTAT_HOME at the temp dir and force the session module to re-read."""
    os.environ["MENTAT_HOME"] = str(tmpdir)
    # If state_machine.session was imported earlier in this process, its
    # home_root() reads MENTAT_HOME on each call, so we don't need to reload.


def _age_file(p: Path, age_seconds: float) -> None:
    """Backdate a file's mtime by age_seconds."""
    now = time.time()
    target = now - age_seconds
    os.utime(p, (target, target))


def test_archivist_rotation(tmp: Path) -> None:
    _set_home(tmp)

    insights_dir = tmp / "insights"
    handoff_dir = tmp / "handoff"
    sessions_dir = tmp / "sessions"
    for d in (insights_dir, handoff_dir, sessions_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Stale insight (8 days old) — should rotate
    stale_insight = insights_dir / "old-session.jsonl"
    stale_insight.write_text(
        '{"type":"note","payload":{"text":"old"},"seq":0,"timestamp":0.0,'
        '"id":"a","session_id":"old-session"}\n',
        encoding="utf-8",
    )
    _age_file(stale_insight, 8 * 86400)

    # Fresh insight (1 day old) — should stay
    fresh_insight = insights_dir / "active-session.jsonl"
    fresh_insight.write_text(
        '{"type":"note","payload":{"text":"new"},"seq":0,"timestamp":0.0,'
        '"id":"b","session_id":"active-session"}\n',
        encoding="utf-8",
    )
    _age_file(fresh_insight, 1 * 86400)

    # Stale handoff (45 days old) — should rotate
    stale_handoff = handoff_dir / "old-session.md"
    stale_handoff.write_text("# stale handoff\n", encoding="utf-8")
    _age_file(stale_handoff, 45 * 86400)

    # Fresh handoff (10 days old) — should stay
    fresh_handoff = handoff_dir / "recent-session.md"
    fresh_handoff.write_text("# fresh handoff\n", encoding="utf-8")
    _age_file(fresh_handoff, 10 * 86400)

    # Stale session (40 days old) — should rotate
    stale_session = sessions_dir / "old-session.json"
    stale_session.write_text('{"session_id":"old"}', encoding="utf-8")
    _age_file(stale_session, 40 * 86400)

    # Fresh session (20 days old) — should stay
    fresh_session = sessions_dir / "recent-session.json"
    fresh_session.write_text('{"session_id":"recent"}', encoding="utf-8")
    _age_file(fresh_session, 20 * 86400)

    # Capture expected gzip contents before deletion
    expected_insight_bytes = stale_insight.read_bytes()

    # Run the archivist
    archivist = importlib.import_module("monitors.archivist")
    importlib.reload(archivist)
    summary = archivist.run_once()

    assert summary["insights_rotated"] == 1, summary
    assert summary["handoff_rotated"] == 1, summary
    assert summary["sessions_rotated"] == 1, summary
    assert summary["insights_errors"] == 0, summary
    assert summary["handoff_errors"] == 0, summary
    assert summary["sessions_errors"] == 0, summary

    assert not stale_insight.exists(), "stale insight should be gone"
    assert not stale_handoff.exists(), "stale handoff should be gone"
    assert not stale_session.exists(), "stale session should be gone"

    assert fresh_insight.exists(), "fresh insight should still exist"
    assert fresh_handoff.exists(), "fresh handoff should still exist"
    assert fresh_session.exists(), "fresh session should still exist"

    archive_root = tmp / "insights.archive"
    assert archive_root.exists(), "archive root should be created"

    # Find the rotated gzip under any YYYY-MM bucket and verify integrity
    found = list(archive_root.glob("*/old-session.jsonl.gz"))
    assert len(found) == 1, f"expected exactly one archived insight gz, got {found}"
    with gzip.open(found[0], "rb") as f:
        recovered = f.read()
    assert recovered == expected_insight_bytes, "gzip round-trip mismatch"

    log = tmp / "log" / "archivist.log"
    assert log.exists(), "archivist log should exist"
    text = log.read_text(encoding="utf-8")
    assert "archivist run started" in text
    assert "old-session.jsonl" in text

    print("  [ok] rotation: 3 stale files rotated, 3 fresh files preserved")
    print("  [ok] gzip integrity: round-trip matches original bytes")
    print(f"  [ok] archivist log written: {log}")


def test_qtable_vacuum(tmp: Path) -> None:
    _set_home(tmp)
    db = tmp / "q_table.sqlite"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS q_values (
            state TEXT NOT NULL,
            tool TEXT NOT NULL,
            value REAL NOT NULL DEFAULT 0.0,
            visits INTEGER NOT NULL DEFAULT 0,
            last_updated REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (state, tool)
        );
        """
    )
    now = time.time()
    stale = now - 100 * 86400        # 100 days old
    fresh = now - 1 * 86400          # 1 day old

    # Should DELETE: stale and low-visit
    conn.execute(
        "INSERT INTO q_values VALUES (?, ?, ?, ?, ?)",
        ("planning", "stale-tool", 0.5, 1, stale),
    )
    # Should KEEP: stale but high-visit (preserve repeated learning)
    conn.execute(
        "INSERT INTO q_values VALUES (?, ?, ?, ?, ?)",
        ("planning", "stale-but-trusted", 0.9, 50, stale),
    )
    # Should KEEP: fresh, low-visit (still being explored)
    conn.execute(
        "INSERT INTO q_values VALUES (?, ?, ?, ?, ?)",
        ("exploring", "new-tool", 0.2, 1, fresh),
    )
    conn.commit()
    conn.close()

    archivist = importlib.import_module("monitors.archivist")
    importlib.reload(archivist)
    summary = archivist.run_once()

    assert summary["qtable_deleted"] == 1, summary
    assert summary["qtable_errors"] == 0, summary

    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        "SELECT state, tool, visits FROM q_values ORDER BY tool"
    ).fetchall()
    conn.close()

    assert ("planning", "stale-but-trusted", 50) in rows
    assert ("exploring", "new-tool", 1) in rows
    assert all(r[1] != "stale-tool" for r in rows), "stale-tool should be gone"
    print("  [ok] q_table vacuum: 1 stale low-confidence row deleted")
    print("  [ok] q_table vacuum: high-visit and fresh rows preserved")


def test_entropy_watcher_idempotency(tmp: Path) -> None:
    _set_home(tmp)

    # Re-import the session module so home_root() returns the new tmpdir
    import state_machine.session as session_mod
    importlib.reload(session_mod)

    sessions_dir = tmp / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    insights_dir = tmp / "insights"
    insights_dir.mkdir(parents=True, exist_ok=True)

    now = time.time()
    sid = "wedged-session"
    # 12 in chain, 6 minutes idle in EXECUTING
    payload = {
        "session_id": sid,
        "state": "executing",
        "chain_depth": 12,
        "drift_count": 0,
        "transition_count": 7,
        "started_at": now - 1800,
        "last_event_at": now - 6 * 60,
        "last_tool": "Bash",
        "last_tool_success": True,
        "notes": [],
    }
    (sessions_dir / f"{sid}.json").write_text(json.dumps(payload), encoding="utf-8")

    entropy = importlib.import_module("monitors.entropy_watcher")
    importlib.reload(entropy)

    n1 = entropy.scan_once()
    n2 = entropy.scan_once()  # immediate second pass — should be a no-op
    assert n1 == 1, f"first pass should emit one spike, got {n1}"
    assert n2 == 0, f"second pass should be a no-op, got {n2}"

    # Verify exactly one ENTROPY_SPIKE landed on disk
    jsonl = insights_dir / f"{sid}.jsonl"
    assert jsonl.exists(), "insight file should exist"
    lines = [
        json.loads(ln)
        for ln in jsonl.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    spikes = [l for l in lines if l["type"] == "entropy_spike"]
    assert len(spikes) == 1, f"expected exactly one ENTROPY_SPIKE, got {len(spikes)}"
    assert spikes[0]["payload"]["tag"] == "stale"
    assert spikes[0]["payload"]["chain_depth"] == 12
    print("  [ok] entropy_watcher: emitted 1 spike on first pass")
    print("  [ok] entropy_watcher: idempotent — second pass emitted 0")


def test_drift_watcher_idempotency(tmp: Path) -> None:
    _set_home(tmp)

    import state_machine.session as session_mod
    importlib.reload(session_mod)

    sessions_dir = tmp / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    insights_dir = tmp / "insights"
    insights_dir.mkdir(parents=True, exist_ok=True)

    now = time.time()
    sid = "drift-stuck-session"
    payload = {
        "session_id": sid,
        "state": "drifting",
        "chain_depth": 4,
        "drift_count": 2,
        "transition_count": 11,
        "started_at": now - 7200,
        "last_event_at": now - 45 * 60,  # 45 minutes ago
        "last_tool": "Edit",
        "last_tool_success": False,
        "notes": [],
    }
    (sessions_dir / f"{sid}.json").write_text(json.dumps(payload), encoding="utf-8")

    drift = importlib.import_module("monitors.drift_watcher")
    importlib.reload(drift)

    n1 = drift.scan_once()
    n2 = drift.scan_once()
    assert n1 == 1, f"first pass should emit one note, got {n1}"
    assert n2 == 0, f"second pass should be a no-op, got {n2}"

    jsonl = insights_dir / f"{sid}.jsonl"
    lines = [
        json.loads(ln)
        for ln in jsonl.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    notes = [l for l in lines if l["type"] == "note" and l["payload"].get("tag") == "drift-stuck"]
    assert len(notes) == 1, f"expected exactly one drift-stuck note, got {len(notes)}"
    print("  [ok] drift_watcher: emitted 1 note on first pass")
    print("  [ok] drift_watcher: idempotent — second pass emitted 0")


def main() -> int:
    print("monitors smoke test")
    print("=" * 60)

    failures = 0
    cases = [
        ("archivist rotation", test_archivist_rotation),
        ("q_table vacuum", test_qtable_vacuum),
        ("entropy_watcher idempotency", test_entropy_watcher_idempotency),
        ("drift_watcher idempotency", test_drift_watcher_idempotency),
    ]

    for label, fn in cases:
        with tempfile.TemporaryDirectory(prefix="mentat-smoke-") as raw:
            tmp = Path(raw)
            print(f"\n[case] {label} (home={tmp})")
            try:
                fn(tmp)
                print(f"[pass] {label}")
            except AssertionError as exc:
                failures += 1
                print(f"[FAIL] {label}: {exc}")
            except Exception as exc:
                failures += 1
                print(f"[ERROR] {label}: {exc!r}")

    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED: {failures} case(s) did not pass")
        return 1
    print(f"PASSED: all {len(cases)} cases green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
