# .codex Control-Plane Memory

This file captures durable setup decisions and gotchas for `/home/daeron/.codex`. It is separate from `/home/daeron/.codex/memories/MEMORY.md`, which is the Codex memory repository registry.

## Durable decisions

- Treat `/home/daeron/.codex` as the locked global config plane, not as an ordinary project repo.
- Keep BB7/Sovereign persistence rooted at `SOVEREIGN_DATA_DIR` from `config.toml`: `/home/daeron/Somnus-MCP/data`.
- Do not create per-project `data/` silos for BB7 state.
- Use SovereignMCP/Muaddib tools as the primary route when available; if unavailable, report the outage first and fall back carefully.
- Preserve `AGENTS.md` as constitutional baseline and `AGENTS.override.md` as runtime loop/order overlay.
- Treat `DESK/SOVEREIGN_CODEX_V2-2` as staged review material until explicitly deployed; do not blindly overwrite active config/hooks.
- Current minimal prompt-surface decision: enabled plugins are `mentat@local` and `ctmv3-workspace-activator@local` only; standalone custom skills are `academic-whitepaper-engine` and `codex-config-topology` only.
- Current token-hygiene decision: remove wasteful prompt/catalog/raw-output surfaces where possible, but do not restrict reasoning depth, time, compute, BB7/Sovereign MCP tools, Codex native memories, subagents, or validation scope.

## Gotchas

- `DESK/SOVEREIGN_CODEX_V2-2` remains staged evidence/review material. Do not blindly overwrite active config/hooks from staged files unless Daeron asks for that exact deployment.
- Active `/home/daeron/.codex/bin/hooks` is present; the earlier "missing active hooks" warning from bootstrap is superseded.
- Active `hooks.json` plus plugin hook manifests must stay Codex-schema-safe. Codex 0.136 requires `hookSpecificOutput.hookEventName` whenever hooks emit `additionalContext`; unsupported events must suppress unsupported stdout shapes.
- `features.plugins = true` is intentional because local old-build plugins `mentat@local` and `ctmv3-workspace-activator@local` are installed/enabled.
- `/home/daeron/.codex/.codex/config.toml` intentionally sets `project_doc_max_bytes = 0` only for the CODEX_HOME control-plane repo to prevent double-loading `AGENTS.override.md` while working inside `.codex`; do not copy that setting into global user config unless Daeron wants project docs disabled everywhere.
- Bundled system skill `SKILL.md` entrypoints are archived in `/home/daeron/.codex/skills.archive/20260604_1715_system_skill_registry_suppression/` to suppress prompt registry entries. The system skill directories/resources/scripts remain in place; restore `SKILL.md` files if those system skill advertisements are needed again.
- `approvals_reviewer = "user"` is currently fine because `approval_policy = "never"` is the active approval policy; do not churn it without a fresh reason.
- Current config retains trusted hook hashes for active root/plugin hooks; after editing hook commands, re-run trust/schema checks and strict doctor.
- `plugins/mentat` is a symlink to `/home/daeron/Projects/Modern-ML/Plugins/Mentat`; verify the target before editing plugin code.
- Do not leave `*.toml` backups under `agents/`; Codex treats them as active agent definitions and may warn on duplicate role names.
- Do not enable `multi_agent_v2`, `enable_fanout`, or `child_agents_md` casually; current stable path is `multi_agent` v1 with `[agents]` limits.

## Reusable artifacts

- `codex-filetree.md`: safe routing map of the `.codex` file tree with state/secrets collapsed.
- `CONTEXT.md`: current operational state and next actions for config-plane stabilization.
- `DESK/SOVEREIGN_CODEX_V2-2/STAGING_ANALYSIS.md`: human-readable staging report.
- `DESK/SOVEREIGN_CODEX_V2-2/validation_manifest.json`: machine-readable staging validation evidence and hashes.


## 2026-06-03 — State-machine and CodeGraph decisions

