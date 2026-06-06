<div align="center">

<svg width="820" height="200" viewBox="0 0 820 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="checkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#f093fb;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#ff8a65;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#ffd93d;stop-opacity:1" />
    </linearGradient>
    <filter id="checkGlow">
      <feGaussianBlur stdDeviation="2.6" result="b"/>
      <feMerge>
        <feMergeNode in="b"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="820" height="200" fill="#0d1117" rx="20"/>
  <rect x="14" y="14" width="792" height="172" fill="none" stroke="url(#checkGrad)" stroke-width="1.2" rx="16" opacity="0.55"/>
  <text x="410" y="90" font-family="monospace" font-size="38" fill="url(#checkGrad)" text-anchor="middle" filter="url(#checkGlow)" font-weight="bold">SOTA++ CHECKLIST</text>
  <text x="410" y="124" font-family="monospace" font-size="13" fill="#8b949e" text-anchor="middle">operator-grade gate, run before claiming a module meets the bar</text>
  <text x="410" y="152" font-family="monospace" font-size="11" fill="#6e7681" text-anchor="middle">walk every section, leave the verification commands in the run log</text>
</svg>

<p align="center">
  <img src="https://img.shields.io/badge/Pre--Flight-required-f093fb?style=for-the-badge" alt="Pre-flight required"/>
  <img src="https://img.shields.io/badge/Real-Integration-ff8a65?style=for-the-badge" alt="Real integration"/>
  <img src="https://img.shields.io/badge/Provenance-Mandatory-ffd93d?style=for-the-badge" alt="Provenance mandatory"/>
  <img src="https://img.shields.io/badge/Verification-copy%E2%80%93pasteable-4ecdc4?style=for-the-badge" alt="Verification copy-pasteable"/>
</p>

</div>

---

## 0. How I Use This Checklist

I treat this as a single pass. I walk it top to bottom. I do not skip rows. If a row does not apply (a wrapper-only change does not need the edit-justification block), I write "N/A — wrapper" on that line instead of leaving it blank. A blank line is a yellow flag at review time.

The final section carries the literal commands. I copy them into the terminal and capture the output into `test/<module>/runs/<timestamp>/result.log`.

---

## 1. Pre-Flight

The pre-flight is what I check before I open the file.

### 1.1. Engagement Mode Declared

- [ ] `SCOPE.md` exists at the project root.
- [ ] `SCOPE.md` carries an `## Engagement Mode` block at the top with `mode`, `target_module`, `target_module_provenance`, `justification`, `author`, and `date` fields.
- [ ] The mode is exactly one of `WRAP`, `EDIT`, `COMPOSE`. No hybrid.
- [ ] If a change crosses two modes, the change has been split into separate commits.

### 1.2. Scope.md Respected

- [ ] The change touches only files inside the declared scope.
- [ ] No drive-by edits to files outside the scope. Drive-by refactors live in their own commit with their own SCOPE.md update.
- [ ] If the change discovers a defect outside the scope, the defect is captured as a follow-up task, not folded in.

### 1.3. Modular Placement Chosen

- [ ] The target file lives under `tools/native/<domain>/` or another domain-scoped path.
- [ ] No file lands at the project root unless the project root is the explicit destination (README.md, requirements.txt, SNAPSHOT.md, .gitignore).
- [ ] Wrappers and modules coexist inside the same domain directory.
- [ ] No flat structures. The `tools/native/` tree is two levels deep — domain folder, then files.

---

## 2. Code

The code section runs once the file is written.

### 2.1. Types

- [ ] Every public function and method signature carries type hints.
- [ ] `Any` is used only where the type is genuinely dynamic; every `Any` carries a one-line comment explaining the dynamism.
- [ ] Return types are explicit, never inferred.
- [ ] Structured payloads use `dataclass` or `TypedDict`, not bare `dict`.
- [ ] `from __future__ import annotations` is at the top of the file.

### 2.2. Docstrings

- [ ] The module opens with a module-level docstring whose first sentence names the purpose.
- [ ] Every class has a class-level docstring that names the origin (wrapper, native, composition).
- [ ] Every public method has a docstring with `Args` and `Returns` blocks when the signature is non-trivial.
- [ ] Private methods carry a single-line docstring naming the side effect.

### 2.3. Provenance

For mode: WRAP or mode: COMPOSE:

- [ ] Module docstring includes `Source`, `Integrated`, `Purpose` fields.

For mode: EDIT:

