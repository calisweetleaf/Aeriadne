"""Scenarios for the persistence_recovery_integrity criterion.

These scenarios verify that the disk-backed state survives a simulated crash.
All persistence side effects are confined to the temp directory the harness
passes in — we set MENTAT_HOME so `home_root()` inside the session module
resolves into our sandbox.

  session_recover  Author a Session, save it, load it, compare field-by-field.
  q_table_resume   Open a QTable, .update() it many times, close, reopen,
                   dump, byte-compare the rows.
  handoff_replay   Produce a fake handoff.md, simulate post-compact (i.e.
                   read it back via the same parse logic the hook would use),
                   confirm the round-trip preserves content. We do NOT
                   invoke the hook subprocess — that's an integration test,
                   not a unit-of-persistence test.
"""
from __future__ import annotations

import os
import sys
from dataclasses import asdict
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from state_machine import QTable, Reward, Session, State, load_session, save_session  # noqa: E402

from ._types import Scenario, ScenarioResult  # noqa: E402


def _make(id_, name, description, fn):
    return Scenario(id=id_, name=name, description=description, fn=fn)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def scenario_session_recover(workdir: Path):
    """Round-trip a Session through save_session/load_session under a sandboxed
    MENTAT_HOME. Compare every field of the dataclass."""
    prior = os.environ.get("MENTAT_HOME")
    os.environ["MENTAT_HOME"] = str(workdir)
    try:
        original = Session(
            session_id="eval-session-recover",
            state=State.VERIFYING,
            chain_depth=7,
            drift_count=2,
            transition_count=42,
            started_at=1715300000.0,
            last_event_at=1715301234.5,
            last_tool="Bash",
            last_tool_success=True,
            notes=["first note", "second note with \"quotes\""],
        )
        save_session(original)
        loaded = load_session(original.session_id)
    finally:
        if prior is None:
            os.environ.pop("MENTAT_HOME", None)
        else:
            os.environ["MENTAT_HOME"] = prior

    orig_d = asdict(original)
    orig_d["state"] = original.state.value
    load_d = asdict(loaded)
    load_d["state"] = loaded.state.value

    diffs = []
    for k, v in orig_d.items():
        if load_d.get(k) != v:
            diffs.append(f"  {k}: saved={v!r} loaded={load_d.get(k)!r}")
    passed = not diffs
    if passed:
        evidence = (
            f"session_recover: all {len(orig_d)} Session fields round-tripped "
            f"identically through JSON"
        )
    else:
        evidence = "session_recover: field diffs:\n" + "\n".join(diffs)
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "field_count": len(orig_d),
        "diff_count": len(diffs),
        "saved": orig_d,
        "loaded": load_d,
    })


def scenario_q_table_resume(workdir: Path):
    """Open a QTable, drive a handful of updates, close, reopen, dump, compare."""
    db = workdir / "qtable_resume.sqlite"

    # Phase 1: write
    q1 = QTable(db)
    try:
        # Drive an episode of (state, tool, reward, next_state) updates.
        steps = [
            (State.PLANNING, "Read", Reward(success=True, latency_ms=120), State.EXPLORING),
            (State.EXPLORING, "Grep", Reward(success=True, latency_ms=80), State.EXPLORING),
            (State.EXPLORING, "Edit", Reward(success=True, latency_ms=200, chain_depth=4),
             State.EXECUTING),
            (State.EXECUTING, "Bash", Reward(success=False, latency_ms=1500), State.BLOCKED),
            (State.BLOCKED, "Bash", Reward(success=True, latency_ms=300), State.EXECUTING),
            (State.EXECUTING, "Bash", Reward(success=True, latency_ms=4000), State.VERIFYING),
            (State.VERIFYING, "Bash", Reward(success=True, latency_ms=2500), State.REFLECTING),
        ]
        for s, t, r, nxt in steps:
            q1.update(s, t, r, nxt)
        dump_pre = q1.dump()
    finally:
        q1.close()

    # Phase 2: reload, dump again, compare
    q2 = QTable(db)
    try:
        dump_post = q2.dump()
    finally:
        q2.close()

    # last_updated is set via time.time() at update time — should be preserved
    # on reload because sqlite is on disk. Compare the full row.
    diffs = []
    if len(dump_pre) != len(dump_post):
        diffs.append(f"row count drift: pre={len(dump_pre)} post={len(dump_post)}")
    for a, b in zip(dump_pre, dump_post):
        for key in ("state", "tool", "value", "visits", "last_updated"):
            if a.get(key) != b.get(key):
                diffs.append(
                    f"  ({a.get('state')}, {a.get('tool')}).{key}: "
                    f"pre={a.get(key)!r} post={b.get(key)!r}"
                )
    passed = not diffs and len(dump_post) > 0
    if passed:
        evidence = (
            f"q_table_resume: {len(dump_post)} rows bit-identical across "
            f"close/reopen cycle"
        )
    else:
        evidence = "q_table_resume: drift:\n" + "\n".join(diffs)
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "row_count": len(dump_post),
        "diff_count": len(diffs),
    })


