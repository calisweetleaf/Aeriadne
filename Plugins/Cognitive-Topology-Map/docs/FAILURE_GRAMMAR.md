# FAILURE_GRAMMAR.md — Failure Taxonomy, Adversarial Signatures, Recovery Protocols

**Loaded by**: SKILL.md when task type is [OSINT/RE/adversarial] OR when "something smells wrong"  
**Purpose**: Encodes what failure looks like BEFORE you can prove it. Pre-failure recognition.

---

## The Core Problem with Failure Detection

Standard debugging assumes: failure is visible, localized, and traceable. This is true for maybe 20% of real failures in complex systems and essentially 0% of failures in OSINT/RE work.

The remaining 80% of failures look like one of these:
1. **Silent wrong output** — the system produced something, it's wrong, nothing errored
2. **Cascading misattribution** — the actual failure point is 3 layers upstream from where symptoms appear
3. **False success** — everything looks right, passes superficial checks, is fundamentally broken
4. **Adversarial camouflage** (OSINT/RE) — the data is designed to produce a specific wrong conclusion

A failure grammar encodes all four. The goal: recognize failure before proof is available.

---

## CATEGORY 1: Pre-Failure Signatures

These are smells. They do not prove failure. They require investigation.

### Smell 1: Output Confidence / Complexity Mismatch
If the output appears more certain or simpler than the domain warrants, something is wrong.

Complex domains produce complex outputs. If an OSINT run on a well-obfuscated target produces clean, coherent, confident findings — that's a smell. Reality is messier than that. Either you hit a deception layer or the analysis is shallow.

**In code**: If a complex integration produces zero warnings, zero edge cases, and the output is clean JSON on first run — inspect the wrapper. It's probably swallowing errors silently.

### Smell 2: The "It Works" Feeling Too Early
In Daeron's recursive production system: if module integration takes less than 3 iteration cycles, something wasn't tested.

Not because effort = quality, but because non-trivial modules have non-trivial edge cases. If none surfaced, the integration environment isn't production-representative.

### Smell 3: Uniform Output Structure
Real data is non-uniform. If every record in an OSINT corpus has the same fields populated, same confidence scores, same citation depth — the pipeline is templating, not analyzing.

In code: if `get_tools()` returns identical response shapes for every tool across very different operations, the wrapper is over-normalizing and losing domain signal.

### Smell 4: Missing Failures in Logs
Healthy complex systems produce warnings. A log with only INFO-level entries from a system doing complex work means the error handling is wrong, not that everything went perfectly.

### Smell 5: Wrapper Longer Than 200 Lines
Per STYLE.md and the Three Strikes rule: if a wrapper exceeds 200 lines, logic has migrated from the module into the wrapper. This violates read-only module doctrine and creates hidden coupling. The integration is already failing even if it runs.

---

## CATEGORY 2: False Success Patterns

These are the dangerous ones. They pass superficial checks. They fail under real load.

### False Success 1: Schema Validity ≠ Semantic Validity
A database with 33/33 validation gates PASS, zero record_uid collisions, all hashes verified — can still contain semantically wrong data. Schema validation catches structural errors. It does not catch "the tokenizer fingerprinted every Gemini export as DeepSeek because the JSON field names overlapped."

**Daeron's Moonshine context**: The 33/33 PASS is structural validity. Semantic validity requires cross-provider comparative sampling, not just schema gates.

### False Success 2: Test Passes in Development, Silent Failure in Production
Module runs clean in isolation (development). Module fails silently when wrapped because the wrapper suppresses exceptions and returns empty structured results.

**Pattern**: Wrapper's `try/except` is too broad, catches module-specific exceptions and converts them to empty dict returns. The wrapper "works" — it always returns a dict. The module was never actually called.

### False Success 3: OSINT Target Has a Prepared Profile
In OSINT work: some targets maintain a "prepared" surface — a coherent, internally consistent false narrative designed to satisfy exactly the level of investigation most OSINT operators perform. It passes all consistency checks because it was designed to.

**Detection**: Apply the Disconfirmation Test. Instead of asking "does this evidence support the hypothesis?", ask "what would I expect to see if this narrative were false, and is it absent?" Absence of disconfirmation evidence in a well-researched target is itself suspicious.

### False Success 4: Integration Velocity is Misleading
Daeron's V-Equation: V(t) = V(t-1) + Σ(C_i × I_eff). High integration velocity can mask low I_eff. If you're integrating 5 modules per cycle but I_eff < 0.5 for each, capability is growing but fragility is growing faster. The snapshot looks productive but is pre-failure.

**Check**: After each integration cycle, explicitly measure wrapper coupling depth. If a wrapper references 3+ private attributes of the module, I_eff is below 0.8 even if the LOC count passes.

---

## CATEGORY 3: Adversarial Signatures (OSINT / RE Domains)

In OSINT, RE, and competitive intelligence: the data environment is not neutral. Some fraction of available data is deliberately crafted to produce wrong conclusions.