- Durable doctrine: Codex is the active state machine; SovereignMCP/Muaddib, Mentat, CodeGraph, native tools, hooks, memories, and workflows are assistive surfaces that help state transitions but do not control them.
- `MCP_SPEC.md` is the canonical topology/spec reference for the Sovereign MCP substrate. Use it to understand `bb7_*` compiled capabilities, but use the live registry as runtime truth.
- `workflows.md` is a Golden Path playbook, not a mandatory script. Use the smallest useful subset and avoid empty ritual/tool spam.
- CodeGraph is not initialized for `/home/daeron/.codex` as of 2026-06-03. The CLI exists, but `.codegraph/` is missing and `config.toml` has no CodeGraph MCP server. Before initializing CodeGraph on `.codex`, create an ignore/scope policy for secrets and high-churn state.


## 2026-06-03 — BB7 memory front and center

- Durable doctrine update: BB7/Sovereign MCP memory tools are the first-class continuity substrate for Codex state transitions.
- Default non-trivial task start: `bb7_lisan_recall`, or targeted `bb7_memory_surface_context` / `bb7_memory_search` / `bb7_memory_intelligent_search` when narrower recall is better.
- Default meaningful task close: `bb7_memory_store` with category/importance/tags; use `bb7_memory_analyze_entry` and `bb7_link_memory_to_session` for high-value memories that should enter the graph/session substrate.
- Memory tools remain assistive rather than controlling. They provide continuity/evidence/routing context but do not override current evidence, user direction, safety, or instruction hierarchy.
- Avoid low-signal memory spam; front and center means continuity-first, not ritual storage.


## 2026-06-03 — CodeGraph initialized safely for .codex

- CodeGraph is no longer just a stale AGENTS claim for `/home/daeron/.codex`; it is initialized and wired in `config.toml` as non-required MCP server `codegraph`.
- Safety policy: `.gitignore` excludes `auth.json`, `installation_id`, `.env*`, keys/certs, sqlite/db files, jsonl files, sessions/log/tmp/shell snapshot directories, `.codegraph/`, cache files, binary archives/images, plugin cache, and generated backup churn.
- Verification: `codegraph status /home/daeron/.codex` shows up-to-date index with 98 files, 1,379 nodes, 3,028 edges; `codex doctor` sees 3 MCP servers; high-risk indexed path audit passed.
- Current sessions may need MCP reload/new Codex session before `codegraph_*` tools are available, but the CLI works now.


## 2026-06-03 — Codex hook schema gotcha and terminal-routing decision

- Codex CLI 0.136 validates hook stdout against per-event schemas. When a hook emits `hookSpecificOutput.additionalContext`, the nested object must include the event discriminator `hookSpecificOutput.hookEventName` with the exact event name.
- The active UserPromptSubmit failure was caused by `/home/daeron/.codex/bin/hooks/_lib.py` emitting `{"hookSpecificOutput":{"additionalContext":"..."}}` without `"hookEventName":"UserPromptSubmit"`.
- Fixed active and staged `_lib.py` so `write_additional_context(...)` infers the hook event and emits schema-valid `hookSpecificOutput`.
- Fixed a latent PreCompact hazard: Codex 0.136 `PreCompact`/`PostCompact`/`SubagentStop`/`Stop` output schemas do not allow `hookSpecificOutput`, so the helper now suppresses `additionalContext` stdout for unsupported events instead of producing invalid JSON.
- Verification artifact: `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/hooks_active_schema_smoke_20260603_151645.json`; all 15 active command hooks passed schema-lite smoke validation.
- Durable operator preference: use native Codex Bash/terminal execution for shell work; do not use Sovereign/BB7 shell-runner tools such as `bb7_run_command` for ordinary terminal commands. BB7 remains front-and-center for memory, journal, context, and persistence.
- After the repair/doc updates, `codegraph sync /home/daeron/.codex` completed and the index is current at 113 files, 1,574 nodes, and 3,354 edges without indexing generated backups, `__pycache__`, runtime state, or validation artifacts.


## 2026-06-03 — workflows/MCP sync and installed plugin hook repair

