---
name: codex-config-topology
description: Inspect, configure, and preserve a customized Codex control plane. Use when the user asks what it takes to configure Codex, how AGENTS.md/AGENTS.override.md/MEMORY.md/CONTEXT.md/USER.md/SOUL-like files load, how CODEX_HOME/config.toml/profiles/project docs work, how to wire MCP or bb7_ tools, hooks, skills, plugins, subagents, permissions, JSON tool-output cleanup, operator semantics, or how to rebuild Codex behavior without crossing external OAuth/runtime boundaries.
---

# Codex Config Topology

Treat Codex as an operator runtime with layered configuration surfaces, not as a single settings file. The job is to identify the owning surface for a behavior, verify the live Codex version/docs, and make reversible changes that preserve Daeron's operator-control-plane doctrine.

## Current truth boundary

Use current evidence before making configuration claims.

1. Run the official Codex manual helper first for Codex-doc questions:
   `node /home/daeron/.codex/skills/.system/openai-docs/scripts/fetch-codex-manual.mjs`
2. Prefer official OpenAI Codex docs when browsing is needed.
3. Inspect the live runtime: `codex --version`, `codex doctor`, `codex doctor --json`, `codex mcp list --json`, `codex features list`, `codex plugin list`, and `codex debug prompt-input` when prompt loading matters.
4. Separate official Codex capabilities from local doctrine, BB7/Sovereign/Mentat/CTM plugins, hooks, and operator preferences.

Do not claim AGENTS.md replaces the upstream OpenAI/system/developer instruction stack. It does not. It is persistent guidance loaded under higher-priority runtime instructions. The achievable Hermes-like design is: Codex upstream runtime + local model instructions + project docs + hooks + MCP + skills/plugins + memory + operator discipline.

## 2026-06-04 configuration surface map

Use `references/current-codex-surfaces-2026-06-04.md` for details. The short map:

| Surface | Owns | Verification |
|---|---|---|
| `CODEX_HOME` | user-level Codex state root, default `~/.codex` | `echo $CODEX_HOME`; `codex doctor` |
| `~/.codex/config.toml` | user config: model, approval, sandbox/permissions, features, MCP, hooks state, plugins | TOML parse; `codex doctor --json` |
| profile files | `~/.codex/<profile>.config.toml` selected by `--profile` | `codex --profile name doctor` |
| project `.codex/config.toml` | trusted project-scoped config; cannot override credential/provider/profile/telemetry keys | trusted-project check; startup warnings |
| `AGENTS.override.md` / `AGENTS.md` | persistent instruction chain | `codex debug prompt-input` |
| fallback project docs | alternate instruction filenames per directory; at most one file per directory is included | `project_doc_fallback_filenames`; prompt-input audit |
| MCP | external tools/context including BB7/Sovereign, CodeGraph, Mentat | `codex mcp list --json`; live tool discovery |
| hooks | lifecycle automation and optional additionalContext injection | `hooks.json`; hook schema smoke |
| skills | reusable workflows with progressive disclosure | skill validation; `/skills`; prompt-input skill list |
| plugins | bundles of skills, apps, hooks, MCP, assets | `codex plugin list` |
| memories | local recall layer, not binding rules | `[features].memories`; memory store files/DB |
| subagents | manually triggered parallel/read-heavy workers | feature list; subagent config |
| permissions/sandbox | local command filesystem/network boundaries | `codex doctor`; permissions docs |

## Operator-control-plane translation

When Daeron says "operator, not agent," preserve that terminology in local docs and skills. Recommended mapping:

- `AGENTS.override.md`: compact runtime law and strict current turn-order rules.
- `AGENTS.md`: larger constitution/identity/operator semantics. This may not autoload when an override wins; verify.
- `USER.md`: stable operator facts. Not magic unless loaded by prompt discovery, hooks, or explicit file reads.
- `MEMORY.md`: durable local control-plane decisions and gotchas. Not a replacement for Codex Memories or BB7 memory.
- `CONTEXT.md`: current state/handoff, often updated after major transitions.
- `MCP_SPEC.md` / `workflows.md`: reference maps and golden paths; load the smallest useful subset.
- optional `SOUL.md`: symbolic/persona layer. If created, make its load path explicit; do not assume Codex reads linked files.

Important discovery gotcha: Codex includes at most one instruction file per directory in project scope, checking override first. A fallback list cannot force multiple same-directory docs to load simultaneously if `AGENTS.override.md` is already selected. For a Hermes-like multi-doc startup, use one or more of:

1. a single aggregator `model_instructions_file` that contains the compact essentials;
2. explicit runtime instruction to read `USER.md`/`MEMORY.md`/`CONTEXT.md` before substantial work;
3. hook `additionalContext` injection for concise state summaries;
4. nested project directories for scoped project docs;
5. skills for workflows and references instead of stuffing everything into startup context.

## BB7/Sovereign/Mentat/CTM posture