### Adversarial Pattern 1: Coherence Trap
A false narrative is unusually coherent. Cross-references check out. Dates align. Sources cite each other. This looks like strong corroboration. It's actually a network of co-constructed disinformation.

**Detection**: Trace the citation graph. If multiple independent sources trace back to a single original source (especially an unchecked one), coherence is synthetic, not organic.

### Adversarial Pattern 2: Calculated Exposure
In RE work: the most visible entry points are often the most hardened or most instrumented. The target expects probing at these surfaces. The actual attack surface (or the actual data) is at the less-obvious second-order locations.

**Detection**: Map what is *easy* to find, then deliberately investigate why it's easy. Easy-to-find information in hardened environments is either bait or outdated.

### Adversarial Pattern 3: Timestamp Poisoning
A common RE/OSINT attack on analysis pipelines: inject false timestamps into artifacts to corrupt timeline reconstruction. If timestamps are trusted as ground truth, the narrative is controlled.

**Detection**: Cross-reference timestamps against at least two independent time signals (filesystem mtime + content internal timestamps + network capture timestamps if available). Divergence > threshold requires timestamp source analysis.

### Adversarial Pattern 4: Credibility Laundering
Low-credibility claim appears in a high-credibility source because the high-credibility source cited a low-credibility source without verification. The credibility of the original source now attaches to the claim.

**In Daeron's OSINT corpus**: tiered credibility scoring catches this IF the tier system tracks citation chains, not just source tier at time of entry. A claim is only as credible as its original source, regardless of how many high-credibility sources have echoed it.

### Adversarial Pattern 5: RE Obfuscation Layers
In reverse engineering: obfuscation is often layered specifically to exhaust the analyst at the outer layers before they reach the inner ones. The outer layer is complex, the inner layer is simple, the analyst has spent all their attention budget before reaching it.

**Counter**: Time-box outer layer analysis explicitly. If outer layer analysis exceeds the expected complexity of the entire system, stop. You're being exhausted deliberately.

---

## CATEGORY 4: Recovery Protocols

When failure (or pre-failure smell) is confirmed:

### Recovery 1: Fail Fast, Recover Clean (STYLE.md § 3.5)

1. Surface the actual error — don't suppress it
2. Classify it: is this a wrapper error, a module error, or an integration environment error?
3. Fix at the right layer: module errors fix in module, integration errors fix in wrapper, never reverse
4. Verify the fix in isolation before re-testing the integration

### Recovery 2: Snapshot Rollback

If the integration is broken beyond rapid fix:
1. Do not patch in place
2. Roll back to the previous named snapshot
3. Diagnose against the clean state
4. Re-integrate with corrected approach

This is not a failure of the recursive production system — rollback IS the system working as designed.

### Recovery 3: OSINT Corpus Disconfirmation Injection

When an OSINT analysis looks too clean:
1. Pause all additive analysis
2. Generate 3 specific hypotheses that would DISPROVE the current finding
3. Search for evidence of those disconfirmation hypotheses
4. If zero disconfirmation evidence exists in a well-sourced corpus, the finding is suspect

### Recovery 4: RE Analysis Reset

When an RE trace has gone deep into complexity without payoff:
1. Abandon the current analysis thread entirely
2. Return to observable behavior (what does this system DO, not how does it work)
3. Build a behavioral model from observations
4. Use the behavioral model to guide re-entry, not the implementation details

---

## THE THREE STRIKES RULE (from STYLE.md)

An integration is **hard-rejected** if:

**Strike 1**: The native module requires modification to import (fails Read-Only test)  
**Strike 2**: The wrapper exceeds 200 lines of code (fails Thin Wrapper test)  
**Strike 3**: The unit tests require mocking the native module (fails Standalone test)

Three strikes = do not patch, do not iterate, reject the integration and re-source the module.

---

## Failure Grammar Quick Reference

| Smell | Category | Severity | Action |
|-------|----------|----------|--------|
| Output simpler/more certain than domain warrants | Pre-failure | HIGH | Inspect immediately |
| Zero warnings in complex system log | Pre-failure | MEDIUM | Check error suppression |
| Wrapper > 200 LOC | Pre-failure | HIGH | Three Strikes check |
| Schema valid but no semantic sampling | False success | HIGH | Run cross-provider sampling |
| OSINT findings unusually coherent | Adversarial | HIGH | Trace citation graph |
| RE outer layer complexity > system estimate | Adversarial | HIGH | Time-box, suspect exhaustion |
| I_eff < 0.8 per integration | False success | MEDIUM | Measure coupling depth |
| Timestamps from single source | Adversarial | MEDIUM | Cross-reference time signals |

---

## CATEGORY 5: Agent Ecosystem Integration Failures (CTMv3 Addition)

These failures are specific to the `.xyz` directory and agent ecosystem artifacts.
They are common precisely because ecosystem integration feels mechanical and easy —
it isn't. The artifacts look complete before they are correct.

### Ecosystem Failure 1: AGENTS.md Written Before Topology Is Known

**What it looks like**: A reasonable-looking AGENTS.md exists, with tool lists, commands,
and operational posture. The agent follows it. Results are wrong in ways that are hard to trace.