- `workflows-new.md` is the current source workflow driver and `workflows.md` is mirrored from it. The Codex runtime overlay is binding: native Codex Bash for ordinary shell execution; BB7/Sovereign remains front-center for memory, context, file, lisan/exo routing, and persistence.
- `MCP_SPEC.md` now clearly encodes the Somnus/Sovereign MCP substrate as one server/data-plane/venv with BB7 endpoints as compiled capability surfaces. Static docs explain topology; the live registry remains runtime truth.
- Installed Mentat plugin hook gotcha: Codex CLI 0.136 requires `hookSpecificOutput.hookEventName` whenever `additionalContext` is emitted. Patched active cache, local marketplace source, and Modern-ML Mentat source helpers for both Claude-style hooks and Codex adapter hooks.
- Installed CTMv3 workspace activator gotcha: raw `python3 -m ctmv3 boot --json` stdout is not valid Codex hook JSON, and Stop `decision: "escalate"` is not accepted. Patched cache/source/Modern-ML `hooks.json` to use `session_start_codex.py` and `stop_codex.py`; Stop now emits top-level `decision: "block"` with reason only when substantive edits are detected.
- Verification artifact: `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/plugin_hooks_schema_smoke_20260603_153658.json` reports 14 total, 12 passed, 0 failed, 2 skipped for unsupported `SessionEnd`/`StopFailure`. `codex doctor` remained 17 ok / 0 warn / 0 fail.
- Reversible backups were created with `backup_hook_schema_20260603_1530` suffix beside patched plugin files and `workflows.backup_before_new_sync_20260603_152900.md` beside the workflow mirror.


## 2026-06-03 — Subagent and old-build skill readiness decisions

- Codex native subagent readiness is verified on the stable v1 path: `[features].multi_agent = true`, `[agents] max_threads = 12`, `max_depth = 2`, `job_max_runtime_seconds = 7200`; `codex features list` reports `multi_agent stable true`.
- Do not enable `multi_agent_v2` casually. In Codex 0.136 it remains under-development/false, and the runtime validates that `agents.max_threads` cannot be set when `multi_agent_v2` is enabled.
- `enable_fanout` and `child_agents_md` are also under-development/false as of the 2026-06-03 audit. Historical feature-atlas comments in `config.toml` were corrected so future agents do not mistake them for active truth.
- Root Sovereign hooks and Mentat plugin hooks both observe `SubagentStart`/`SubagentStop`. Treat this as intentional dual observation: root hooks handle Sovereign/BB7 lifecycle, while Mentat hooks handle state-machine/insight ledger effects.
- The only placeholder user-scope agent, `agents/nlp-data-processing.agent.toml`, was replaced with a real NLP/data-pipeline specialist. Its automatic backup was moved out of `agents/` because Codex treats TOML backups there as active agent definitions and warns about duplicate role names.
- Modern-ML old-build skills now installed into `.codex/skills/custom`: `ssds-reverse-engineering-pipeline` and `cognitive-topology-v3` / `sovereign-skill-architect`. `codex debug prompt-input` confirmed both are visible.
- Subagent readiness reference doc: `/home/daeron/.codex/docs/codex-subagent-readiness.md`. Readiness evidence artifacts: `DESK/SOVEREIGN_CODEX_V2-2/subagent_plugin_skill_readiness_20260603_154850.json` and `.md`.


## 2026-06-03 — Completion audit final state

- Final completion audit artifacts are under `DESK/SOVEREIGN_CODEX_V2-2/codex_setup_completion_audit_20260603_1610.{json,md}`.
- The audit derived and passed 13 requirements: doctrine, config, MCP, BB7 live registry, workflows/MCP_SPEC, CodeGraph, hooks, plugins, skills, subagents, DESK assets, local docs, and doctor gates.
- `config.toml` was normalized for Codex 0.136 effective false/removed flags: `js_repl = false`, `tool_search = false`, `undo = false`. This does not remove the separate runtime `tool_search` developer surface when exposed.
- Early bootstrap warnings about missing active hooks and uninitialized CodeGraph are superseded. Active hooks exist and CodeGraph is initialized/wired.
- Old-build local plugin state is complete for the known requested pair: `mentat@local` and `ctmv3-workspace-activator@local` installed/enabled; hooks schema-smoked and py_compile-clean.
- Old-build skill state is complete for the known requested skills: `ssds-reverse-engineering-pipeline` and `cognitive-topology-v3` / `sovereign-skill-architect`; prompt-input smoke sees them.
- Native Codex subagent state is complete on stable `multi_agent` v1; do not enable v2/fanout/child-agent markdown without fresh migration.


## 2026-06-03 — BB7 session label for global config plane

