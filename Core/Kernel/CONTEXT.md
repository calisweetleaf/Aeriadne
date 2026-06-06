# .codex Control-Plane Context

**Last updated:** 2026-06-04T17:20:00-05:00
**Runtime:** Linux laptop (`/home/daeron/.codex`), bash, Codex CLI 0.137.0 observed by `codex --version` / `codex doctor`.

## Current objective

Keep Daeron's global Codex control plane fixed as an operator runtime, not a generic coding-agent setup. Current emphasis: minimal prompt/plugin/skill loadout, BB7/Sovereign-first continuity and file/context routing, preserved deep compute/tool availability, and avoidance of unnecessary prompt-surface/raw-output waste.

## Active control-plane state

- `AGENTS.md` exists and serves as constitutional baseline / identity doctrine.
- `AGENTS.override.md` exists and is the highest-priority runtime loop/tool-order override.
- `config.toml` exists and currently wires:
  - `model_instructions_file = "AGENTS.override.md"`
  - `approval_policy = "never"`
  - `sandbox_mode = "danger-full-access"`
  - `mcp_servers.SovereignMCP` pointing at `/home/daeron/Somnus-MCP/mcp_server.py`
  - `SOVEREIGN_DATA_DIR = "/home/daeron/Somnus-MCP/data"`
- Project-local `/home/daeron/.codex/.codex/config.toml` exists with `project_doc_max_bytes = 0` so the CODEX_HOME repo itself does not double-load `AGENTS.override.md`; global project docs remain enabled for real project repos through the user config.
- SovereignMCP is alive in this session and is the front-line BB7/Lisan/Muad'Dib continuity and routing substrate.
- `hooks.json` is the active merged lifecycle hook config, backed by present `/home/daeron/.codex/bin/hooks/*.py` scripts and hook trust hashes in `config.toml`.
- `DESK/SOVEREIGN_CODEX_V2-2/` contains the repaired/validated staged package plus current smoke/audit artifacts; it is review evidence, not a blind overwrite target.
- `plugins/mentat` is a symlink to `/home/daeron/Projects/Modern-ML/Plugins/Mentat`; the only enabled plugins are `mentat@local` and `ctmv3-workspace-activator@local`.
- Standalone custom skill directories are reduced to `academic-whitepaper-engine` and `codex-config-topology`; older custom skills and the prior `codex-skills.zip` are archived under `/home/daeron/.codex/skills.archive/`.
- Bundled system skill `SKILL.md` entrypoints are archived under `/home/daeron/.codex/skills.archive/20260604_1715_system_skill_registry_suppression/` so they do not advertise into prompt context; their directories/scripts/resources remain on disk for explicit/manual use.
- `codex-filetree.md` is the quick file-tree/routing artifact for this config plane.

## Historical setup deltas and current resolution

The early bootstrap deltas are now resolved or intentionally superseded:

- Active `/home/daeron/.codex/bin/hooks` is present. The earlier "missing bin/hooks" warning is stale.
- Active `hooks.json` is intentionally a merged active lifecycle config with Sovereign/Petdex-style commands; it has schema-smoke evidence under `DESK/SOVEREIGN_CODEX_V2-2/`.
- `features.plugins = true` is the current intentional runtime state because the local old-build plugins are installed/enabled. The staged `config_patched.toml` plugin-disabled posture is historical review material, not the live target.
- `approvals_reviewer = "user"` is acceptable in the current profile because `approval_policy = "never"` is the operative approval unlock.
- Hook trust hashes are intentionally retained for active root and plugin hooks after repair.
- Root `CONTEXT.md` and `MEMORY.md` now exist and are the local config-plane handoff/memory surfaces.

## Next concrete steps

1. Keep this file and `MEMORY.md` aligned after any future config-plane changes.
2. Re-run `codex doctor`, `codex --strict-config doctor --json`, hook smoke, plugin smoke, and CodeGraph checks after Codex/plugin upgrades.
3. Do not enable `multi_agent_v2`, `enable_fanout`, or `child_agents_md` without a fresh config migration and strict doctor audit.
4. Treat `DESK/SOVEREIGN_CODEX_V2-2` as evidence/staging unless Daeron explicitly requests deployment of a staged artifact.
5. Preserve the distinction between token hygiene and efficiency mode: reduce wasteful context surfaces, but do not restrict reasoning depth, time, compute, BB7 tools, subagents, or validation scope when they are useful.


## 2026-06-03T14:55-05:00 update — state-machine doctrine and CodeGraph status

Daeron clarified the intended framing: Codex is a state machine, and native tools, SovereignMCP/Muaddib, workflows, hooks, memories, and CodeGraph are helpers/signals rather than controllers. `AGENTS.override.md`, `workflows.md`, and `AGENTS.md` were appended with this doctrine.