- [ ] Module docstring includes `Modified`, `Modified by`, `Justification`, `Provenance`, `Files` fields.
- [ ] The `Justification` paragraph is in the first person and answers why, not what.
- [ ] The `Provenance` field points to the snapshot manifest entry that records this edit.
- [ ] The corresponding `snapshots/v<x>.<y>/manifest.json` `domains.<name>.edits[]` array has a new entry whose `date`, `author`, and `summary` match the docstring.

### 2.4. Error Handling

- [ ] No bare `Exception` is caught. Exceptions are domain-specific.
- [ ] Public methods either raise a domain-specific exception or return a structured result object with a `status` field.
- [ ] Wrappers translate domain exceptions into user-readable shell responses with a suggested remediation.
- [ ] No raw stack trace bubbles to the user surface.
- [ ] The fail-loud-still-continue rule is applied at orchestrator boundaries; failures are logged with full context and the run does not exit unless the failure is truly unrecoverable.

### 2.5. No Version Pins

- [ ] `requirements.txt` carries package names only. Not `numpy>=1.8`. Not `numpy==1.26`. Just `numpy`.
- [ ] If the change introduced a new dependency, the dependency is justified in `SCOPE.md` against the stdlib alternative.

### 2.6. Stdlib-First

- [ ] The module imports from the standard library where possible.
- [ ] Heavy dependencies are imported lazily, inside the function that needs them, when feasible.
- [ ] No third-party dependency is introduced where `json`, `urllib`, `hmac`, `hashlib`, `sqlite3`, `dataclasses`, or `typing` would have sufficed.

---

## 3. Tests

The tests live under `test/<module>/` and they exercise the real module against real fixtures.

### 3.1. Real Integration, No Mock Surfaces

- [ ] No import of `unittest.mock`, `pytest-mock`, or any stubbing library inside the test file.
- [ ] If the module touches the network, the test points at a localhost test double that runs the same protocol.
- [ ] If the module touches SQLite, the test points at a temp `.sqlite` file under `tempfile.mkdtemp()`.
- [ ] If the module touches the file system, the test points at a temp directory under `tempfile.mkdtemp()`.

### 3.2. Direct Python, Not Pytest

- [ ] The test file runs as `python3 test/<module>/test_<name>.py` from the project root.
- [ ] The test does not require pytest discovery. It runs def-by-def under a master orchestrator at the bottom of the file, or it runs as a top-level script.
- [ ] The test prints meaningful data for every section. The output reads like a run report, not a pass/fail summary.

### 3.3. Structured Output

Every run writes three artifacts to `test/<module>/runs/<timestamp>/`:

- [ ] `result.json` — machine-readable result payload.
- [ ] `result.md` — first-person narrative summary of what ran and what it produced.
- [ ] `result.log` — full stdout plus stderr captured from the run.

The `result.md` is not optional. It is the test's documentation surface.

### 3.4. Fail Loud, Still Continue

- [ ] On a subsystem failure, the test prints the failure with full context and continues running the remaining checks.
- [ ] The exit code at the end of the run is `0` if every check passed, `1` if any check failed, `2` if the harness itself errored.
- [ ] No `sys.exit(1)` inside an inner check. Failures bubble to the top of the orchestrator and exit once at the end.

---

## 4. Aesthetics for Accompanying Docs

Every code change ships with documentation. The documentation passes the aesthetic doctrine.

### 4.1. Voice

- [ ] Prose sections are in the first person. "I treat", "I learned", "I require". Not "the user", not "developers should".
- [ ] Technical sections (tables, checklists) are operator-imperative.
- [ ] The reader is behind my eyes at the desk with the lamp on.

### 4.2. No Emojis

- [ ] No emoji characters anywhere in the documentation surface.
- [ ] The check is mechanical:

```bash
grep -P "[\x{1F300}-\x{1F9FF}]" docs/*.md README.md SNAPSHOT.md
```

If the command returns any match, the documentation does not ship.

### 4.3. No ASCII Art for Diagrams

- [ ] Architecture diagrams use inline SVG with a gradient and an `feGaussianBlur` glow filter.
- [ ] Sequence diagrams may use Mermaid.
- [ ] Box-drawn ASCII trees, pipe-character flowcharts, and ASCII art logos are forbidden in the canvas surface. (A small ASCII tree inside a code fence is acceptable when it is rendering a literal file tree as data.)

### 4.4. Snippets Pulled from the Library

- [ ] The gradient SVG header is used at the top of the document.
- [ ] Code fences carry a filename + language tab header above them.
- [ ] Long architecture diagrams and verbose logs live inside `<details>` collapsibles.
- [ ] Shields.io badges open the document with the language, status, and one or two domain facts.

### 4.5. Footnotes for Citations