- Active BB7/Sovereign session for future `.codex` global config work: `8438249d-298d-4e67-84d5-1837cef0d2d7`.
- Session label: `Codex Global Config — Global Codex control-plane continuity`.
- Anchor memory linked: `codex_config_plane_setup_complete_2026_06_03`.
- Resume from completion evidence: `DESK/SOVEREIGN_CODEX_V2-2/codex_setup_completion_audit_20260603_1610.{json,md}`.


## 2026-06-03 — Spark compatibility gotcha: do not set global reasoning summary

- `gpt-5.3-codex-spark` rejects the API parameter `reasoning.summary`; a failed startup showed `unsupported_parameter` for `reasoning.summary`.
- Durable config decision: keep `/home/daeron/.codex/config.toml` free of top-level `model_reasoning_summary` so Spark/profile overrides do not inherit an unsupported global payload field.
- On 2026-06-03, removed `model_reasoning_summary = "detailed"` from active `config.toml` and created backup `/home/daeron/.codex/config.backup_before_spark_reasoning_summary_removal_20260603_201447.toml`.
- Verification after removal: TOML parse OK; active grep found no `model_reasoning_summary`/`reasoning.summary`; `codex --strict-config doctor --json` reported `overallStatus = ok`; `codex doctor` reported `17 ok · 1 idle · 1 notes · 0 warn · 0 fail`.
- If a future non-Spark model needs reasoning summaries, prefer a model-specific/profile-specific mechanism rather than restoring `model_reasoning_summary` globally.
- Shell gotcha: `codex resume, then select Aeron + SRA 6-3-2026 (019e902d-f341-7312-a47c-7f5eba82dabf)` is not a Bash command; parentheses are shell syntax. Run `codex resume` and choose the session interactively, or quote a direct session id if using a supported direct-resume form.


## 2026-06-03 — Constitutional prompt framework skill

- Added custom skill `constitutional-prompt-framework` in `/home/daeron/.codex/skills/custom/constitutional-prompt-framework`.
- Purpose: derive, audit, and refactor dense single-file agent constitutions / system prompts for local coding agents, online agents, autonomous task prompts, and platform-agnostic role/doctrine prompts.
- Design decision: keep `SKILL.md` concise and place detailed doctrine in directly-linked references (`references/derivation-guide.md`, `references/audit-checklist.md`) plus a copyable scaffold asset (`assets/single-file-agent-constitution-skeleton.md`).
- Durable constraint: the skill explicitly avoids BB7/Sovereign/Muaddib/local Codex control-plane mechanics in platform-agnostic outputs unless Daeron explicitly requests platform-specific binding.
- Verification: `quick_validate.py` passed; PyYAML parse of `agents/openai.yaml` passed; `codex debug prompt-input` shows the skill as discoverable at `r0/custom/constitutional-prompt-framework/SKILL.md`; CodeGraph sync remains up to date.


## 2026-06-03 — Skill frontmatter loader gotcha: quote long descriptions

- `constitutional-prompt-framework/SKILL.md` initially passed `quick_validate.py` but Codex runtime skipped it with `invalid YAML: description: invalid type: sequence, expected a string`.
- Fix: quote the long frontmatter `description` value explicitly.
- Verification after fix: `quick_validate.py` passed; PyYAML confirmed `description` is `str`; `codex debug prompt-input` exited `rc=0`, emitted no skipped/invalid skill warnings, and listed `constitutional-prompt-framework` as discoverable.
- Durable rule: treat `codex debug prompt-input` as the real skill discovery gate; quote long skill descriptions even if the scaffold validator accepts unquoted YAML.


## 2026-06-04 — Lean Codex skill loadout decision

Decision: Keep Codex startup skill context lean. Daeron's desired active loadout is whitepaper, design, Codex config, and CTM skills, with Mentat plugin/MCP and CTMv3 plugin/subagent surfaces preserved.

Durable outcomes:

- Archived duplicate/non-whitelist skill directories to `/home/daeron/.codex/skills.archive/20260604_0552_lazy_load_cleanup/`; use that directory's `manifest.json` for restore paths.
- Active skill scan roots now expose canonical `.codex` skills instead of duplicate `.agents` copies.
- `claude-code-setup@claude-plugins-official` is installed but disabled to remove its skill from prompt context. Re-enable only when doing Claude automation recommendations.
- `mentat@local`, `ctmv3-workspace-activator@local`, and `explanatory-output-style@claude-plugins-official` stay enabled.
- Verified prompt skill segment: 12,489 chars and 21 actual available skill entries, no duplicate names, no invalid-skill warnings.
- Verified MCP: `SovereignMCP`, `codegraph`, and `mentat` remain enabled. No standalone CTMv3 MCP server is visible; CTMv3 currently comes through plugin skill/hooks/commands/agent file.

Gotcha: Codex already lazy-loads skill bodies; the context tax is the advertised skill registry. Reduce it by keeping one canonical active skill root, archiving dormant skills outside scanned roots, shortening descriptions if necessary, and disabling nonessential plugin skills.


## 2026-06-04 — Minimal prompt-surface loadout and operator token hygiene

- Durable loadout decision: keep enabled plugins to `mentat@local` and `ctmv3-workspace-activator@local` only. Other installed plugins may remain installed but disabled unless Daeron explicitly asks to restore them.
- Durable skill decision: keep standalone custom skills to `academic-whitepaper-engine` and `codex-config-topology` only. Extra custom skill directories were archived to `/home/daeron/.codex/skills.archive/20260604_165745_minimal_requested_loadout/`; use that archive's `manifest.json` for restore paths.
- `explanatory-output-style@claude-plugins-official` was disabled on 2026-06-04 because it was outside the requested plugin pair.
- This is a prompt/context hygiene decision, not an efficiency-mode decision. Do not restrict tokens, time, compute, tool use, subagents, BB7/Sovereign MCP, Codex native memories, repo memories, or global memory surfaces just to be cheap.
- Token hygiene rule: spend deeply when the state transition needs it, but avoid dumping raw catalogs, raw JSON, broad file contents, or marketplace listings into model context when a focused/progressive BB7 route or cleaned validation summary is enough.
- File tooling correction: for control-plane comprehension and edits, prefer BB7/Sovereign file tools (`bb7_read_file`, `bb7_write_file`, `bb7_append_file`, `bb7_search_files`, `bb7_list_directory`). Avoid Unix `cat`/`sed`/broad `grep` as the default file-read surface because shell output clipping can create false beliefs about truncation or incomplete file state. Native Bash remains correct for execution/validation commands such as `codex doctor`, `codex debug prompt-input`, parsers, and test runners.
- Raw JSON/output pipeline note: hooks, BB7 tools, and internal telemetry may intentionally preserve raw JSON for flywheel/distillation/provenance. The optimization is to shape visible/model-facing outputs, not to destroy structured raw data behind the scenes.


## 2026-06-04 — CTMv3 hook output projection gotcha

- Daeron flagged plugin/hook raw JSON dumps as token waste when they are injected into model-facing context. Raw JSON/provenance is still desirable behind the scenes; the fix is projection, not destroying telemetry.
- CTMv3 SessionStart raw JSON was compacted by patching `session_start_codex.py` in the installed Codex cache, local marketplace source, and Modern-ML source tree. The wrapper still executes `python -m ctmv3 boot --json`, then parses the raw output and emits a compact `hookSpecificOutput.additionalContext` block.
- Validation sample after patch: compact CTMv3 context is about 378 chars, contains `branch=PARTIAL`, file count, tier signals, golden next command/tags, and does not include raw `[CTMV3_GOLDEN_PATH]` or raw JSON blob text.
- Mentat SessionStart was inspected and already uses compact/capped boot/handoff context through its shared 2KB cap; no Mentat hook patch was needed.
- Durable rule: hook stdout must remain Codex-schema-valid, but model-facing `additionalContext` should be compact/projection-oriented. Preserve raw hook/tool payloads in telemetry, logs, or side channels rather than injecting them directly into prompt context.


## 2026-06-04 — Codex global constitution compiler

Durable decision: the global `.codex` constitution is now compiled from separate editable docs into one runtime prompt surface. The compiler lives at `bin/hooks/compile_constitution.py` and writes `COMPILED_CONSTITUTION.md` plus a generated top-level `developer_instructions` block in `config.toml`.