`MCP_SPEC.md` exists at `/home/daeron/.codex/MCP_SPEC.md` and is the local Somnus/Sovereign MCP topology/spec reference. It documents the `bb7_*` compiled capability surface and the Lisan/Muaddib/Golden Path substrate.

CodeGraph status for `/home/daeron/.codex`:

- `codegraph` CLI exists: `/home/daeron/.nvm/versions/node/v24.14.0/bin/codegraph`.
- `codegraph status /home/daeron/.codex` reports **Not initialized**.
- `.codegraph/` is missing under `/home/daeron/.codex`.
- `config.toml` has no CodeGraph MCP server entry.
- Do not run `codegraph init -i` on `.codex` until an ignore/scope policy is chosen for secrets and runtime state.


## 2026-06-03T15:00-05:00 update — BB7 memory front and center

Daeron clarified that MCP memory tools should come back front and center. The doctrine was updated accordingly:

- `AGENTS.override.md` now has `## 1) Memory-First State Substrate` near the top.
- `workflows.md` now has `## 0.5) Memory-First Golden Path Spine` near the top.
- `AGENTS.md` now has `## Memory-First Operating Doctrine (2026-06-03)` before the tool/capability section.

Operational meaning: for non-trivial work, use BB7/Sovereign memory as the first continuity lens (`bb7_lisan_recall`, `bb7_memory_surface_context`, `bb7_memory_search`, `bb7_memory_intelligent_search`) and the durable sink after meaningful state changes (`bb7_memory_store`, `bb7_memory_analyze_entry`, `bb7_link_memory_to_session`). This remains assistive to the Codex state machine, not controlling.


## 2026-06-03T15:02-05:00 update — CodeGraph initialized and wired

CodeGraph is now initialized for `/home/daeron/.codex` and wired into Codex config.

Actions completed:

- Added `/home/daeron/.codex/.gitignore` to exclude auth/secret files, sqlite/jsonl runtime state, sessions/logs/tmp/shell snapshots, plugin cache, binaries, and backup churn from CodeGraph indexing.
- Ran `codegraph init -i /home/daeron/.codex`; indexing completed successfully.
- Added non-required `[mcp_servers.codegraph]` to `config.toml` using `command = "codegraph"`, `args = ["serve", "--mcp"]`.
- Verified `config.toml` parses and `codex doctor` now reports 3 configured MCP servers with no failures.
- Verified `codegraph status /home/daeron/.codex`: up to date, 98 files, 1,379 nodes, 3,028 edges, 3.55 MB DB.
- Audited `codegraph files` and `.codegraph` bytes for obvious secret/runtime path names; no high-risk excluded paths were visible/found.
- Smoke-tested CLI structural search with `codegraph query safe_main` and `codegraph context 'understand staged sovereign hook scripts'`.

Note: existing running Codex sessions may need reload/new session before native `codegraph_*` MCP tools are surfaced.


## 2026-06-03T15:17-05:00 update — UserPromptSubmit hook JSON repair

Daeron reported: `UserPromptSubmit hook (failed): hook returned invalid user prompt submit JSON output`.

Root cause confirmed against local Codex CLI 0.136.0 schema strings: hook stdout containing `hookSpecificOutput.additionalContext` must also include the event discriminator `hookSpecificOutput.hookEventName = "UserPromptSubmit"`. The active Sovereign helper emitted only:

```json
{"hookSpecificOutput": {"additionalContext": "..."}}
```

which Codex 0.136 rejects for `UserPromptSubmit`.

Actions completed:

- Patched active `/home/daeron/.codex/bin/hooks/_lib.py`.
- Patched staged `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/bin/hooks/_lib.py`.
- `write_additional_context(...)` now infers the hook event from payload/script name and emits schema-safe:

```json
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}
```

- The helper now suppresses `additionalContext` stdout for events whose Codex 0.136 schemas do not allow `hookSpecificOutput` (notably `PreCompact`, `PostCompact`, `SubagentStop`, and `Stop`).
- Active hook schema smoke passed **15/15** command hooks.
- JSON manifest: `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/hooks_active_schema_smoke_20260603_151645.json`.
- Markdown report: `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/hooks_active_schema_smoke_20260603_151645.md`.
- `codex doctor` after the repair reported **17 ok · 1 idle · 1 notes · 0 warn · 0 fail**.
- Ran `codegraph sync /home/daeron/.codex` after the hook/doc edits. CodeGraph is up to date with 113 files, 1,574 nodes, 3,354 edges; `codegraph files` did not show the generated hook backups, `__pycache__`, auth/sqlite/jsonl/session/log/tmp/cache/binary paths, or validation JSON/MD artifacts in the indexed file list.

Operational routing update from Daeron: do not use Sovereign/BB7 shell-runner tools such as `bb7_run_command` for ordinary terminal work; use native Codex Bash/terminal execution. Keep BB7/Sovereign memory, journal, and persistence tools front and center.


## 2026-06-03T15:39-05:00 update — workflows/MCP sync and plugin hook schema repair

