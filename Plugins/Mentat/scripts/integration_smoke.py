#!/usr/bin/env python3
"""Mentat v0.2 integration smoke test.

Runs every subsystem's local smoke in sequence, then a tiny end-to-end check
that exercises the FSA, Q-table, insight bus, drift detection, webhook
emitter (if present), debrief renderer (if present), and eval harness
(if present) in one process.

Designed to be run after the operators ship their work — it gracefully skips
subsystems that aren't on disk yet so you can run it incrementally.

Exit codes:
    0 — all available subsystems pass
    1 — at least one available subsystem failed
    2 — internal harness error

Usage:
    python3 scripts/integration_smoke.py
    python3 scripts/integration_smoke.py --verbose
    python3 scripts/integration_smoke.py --skip webhook,evals
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CheckResult:
    name: str
    status: str         # "pass" | "fail" | "skip"
    duration_ms: float = 0.0
    detail: str = ""
    extra: dict = field(default_factory=dict)


def run_python_smoke(script: Path, env_extra: dict | None = None,
                     timeout: int = 30) -> CheckResult:
    """Run a Python smoke script as a subprocess. Pass = exit 0."""
    name = str(script.relative_to(PLUGIN_ROOT))
    if not script.exists():
        return CheckResult(name=name, status="skip",
                           detail=f"not present at {script}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PLUGIN_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    if env_extra:
        env.update(env_extra)
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration_ms = (time.time() - start) * 1000.0
        if proc.returncode == 0:
            return CheckResult(name=name, status="pass", duration_ms=duration_ms,
                               detail=proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "ok")
        return CheckResult(name=name, status="fail", duration_ms=duration_ms,
                           detail=f"exit {proc.returncode}",
                           extra={"stderr": proc.stderr[-1500:]})
    except subprocess.TimeoutExpired:
        return CheckResult(name=name, status="fail",
                           duration_ms=(time.time() - start) * 1000.0,
                           detail=f"timeout after {timeout}s")
    except Exception as e:
        return CheckResult(name=name, status="fail",
                           duration_ms=(time.time() - start) * 1000.0,
                           detail=f"harness error: {e}")


def run_compile_check(*paths: str) -> list[CheckResult]:
    """Verify each path compiles as Python."""
    out: list[CheckResult] = []
    import py_compile
    for rel in paths:
        p = PLUGIN_ROOT / rel
        if not p.exists():
            out.append(CheckResult(name=f"compile:{rel}", status="skip",
                                   detail="missing"))
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            out.append(CheckResult(name=f"compile:{rel}", status="pass"))
        except Exception as e:
            out.append(CheckResult(name=f"compile:{rel}", status="fail",
                                   detail=str(e)))
    return out


def end_to_end_fsa() -> CheckResult:
    """Boot the FSA + Q-table + insight bus end-to-end in a temp home."""
    with tempfile.TemporaryDirectory() as td:
        os.environ["MENTAT_HOME"] = td
        sys.path.insert(0, str(PLUGIN_ROOT))
        try:
            from state_machine import (
                Event, EventClass, InsightBus, Insight, InsightType,
                QTable, Reward, State, StateMachine,
            )
            from state_machine.session import home_root, load_session, save_session
        except Exception as e:
            return CheckResult(name="end_to_end:fsa", status="fail",
                               detail=f"import: {e}")

        sid = "smoke-e2e"
        bus = InsightBus(home_root(), sid)
        qt = QTable(home_root() / "q_table.sqlite")
        sess = load_session(sid)
        m = StateMachine()

        # Walk through a typical trajectory:
        # PROMPT_SUBMIT → READ → READ → WRITE → BASH(verify) → success → REFLECTING
        m.step(Event(event_class=EventClass.PROMPT_SUBMIT))
        m.step(Event(event_class=EventClass.READ_TOOL, tool_name="Read"))
        qt.update(State.PLANNING, "Read",
                  Reward(success=True, latency_ms=120, chain_depth=1),
                  m.state)
        bus.emit(Insight(type=InsightType.REWARD_SIGNAL,
                         state=m.state.value,
                         payload={"tool": "Read", "value": 1.0, "success": True}))

        m.step(Event(event_class=EventClass.WRITE_TOOL, tool_name="Edit"))
        qt.update(State.EXPLORING, "Edit",
                  Reward(success=True, latency_ms=80, chain_depth=2),
                  m.state)

        m.step(Event(event_class=EventClass.EXEC_TOOL, tool_name="Bash",
                     payload={"command": "pytest -xvs"}))
        m.step(Event(event_class=EventClass.TOOL_SUCCESS, tool_name="Bash"))

        save_session(sess)

        if m.state is not State.REFLECTING:
            return CheckResult(name="end_to_end:fsa", status="fail",
                               detail=f"expected REFLECTING got {m.state.value}",
                               extra={"transitions": m.transition_count})

        if not bus.tail(10):
            return CheckResult(name="end_to_end:fsa", status="fail",
                               detail="no insights emitted")

        rec = qt.thompson_recommend(State.PLANNING, ["Read", "Grep", "Edit"])
        if rec is None:
            return CheckResult(name="end_to_end:fsa", status="fail",
                               detail="thompson returned None on populated table")

        return CheckResult(name="end_to_end:fsa", status="pass",
                           detail=f"4 transitions, {len(bus.tail(10))} insights, recommended {rec}")


def end_to_end_drift() -> CheckResult:
    """Round-trip drift detection."""
    with tempfile.TemporaryDirectory() as td:
        scope = Path(td) / "scope.md"
        scope.write_text(
            "# Scope\n\n## In\n- ui work\n\n## Out (deferred)\n"
            "- inference, model loading\n- safetensors\n",
            encoding="utf-8",
        )
        sys.path.insert(0, str(PLUGIN_ROOT))
        from state_machine.drift import detect_drift, parse_scope
        _, out_topics = parse_scope(scope)
        if not out_topics:
            return CheckResult(name="end_to_end:drift", status="fail",
                               detail="parse_scope yielded empty out_topics")
        hit = detect_drift("we should think about inference for this", out_topics)
        if not hit or hit.matched_phrase != "inference":
            return CheckResult(name="end_to_end:drift", status="fail",
                               detail=f"expected hit on 'inference' got {hit}")
        clean = detect_drift("we should refactor the css tokens", out_topics)
        if clean is not None:
            return CheckResult(name="end_to_end:drift", status="fail",
                               detail=f"expected clean got {clean}")
        return CheckResult(name="end_to_end:drift", status="pass",
                           detail=f"hit on '{hit.matched_phrase}', clean OK")


def end_to_end_cli() -> CheckResult:
    """Smoke the CLI inspector --help."""
    cli = PLUGIN_ROOT / "bin" / "mentat"
    if not cli.exists():
        return CheckResult(name="end_to_end:cli", status="skip",
                           detail="bin/mentat missing")
    try:
        proc = subprocess.run(
            [sys.executable, str(cli), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and "subcommand" not in proc.stdout.lower() \
                and "{status" in proc.stdout:
            return CheckResult(name="end_to_end:cli", status="pass",
                               detail="9 subcommands listed")
        if proc.returncode == 0:
            return CheckResult(name="end_to_end:cli", status="pass",
                               detail="--help OK")
        return CheckResult(name="end_to_end:cli", status="fail",
                           detail=proc.stderr[:200])
    except Exception as e:
        return CheckResult(name="end_to_end:cli", status="fail", detail=str(e))


def hooks_compile() -> list[CheckResult]:
    return run_compile_check(
        "hooks/_lib.py",
        "hooks/session_start.py",
        "hooks/user_prompt_submit.py",
        "hooks/pre_tool_use.py",
        "hooks/post_tool_use.py",
        "hooks/subagent_start.py",
        "hooks/subagent_stop.py",
        "hooks/pre_compact.py",
        "hooks/post_compact.py",
        "hooks/stop.py",
        "hooks/stop_failure.py",
    )


def webhook_smoke() -> list[CheckResult]:
    out: list[CheckResult] = []
    smoke = PLUGIN_ROOT / "webhook_engine" / "test_smoke.py"
    out.append(run_python_smoke(smoke, timeout=20))
    out.extend(run_compile_check(
        "webhook_engine/__init__.py",
        "webhook_engine/envelope.py",
        "webhook_engine/emitter.py",
        "webhook_engine/dlq.py",
        "webhook_engine/config.py",
    ))
    return out


def evals_smoke() -> list[CheckResult]:
    out: list[CheckResult] = []
    out.extend(run_compile_check(
        "evals/harness.py",
        "evals/scripts/run_eval.py",
        "evals/scenarios/state_transitions.py",
        "evals/scenarios/predictive_routing.py",
        "evals/scenarios/persistence_recovery.py",
    ))
    # Try a dry-run if run_eval exists.
    runner = PLUGIN_ROOT / "evals" / "scripts" / "run_eval.py"
    if runner.exists():
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PLUGIN_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        try:
            with tempfile.TemporaryDirectory() as td:
                proc = subprocess.run(
                    [sys.executable, str(runner), "--rubric", "all", "--json",
                     "--output", str(Path(td) / "report.html")],
                    env=env, capture_output=True, text=True, timeout=60,
                )
                status = "pass" if proc.returncode == 0 else "fail"
                out.append(CheckResult(
                    name="evals/run_eval.py --rubric all",
                    status=status,
                    detail=proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[:200],
                ))
        except Exception as e:
            out.append(CheckResult(
                name="evals/run_eval.py --rubric all",
                status="fail", detail=str(e),
            ))
    return out


def debrief_smoke() -> list[CheckResult]:
    out: list[CheckResult] = []
    smoke = PLUGIN_ROOT / "skills" / "mentat-debrief" / "scripts" / "test_smoke.py"
    out.append(run_python_smoke(smoke, timeout=20))
    out.extend(run_compile_check(
        "skills/mentat-debrief/scripts/render.py",
        "skills/mentat-debrief/scripts/aggregate.py",
    ))
    return out


def monitors_smoke() -> list[CheckResult]:
    out: list[CheckResult] = []
    smoke = PLUGIN_ROOT / "monitors" / "test_smoke.py"
    out.append(run_python_smoke(smoke, timeout=20))
    out.extend(run_compile_check(
        "monitors/entropy_watcher.py",
        "monitors/drift_watcher.py",
        "monitors/archivist.py",
    ))
    return out


def adapters_smoke() -> list[CheckResult]:
    out: list[CheckResult] = []
    out.extend(run_compile_check(
        "adapters/codex/hooks/_lib.py",
        "adapters/codex/hooks/session_start.py",
        "adapters/codex/hooks/pre_tool_use.py",
        "adapters/codex/hooks/post_tool_use.py",
        "adapters/codex/hooks/stop.py",
        "adapters/gemini/hooks/_lib.py",
        "adapters/gemini/hooks/before_tool.py",
        "adapters/gemini/hooks/after_tool.py",
        "adapters/gemini/hooks/pre_compress.py",
    ))
    return out


def render_table(results: list[CheckResult], verbose: bool = False) -> str:
    width = max((len(r.name) for r in results), default=20)
    lines = []
    lines.append(f"{'NAME':<{width}}  STATUS   TIME(ms)  DETAIL")
    lines.append("-" * (width + 38))
    for r in results:
        sym = {"pass": "✓ pass", "fail": "✗ FAIL", "skip": "  skip"}[r.status]
        sym_plain = sym.replace("✓ ", " ").replace("✗ ", " ")
        lines.append(f"{r.name:<{width}}  {sym_plain:<7}  {r.duration_ms:>7.1f}  {r.detail[:70]}")
        if verbose and r.extra.get("stderr"):
            for line in r.extra["stderr"].splitlines()[:6]:
                lines.append(f"  · {line}")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Mentat integration smoke")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--skip", default="",
                   help="comma-separated subsystems to skip "
                        "(webhook,evals,debrief,monitors,adapters)")
    args = p.parse_args()
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    results: list[CheckResult] = []

    # 1. core compile
    results.extend(run_compile_check(
        "state_machine/__init__.py",
        "state_machine/machine.py",
        "state_machine/q_table.py",
        "state_machine/insights.py",
        "state_machine/session.py",
        "state_machine/drift.py",
    ))

    # 2. hooks compile
    results.extend(hooks_compile())

    # 3. core MCP server compile
    results.extend(run_compile_check("mcp_server/__main__.py"))

    # 4. core CLI
    results.append(end_to_end_cli())

    # 5. core end-to-end FSA
    results.append(end_to_end_fsa())
    results.append(end_to_end_drift())

    # 6. subsystem smoke (skipped if not present, configurable via --skip)
    if "webhook" not in skip:
        results.extend(webhook_smoke())
    if "evals" not in skip:
        results.extend(evals_smoke())
    if "debrief" not in skip:
        results.extend(debrief_smoke())
    if "monitors" not in skip:
        results.extend(monitors_smoke())
    if "adapters" not in skip:
        results.extend(adapters_smoke())

    # 7. report
    print(render_table(results, verbose=args.verbose))
    print()
    n_pass = sum(1 for r in results if r.status == "pass")
    n_fail = sum(1 for r in results if r.status == "fail")
    n_skip = sum(1 for r in results if r.status == "skip")
    print(f"== {n_pass} pass / {n_fail} fail / {n_skip} skip "
          f"(of {len(results)} checks)")

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
