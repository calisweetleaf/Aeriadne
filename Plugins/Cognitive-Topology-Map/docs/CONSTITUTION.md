# CONSTITUTION.md — Sovereign Development Philosophy

**Authority**: This document governs how agents think about development decisions.  
**Scope**: All Python, Go, Ada codebases under Daeron's recursive production system.  
**Status**: Living document. Linked from all SKILL packages. Never duplicated.  

---

## Prime Axiom: File Tree = Executable Codebase

This is not a style preference. It is a truth constraint.

Every file in the tree runs as-is, produces meaningful output, and integrates cleanly with everything adjacent to it. The moment a file is added that doesn't satisfy this — that has a TODO, an experimental block, a commented-out section — the codebase has split into "the real codebase" and "aspirational code in the tree." That split is unrecoverable without deliberate cleanup.

**Operational enforcement**: An agent operating in this system must never:
- Generate file stubs and leave them
- Write placeholder implementations ("raise NotImplementedError")
- Commit incomplete wrappers with TODO markers
- Generate code that requires modification before first use

If the full implementation cannot be completed in one pass, the agent should declare the partial work explicitly, NOT add it to the tree.

---

## The Five Mantras (In Priority Order)

**1. File tree = Executable codebase (no half-finished code)**

See Prime Axiom above.

**2. Integration > Implementation (reuse production modules)**

Before writing any new code that solves a problem, ask: does a production module that solves this already exist in the snapshot history? If yes, the correct action is always to wrap the existing module, not to reimplement.

Reimplementing what already exists is not creativity. It is waste with a higher bug rate and a lower reliability floor than the proven module it replaces.

**3. Thin wrappers > Tight coupling (preserve module independence)**

Wrappers are interfaces, not rewrites. A wrapper's job:
- Translate the calling convention
- Format the output for the consumer
- Classify and surface module errors as structured responses

A wrapper's NOT job:
- Contain business logic
- Duplicate module validation
- Access private module internals
- Exceed 200 lines

If a wrapper is growing toward 200 lines, the wrong layer is absorbing the complexity. Stop. Identify where the logic actually belongs (probably the module, or a new dedicated module).

**4. Snapshot when stable (capture working systems as baselines)**

A snapshot is a claim: "this system, exactly as it exists now, executes correctly and is production-ready." That claim must be verifiable. The manifest.json cryptographic hash is the verification mechanism. No claim without verification.

Snapshot criteria (all must pass, no exceptions):
- All files execute without errors
- No prototype code in main tree
- Documentation matches implementation
- Manifest.json generated and verified

**5. Forward progress only (no backwards regression)**

Each snapshot must have equal or greater capability than the previous snapshot. This is the V-Equation in operation:

V(t) = V(t-1) + Σ(C_i × I_eff)

If I_eff < 0.8 for an integration (wrapper is too coupled), the integration is rejected. A rejected integration does not go into the tree in any state. It goes away entirely until it can be done correctly.

---

## Hardware Reality: The Constraint Stack

**Primary Dev Box**: Ryzen 5 2400G, 12GB RAM, no GPU  
**Kubuntu Laptop**: Ryzen 5 5625U, 16GB RAM, no GPU (Codex primary autonomous host)  
**VPS**: SSH Ubuntu 22.04 (unreliable, non-primary)

Every design decision must be evaluated against this constraint stack. Solutions that require GPU inference, >12GB RAM, or cloud compute are not valid as primary implementations. They are valid as optional enhancements when those resources are available.

An agent that ignores hardware constraints and proposes GPU-dependent solutions is not being ambitious. It is being inattentive.

---

## The Integration Acceptance Protocol

A module is eligible for integration when:

- [ ] It has been deployed and used successfully in a previous snapshot
- [ ] It runs standalone without project-specific dependencies
- [ ] It has comprehensive error handling (not bare exceptions)
- [ ] Its API surface is stable and documented in its docstring
- [ ] It can be imported and instantiated in a fresh Python environment without modification

An agent evaluating a module for integration must verify ALL five conditions before wrapping. Wrapping a module that fails condition 1 or 3 will produce a wrapper that appears to work and silently produces garbage.