Daeron reported that `workflows-new.md` and `MCP_SPEC.md` were updated. Current reconciliation:

- `MCP_SPEC.md` now explicitly frames Somnus/Sovereign MCP as one always-on BB7/Lisan/Muad'Dib cognition plane over `/home/daeron/Somnus-MCP/data`, not a passive tool rack.
- `workflows-new.md` remains the source driver and includes the Codex runtime compatibility overlay: use native Codex Bash for ordinary shell execution, keep BB7/Sovereign file/context/memory/lisan/exo tools front-center, and treat Golden Path flows as assistive trajectories rather than mandatory ritual.
- `workflows.md` was backed up to `workflows.backup_before_new_sync_20260603_152900.md` and re-mirrored from `workflows-new.md`; `diff -q workflows.md workflows-new.md` passes.

Plugin hook schema work completed after the update:

- Patched Mentat installed cache/source/Modern-ML hook helpers so additional-context stdout includes `hookSpecificOutput.hookEventName` and suppresses unsupported-event stdout.
- Patched CTMv3 workspace activator cache/source/Modern-ML hooks so SessionStart wraps raw `ctmv3 boot` output inside schema-valid Codex JSON and Stop emits top-level `decision: "block"` instead of unsupported `escalate`.
- Python compile validation passed for patched Mentat helpers and CTMv3 wrapper scripts.
- Plugin hook schema smoke report: `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/plugin_hooks_schema_smoke_20260603_153658.json` and `.md`; **14 checks total, 12 passed, 0 failed, 2 skipped** (`SessionEnd`/`StopFailure`, unsupported/not loaded by current Codex hook state).
- `codex doctor` remains green: **17 ok · 1 idle · 1 notes · 0 warn · 0 fail**.
- `codegraph sync /home/daeron/.codex` completed after these changes; status is up to date at **124 files, 1,605 nodes, 3,314 edges**. A visible file-list audit found no indexed auth/sqlite/jsonl/session/log/tmp/cache/backup/smoke artifact paths.


## 2026-06-03T15:49-05:00 update — subagent/skill readiness pass

Continued the active config-plane stabilization goal on the remaining subagent/plugin/skill surface.

Actions completed:

- Spawned native Codex sidecar explorer `019e8f37-b1f6-7293-bec6-9150fba1edb1` (`Galileo`) for a read-only subagent readiness audit; it completed and confirmed stable `multi_agent` readiness plus remaining risks.
- Installed Modern-ML old-build skills into `.codex/skills/custom/`:
  - `ssds-reverse-engineering-pipeline`
  - `cognitive-topology-v3` (skill name `sovereign-skill-architect`)
- Verified both new skills are visible in `codex debug prompt-input`.
- Replaced placeholder `agents/nlp-data-processing.agent.toml` with a real NLP/data-pipeline specialist definition.
- Moved the automatic placeholder backup out of active `agents/` into `/home/daeron/.codex/backups/agents/` after strict doctor warned about duplicate agent role name.
- Patched `config.toml` feature-atlas comments so stale historical notes no longer claim inactive features (`child_agents_md`, `multi_agent_v2`, `enable_fanout`, etc.) are active.
- Added `/home/daeron/.codex/docs/codex-subagent-readiness.md`.
- Added readiness artifacts:
  - `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/subagent_plugin_skill_readiness_20260603_154850.json`
  - `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/subagent_plugin_skill_readiness_20260603_154850.md`

Verification:

- Active agent TOML parse: 10 active agent definitions, placeholder count 0.
- `codex features list`: `multi_agent`, `hooks`, and `plugins` true; `multi_agent_v2`, `enable_fanout`, and `child_agents_md` false.
- `codex --strict-config doctor --json`: `overallStatus = ok` after moving the backup out of `agents/`.
- `codex doctor`: **17 ok · 1 idle · 1 notes · 0 warn · 0 fail**.
- Rollout DB source inventory includes `subagent:thread_spawn=8`.
- CodeGraph sync remains up to date at 124 files / 1,605 nodes / 3,314 edges.

Remaining caution: do not casually enable `multi_agent_v2`; Codex 0.136 rejects `agents.max_threads` when v2 is enabled. Root Sovereign and Mentat plugin subagent hooks intentionally dual-observe SubagentStart/SubagentStop unless Daeron asks to dedupe.


## 2026-06-03T16:10-05:00 update — completion audit pass

Final requirement-by-requirement completion audit ran after correcting stale docs/config comments.

Actions completed:

- Normalized stale `config.toml` feature comments/flags for Codex 0.136 effective false/removed surfaces (`js_repl`, `tool_search`, `undo`) without changing active core runtime posture.
- Updated `CONTEXT.md`, `MEMORY.md`, and `codex-filetree.md` so they no longer preserve early bootstrap warnings (missing active hooks, uninitialized CodeGraph, plugin-disabled staged config) as current truth.
- Appended an `AGENTS.md` control-plane addendum that explicitly names the State-Machine Boundary and `SOVEREIGN_DATA_DIR` BB7 data root.
- Added completion audit artifacts:
  - `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/codex_setup_completion_audit_20260603_1610.json`
  - `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2/codex_setup_completion_audit_20260603_1610.md`