Current local override wins over older references: start non-trivial work with memory/context resurrection (`bb7_lisan_recall`, targeted memory/context tools) before broad exploration. Do not use BB7/Sovereign shell-runner tools for ordinary terminal work; use native Codex shell. Use BB7 for memory, sessions, journal, file/context persistence, and cognitive routing when it adds signal.

BB7 tools cannot become OpenAI-native tools by config alone. As of this skill snapshot, the closest supported Codex configuration is always-on MCP wiring with server instructions, tool allowlists/policy, startup docs, hooks, and skill routing. True native built-ins would require Codex source/runtime changes or an official extension surface beyond config.

## JSON tool-output hygiene

Use `references/json-tool-output-hygiene.md` and the audit script when cleaning tool output. Core rule: capture structured output to a file or pipe into `python3 -c`/`jq`. Do not pipe JSON into `python3 - <<'PY'`; the heredoc consumes stdin and starves the pipe.

Preferred pattern:

```bash
tmp=$(mktemp)
codex doctor --json > "$tmp"
python3 -c 'import json,sys; obj=json.load(open(sys.argv[1])); print(obj.get("overallStatus"))' "$tmp"
rm -f "$tmp"
```

Use clean manifests for long validation passes: Markdown report for humans, JSON manifest for future operators/agents, raw terminal snippets only where they add evidence.

## Workflow

1. **Sync context**
   - Detect host/runtime: OS, shell, CWD, Codex version.
   - Run BB7 memory/context resurrection for non-trivial work.
   - Read local `AGENTS.override.md`, `CONTEXT.md`, `MEMORY.md`, and task-relevant `workflows.md`/`MCP_SPEC.md`.
   - Fetch current Codex docs/manual for OpenAI/Codex behavior.
2. **Map surfaces**
   - Identify whether the behavior belongs to config, profile, project docs, hooks, MCP, skills, plugins, memories, subagents, host profile, or wrapper.
3. **Plan edit**
   - State the owning surface, runtime effect, verification command, and rollback path.
   - Avoid broad destructive edits; preserve operator vocabulary.
4. **Execute**
   - Use direct file tools for persistent source/config/doc edits.
   - Keep secrets out of terminal output and docs.
5. **Verify**
   - TOML/JSON/YAML parse checks.
   - `codex doctor --json`, relevant CLI list commands, and `codex debug prompt-input` for prompt-loading changes.
   - Skill validation for skill edits.
6. **Persist**
   - Update local `CONTEXT.md`/`MEMORY.md` after meaningful transitions.
   - Store durable BB7 memory only for reusable signal, not empty ritual.

## Semantic router

| Task type | Load first | Then load/use |
|---|---|---|
| "what does it take to configure Codex" | `references/current-codex-surfaces-2026-06-04.md` | audit script |
| Hermes-like AGENTS/MEMORY/CONTEXT/SOUL semantics | `references/operator-control-plane.md` | `codex debug prompt-input` |
| JSON tool output cleanup/formatting | `references/json-tool-output-hygiene.md` | audit script |
| BB7/Mentat/CTM integration | `references/bb7-exo-loop.md` | MCP list + hook audit |
| startup/profile/autoload bug | `references/failure-grammar.md` | prompt-input + doctor |
| permission or full terminal posture | `references/host-surface.md` | doctor + config/permissions docs |
| skill/plugin packaging | official skills/plugins docs | skill validation |

Load only the minimum references needed.

## Non-negotiable gotchas

- `AGENTS.override.md` can shadow `AGENTS.md`; verify, do not assume.
- `project_doc_fallback_filenames` does not load every listed file; it supplies alternate names after `AGENTS.override.md`/`AGENTS.md` checks.
- Project `.codex/config.toml` loads only in trusted projects and cannot override provider/auth/profile/telemetry-style keys.
- Profile files are `~/.codex/<name>.config.toml` in current Codex docs; do not use stale `[profiles.<name>]` guidance unless verified.
- Hooks with `additionalContext` must emit schema-valid JSON for that event; unsupported events should emit nothing.
- Multiple matching hooks can run; do not assume higher-precedence hooks replace lower ones.
- `codex plugin list` is human/table output in this runtime; sanitize before handing to another operator/agent.
- Keep `SOVEREIGN_DATA_DIR` rooted at `/home/daeron/Somnus-MCP/data`; never create ad-hoc BB7 data silos.
- Do not cross Hermes/OpenAI/xAI/Gemini OAuth boundaries unless Daeron explicitly authorizes it.

## Packaged resources

- `references/current-codex-surfaces-2026-06-04.md` — official and local Codex surface map.
- `references/operator-control-plane.md` — operator semantics and Hermes-like doc-stack design.
- `references/json-tool-output-hygiene.md` — JSON parsing, redaction, reports, manifests.
- `references/failure-grammar.md` — stale-config and false-success patterns.
- `references/bb7-exo-loop.md` — current BB7/Sovereign loop boundary.
- `references/doctrine-stack.md` — instruction/document stack reasoning.
- `references/host-surface.md` — host/profile/wrapper/permissions inspection.
- `references/topology.md` — concise topology map.
- `scripts/audit_codex_control_plane.py` — local redacted audit helper.
