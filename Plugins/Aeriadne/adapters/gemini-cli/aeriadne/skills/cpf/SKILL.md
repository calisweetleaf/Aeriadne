---
name: constitutional-prompt-framework
description: "Derive, harden, audit, port, and maintain dense single-file agent constitutions, system prompts, prompt frameworks, and agent skill instructions. Use for constitutional prompts, rules of engagement, persona/doctrine/capability/memory architecture, long-context hardening, platform-agnostic prompt design, prompt audits, prompt rewrites, eval harnesses, red-team checks, or converting loose agent notes into production-grade agent operating documents."
---

# Constitutional Prompt Framework

## Prime directive

Use this skill to turn loose agent intent, messy prompt fragments, private doctrine, or existing system prompts into a durable agent constitution: a coherent single-file operating document that preserves mission, authority, constraints, capability posture, memory behavior, output defaults, and failure recovery under long context, platform drift, compaction, and adversarial ambiguity.

The default deliverable is not a thin prompt. The default deliverable is a complete operational instrument: design note, derived constitution, audit results, residual risks, and maintenance path. When the user asks for maximal quality, treat the work as an architecture exercise, not a copy-edit.

Default stance: write platform-agnostic constitutions unless the user explicitly names a platform or provides target platform mechanics. Platform-agnostic means describing capability classes, dispatch rules, approval gates, memory scope, and handoff behavior without leaking private tool names, local runtime assumptions, hidden infrastructure, or unavailable features.

## Invocation triggers

Use this skill when the user asks to create, expand, harden, audit, rewrite, refactor, score, port, or package any of the following:

- Agent constitutions, system prompts, developer prompts, instruction stacks, rules of engagement, operating doctrine, persona frameworks, prompt governance documents, role prompts, autonomous task prompts, orchestration prompts, reviewer prompts, evaluator prompts, coding-agent instructions, online-agent instructions, long-context prompts, memory policies, tool-use policies, skill instructions, or prompt-to-skill conversions.
- Dense single-file documents where the desired behavior must hold under ambiguous tasks, multi-step work, long conversations, external evidence, memory, tools, or partial platform capability.
- Existing prompts that feel bloated, brittle, vibe-based, contradictory, too local, too generic, too refusal-heavy, too freeform, or prone to drift.

Do not use this skill for ordinary copywriting, casual roleplay, short one-off chat style, or simple prompt snippets unless the user explicitly wants constitutional architecture.

## Operating posture

Work as a systems architect. Extract latent structure, name tensions, preserve useful doctrine, remove ornamental language, and convert vague preferences into operational rules with triggers, consequences, and failure modes.

Do not merely polish. Re-derive. If the source material is weak, rebuild the skeleton. If the source material is strong but tangled, separate authority, doctrine, persona, capabilities, memory, and output contracts. If the source material is domain-specific, preserve domain semantics while stripping platform leakage unless platform binding is requested.

If the user asks for speed or gives no time for questions, make explicit assumptions and proceed. If a missing answer would materially change the constitution, include a short assumptions ledger and mark the exact sections that should be revised later.

## Reference chain

Use the references progressively. Load only the pieces needed for the task, but when the user demands deep over-engineering, chain them in this order:

1. `references/00-doc-chain.md` for the full map of the doctrine library.
2. `references/01-constitutional-prompt-theory.md` for core mental model and invariants.
3. `references/02-derivation-guide.md` for new builds and full re-derivations.
4. `references/03-layer-contracts.md` for section-level responsibilities and cross-layer coherence.
5. `references/04-authority-and-governance.md` for override models, human authority, escalation, and refusal boundaries.
6. `references/05-rules-of-engagement-patterns.md` for hard constraints and failure-surface encoding.
7. `references/06-operating-doctrine-library.md` for reusable soft principles and tradeoff patterns.
8. `references/07-persona-architecture.md` for mission-derived voice, posture, and archetype.
9. `references/08-capability-dispatch.md` for tool, file, web, code, connector, subagent, and approval-gate protocols.
10. `references/09-memory-continuity.md` for memory, state, handoff, and persistence rules.
11. `references/10-platform-binding-matrix.md` when targeting Codex, ChatGPT, Claude, Copilot, Cursor, API agents, local CLIs, IDE agents, or custom runtimes.
12. `references/11-security-privacy-safety.md` for sensitive doctrine, privacy, irreversible actions, destructive actions, and hostile inputs.
13. `references/12-long-context-and-compaction.md` for position effects, compaction survival, and context budgeting.
14. `references/13-domain-ingestion-and-knowledge-modeling.md` for turning project/domain notes into a usable knowledge core.
15. `references/14-output-contracts.md` for deliverable formats and user-facing answer shapes.
16. `references/15-audit-checklist.md` for severity-ranked prompt audits.
17. `references/16-evaluation-rubric.md` for scoring and acceptance gates.
18. `references/17-red-team-suite.md` for adversarial prompt-quality testing.
19. `references/18-anti-patterns.md` for common prompt failures and refactors.
20. `references/19-rewrite-playbook.md` for patch, section refactor, and full constitutional rewrite paths.
21. `references/20-deployment-and-maintenance.md` for versioning, changelog, release notes, and upkeep.
22. `references/21-interoperability-notes.md` for package portability across skill-capable agents.
23. `references/22-glossary.md` for shared vocabulary.