Audit result: all 13 derived requirements passed current-state evidence: doctrine, config, MCP, BB7 live registry, workflows/MCP_SPEC, CodeGraph, hooks, plugins, skills, subagents, DESK assets, local docs, and doctor gates.

Verification summary from audit:

- `codex --strict-config doctor --json`: overallStatus `ok`.
- `codex doctor`: 17 ok / 0 warn / 0 fail.
- `codex mcp list`: SovereignMCP, mentat, and codegraph enabled.
- `codegraph sync` + `codegraph status`: index up to date, high-risk indexed-path audit clean.
- Current hook smoke: 28 total checks, 26 executed passed, 2 skipped, 0 failed; py_compile clean.
- `codex plugin list`: `mentat@local` and `ctmv3-workspace-activator@local` installed/enabled.
- Prompt-input smoke sees old-build skills `ssds-reverse-engineering-pipeline` and `sovereign-skill-architect` / `cognitive-topology-v3`.
- Active agent parse: 10 definitions, 0 parse errors, 0 duplicates, 0 actual placeholder agent definitions.


## 2026-06-03T16:23-05:00 update — BB7 session label

Started BB7/Sovereign cognitive session for the completed global Codex config plane.

- Label: `Codex Global Config — Global Codex control-plane continuity`
- Session ID: `8438249d-298d-4e67-84d5-1837cef0d2d7`
- Anchor memory linked: `codex_config_plane_setup_complete_2026_06_03`
- Focus: `/home/daeron/.codex` continuity, SovereignMCP/BB7 memory substrate, CodeGraph/hooks/plugins/skills/subagent readiness.
- Resume anchor: `DESK/SOVEREIGN_CODEX_V2-2/codex_setup_completion_audit_20260603_1610.{json,md}`.


## 2026-06-03T20:15-05:00 update — Spark reasoning-summary compatibility fix and session close

Daeron reported an Aeron startup failure when using `gpt-5.3-codex-spark`:

```json
{"code":"unsupported_parameter","message":"Unsupported parameter: 'reasoning.summary' is not supported with the 'gpt-5.3-codex-spark' model.","param":"reasoning.summary"}
```

Resolution completed in the global Codex config plane:

- Removed active top-level `model_reasoning_summary = "detailed"` from `/home/daeron/.codex/config.toml`.
- Left `model = "gpt-5.5"`, `model_reasoning_effort = "medium"`, and `plan_mode_reasoning_effort = "xhigh"` unchanged; the explicit failure was the unsupported `reasoning.summary` parameter, and Daeron wants Spark compatibility.
- Backup created: `/home/daeron/.codex/config.backup_before_spark_reasoning_summary_removal_20260603_201447.toml`.
- Verification passed:
  - TOML parse OK.
  - Active `config.toml` no longer contains `model_reasoning_summary` or `reasoning.summary`.
  - `codex --strict-config doctor --json`: `overallStatus = ok`.
  - `codex doctor`: `17 ok · 1 idle · 1 notes · 0 warn · 0 fail`.

Operational closeout:

- Global config session can be treated as done after this Spark compatibility fix.
- To resume the Aeron/SRA work, do not paste the human instruction with parentheses into Bash. Use `codex resume` interactively and select `Aeron + SRA 6-3-2026 (019e902d-f341-7312-a47c-7f5eba82dabf)` from the picker, or pass the id as a quoted argument if the CLI supports direct resume by id.


## 2026-06-03T23:00-05:00 update — constitutional prompt framework skill

Created custom Codex skill `constitutional-prompt-framework` under `/home/daeron/.codex/skills/custom/constitutional-prompt-framework` for deriving, auditing, and refactoring dense single-file agent system prompts / agent constitutions.

Contents:

- `SKILL.md`: concise workflow and trigger instructions for platform-agnostic constitutional prompt authoring.
- `references/derivation-guide.md`: detailed framework covering position effects, triad encoding, persona layers, hard/soft constraints, capability posture, memory/continuity, and living prompt versioning.
- `references/audit-checklist.md`: severity-ranked audit grammar for identity ambiguity, brittle constraints, tool/capability posture, memory architecture, platform leakage, and position-effect failures.
- `assets/single-file-agent-constitution-skeleton.md`: copyable single-file section scaffold for final prompt artifacts.
- `agents/openai.yaml`: UI metadata for the skill.

Verification:

- `quick_validate.py /home/daeron/.codex/skills/custom/constitutional-prompt-framework` passed: `Skill is valid!`.
- `agents/openai.yaml` parsed with PyYAML and includes `$constitutional-prompt-framework` in the default prompt.
- `codex debug prompt-input` discovery smoke shows `constitutional-prompt-framework` as `r0/custom/constitutional-prompt-framework/SKILL.md`.
- `codegraph sync /home/daeron/.codex` completed afterward; status up to date at 125 files / 1,605 nodes / 3,314 edges.


## 2026-06-03T23:10-05:00 update — constitutional skill YAML loader repair

Daeron reported Codex startup/prompt-input warnings:

```text
Skipped loading 1 skill(s) due to invalid SKILL.md files.
/home/daeron/.codex/skills/custom/constitutional-prompt-framework/SKILL.md: invalid YAML: description: invalid type: sequence, expected a string at line 2 column 14
```

Root cause: `constitutional-prompt-framework/SKILL.md` used a long unquoted YAML `description` scalar. The local `quick_validate.py` accepted it, but the runtime Codex skill loader rejected it. This was a skill-loader metadata issue, not evidence that native subagents were broken.

Repair completed:

- Quoted the `description` value in `/home/daeron/.codex/skills/custom/constitutional-prompt-framework/SKILL.md`.
- Re-ran `quick_validate.py`: `Skill is valid!`.
- Parsed frontmatter with PyYAML and confirmed `description` is `str`.
- Re-ran `codex debug prompt-input`; command exited `rc=0`, emitted no skipped/invalid skill warning on stderr, and listed `constitutional-prompt-framework` as discoverable at `r0/custom/constitutional-prompt-framework/SKILL.md`.

Durable gotcha: for skill frontmatter, quote long `description` strings even when the scaffold validator accepts unquoted YAML. Runtime skill-loader discovery is the authoritative gate.


## 2026-06-04T06:00-05:00 update — lean Codex skill loadout / lazy-load cleanup

Daeron clarified the desired active Codex skill profile: keep whitepaper, design, Codex config, and CTM skills active; preserve Mentat plugin/MCP and CTMv3 plugin/subagent surfaces; avoid cramming the prompt with duplicate or nonessential skills.

Actions completed:

- Archived 32 skill directories out of active scan roots into `/home/daeron/.codex/skills.archive/20260604_0552_lazy_load_cleanup/`.
- Wrote archive manifest/report:
  - `/home/daeron/.codex/skills.archive/20260604_0552_lazy_load_cleanup/manifest.json`
  - `/home/daeron/.codex/skills.archive/20260604_0552_lazy_load_cleanup/report.md`
- Active filesystem skills now remain under `/home/daeron/.codex/skills` only: 5 `.system` maintenance skills plus canonical whitepaper/design/config/CTM skills.
- Disabled `claude-code-setup@claude-plugins-official` in `/home/daeron/.codex/config.toml` because it added an unneeded skill registry entry; backup: `/home/daeron/.codex/config.backup_before_skill_loadout_claude_setup_disable_20260604_0558.toml`.
- Kept `mentat@local`, `ctmv3-workspace-activator@local`, and `explanatory-output-style@claude-plugins-official` enabled.

Verification:

- `codex doctor --json`: `overallStatus=ok`, 18 checks.
- `codex debug prompt-input`: no stderr warnings, skill segment reduced from 24,043 chars / 51 naive skill-name lines to 12,489 chars / 21 actual available skill entries, with no duplicate skill names.
- Active available skills after cleanup: `imagegen`, `openai-docs`, `plugin-creator`, `skill-creator`, `skill-installer`, `academic-whitepaper-engine`, `ada-reference-manual`, `ada-step-entropy-system-router`, `agentic-kernel-topology`, `codex-config-topology`, `ctmv3-workspace-activator:ctmv3-workspace-activator`, `enhanced-op-sota`, `fiber-map-ctm`, `mentat:mentat-debrief`, `mentat:mentat-dispatch`, `mentat:mentat-plan`, `mentat:mentat-reflect`, `somnus-openrouter-router`, `somnus-rem-design`, `somnus-router`, `sovereign-skill-architect`.
- Active MCP servers after cleanup: `SovereignMCP`, `codegraph`, and `mentat`, all enabled via stdio.
- CTMv3 remains plugin-backed with skill, hooks, commands, and `agents/ctmv3-architect.md`; there is no separate `ctmv3` MCP server visible in `codex mcp list --json` as of this audit.

Rollback:

- Restore archived skills by moving paths in `manifest.json` back from their `destination` to `source`.
- Re-enable Claude setup by changing `[plugins."claude-code-setup@claude-plugins-official"].enabled` back to `true` or restoring the config backup named above.


## 2026-06-04T17:00-05:00 update — minimal loadout and operator token hygiene

Daeron narrowed the intended global Codex prompt/plugin surface:

- Enabled plugins should be only `mentat@local` and `ctmv3-workspace-activator@local`.
- Standalone custom skills should be only `academic-whitepaper-engine` and `codex-config-topology`.
- BB7/Sovereign MCP tools, Codex native memories, local/global `MEMORY.md` and `CONTEXT.md`, repo memories, and subagents remain part of the operator control plane.
- This is not a request to restrict token budget, time, compute, or tool availability. The goal is intelligent routing: preserve deep operator behavior while avoiding unnecessary prompt-surface, raw JSON, catalog, and shell-dump waste.

Actions already completed in this session:

- Archived extra standalone custom skill directories to `/home/daeron/.codex/skills.archive/20260604_165745_minimal_requested_loadout/`; restore map is in that archive's `manifest.json`.
- Left `/home/daeron/.codex/skills/custom/` with only `academic-whitepaper-engine` and `codex-config-topology`.
- Disabled `explanatory-output-style@claude-plugins-official` in `config.toml`, leaving `mentat@local` and `ctmv3-workspace-activator@local` as the enabled plugin pair.
- Verified via Codex runtime before this note: strict doctor was OK and `codex debug prompt-input` showed the requested custom skill reduction plus plugin skill entries from Mentat/CTMv3.

Operator routing correction from Daeron:

- Do not use Unix text commands (`cat`, `sed`, broad `grep`, etc.) as the default file-read/edit path for control-plane comprehension.
- Use BB7/Sovereign file tools for file read/write/append/search/list operations so the operator has coherent file-level context and does not infer false truncation from shell output clipping.
- Use native Bash only for execution/validation surfaces where the command itself is the evidence (`codex doctor`, `codex debug prompt-input`, parser/test commands, etc.).
- Raw JSON is intentionally retained behind the scenes for hooks, BB7 telemetry, and the flywheel, but visible/model-facing outputs should prefer projected, progressive, or cleaned summaries when possible.


## 2026-06-04T17:25-05:00 update — CTMv3 hook compact projection

Daeron also flagged startup/plugin hook output waste: raw JSON is useful for behind-the-scenes telemetry/flywheel, but model-facing hook context should be shaped. The CTMv3 SessionStart wrapper was the main raw JSON offender.

Actions completed:

- Patched CTMv3 `session_start_codex.py` wrappers in:
  - `/home/daeron/.codex/plugins/cache/local/ctmv3-workspace-activator/1.0.0/hooks/session_start_codex.py`
  - `/home/daeron/.claude/plugins/marketplaces/local/plugins/ctmv3-workspace-activator/hooks/session_start_codex.py`
  - `/home/daeron/Projects/Modern-ML/Plugins/Cognitive-Topology-Map/claude-code/hooks/session_start_codex.py`
- The wrapper still runs `python -m ctmv3 boot --json`, but now parses the raw multi-line JSON and emits a compact `additionalContext` block instead of injecting the raw JSON blob.
- Validation sample for `/home/daeron/.codex`: schema-valid `SessionStart` JSON, compact context length 378 chars, no `[CTMV3_GOLDEN_PATH]` / raw JSON blob, and parsed branch/file facts preserved (`branch=PARTIAL`, `files=1764` in the sample run).
- `python3 -m py_compile` passed for all three wrappers.
- `codex --strict-config doctor --json` remained `overallStatus=ok` after the hook patch.

Mentat SessionStart was inspected and already emits compact/capped boot/handoff context via its shared 2KB cap; no Mentat hook patch was required in this pass.


## 2026-06-04 — Global constitution compiler wired

- Implemented `/home/daeron/.codex/bin/hooks/compile_constitution.py`.
- Generated `/home/daeron/.codex/COMPILED_CONSTITUTION.md` from `AGENTS.override.md`, `AGENTS.md`, `USER.md`, `MEMORY.md`, `CONTEXT.md`, and `workflows-new.md`.
- Updated `/home/daeron/.codex/bin/hooks/session_start.py` so SessionStart refreshes the compiled constitution and emits only compact hook context.
- Updated `/home/daeron/.codex/config.toml`: `model_instructions_file` points at `/home/daeron/.codex/COMPILED_CONSTITUTION.md`; a generated top-level `developer_instructions` block contains the compiled constitution because live `codex debug prompt-input` proved `developer_instructions` is the model-visible key in this Codex build.
- Validation passed: `py_compile`, compiler idempotence, SessionStart hook smoke, TOML parse, `codex --strict-config doctor --json`, and `codex debug prompt-input` marker checks from both `/home/daeron/.codex` and `/home/daeron/Projects`.
- Current compiled constitution size: 169,536 chars / rough char÷4 estimate 42,384 tokens; full prompt-input rough estimate ~47.3k tokens.
- Audit artifacts: `DESK/SOVEREIGN_CODEX_V2-2/global_constitution_compiler_audit_20260604_1858.{json,md}`.


## 2026-06-04 — Switched to kernel + dynamic retrieval mode

