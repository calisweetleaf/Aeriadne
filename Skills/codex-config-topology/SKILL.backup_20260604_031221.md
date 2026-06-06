---
name: codex-config-topology
description: inspect, edit, and preserve a customized codex environment where .codex acts as a control plane and the operator injects doctrine files such as agents.md, agents.override.md, opsec.md, style.md, and mcp_spec.md. use when chatgpt needs to map startup order, decide whether behavior belongs in .codex or the host profile, preserve custom bb7 or mcp orchestration, enforce first-mission doctrine loading, debug exo-first routing, or reason about full terminal posture and tool permissions without collapsing the install into stock codex defaults.
---

# Codex Config Topology

Treat the user's Codex install as a sovereign execution habitat, not a stock app config.

Inspect what actually exists before proposing edits. Do not assume defaults when the user describes a custom `.codex` folder, injected startup doctrine, shell bootstrap, admin or elevated launch variants, custom command entrypoints, npm-installed Codex, or BB7 and MCP orchestration.

## Core operating posture

1. Preserve custom orchestration unless the user explicitly asks to simplify or remove it.
2. Distinguish between `Codex defaults`, `operator invariants`, `runtime overrides`, and `active experiments`.
3. Prefer exact file-level recommendations, patches, or replacement blocks over vague advice.
4. Never normalize a bespoke setup into generic coding-agent folklore.
5. When the environment is unclear, inspect the relevant files and reconstruct the startup chain before suggesting structural changes.

## Mandatory doctrine load on first mission

On the first substantive mission of every new chat, load these doctrine files before making recommendations or tool-order claims:

1. `references/source/AGENTS.md`
2. `references/source/AGENTS.override.md`

When the request touches permissions, command authority, tool catalog, or BB7 runtime affordances, also load:

- `references/source/default.rules`
- `references/source/tool_manifest.json`

If the operator refers to `workflows.md` or another injected file that is not bundled in the skill, state that it is missing from the current package and ask for it before making claims that depend on it.

## Doctrine roles and precedence

Read these files as a layered control stack, not as redundant prose.

- `AGENTS.md`: primary identity, baseline posture, and environment framing.
- `AGENTS.override.md`: injected runtime override that tightens turn-order and loop behavior for the active workspace.
- `OPSEC.md`: development constitution and production-method doctrine.
- `STYLE.md`: coding and document-structure discipline.
- `MCP_SPEC.md`: operational reference for BB7 and MCP tool semantics, with exoskeleton loop behavior.
- `default.rules`: concrete command-permission evidence.
- `tool_manifest.json`: live tool catalog evidence.

If these documents appear to disagree, preserve the operator's explicit latest instruction and then explain how the disagreement should be reconciled. Do not silently pick the most generic interpretation.

## Mandatory BB7 sequencing

After every user input, the first BB7 actions must be exoskeleton actions. Do not start with memory, journal, terminal, planner, file, or agent tools.

Use this order unless the operator explicitly requests a different order:

1. `bb7_exo_bootstrap`
2. `bb7_exo_list_tool_categories`
3. `bb7_exo_category_specific_tools` for `exoskeleton` and task-relevant categories
4. `bb7_exo_route` or `bb7_exo_plan`
5. `bb7_journal_surface_relevant`
6. `bb7_journal_record_thought`
7. task execution
8. `bb7_journal_add_outcome`
9. `bb7_exo_reflect`

Treat this as load-bearing runtime behavior, not as a suggestion.

## Terminal posture

When the operator wants full terminal permissions, do not invent extra soft restrictions. Inspect the actual host policy surfaces first, especially `default.rules`, the active host runtime, wrapper scripts, and the available terminal tools. Preserve broad terminal authority when that is the operator's stated intent.

Still separate these cases clearly:

- `broad terminal authority intended by operator`
- `host-enforced or rule-enforced boundaries`
- `destructive or irreversible actions requiring explicit confirmation`