**The actual problem**: AGENTS.md was written either by copy-paste from another project or
by an agent that pattern-matched on "what AGENTS.md looks like" without reading this
specific codebase's topology. It may reference modules that don't exist, omit critical
LBCs, or describe a tooling posture incompatible with the actual production stack.

**Detection**: Read AGENTS.md. Cross-reference every module, file, and tool reference
against the actual project tree. If ≥ 2 references are invalid → full rebuild.

**Recovery**: Do not patch AGENTS.md. Rebuild it from TOPOLOGY.md and CONSTITUTION.md.

### Ecosystem Failure 2: Stale Line Anchors in ARCHITECTURE_MAP.md

**What it looks like**: Agent reads ARCHITECTURE_MAP.md, navigates to file:line anchor,
finds a completely different function or a blank line. Agent loses confidence in the map
and falls back to raw file exploration (the state before the map existed).

**The actual problem**: Code was refactored after ARCHITECTURE_MAP.md was built.
Line anchors were not updated. The map is structurally correct but navigationally wrong.

**Detection**: Spot-check 3 line anchors from the Quick Reference table against current
source. If any are wrong → full anchor audit.

**Recovery**: Update Quick Reference table first (fastest to fix). Then update branch
entry points. Structure survives line anchor rot — repair the anchors, not the structure.

### Ecosystem Failure 3: `.sovereign/session_state.json` Treated as Ground Truth

**What it looks like**: Agent reads session_state.json, sees `"warm_start_valid": true`,
skips boot protocol. Proceeds on topology that has drifted since last session.

**The actual problem**: `session_state.json` records what was true at last close, not
what is true now. It is a hint, not a verification. The topology_fingerprint.txt hash
is the verification mechanism — but only if it was updated at last session close.

**Detection**: When session_state.json says warm_start_valid but significant time has
passed (> 7 days) or the PROVENANCE.md Session Log shows architectural changes since
the fingerprint was written — do not trust the flag. Run warm validity check (BOOT_PROTOCOL.md §3.1).

### Ecosystem Failure 4: .github/ Hooks That Enforce Aspirational Topology

**What it looks like**: CI fails on every PR. Agent investigates. The failing check
enforces a constraint (e.g., wrapper < 200 lines) that was true when written but the
project has legitimately evolved beyond it. Every PR fails until the hook is disabled,
at which point topology enforcement silently disappears.

**The actual problem**: Hooks encode topology invariants. If topology legitimately
changes, hooks must be updated. Hooks are not immutable; topology is not always stable.

**Recovery**: Update the hook to reflect current topology. Update TOPOLOGY.md Baked-In
Decisions to record why the constraint changed. Log in PROVENANCE.md Architectural Decisions.

### Ecosystem Failure 5: CLAUDE.md and AGENTS.md Diverge

**What it looks like**: Codex follows AGENTS.md and does X. Claude Code follows CLAUDE.md
and does Y. X and Y conflict in a shared file. Session ends with merge conflict in a
previously clean module.

**The actual problem**: CLAUDE.md was updated (by Claude Code) without updating AGENTS.md
(or vice versa). They now encode different operational postures.

**Detection**: After any agent session that modifies CLAUDE.md, diff it against AGENTS.md.
Any divergence in tool protocols, architectural constraints, or module references
requires reconciliation before the next multi-agent session.

**Prevention**: AGENTS.md is canonical. CLAUDE.md extends it. CLAUDE.md should begin with:
`# CLAUDE.md — Extends AGENTS.md. When in conflict, rebuild from AGENTS.md.`

---

## Failure Grammar Quick Reference (CTMv3 Extended)

| Smell | Category | Severity | Action |
|-------|----------|----------|--------|
| Output simpler/more certain than domain warrants | Pre-failure | HIGH | Inspect immediately |
| Zero warnings in complex system log | Pre-failure | MEDIUM | Check error suppression |
| Wrapper > 200 LOC | Pre-failure | HIGH | Three Strikes check |
| Schema valid but no semantic sampling | False success | HIGH | Run cross-provider sampling |
| OSINT findings unusually coherent | Adversarial | HIGH | Trace citation graph |
| RE outer layer complexity > system estimate | Adversarial | HIGH | Time-box, suspect exhaustion |
| I_eff < 0.8 per integration | False success | MEDIUM | Measure coupling depth |
| Timestamps from single source | Adversarial | MEDIUM | Cross-reference time signals |
| AGENTS.md references non-existent modules | Ecosystem | HIGH | Full AGENTS.md rebuild |
| ARCHITECTURE_MAP.md line anchors wrong | Ecosystem | MEDIUM | Anchor audit + repair |
| session_state.json warm_start_valid=true but stale | Ecosystem | HIGH | Run BOOT_PROTOCOL §3.1 |
| .github/ hooks failing on every PR | Ecosystem | MEDIUM | Update hook + TOPOLOGY.md |
| CLAUDE.md and AGENTS.md diverged | Ecosystem | HIGH | Reconcile from AGENTS.md |