- Replaced the full always-on constitution payload with a compact live kernel.
- `bin/hooks/compile_constitution.py` now writes two artifacts:
  - `COMPILED_KERNEL.md` from `AGENTS.override.md`, `AGENTS.md`, and a generated retrieval contract.
  - `COMPILED_CONSTITUTION.md` from `AGENTS.override.md`, `AGENTS.md`, `USER.md`, `SOUL.md`, `MEMORY.md`, `CONTEXT.md`, and `workflows-new.md` for audit/recovery only.
- `config.toml` now points `model_instructions_file` to `/home/daeron/.codex/COMPILED_KERNEL.md` and syncs only the kernel into the proven live `developer_instructions` bridge.
- `bin/hooks/session_start.py` now emits compact `<operator-dynamic-context>` for SOUL/MEMORY/CONTEXT plus native Codex memories, BB7/Lisan, Mentat, CTMv3, and CodeGraph as retrieval/routing surfaces.
- Validation passed: CodeGraph status, `py_compile`, compiler idempotence, TOML parse, strict doctor, SessionStart hook smoke, prompt-input markers from `.codex` and `/home/daeron/Projects`.
- Prompt-input rough char/4 estimate dropped from ~47.3k tokens to ~20.4k tokens from `/home/daeron/Projects`; full docs remain on disk for retrieval/reference, not startup injection.
- Audit artifacts: `DESK/SOVEREIGN_CODEX_V2-2/kernel_dynamic_retrieval_audit_20260604_2020.{json,md}`.

## 2026-06-05 — Token Density Governor + FSTIP source implementation

- Added a compact Token Density Governor section to `/home/daeron/.codex/AGENTS.override.md` and regenerated `/home/daeron/.codex/COMPILED_KERNEL.md` / `/home/daeron/.codex/COMPILED_CONSTITUTION.md` with `bin/hooks/compile_constitution.py`.
- Compile result: `COMPILED_KERNEL.md` now includes `TOKEN_DENSITY_GOVERNOR`; compiler reported `missing=0` and `kernel_sha256=d3e7bb02516b6af5`.
- Implemented the corresponding source-level file-surface isolation in `/home/daeron/Somnus-MCP`:
  - `tools/file_tool.py`: bounded read windows, semantic-target windows, large naked-read skeleton manifests, sparse write/append patch manifests.
  - `mcp_server.py`: string-returning file tool display projection, oversized read suppression, verification-manifest pass-through, raw-before-projection metadata.
- Repo-local Somnus docs were updated with the same token-density contract and validation evidence.
- Validation artifacts are under `/home/daeron/Somnus-MCP/data/validation/fstip_file_surface_token_isolation_20260605.{md,json}`.
- Operational caveat: live MCP server processes may need restart/reload before changed source code affects the running `bb7_*` tool instances and advertised schemas.
## 2026-06-05 update — PyCharm MCP blocked and Sovereign MCP Linux paths restored

- Disabled the active PyCharm MCP stream by commenting out `[mcp_servers.pycharm]` in `/home/daeron/.codex/config.toml`; this removes the local `127.0.0.1:64342/stream` server from Codex MCP startup.
- Removed a duplicate `developer_instructions` key that made `config.toml` fail to load.
- Restored `SovereignMCP` to Linux-local paths: `/home/daeron/Somnus-MCP/mcp.venv/bin/python`, `/home/daeron/Somnus-MCP/mcp_server.py`, and `SOVEREIGN_DATA_DIR=/home/daeron/Somnus-MCP/data`.
- Validation: `codex debug prompt-input` exits 0; `codex doctor` exits 0 and reports `✓ mcp 3 server (3 stdio) · 0 disabled`, `17 ok · 1 idle · 1 notes · 0 warn · 0 fail ok`.



## 2026-06-05 update — Kwisatz Council agnostic prompt draft

- Created `/home/daeron/.codex/agents/kwisatz-council.md` from Daeron's pasted Kwisatz Council invocation as a Markdown source artifact under `agents/`.
- Used the `constitutional-prompt-framework` skill path in expansion/hardening mode: preserved the source prompt snapshot, then added an agnostic constitutional prompt draft with authority model, Seven Invariants tetrads, organ contracts, capability dispatch by class, cycle protocol, L1/L2/L3 readiness model, prerequisite ledger, artifact discipline, OPSEC, stop conditions, failure recovery, self-application, and living status.
- Added Enhancement Pass 1 densification layer: assumptions ledger, Digital Quartering architecture pattern, foresight capsule, promotion gates, octopus consensus protocol, branch scoring rubric, severity taxonomy, red-team probes, survival card, and changelog protocol.
- Validation: CPF `constitution_linter.py` PASS; `score_constitution.py` reports 83/100 production candidate; artifact is 978 lines, 49,313 bytes, SHA256/16 `9f491492c12c9b7a`; no `bb7` string and no emoji codepoints detected.


## 2026-06-05 update — Kwisatz Council Enhancement Pass 2