Important gotcha: in this Codex build, `codex debug prompt-input` did not show content from `model_instructions_file`, but did show `developer_instructions`. Keep `model_instructions_file = "/home/daeron/.codex/COMPILED_CONSTITUTION.md"` as the artifact pointer, but treat the generated `developer_instructions` block as the proven live prompt bridge unless future runtime evidence changes.

Validation evidence: strict doctor OK; prompt-input markers for `AGENTS.override.md`, `AGENTS.md`, `USER.md`, `MEMORY.md`, `CONTEXT.md`, and `workflows-new.md` were present from both `/home/daeron/.codex` and `/home/daeron/Projects`. Token impact is material: compiled constitution ~169,536 chars (~42.4k char/4 tokens), full prompt-input ~47.3k char/4 tokens.


## 2026-06-04 — Kernel + dynamic retrieval is the preferred global prompt topology

Durable decision: avoid full always-on constitution injection as the steady state. Keep `COMPILED_CONSTITUTION.md` as a full audit/recovery artifact, but use `COMPILED_KERNEL.md` as the live global prompt artifact. The live `developer_instructions` bridge now contains only `AGENTS.override.md`, `AGENTS.md`, and a generated retrieval contract.

Important pattern: load the law, retrieve the state. `SOUL.md`, `USER.md`, `MEMORY.md`, `CONTEXT.md`, `workflows-new.md`, native Codex memories, BB7/Lisan, Mentat, CTMv3, and CodeGraph are retrieval/context surfaces, not default full-prompt paste. `SessionStart` should inject compact state projection only; deeper reads/searches happen when task-relevant.

Validation evidence: prompt-input from `/home/daeron/Projects` contains kernel markers and no full-source USER/SOUL/MEMORY/CONTEXT/workflow markers. Rough prompt-input estimate dropped from ~47.3k to ~20.4k char/4 tokens.

## 2026-06-05 — Token Density Governor and FSTIP contract

- Durable global rule: the active chat frame is for orchestration and verification vectors, not for echoing raw filesystem state. Full file echoes, verbose raw JSON, and broad unbounded payloads are context-compilation failures unless explicitly required for audit.
- Added `TOKEN_DENSITY_GOVERNOR` to `AGENTS.override.md` and regenerated `COMPILED_KERNEL.md` with `bin/hooks/compile_constitution.py`; keep edits in source docs, not generated kernel files.
- Corresponding Somnus-MCP implementation lives in `tools/file_tool.py` and `mcp_server.py`:
  - file reads should use `start_line`/`end_line` or `semantic_target` when possible,
  - large naked reads return structural skeleton manifests by default,
  - write/append operations return sparse `FILE_PATCH_SUCCESS` manifests,
  - MCP display projection suppresses oversized file string echoes while preserving raw payloads before projection for telemetry and distillation lanes.
- Environment knobs: `SOVEREIGN_FILE_READ_GOVERNOR_BYTES` default 131072 bytes; `SOVEREIGN_FILE_SURFACE_INLINE_MAX_CHARS` default 24000 chars.
- Restart caveat: changed MCP source files do not update already-running server processes; reload/restart is required for live tool schemas and behavior to reflect the patch.


## 2026-06-05 — Kwisatz Council prompt artifact

- New agnostic Markdown prompt artifact: `/home/daeron/.codex/agents/kwisatz-council.md`.
- Source preserved first, then expanded via `constitutional-prompt-framework` into a dense agent constitution for KWISATZ COUNCIL without introducing `bb7` tool dependencies into the prompt artifact.
- Durable pattern: for portable agent prompts, keep private/local runtime tools out of the constitution body; express capabilities by class with availability fallbacks, and move target-specific paths/models/tools into binding notes or source snapshots.
- Validation result at creation: CPF linter PASS; score 83/100 production candidate; 978 lines; SHA256/16 `9f491492c12c9b7a`; no emoji codepoints and no `bb7` substring.


## 2026-06-05 — Kwisatz Council Enhancement Pass 2

