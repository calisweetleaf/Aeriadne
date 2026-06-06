# SSDS SOVEREIGN INVESTIGATION WORKSPACE

**Version:** 2.0
**Authority:** Sovereign Node Naltandur / Somnus Sovereign Defense Systems
**Compatibility:** Cross-agent (Claude, GPT, Gemini, Codex, Kimi, local models)

---

## What This Is

A portable, self-contained investigation workspace for strategic intelligence analysis. It is not a chatbot plugin or a simple prompt template. It is a complete analytical operating environment with its own cognitive constitution, evidence management system, source validation framework, and per-investigation casefile isolation.

When an agent loads this workspace, it receives:

1. **SKILL.md** — Entry point. Activation protocol and semantic router.
2. **AGENTS.md** — Heavyweight cognitive injection. 450+ lines encoding the Varys Strategic Reasoning Framework (7 invariants), the Sovereign Doctrine (7 philosophical principles), the Five-Phase Investigation Pipeline, Failure Grammar, Source Validation (Admiralty Code), and the ROE Engine.
3. **SIC Template** — The Sovereign Intelligence Casefile template (v4.0) used as the output format for every investigation.
4. **Deep References** — Extended reasoning doctrine and philosophical substrate, loaded on demand when AGENTS.md is insufficient.
5. **Casefile System** — Per-investigation directory isolation with evidence hashing, source grading, and cross-reference protocol.

## Quick Start

**For agents:** Read `SKILL.md` first. It will direct you to load `AGENTS.md`, orient on workspace state, and await the investigation seed.

**For the operator:** Provide an investigation seed (target, anomaly description, initial breadcrumbs, ROE level) and the agent handles the rest.

**To initialize a new casefile manually:**
```bash
./scripts/init_casefile.sh 20260510 TARGET_NAME
```

## Directory Layout

```
├── SKILL.md                  # Entry point — load this first
├── AGENTS.md                 # Cognitive injection — load this second (mandatory)
├── README.md                 # You are here
├── assets/
│   └── ssds_sic_template.md  # SIC v4.0 template
├── casefiles/                # Per-investigation directories
│   └── SSDS-SIC-DATE-TARGET/ # One per investigation (see AGENTS.md Part IV)
├── references/
│   ├── varys_strategic_substrate.md  # Deep: Varys reasoning patterns
│   └── sovereign_doctrine.md         # Deep: philosophical substrate
└── scripts/
    └── init_casefile.sh      # Casefile scaffolding utility
```

## Key Principles

- **One investigation, one casefile.** Never mix evidence across investigations.
- **SHA-256 everything.** Every evidence file gets hashed on ingestion.
- **Grade every source.** Admiralty Code (Reliability A–F, Credibility 1–6) on ingestion.
- **Never one scenario.** Alpha + Beta + Gamma minimum.
- **Red-team is mandatory.** Phase 4 (Challenger) executes with genuine adversarial intent.
- **Log what you cannot do.** Silent omission is a failure mode.
- **ICD 203 language.** Standardized probability terms only.

## License

Sovereign Anti-Exploitation Software License. All rights reserved by Sovereign Node Naltandur.

---

*SSDS Sovereign Investigation Workspace v2.0*