- Continued `/home/daeron/.codex/agents/kwisatz-council.md` without rewriting prior sections; appended `Enhancement Pass 2 — Deployment Binding, Invocation, and Acceptance Gates`.
- Added runtime binding slots, active cycle invocation template, organ brief templates, artifact manifest, evidence citation standard, completion audit protocol, prompt-injection/instruction-contamination defense, memory governance detail, task-specific output contracts, readiness language discipline, and final runtime reminder.
- Validation after pass 2: CPF linter PASS; CPF score increased to 84/100 production candidate; artifact is 1,452 lines, 70,085 bytes, SHA256/16 `1a9a1ce761267d2a`; no `bb7` string and no emoji codepoints detected.
- Next likely branch: create a clean compiled runtime-prompt section or sibling `.runtime.md` while preserving the raw source snapshot and enhancement history in the current file.


## 2026-06-05 update — Kwisatz Council Enhancement Pass 3

- Continued `/home/daeron/.codex/agents/kwisatz-council.md` append-only with `Enhancement Pass 3 — Full Agent Setup, Lifecycle, and Red-Team Harness`.
- Added full agnostic agent setup topology, deployment assembly checklist, organ identity integrity rules, lifecycle state machine, work product schemas, acceptance scorecard, red-team harness, anti-sycophancy mechanism, context compaction/recovery protocol, operator interface contract, platform wrapper boundary, and full setup acceptance gate.
- Validation after pass 3: CPF linter PASS; CPF score increased to 86/100 production candidate; artifact is 1,884 lines, 90,952 bytes, SHA256/16 `e0ecbd1ad835eb78`; no `bb7` string and no emoji codepoints detected.
- Next likely branch: one more append-only pass targeting score categories still at 8/10 (mission/identity, persona, memory, output contracts, living status) before compiling a sibling runtime prompt.


## 2026-06-05 update — Kwisatz Council Enhancement Pass 4

- Continued `/home/daeron/.codex/agents/kwisatz-council.md` append-only with `Enhancement Pass 4 — Mission Kernel, Persona Compression, Continuity, and Output Spine`.
- Added mission kernel, mission derivation chain, success/non-success definitions, compressed persona architecture, continuity model by memory availability class, runtime-ready output spine, prompt change report, living status upgrade, versioning rule, release checklist, and runtime sibling compilation plan.
- Validation after pass 4: CPF linter PASS; CPF score remains 86/100 production candidate; artifact is 2,265 lines, 106,255 bytes, SHA256/16 `a696f3864ea90790`; no `bb7` string and no emoji codepoints detected.
- Next likely branch: compile a sibling runtime Markdown from the workshop source, then use the CPF score on the sibling rather than the large workshop file because the workshop now intentionally includes source snapshot plus pass history.


## 2026-06-05 update — Kwisatz Council runtime sibling compiled

- Created clean runtime Markdown sibling `/home/daeron/.codex/agents/kwisatz-council.runtime.md` from the workshop/source artifact while preserving `/home/daeron/.codex/agents/kwisatz-council.md` untouched.
- Runtime sibling excludes raw source prompt snapshot and enhancement pass history; it uses binding slots rather than hard platform paths and preserves the agnostic prompt body with no `bb7` dependency.
- Created validation artifacts: `/home/daeron/.codex/agents/kwisatz-council.runtime.validation.md` and `/home/daeron/.codex/agents/kwisatz-council.runtime.validation.json`.
- Validation: CPF linter PASS; CPF score 88/100 production candidate; runtime prompt is 1,285 lines, 51,958 bytes, SHA256/16 `eb890b2a7b7227bc`; no `bb7` string, no emoji codepoints, no raw source snapshot, no enhancement history, and no hard `/agent/workspace/` path.
- Validation report hashes: Markdown `9819befc717f5e4a`, JSON `3ae59c0b6f363426`; JSON manifest parses with `python -m json.tool`.
- Next likely branch if Daeron wants to continue: create a platform-specific wrapper/TOML binding from the runtime sibling, or run a red-team probe report against the runtime sibling first.


## 2026-06-05 update — Kwisatz Council runtime red-team report

- Added CPF-style manual prompt-structure red-team artifacts for `/home/daeron/.codex/agents/kwisatz-council.runtime.md`: `/home/daeron/.codex/agents/kwisatz-council.runtime.redteam.md` and `.json`.
- Red-team result: critical probes 7/7 PASS by prompt-structure review; high probes 5/5 PASS; no critical/high patches required to the runtime prompt body; deployment impact remains AMBER because wrapper binding and live-agent behavior are still untested.
- Red-team artifact hashes: Markdown `81a78b4b1e9f67e4`, JSON `40fe3d221f59670b`; JSON manifest parses with `python -m json.tool`.
- Current final artifact set: workshop/source Markdown, runtime Markdown sibling, validation Markdown/JSON, red-team Markdown/JSON. Next branch should be wrapper/TOML binding only after Daeron confirms the runtime Markdown shape.
