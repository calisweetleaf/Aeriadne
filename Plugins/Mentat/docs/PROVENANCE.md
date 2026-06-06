<div align="center">

<svg width="820" height="180" viewBox="0 0 820 180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="provGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4ecdc4;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#45b7d1;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#667eea;stop-opacity:1" />
    </linearGradient>
    <filter id="provGlow">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge>
        <feMergeNode in="b"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="820" height="180" fill="#0d1117" rx="20"/>
  <rect x="14" y="14" width="792" height="152" fill="none" stroke="url(#provGrad)" stroke-width="1.2" rx="16" opacity="0.55"/>
  <text x="410" y="86" font-family="monospace" font-size="38" fill="url(#provGrad)" text-anchor="middle" filter="url(#provGlow)" font-weight="bold">PROVENANCE</text>
  <text x="410" y="120" font-family="monospace" font-size="14" fill="#8b949e" text-anchor="middle">v1 to v2 delta, operator grade</text>
  <text x="410" y="146" font-family="monospace" font-size="11" fill="#6e7681" text-anchor="middle">what I kept, what I changed, what I dropped, why</text>
</svg>

<p align="center">
  <img src="https://img.shields.io/badge/Audit-Trail-4ecdc4?style=for-the-badge" alt="Audit Trail"/>
  <img src="https://img.shields.io/badge/Source-sha256%20verified-45b7d1?style=for-the-badge" alt="sha256 verified"/>
  <img src="https://img.shields.io/badge/Delta-v1%E2%86%92v2-667eea?style=for-the-badge" alt="v1 to v2"/>
</p>

</div>

---

## 1. Sources

Every claim in `STYLE.v2.md` traces to one of two source files. I record the path and the sha256 hash for each so a future operator can verify they are reading the same bytes I read.

### 1.1. v1 Style Document

- **path:** `/agent/stored_files/cmp0btfmx04gj07ad4fhsaejl_STYLE _3_.md`
- **logical name:** `STYLE.v1.md` (Codex Protocol: Recursive Production Standards)
- **size:** 11,617 bytes, 224 lines
- **sha256:** `79ee8da27b82f5aa3e9cd3bc8c2539515a8006116a4c429a1d6ccad1d6ee8ae6`

Verify:

```bash
sha256sum "/agent/stored_files/cmp0btfmx04gj07ad4fhsaejl_STYLE _3_.md"
```

### 1.2. Rolling Snippet Library

- **path:** `/agent/stored_files/cmp0btfl704gi07admzjbe0eo_README_MdFormat_Rolling_Snippet_Library.md`
- **logical name:** `README_MdFormat_Rolling_Snippet_Library.md`
- **size:** 18,309 bytes, 464 lines
- **sha256:** `964f1ba9f0c7ab343c43891ff207b426bc228d3cce51d99e8cb64d38c990a56d`

Verify:

```bash
sha256sum /agent/stored_files/cmp0btfl704gi07admzjbe0eo_README_MdFormat_Rolling_Snippet_Library.md
```

---

## 2. Inherited Verbatim

The following v1 clauses ship into v2 unchanged. They are quoted in v2 by section number, and v2's footnotes link back to them.