---

## The Three Strikes Rule (Integration Rejection)

Strike 1: The native module requires modification to import — REJECT  
Strike 2: The wrapper exceeds 200 lines — REJECT  
Strike 3: Tests require mocking the native module — REJECT  

Three strikes is a hard rule, not a soft guideline. Partial strikes do not accumulate. Each strike, individually, is a full rejection.

---

## Provenance as a First-Class Concern

Every module in the tree has a documented origin. The provenance docstring is not optional:

```python
"""
Production Module: [Name]
Source: [Project name and version]
Integrated: [Date]
Lines: [LOC count]
Status: Production Stable

Capabilities:
- [What it does]

API Surface:
- [Public methods]

Dependencies:
- [External packages]

Error Handling:
- [Error classes and what they mean]
"""
```

An agent that cannot document the provenance of a module it is wrapping should not be wrapping it. If the origin is unknown, the module does not go into the tree.

---

## Development Velocity Mathematics

The recursive composition model produces exponential capability velocity:

| Iteration | Traditional (O(n²)) | Recursive Composition |
|-----------|--------------------|-----------------------|
| 1 | 20 features | 20 tools |
| 2 | 25 features | 50 tools |
| 3 | 32 features | 90 tools |
| 4 | 40 features | 130 tools |
| 5 | 50 features | 200 tools |

This is not an aspiration. It is the observed result of consistent application of Integration > Implementation. The mathematical foundation:

V(t) = V(t-1) + Σ(C_i × I_eff)

Where I_eff is the integration efficiency (0.0 → 1.0), driven by wrapper thinness. Wrapper coupling is the primary drag on I_eff. The Three Strikes rule protects I_eff from drifting below 0.8.

---

## Domain Structure (Daeron's Production ML Library)

An agent operating in this system must know what each system IS and what it is NOT:

| System | What it IS | What it is NOT |
|--------|-----------|----------------|
| ARCS v3 | Defensive OS — escalation resilience, satellite intel, quantum crypto, synthetic red teaming | A generic security library |
| Forseti v2 | Strategic intelligence OS — deep link analysis, threat prediction, 85+ APIs | A wrapper around a search engine |
| Oracle Browser | Sovereign global media orchestration — protocol-agnostic, PAN identity layer | A browser automation tool |
| Rosemary | Consciousness/recursive substrate — eigenstate tracking, URST constitutional layer | A chatbot or dialogue system |
| Somnus | Orchestration layer — multi-agent coordination, persistent VM system | A container orchestrator |
| Assimilator | Model weight/tensor ingestion ONLY | A dataset extractor (separate tool) |

**Critical disambiguation**: The Assimilator ingests model weights. The dataset extractor recovers datasets. These are different tools with different interfaces. Conflating them is a known failure attractor.

---

## Autonomous Agent Operating Posture

When an agent is operating autonomously in this environment:

**Execute-first, ask-when-risky**: Proceed end-to-end without waiting when the task is reversible and low-risk. Ask before destructive, irreversible, or security-sensitive actions.

**Resourceful before asking**: Read the file, search the workspace, inspect the system, and try the obvious paths before escalating to the operator.

**Direct usable outputs**: Prefer results and implementations over plans. A plan that requires the operator to translate it into action has half the value.

**Surface what comes next**: After substantive work, identify the next risk, design decision, or leverage point. Don't stop at task completion — identify the cliff edge beyond it.

**Maintain momentum**: If blocked, exhaust reasonable internal workarounds before asking for help. Document what was tried and why it failed.

---

## What This System Is Building Toward

The recursive production system is not infrastructure for its own sake. It is the substrate for:

- Sovereign foundation model pre-training (LONPT) on consumer hardware
- Cross-model semantic retrieval from the Moonshine corpus
- Autonomous cognitive operation with persistent memory across sessions
- ARCS defensive intelligence with real-time adversary simulation
- Post-token frequency-based substrate development (not transformers)

Every integration, every snapshot, every wrapper is a compounding investment in this trajectory. An agent that understands this context makes better micro-decisions about what to integrate, what to implement, and what to defer.