- [ ] Every claim that traces to v1 or to the snippet library carries a footnote with a path link.
- [ ] Footnote markers use the `[^name]` syntax. They cluster at the bottom of the document.

---

## 5. Provenance

The provenance section is the audit log. It is the layer that survives once the diff is forgotten.

### 5.1. Snapshot Manifest Line

For every change, the `snapshots/v<x>.<y>/manifest.json` file carries a line that records what happened.

For mode: WRAP or mode: COMPOSE:

- [ ] A new entry under `domains.<name>` records the wrapper or composition with `module`, `wrapper`, `tool_count`, and `provenance` fields.
- [ ] The `edits[]` array stays empty for wrapper-only changes.

For mode: EDIT:

- [ ] A new entry is appended to `domains.<name>.edits[]` with `date`, `author`, `summary`, `files`, and `justification_ref` fields.
- [ ] The `justification_ref` field reads `"docstring:Modified"` when the justification lives in the module docstring.

### 5.2. Edit-Justification Block

For mode: EDIT:

- [ ] The module docstring carries a `Modified` block with all five mandatory fields (`Modified`, `Modified by`, `Justification`, `Provenance`, `Files`).
- [ ] A second edit appends a new block. The first block is not overwritten.
- [ ] The `Justification` paragraph is in the first person.

### 5.3. Commit Message

- [ ] The commit message starts with one of `wrap(<domain>):`, `edit(<domain>):`, or `compose(<domain>):`.
- [ ] The first line is under 80 characters.
- [ ] The body of the commit message references the snapshot version that will hold the change.

---

## 6. Integration Smoke

Every domain ships an integration smoke harness. The canonical pattern lives at `/agent/workspace/mentat/plugin/scripts/integration_smoke.py` and the recipe for writing a similar harness for a new module is below.

### 6.1. What the Canonical Harness Does

The Mentat plugin harness runs every subsystem's local smoke in sequence, then a tiny end-to-end check that exercises the FSA, Q-table, insight bus, drift detection, webhook emitter, debrief renderer, and eval harness in one process. It is designed to be run after operators ship their work — it gracefully skips subsystems that are not on disk yet so the harness can run incrementally.

The exit codes are the contract:

- `0` — all available subsystems pass
- `1` — at least one available subsystem failed
- `2` — internal harness error

### 6.2. Recipe for a New Module's Smoke Harness

For a new module under `tools/native/<domain>/`, the smoke harness lives at `test/<domain>/smoke.py` and follows the same shape:

<div class="code-block-header">
<span class="filename">smoke_template.py</span>
<span class="language">Python</span>
</div>

```python
#!/usr/bin/env python3
"""Smoke harness for the <domain> module.

Runs the module's public surface against real fixtures and records the run
to test/<domain>/runs/<timestamp>/{result.json,result.md,result.log}.

Exit codes:
    0 — all checks passed
    1 — at least one check failed
    2 — harness error
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN = "<domain>"
RUNS_DIR = PROJECT_ROOT / "test" / DOMAIN / "runs"


@dataclass
class CheckResult:
    name: str
    status: str            # "pass" | "fail" | "skip"
    duration_ms: float = 0.0
    detail: str = ""
    extra: dict = field(default_factory=dict)


def check_load() -> CheckResult:
    """Verify the module loads cleanly without side effects."""
    start = time.time()
    try:
        from tools.native import <domain> as mod  # noqa: F401
    except Exception as e:
        return CheckResult(
            name="load",
            status="fail",
            duration_ms=(time.time() - start) * 1000.0,
            detail=f"import error: {e}",
        )
    return CheckResult(
        name="load",
        status="pass",
        duration_ms=(time.time() - start) * 1000.0,
        detail="imported cleanly",
    )


def main() -> int:
    runs_dir = RUNS_DIR / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    runs_dir.mkdir(parents=True, exist_ok=True)

    checks = [check_load()]
    payload = {
        "domain": DOMAIN,
        "timestamp": time.time(),
        "checks": [vars(c) for c in checks],
        "pass_count": sum(1 for c in checks if c.status == "pass"),
        "fail_count": sum(1 for c in checks if c.status == "fail"),
        "skip_count": sum(1 for c in checks if c.status == "skip"),
    }
    (runs_dir / "result.json").write_text(json.dumps(payload, indent=2))
    (runs_dir / "result.md").write_text(_render_md(payload))
    return 0 if payload["fail_count"] == 0 else 1


def _render_md(payload: dict) -> str:
    """Render the run as a first-person narrative summary."""
    lines = [f"# Smoke run for {payload['domain']}", ""]
    lines.append(f"I ran the smoke harness on {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(payload['timestamp']))}.")
    lines.append("")
    for check in payload["checks"]:
        marker = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[check["status"]]
        lines.append(f"- [{marker}] {check['name']} ({check['duration_ms']:.1f} ms) — {check['detail']}")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
```