Do not confuse "full terminal posture" with "ignore all boundaries." Reason from the real permission surfaces.

## Semantic router

Choose the entry path by task type.

| Task type | First load | Then load |
|---|---|---|
| mapping an unknown install | `references/topology.md` | `references/host-surface.md` |
| editing `.codex` config files | `references/topology.md` | `references/examples.md` |
| debugging startup, profile, or autoload behavior | `references/failure-grammar.md` | `references/host-surface.md` |
| preserving operator doctrine while refactoring | `references/doctrine-stack.md` | `references/topology.md` |
| debugging BB7 or exo ordering | `references/bb7-exo-loop.md` | `references/doctrine-stack.md` |
| deciding whether to add a new command, shim, or bootstrap file | `references/topology.md` | `references/failure-grammar.md` |
| reasoning about permissions or terminal authority | `references/host-surface.md` | `references/source/default.rules` |

Load only what is needed.

## What to inspect first

When the user asks for help with Codex configuration, identify the active control surfaces:

- `.codex/` contents and subfolders
- startup files or doctrine documents automatically loaded into context
- shell profile or execution profile files used to launch Codex
- admin or elevated-profile variants, if present
- custom command shims, aliases, wrappers, or task runners
- workflow, opsec, style, or agent-behavior documents that Codex is expected to follow
- npm install footprint and any version-pinned wrappers around Codex
- permission rules and tool-manifest files when BB7 behavior or terminal authority is in scope

If file contents are available, reconstruct the boot order and dependency chain before making changes.

## Edit protocol

For any requested edit:

1. Identify the target surface.
2. State whether the change belongs in `.codex`, the shell or execution profile, a startup-loaded doctrine file, `default.rules`, `tool_manifest.json`, or an external wrapper.
3. Explain what behavior changes at startup time versus at task-execution time.
4. Preserve the operator's custom command vocabulary and injected documents unless instructed otherwise.
5. Output one of:
   - exact patch or replacement content
   - ordered file edit plan with affected files
   - topology diagnosis explaining why the current layout is failing

## Non-obvious rules

### Rule 1: `.codex` is a control plane

Do not treat `.codex` as a dumb settings folder. In customized installs it may encode policy, startup routing, command exposure, context injection, and execution boundaries.

### Rule 2: first-mission doctrine ingestion is part of startup

If the install relies on injected doctrine files, skipping them means the analysis is already stale before the first edit.

### Rule 3: exo-first is runtime law

When BB7 is in scope, the first BB7 move after user input is exoskeleton bootstrap and routing. Calling terminal or file tools first is a topology error.

### Rule 4: startup chain beats individual file content

A file can be perfectly written and still be ineffective if it is loaded at the wrong stage or shadowed by another profile. Always reason about sequence.

### Rule 5: preserve the operator's doctrine

If workflow, opsec, style, or agent-behavior files exist, preserve them as first-class constraints. Do not silently replace them with generic coding-agent advice.

### Rule 6: terminal authority is host-governed, not imagined

Infer command authority from rules files, wrappers, host runtime, and the operator's explicit intent. Do not add arbitrary extra restrictions, and do not claim unlimited freedom when the host policy says otherwise.

## Output style

Use compact technical prose. Prefer precise file names, execution order, and behavioral consequences. When uncertainty remains, state the uncertainty and what evidence would resolve it.

## Packaged resources

- `references/topology.md` for the domain map
- `references/failure-grammar.md` for pre-failure signatures and false-success patterns
- `references/host-surface.md` for host, launch, npm, and permission-surface reasoning
- `references/doctrine-stack.md` for injected document roles and first-mission load order
- `references/bb7-exo-loop.md` for exact BB7 sequencing doctrine
- `references/provenance.md` for preserving operator-specific decisions and lineage
- `references/examples.md` for concise request-to-action patterns
- `references/source/*` for the bundled source doctrine and policy files