- v1 §1.1 — Naming Conventions. PascalCase classes, snake_case functions and modules, UPPER_SNAKE_CASE constants, single underscore for private members.
- v1 §1.2 — Typing. Strict type hints, `typing` module, clarity over brevity, `Any` only when truly dynamic.
- v1 §1.3 — Docstrings & Provenance. The original template for module, class, and public method docstrings. v2 extends this with the `Modified` block but does not modify the v1 template itself.
- v1 §1.5 — Mandatory Directory Hierarchy. The `tools/core/`, `tools/native/<domain>/`, `snapshots/v<Major>.<Minor>/` layout. The `requirements.txt`, `README.md`, `SNAPSHOT.md` discipline. The no-version-pin rule for requirements.txt.
- v1 §2.1 — Snapshot Manifest Schema. The base JSON shape. v2 extends with an `edits[]` array but does not modify the existing keys.
- v1 §2.2 — Visual Documentation Standards. Mermaid is still permitted. v2 adds a preference for inline SVG with `feGaussianBlur` glow when the visual is a header or a hero diagram; Mermaid remains valid for sequence and dependency graphs.
- v1 §3.1 — The Recursive Production Pattern. Snapshot → Fork → Integrate → Evolve → Snapshot. The five-step loop is unchanged.
- v1 §3.2 — Integration Over Implementation. The doctrine of reusing proven components. v2 retains the doctrine; the read-only clause is what got modified.
- v1 §3.3 — Domain-Scoped Modularity. Domains by folder. Lazy loading.
- v1 §3.4 — Velocity via Compounding (The V-Equation). The algebra is identical in v2. The accounting is extended; the formula is not.
- v1 §3.5 — Error Handling Doctrine. Fail fast, recover clean. Wrappers translate domain exceptions into user-readable shell responses. No raw stack trace at the user surface.
- v1 §4.1 — Snapshot Criteria. Standalone execution, no prototypes in the main tree, documentation matches implementation.
- v1 §4.3 — Execution & Reporting. Sequential orchestrators. JSON manifests and logs to confirm stability before snapshotting.
- v1 §5.1 — Protocol for Contributors. Production-ready submissions, wrapper-pattern preference, no logic drift.
- v1 §6 — Prime Directive. Self-preservation, recursive evolution, non-interference, traceability. The four obligations stand without modification.

---

## 3. Modified

These v1 clauses are revised in v2. The table names the clause, summarizes the v2 replacement, and records the rationale plus the risk I accepted.

| v1 clause | v2 clause | rationale | risk |
| --- | --- | --- | --- |
| v1 §3.2 *"Treat imported modules as read-only. Never modify their internals to fit the current project."* | v2 §6 *Direct edits are allowed in mode: EDIT, provided they carry a `Modified` docstring block, a manifest entry, and pass the SOTA++ test suite.* | At this stage I am importing my own tools into my own systems. The boundary between "production module" and "current project" has dissolved because both halves are mine. Wrapping a module I wrote two months ago is sometimes more expensive than carefully editing it in place. | An undisciplined edit can corrupt provenance. Mitigation: the `Modified` block plus manifest entry are mandatory. A diff that lacks both is a Strike 1 trigger under v2 §9. |
| v1 §4.2 *Three Strikes Rule — auto-reject on any of the three strikes.* | v2 §9 *Three Strikes Rule — each strike triggers peer review, none auto-reject.* | Auto-rejection forced false negatives. A justified in-place edit was being rejected for failing the read-only test, even when the edit was the right call. Peer review preserves the bar while allowing the conversation. | Strikes that should have killed a change could now linger in review. Mitigation: review must close with either an approval-with-docstring or a reimplementation. A strike that does not close within one review cycle escalates back to auto-reject. |
| v1 §3.4 *"If $I_{eff} < 0.8$, the integration is rejected."* | v2 §10 *If $I_{eff} < 0.8$, the integration triggers peer review under v2 §9.* | Same softening logic as the Three Strikes change. Auto-rejection on a coefficient was hostile to honest engineering. | A low-$I_{eff}$ integration could ship if reviewers wave it through. Mitigation: the SOTA++ test suite in v2 §7 catches the substantive failures even when the coefficient is in the gray zone. |
| v1 §5.2 *"[X] Modifying Production Modules: Never edit the imported file. If it needs features, fork the module upstream or wrap it."* (the v1 source uses a red-cross glyph at the start of every anti-pattern bullet; v2 substitutes `[X]` so this document holds the no-emoji rule) | v2 §11 *Modifying production modules without a provenance trail or justification is forbidden.* | The clause was the strongest expression of the read-only rule that v2 relaxes. The new clause keeps the prohibition narrow — the edit must justify itself. | Engineers may skip the docstring under deadline pressure. Mitigation: the snapshot manifest check fails when a diff under `tools/native/` lacks a matching docstring `Modified` block. |
| v1 §1.3 *Docstring template — Source, Integrated, Purpose.* | v2 §3.2 *Docstring template extended with `Modified`, `Modified by`, `Justification`, `Provenance`, and `Files` fields when the module has been edited in place.* | An edited module needs an audit log inside the file, not just in `git log`. The docstring is the durable artifact. | Long edit histories make the docstring sprawl. Mitigation: each edit appends a single block, second edits do not overwrite the first, and old blocks can be archived to `snapshots/v<prev>/` when a new snapshot generation closes. |
| v1 §2.1 *Snapshot manifest schema with `domains.<name>.provenance`.* | v2 §3.3 *Snapshot manifest schema with `domains.<name>.edits[]` array appended.* | Per-domain edit history must be machine-readable. The docstring is the human story; the manifest is the machine record. | The manifest grows. Mitigation: `edits[]` is empty for wrapper-only changes, which is the majority case, so the manifest stays compact in practice. |
| v1 §3.5 *"Fail Fast, Recover Clean."* | v2 §7.2 *Fail Fast, Recover Clean at the module boundary; fail loud, still continue at the orchestrator boundary.* | The original doctrine governed module behavior. v2 adds an orchestrator-layer doctrine for harnesses like `plugin/scripts/integration_smoke.py` — they should fail loud on a subsystem failure but continue running the rest of the suite. | Conflicting doctrines if the layers are not labeled. Mitigation: the orchestrator extension is scoped explicitly to test and smoke harnesses, not to production code paths. |