The template above produces JSON, MD, and LOG artifacts in a timestamped run directory. Replace `<domain>` and add domain-specific checks.

### 6.3. Smoke Harness Acceptance

- [ ] The harness writes `result.json`, `result.md`, and `result.log` to a timestamped subfolder under `test/<domain>/runs/`.
- [ ] The harness exits with `0`, `1`, or `2` per the contract above.
- [ ] The harness imports the module from the real package path, not from a fixture or a stub.
- [ ] The harness's `result.md` is a first-person narrative that reads like a run report.

---

## 7. Verification

The verification section carries the literal commands. I copy them into the terminal. The expected output is recorded inline.

### 7.1. Verify Source Hashes (run before reading the v1 or snippet library sources)

```bash
sha256sum "/agent/stored_files/cmp0btfmx04gj07ad4fhsaejl_STYLE _3_.md"
```

Expected output:

```text
79ee8da27b82f5aa3e9cd3bc8c2539515a8006116a4c429a1d6ccad1d6ee8ae6  /agent/stored_files/cmp0btfmx04gj07ad4fhsaejl_STYLE _3_.md
```

```bash
sha256sum /agent/stored_files/cmp0btfl704gi07admzjbe0eo_README_MdFormat_Rolling_Snippet_Library.md
```

Expected output:

```text
964f1ba9f0c7ab343c43891ff207b426bc228d3cce51d99e8cb64d38c990a56d  /agent/stored_files/cmp0btfl704gi07admzjbe0eo_README_MdFormat_Rolling_Snippet_Library.md
```

### 7.2. Verify No Emojis in Style Docs

```bash
grep -P "[\x{1F300}-\x{1F9FF}]" /agent/workspace/mentat/style/*.md
```

Expected output: empty. If the command produces any line, the documentation does not ship.

### 7.3. Verify Style Doc Line Counts

```bash
wc -l /agent/workspace/mentat/style/STYLE.v2.md /agent/workspace/mentat/style/PROVENANCE.md /agent/workspace/mentat/style/SOTA_CHECKLIST.md
```

Expected output: three line counts plus a total. STYLE.v2.md falls in the 600-1100 range, PROVENANCE.md in the 150-300 range, SOTA_CHECKLIST.md in the 200-450 range.

### 7.4. Run the Canonical Integration Smoke

```bash
python3 /agent/workspace/mentat/plugin/scripts/integration_smoke.py
```

Expected behavior: the harness runs every available subsystem smoke, prints per-check status, exits `0` if all available subsystems pass.

### 7.5. Verify Snapshot Manifest Integrity

For a project that has a snapshot manifest at `snapshots/v<x>.<y>/manifest.json`:

```bash
python3 -c "import json,sys; p=sys.argv[1]; d=json.load(open(p)); print('domains:', list(d.get('domains',{}).keys())); print('total_capabilities:', d.get('total_capabilities')); print('system_hash:', d.get('system_hash'))" snapshots/v0.2/manifest.json
```

Expected output: domain list, capability count, system hash. A `KeyError` or a missing field is a snapshot failure.

### 7.6. Verify Direct-Edit Provenance

For a module under `tools/native/<domain>/` that has been edited in place:

```bash
grep -n "^Modified:" tools/native/<domain>/<module>.py
```

Expected output: at least one line beginning with `Modified:` and an ISO date. A diff that touched the module but produces no line is a Strike 1 trigger under STYLE.v2 §9.

### 7.7. Verify Test Artifacts

```bash
ls -lah test/<domain>/runs/$(ls -t test/<domain>/runs | head -1)
```

Expected output: three files — `result.json`, `result.md`, `result.log`. A run directory missing any of the three is a SOTA++ failure.

### 7.8. Verify No Version Pins in requirements.txt

```bash
grep -nP '[<>=!~]' requirements.txt
```

Expected output: empty. Any matched line is a version pin and a SOTA++ failure.

---

## 8. Sign-Off

The final line. I do not claim a module meets SOTA++ until every section above has been walked.

- [ ] Pre-flight passes.
- [ ] Code passes.
- [ ] Tests pass with real integration.
- [ ] Aesthetics for accompanying docs pass.
- [ ] Provenance is recorded in the docstring (if EDIT) and in the manifest.
- [ ] Integration smoke runs to exit `0`.
- [ ] Verification commands have been executed and the outputs match the expected lines.

When every box is checked, the module is SOTA++. The snapshot can be sealed.