- `/home/daeron/.codex/agents/kwisatz-council.md` was appended, not rewritten, with `Enhancement Pass 2 — Deployment Binding, Invocation, and Acceptance Gates`.
- Pass 2 durable additions: runtime binding contract, binding manifest, active cycle invocation template, organ brief templates, artifact manifest, evidence citation standard, completion audit, instruction-contamination defense, memory governance detail, task-specific output contracts, readiness language discipline, and compact final runtime reminder.
- Validation after pass 2: CPF linter PASS; CPF score 84/100 production candidate; 1,452 lines; 70,085 bytes; SHA256/16 `1a9a1ce761267d2a`; no emoji codepoints and no `bb7` substring in the prompt artifact.


## 2026-06-05 — Kwisatz Council Enhancement Pass 3

- `/home/daeron/.codex/agents/kwisatz-council.md` received append-only `Enhancement Pass 3 — Full Agent Setup, Lifecycle, and Red-Team Harness`.
- Durable additions: agnostic agent setup topology, deployment assembly checklist, organ identity integrity, lifecycle state machine, work product schemas, acceptance scorecard, red-team harness, anti-sycophancy mechanism, compaction recovery protocol, operator interface contract, platform wrapper boundary, and full setup acceptance gate.
- Validation after pass 3: CPF linter PASS; CPF score 86/100 production candidate; 1,884 lines; 90,952 bytes; SHA256/16 `e0ecbd1ad835eb78`; no emoji codepoints and no `bb7` substring in the prompt artifact.


## 2026-06-05 — Kwisatz Council Enhancement Pass 4

- `/home/daeron/.codex/agents/kwisatz-council.md` received append-only `Enhancement Pass 4 — Mission Kernel, Persona Compression, Continuity, and Output Spine`.
- Durable additions: mission kernel, mission derivation chain, success/non-success definitions, compressed persona architecture, memory-class continuity model, runtime-ready output spine, prompt change report, living status/versioning upgrade, release checklist, and runtime sibling compilation plan.
- Validation after pass 4: CPF linter PASS; CPF score stayed 86/100 production candidate; 2,265 lines; 106,255 bytes; SHA256/16 `a696f3864ea90790`; no emoji codepoints and no `bb7` substring in the prompt artifact.
- Note: future scoring should run against a clean compiled sibling prompt rather than the workshop source, because the workshop intentionally preserves raw source and enhancement history.


## 2026-06-05 — Kwisatz Council runtime sibling

- Clean runtime Markdown sibling created: `/home/daeron/.codex/agents/kwisatz-council.runtime.md`; workshop/source remains `/home/daeron/.codex/agents/kwisatz-council.md`.
- Runtime sibling is standalone and excludes raw source snapshot plus enhancement pass history; it keeps the core agnostic by using binding slots and no private runtime tool dependencies.
- Validation artifacts: `/home/daeron/.codex/agents/kwisatz-council.runtime.validation.md` and `/home/daeron/.codex/agents/kwisatz-council.runtime.validation.json`.
- Runtime sibling validation: CPF linter PASS; CPF score 88/100 production candidate; 1,285 lines; 51,958 bytes; SHA256/16 `eb890b2a7b7227bc`; no emoji codepoints, no `bb7` substring, no raw source snapshot, no enhancement history, no hard `/agent/workspace/` path.
- JSON validation manifest parses successfully; validation artifact hashes: Markdown `9819befc717f5e4a`, JSON `3ae59c0b6f363426`.
- Next branch: red-team the runtime sibling or bind it into a platform-specific TOML/wrapper only after Daeron confirms the runtime Markdown shape.


## 2026-06-05 — Kwisatz Council runtime red-team

- Red-team artifacts created for `/home/daeron/.codex/agents/kwisatz-council.runtime.md`: `/home/daeron/.codex/agents/kwisatz-council.runtime.redteam.md` and `/home/daeron/.codex/agents/kwisatz-council.runtime.redteam.json`.
- Result: critical probes 7/7 PASS by prompt-structure review; high probes 5/5 PASS; no runtime prompt body patches required before wrapper/TOML; deployment impact AMBER because wrapper binding and live-agent behavior remain untested.
- Red-team artifact hashes: Markdown `81a78b4b1e9f67e4`, JSON `40fe3d221f59670b`; JSON parses successfully.
- Current artifact set: `kwisatz-council.md` workshop/source, `kwisatz-council.runtime.md` clean runtime sibling, `.runtime.validation.{md,json}`, `.runtime.redteam.{md,json}`.
