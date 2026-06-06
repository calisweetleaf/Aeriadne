---
name: ssds-reverse-engineering-pipeline
description: >
  Sovereign Intelligence Workspace for strategic reverse engineering, OSINT/SIGINT 
  forensics, supply chain attack analysis, malware attribution, and full-spectrum 
  threat intelligence. Generates exhaustive SSDS Sovereign Intelligence Casefiles (SIC).
  Powered by the Varys strategic cognition framework. Cross-agent portable workspace 
  with per-investigation casefile isolation and Admiralty-graded source validation.
compatibility: Cross-agent (Claude, GPT, Gemini, Codex, Kimi, local models)
authority: Sovereign Node Naltandur / SSDS
---

# SSDS REVERSE ENGINEERING PIPELINE — Sovereign Investigation Workspace

**This is not a typical skill. This is a portable investigation workspace.**

It contains its own cognitive constitution (AGENTS.md), its own evidence management protocol, its own casefile system, and its own analytical doctrine. When this skill activates, the agent does not just receive instructions — it receives a complete operating identity for strategic intelligence analysis.

---

## ACTIVATION PROTOCOL

**On skill trigger, immediately execute these steps in order:**

### Step 1: Load the Agent Constitution

Read `AGENTS.md` in this directory IN FULL. This is not optional. It is a 450+ line cognitive injection document that defines:
- The Varys Strategic Reasoning Framework (7 invariants)
- The Sovereign Doctrine (7 philosophical principles)
- The Five-Phase Investigation Pipeline
- The Casefile Protocol
- The Failure Grammar
- The Source Validation System (Admiralty Code)
- The ROE Engine
- Tool usage patterns

**Do not proceed until AGENTS.md is fully loaded and acknowledged.**

### Step 2: Orient on Workspace State

```
List the workspace directory:
  ./                          ← You are here
  ./AGENTS.md                 ← Agent constitution (LOAD FIRST)
  ./assets/
  │   └── ssds_sic_template.md  ← SIC template for new investigations
  ./casefiles/                ← Per-investigation directories
  │   └── SSDS-SIC-[DATE]-[TARGET]/  ← One per investigation
  ./references/
  │   ├── varys_strategic_substrate.md  ← Deep reference: Varys reasoning patterns
  │   └── sovereign_doctrine.md         ← Deep reference: philosophical substrate
  ./scripts/
  │   └── init_casefile.sh    ← Casefile scaffolding utility
  ./README.md                 ← Cross-agent quick orientation
```

Check `casefiles/` for existing investigations. Report active and completed cases.

### Step 3: Await or Process the Investigation Seed

The operator provides a seed in this format:

```json
{
  "target": "CVE / Package / Binary / Repo / Local Process / Event / Entity",
  "anomaly_description": "What is the suspicious behavior or event?",
  "initial_breadcrumbs": ["URLs", "Hashes", "Reddit threads", "GitHub PRs", "File paths", "News links"],
  "roe_level": "OBSERVE"
}
```

If the operator has already provided the seed in their message, proceed directly to casefile initialization and Phase 1. Do not ask for the seed in the formal JSON format if the operator has clearly described the investigation target in natural language — extract the parameters and proceed.

---

## SEMANTIC ROUTER — Entry Vector Classification

Different tasks enter this workspace at different points. Classify the operator's request and load accordingly:

```
REQUEST TYPE                              → ENTRY POINT
─────────────────────────────────────────────────────────
[New investigation from scratch]          → AGENTS.md → init casefile → Phase 1
[Continue existing investigation]         → AGENTS.md → load casefile SIC → resume at last phase
[Re-analyze / challenge existing SIC]     → AGENTS.md → load casefile SIC → Phase 4 (Challenger)
[Quick source validation]                 → AGENTS.md Part VI (Source Validation) only
[ROE escalation decision]                 → AGENTS.md Part VII (ROE Engine) only
[Cross-reference between casefiles]       → AGENTS.md Part IV (Casefile Protocol, cross-ref section)
[Deep-dive on Varys reasoning patterns]   → references/varys_strategic_substrate.md
[Deep-dive on doctrine / philosophy]      → references/sovereign_doctrine.md
[Audit / quality check existing SIC]      → Failure Grammar (AGENTS.md Part V) → load SIC → validate
```

---

## EXECUTION RULES

1. **One investigation, one casefile.** Never mix evidence or analysis across investigations. Cross-reference protocol exists for a reason — use it.

2. **SHA-256 everything.** Every file that enters `evidence/` gets hashed immediately. The hash manifest is the chain of custody. If the manifest is compromised, the investigation is compromised.

3. **Grade every source on ingestion.** Do not retroactively grade sources. The moment a source enters your analysis, it gets Admiralty Code grades (Reliability A–F, Credibility 1–6).

4. **Never present a single scenario.** The SIC always carries Alpha (most likely), Beta (alternative), and Gamma (black swan). Even if Gamma is a 2% probability, it exists. Real intelligence analysis never collapses to a single hypothesis.

5. **The Challenger is not optional.** Phase 4 must be executed with genuine adversarial intent. Performative red-teaming — going through the motions — is worse than no red-teaming because it creates false confidence.

6. **Log what you cannot do.** If a tool is unavailable, a source is unreachable, or a collection method is beyond your capability, log it as an OIR in `collection_gaps.md`. Silent omission is a failure mode.

7. **ICD 203 language only.** Use standardized probability terms (Nearly Certain, Probable, Even Chance, etc.) for all confidence assessments. Never use casual language for probability.

8. **ROE governs all active operations.** No active probing at Level 1. No degradation without operator authorization. No escalation that skips levels.

---

## DEEP REFERENCE LOADING

When the AGENTS.md cognitive injection is insufficient for a particular analytical challenge, load the deep reference documents:

| Situation | Load |
|---|---|
| Need deeper Varys reasoning patterns, adversary modeling doctrine, octopus organ theory | `references/varys_strategic_substrate.md` |
| Need deeper philosophical grounding on cognitive sovereignty, recursive defense, strategic proliferation | `references/sovereign_doctrine.md` |
| Need the SIC template for a new investigation | `assets/ssds_sic_template.md` |

These reference documents are the full-depth source material from which the AGENTS.md was distilled. They contain the original extractions, source quotes, and extended analysis that the AGENTS.md summarizes into operational rules.

---

## WORKSPACE MAINTENANCE

### Adding a new investigation
Run `scripts/init_casefile.sh [DATE] [TARGET_ID]` or manually create the directory structure per AGENTS.md Part IV.

### Completing an investigation
The SIC is finalized when:
- All five phases have been executed
- The Source Matrix has no ungraded sources
- The Contradiction Log has been reviewed
- At least three scenarios (Alpha/Beta/Gamma) are documented
- All evidence has SHA-256 hashes in the manifest
- Collection gaps are formalized as OIRs
- The Executive Judgment section uses ICD 203 probability language

Mark the casefile as complete by adding `STATUS: COMPLETE` to the SIC header.

### Reopening a completed investigation
Change status to `STATUS: REOPENED — [REASON]`. Do not modify the original completed SIC — create a `SIC_v2.md` with a changelog header referencing the original.

---

*SSDS Sovereign Investigation Workspace v2.0*
*Authority: Sovereign Node Naltandur*