def scenario_handoff_replay(workdir: Path):
    """Write a handoff.md to the expected path, read it back, confirm content
    is intact. Verifies the file-IO contract that the SessionStart hook relies
    on without invoking the hook itself.
    """
    # Mirror the layout under home_root(): ~/.mentat/handoff/<session-id>.md
    handoff_dir = workdir / "handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    session_id = "eval-session-handoff"
    handoff_path = handoff_dir / f"{session_id}.md"

    content = (
        "# Mentat handoff — pre-compact snapshot\n"
        "\n"
        "## State at snapshot\n"
        "- session_id: eval-session-handoff\n"
        "- state: VERIFYING\n"
        "- chain_depth: 6\n"
        "- last_tool: pytest\n"
        "- drift_count: 0\n"
        "\n"
        "## Recent insights (latest 5)\n"
        "1. STATE_TRANSITION exploring → executing (write_tool: Edit)\n"
        "2. REWARD_SIGNAL exec/Bash success +1.1\n"
        "3. REWARD_SIGNAL verify/Bash success +1.0\n"
        "4. STATE_TRANSITION executing → verifying (verify_tool: pytest)\n"
        "5. STATE_TRANSITION verifying → reflecting (tool_success)\n"
        "\n"
        "## Next move\n"
        "Re-enter REFLECTING and synthesize the result of the test cycle.\n"
    )
    handoff_path.write_text(content, encoding="utf-8")

    # Simulate the SessionStart hook IO: read the latest handoff for a session.
    if not handoff_path.exists():
        return ScenarioResult(passed=False, evidence="handoff_replay: file vanished after write",
                              details={})
    loaded = handoff_path.read_text(encoding="utf-8")

    # Parse the snapshot block — a SessionStart hook would extract state +
    # last_tool from it. We exercise the same field-extraction logic.
    extracted_state = _extract_field(loaded, "state")
    extracted_tool = _extract_field(loaded, "last_tool")
    extracted_chain = _extract_field(loaded, "chain_depth")

    passed = (
        loaded == content
        and extracted_state == "VERIFYING"
        and extracted_tool == "pytest"
        and extracted_chain == "6"
    )
    if passed:
        evidence = (
            f"handoff_replay: round-tripped {len(content)} bytes; "
            f"extracted state={extracted_state}, last_tool={extracted_tool}, "
            f"chain_depth={extracted_chain}"
        )
    else:
        evidence = (
            f"handoff_replay: parse mismatch — state={extracted_state!r}, "
            f"tool={extracted_tool!r}, chain={extracted_chain!r}; "
            f"bytes_match={loaded == content}"
        )
    return ScenarioResult(passed=passed, evidence=evidence, details={
        "byte_match": loaded == content,
        "extracted_state": extracted_state,
        "extracted_tool": extracted_tool,
        "extracted_chain_depth": extracted_chain,
    })


def _extract_field(md: str, key: str) -> str | None:
    """Pull `- key: value` lines out of a markdown body."""
    for line in md.splitlines():
        s = line.strip().lstrip("-").strip()
        if s.lower().startswith(f"{key}:"):
            return s.split(":", 1)[1].strip()
    return None


SCENARIOS = [
    _make("session_recover", "Session JSON round-trip",
          "Save + load of a populated Session is field-identical.",
          scenario_session_recover),
    _make("q_table_resume", "Q-table close/reopen",
          "SQLite-backed Q-table survives a close/reopen cycle bit-identically.",
          scenario_q_table_resume),
    _make("handoff_replay", "Pre-compact handoff IO",
          "handoff.md is written, read back, and field-extracted to the same values.",
          scenario_handoff_replay),
]