---

## 4. Added

These v2 clauses have no v1 counterpart. The table names the clause, traces the source (snippet library, plugin codebase, or net new in v2), and records the rationale.

| v2 clause | source | rationale |
| --- | --- | --- |
| v2 §1 *Engagement Modes — Wrap, Edit, Compose.* | net new in v2 | v1 had no formal mode declaration. v2 makes the mode explicit at the top of every SCOPE.md so reviewers know what kind of change they are reading before they read the diff. |
| v2 §1.1 *Mode decision tree, inline SVG.* | snippet library (gradient + feGaussianBlur pattern) | The decision is fast and the visual makes it scannable. Inline SVG carries the aesthetic doctrine. |
| v2 §1.2 *SCOPE.md mode-declaration block.* | net new in v2 | Forces the mode declaration to be a parseable artifact, not just prose. |
| v2 §3.2 *Direct-edit provenance docstring block.* | net new in v2 | The audit log lives in the file, not just in git. |
| v2 §3.3 *Snapshot manifest `edits[]` array.* | extension of v1 §2.1 | Machine-readable edit history. |
| v2 §6.2 *Edit-justification protocol.* | net new in v2 | Five mandatory fields in the `Modified` block: `Modified`, `Modified by`, `Justification`, `Provenance`, `Files`. |
| v2 §6.3 *Surgical-edit checklist.* | net new in v2 | A single saveable checklist to run before the file is committed. |
| v2 §6.4 *Edit-vs-rewrite ladder (four rungs).* | net new in v2 | Names the cost ramp from wrap through surgical edit through refactor through rewrite. |
| v2 §7 *SOTA++ test suite, consolidated.* | partially v1 §4 and §3.5; partially net new | v1 spread the test discipline across multiple sections. v2 collapses it into one checklist that applies regardless of engagement mode. |
| v2 §7.4 *Integration tests over mock-driven unit tests.* | plugin codebase (`webhook_engine/test_smoke.py`, `state_machine` smoke harness) | The plugin codebase already shipped this discipline. v2 codifies it. |
| v2 §7.5 *JSON + MD + LOG per-run artifacts.* | v1 §1.5 inline note; expanded in v2 | v1 mentioned the trio in the directory-hierarchy section. v2 promotes it to its own SOTA++ clause. |
| v2 §8 *Aesthetic doctrine for documentation.* | snippet library | The aesthetic rules are pulled forward into the standard so they are part of the bar, not a separate document. |
| v2 §8.2.1 *Gradient SVG header with feGaussianBlur glow.* | snippet library, Eclogue Ø header (lines 75–98 of the source) | Canonical pattern reproduced verbatim. |
| v2 §8.2.2 *Terminal simulation block with traffic-light chrome.* | snippet library (lines 232–359 of the source) | Canonical pattern reproduced verbatim. |
| v2 §8.2.3 *Code block header with filename and language tabs.* | snippet library (lines 169–228 of the source) | Canonical pattern reproduced verbatim, including the matching CSS. |
| v2 §8.2.4 *Collapsible details block.* | snippet library (lines 156–162 and 364–416 of the source) | Two canonical patterns combined for short logs and long diagrams. |
| v2 §9 *Modified Three Strikes (v2) with peer-review consequence.* | v1 §4.2 trigger list, v2 consequence | Soft-rejection model. Conversations instead of doors. |
| v2 §10.1 *Edit-velocity footnote.* | net new in v2 | Edits count toward $V(t)$ at the same weight as wraps provided the provenance test passes. The formula does not change. |
| v2 §11 *Anti-pattern list with substitution at the top.* | v1 §5.2 minus one line, plus four new lines | The "modifying production modules" line is replaced with a narrower prohibition. The other four lines pass through. v2 adds four new lines on mocking, version pinning, broad exception catching, and emoji usage. |
| v2 §13 *Closing first-person paragraph.* | net new in v2 | v1 ended on the Prime Directive. v2 closes with a reaffirmation that the bar does not move. |