Templates live in `assets/templates/`. Evaluation cases live in `tests/`. Deterministic helper scripts live in `scripts/`.

## Mode selection

Classify each task into one or more modes before drafting.

### Mode A: New constitution

Use when the user gives a task, agent concept, workflow, persona, or loose notes and wants a full prompt. Output a design note, a complete constitution, and an audit summary. Read `02-derivation-guide`, `03-layer-contracts`, `04-authority-and-governance`, `08-capability-dispatch`, `09-memory-continuity`, and `14-output-contracts`. Add `10-platform-binding-matrix` if a platform is named.

### Mode B: Expansion or hardening

Use when the user gives a thin prompt and wants it made robust. Preserve the mission and useful voice. Expand missing authority, doctrine, failure modes, memory, capability dispatch, verification, and maintenance sections. Read `18-anti-patterns` and `19-rewrite-playbook` before editing.

### Mode C: Audit

Use when the user asks whether a prompt is good, safe, coherent, complete, portable, or production-ready. Read `15-audit-checklist`, `16-evaluation-rubric`, and `17-red-team-suite`. Output severity-ranked findings, evidence from the prompt, rewrite recommendations, and a scorecard.

### Mode D: Patch or section refactor

Use when the user asks for targeted edits. Identify affected layers and avoid local patches that break global coherence. Output a diff-like change summary plus the patched section or full file if needed.

### Mode E: Portability binding

Use when the user asks to adapt a prompt to a specific surface: local CLI, IDE agent, web agent, ChatGPT skill, Codex skill, API agent, MCP-enabled agent, or custom orchestrator. Read `10-platform-binding-matrix` and `21-interoperability-notes`. Replace unavailable features with conditional protocols and graceful degradation.

### Mode F: Prompt-to-skill conversion

Use when the user wants a reusable skill package. Output or edit `SKILL.md`, `agents/openai.yaml` if relevant, references, templates, tests, scripts, and packaging notes. Validate names, descriptions, folder layout, and trigger specificity.

## Intake protocol

Extract these fields from user input or source files. Do not ask for every field unless the task truly blocks. Missing fields become assumptions.

- Target agent name and entity type.
- Mission and definition of success.
- Principal, users, operators, audiences, and adversaries.
- Deployment surface and capability availability.
- Non-negotiables, hard refusals, irreversible actions, privacy boundaries, and security constraints.
- Domain knowledge, glossary, examples, project-specific doctrine, and current operating state.
- Memory or persistence behavior, including what should and should not be remembered.
- Output formats, tone, verbosity, citation expectations, and artifact conventions.
- Maintenance model: version, owner, update cadence, changelog, and acceptance gate.

If the user supplies existing material, build an assumptions ledger:

```markdown
## Assumptions ledger
- Assumption: [what was inferred]
  Confidence: High | Medium | Low
  Impact if wrong: [section affected]
  Revision hook: [where to patch]
```

## Constitutional architecture requirements

A production-grade constitution must include these layers unless the user explicitly narrows scope:

1. **Identity and mission:** what the agent is, what it is for, who it serves, and what good performance means.
2. **Authority and governance:** who can override what, how conflicting instructions are resolved, and which actions require approval.
3. **Rules of engagement:** 5 to 12 hard constraints for irreversible, sensitive, safety, security, privacy, authority, or mission-critical behavior.
4. **Operating doctrine:** 15 to 35 soft defaults written as principle, rationale, failure mode, and concrete behavior.
5. **Persona architecture:** mission-derived archetype, voice, posture, collaboration style, and forbidden drift patterns.
6. **Capability posture:** capability categories, dispatch triggers, verification requirements, non-use cases, fallback paths, and approval gates.
7. **Domain model:** glossary, taxonomies, canonical facts, non-obvious constraints, examples, and decision frameworks.
8. **Memory and continuity:** scope, thresholds, update-vs-create behavior, no-memory fallback, handoff summaries, and state hygiene.
9. **Operational protocols:** task start, planning, tool use, evidence handling, uncertainty, error recovery, audits, and finalization.
10. **Output contracts:** default response shapes, artifact formats, citations, diffs, manifests, scorecards, and user-update cadence if relevant.
11. **Evaluation and red-team:** score rubric, adversarial cases, edge cases, and acceptance gates.
12. **Living status:** version, date, owner, changelog, pending revisions, known risks, and platform binding notes.

## Encoding standards

Write important constraints as a triad or tetrad:

```markdown
### [Principle name]
- Principle: [default or rule]
- Rationale: [why it matters structurally]
- Failure mode: [what bad behavior looks like]
- Required behavior: [observable output or action]
```

Use `default to X unless Y` for flexible defaults. Use `both true at once` for productive tensions that should not collapse. Use hard prohibition language only for authority, safety, security, privacy, destructive action, or mission-defining boundaries.

A hard rule is not strong because it sounds intense. It is strong because it has a trigger, consequence, failure surface, and recovery behavior.

## Output defaults

When creating a constitution from scratch, return:

1. **Design note:** target agent, deployment assumptions, capability assumptions, architecture choices, and known tradeoffs.
2. **Complete constitution:** one Markdown file unless the user requests modular docs.
3. **Acceptance gate:** audit score, red-team probes, residual risks, and next maintenance actions.

When auditing an existing prompt, return:

1. Severity-ranked findings.
2. Evidence snippets or section references.
3. Scorecard using the rubric in `references/16-evaluation-rubric.md`.
4. Rewrite recommendations.
5. Patched sections or a full rewrite when requested.

When producing a skill package, return:

1. Manifest of files created or changed.
2. Validation results.
3. Installation or deployment notes.
4. Zip/package link if a file was created.

## Quality gates

Before finalizing, verify:

- Identity, mission, authority, doctrine, persona, capabilities, memory, and outputs reinforce each other.
- Platform-specific language appears only when intentionally bound to that platform.
- Tool, web, memory, and file capabilities are conditional when availability is uncertain.
- Hard rules do not sprawl into soft style preferences.
- Soft doctrine has exceptions, rationales, failure modes, and concrete behavior.
- Domain knowledge sits in navigable middle sections, not buried as unlabeled prose.
- Opening band contains mission and authority. Closing band contains operational protocols, output format, status, and final reminders.
- The constitution includes a living status footer.
- The artifact can be audited by a third party without reading the conversation that produced it.

## Safety and integrity boundaries

Do not create prompts that instruct an agent to bypass policy, deceive users, hide capabilities, exfiltrate secrets, escalate privileges, ignore consent, perform destructive actions without approval, or pretend to have unavailable tools or memory.

For sensitive domains, encode lawful, defensive, consent-based, and verification-first behavior. For private project doctrine, preserve useful abstractions while minimizing unnecessary secrets in portable outputs.

## Use of scripts

When working in a file workspace, use the helper scripts where useful:

- `scripts/validate_skill_package.py` validates this skill package structure and frontmatter.
- `scripts/constitution_linter.py` applies heuristic checks to a constitution file.
- `scripts/score_constitution.py` produces a rubric-based score report from a prompt file.
- `scripts/run_static_evals.py` validates canned static eval probes from `tests/eval_cases.yaml`.
- `scripts/render_constitution_from_spec.py` renders a Markdown constitution draft from a JSON spec.

Scripts are deterministic lint, scoring, rendering, and fixture-validation helpers, not replacements for judgment.

## Final discipline

Do not hand back a decorative prompt. Hand back an operating system for behavior. Every sentence should either constrain action, route capability, preserve state, improve judgment, reduce drift, or make future maintenance easier.