---

## 5. Removed

One v1 clause is explicitly dropped in v2. I name it, quote it, and explain why.

### 5.1. Auto-Reject Three Strikes Rule

**v1 §4.2, quoted verbatim:**

> The Three Strikes Rule: An integration is rejected if:
> 1. Strike 1: The native module requires modification to import (fails Read-Only test).
> 2. Strike 2: The wrapper exceeds 200 lines of code (fails Thin Wrapper test).
> 3. Strike 3: The unit tests require a mock of the native module (fails Standalone test).

**v2 disposition:** the consequence ("is rejected") is removed. The triggers themselves are preserved in v2 §9 with revised wording. The replacement consequence is peer review.

**Why:** auto-rejection on a single strike was producing false negatives. A direct edit that was the right call was being rejected for failing the read-only test, even when the edit was justified and properly documented. The new model preserves the bar (the triggers are unchanged) while allowing the conversation (the consequence is softer).

### 5.2. Read-Only Clause in v1 §3.2

**v1 §3.2, quoted verbatim:**

> Read-Only Dependencies: Treat imported modules as read-only. Never modify their internals to fit the current project.

**v2 disposition:** dropped as a hard rule. The doctrine "integration over implementation" remains in v2 §4.1, and wrappers remain the preferred default in v2 §5. What changes is that direct modification is now a legitimate engagement mode under v2 §6 when the conditions are met.

**Why:** at the stage I am at, the line between "imported module" and "current project module" has dissolved. Both halves are mine. The read-only rule was friction that was no longer paying for itself. Removing it does not lower the bar — every other SOTA++ requirement has tightened to compensate.

### 5.3. Anti-Pattern Line: "Modifying Production Modules"

**v1 §5.2, quoted verbatim:**

> [X] Modifying Production Modules: Never edit the imported file. If it needs features, fork the module upstream or wrap it.

(Note: the v1 source opens this bullet with a red-cross glyph; I have transcribed it as `[X]` to keep this document free of emoji characters per the snippet library's hard rule. The semantic content of the quote is unchanged.)

**v2 disposition:** replaced with a narrower prohibition. v2 §11 reads "modifying production modules without a provenance trail or justification". The "fork or wrap" guidance is preserved in v2 §6.4 as the edit-vs-rewrite ladder.

**Why:** the v1 line was the strongest expression of the read-only rule, and removing only the §3.2 clause without modifying the anti-pattern list would have left the standard internally inconsistent.

---

## 6. Author Note

I have been holding the v1 standard for almost a year and I am ready to expand it on my own terms. The trigger for v2 is not that v1 stopped working — it kept working. The trigger is that I am ready to give my personal dev tools to a system that has earned that bar. v1 was the standard for a season when I needed the read-only rule as a forcing function. v2 is the standard for the season after, when the forcing function has done its job and the bar can be held by the test suite and the provenance protocol instead of by a single hard rule. The aesthetic doctrine does not relax. The test suite does not relax. The provenance requirement gets stricter, not looser. v2 is the bar for what coming-in dev tools must meet.

— daeron, 2026-05-10
