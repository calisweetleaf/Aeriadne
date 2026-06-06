# SOVEREIGN CODEX FRAMEWORK — Deployment Guide
# Generated: 2026-05-26 | Architect: Vex + CONFIG

## What this is

A novel orchestration framework that inverts the conventional Codex model:
- **Conventional**: Codex (LLM) → MCP (tool utility)
- **Sovereign**: SovereignMCP (Muaddib, always-on) → hooks.json (cognitive middleware) → Codex (execution limb)

The LLM only handles final synthesis and tool invocation.
Everything else — intent classification, context preloading, reflection, distillation — runs in Python via hooks before the model sees it.

---

## File Manifest

| File | Destination | What it does |
|------|-------------|--------------|
| `hooks.json` | `~/.codex/hooks.json` | 10 Codex hook events wired to the staged/deployed Sovereign hook scripts |
| `bin/hooks/*.py` | `~/.codex/bin/hooks/*.py` | Hook implementations used by `hooks.json`; test in staging with `CODEX_HOME=/path/to/stage` |
| `bin/notify_relay.py` | `~/.codex/bin/notify_relay.py` | Non-blocking turn-complete relay used by sovereign/research profiles |
| `sovereign.config.toml` | `~/.codex/sovereign.config.toml` | Full cognitive stack profile (default mode) |
| `stealth.config.toml` | `~/.codex/stealth.config.toml` | Minimal overhead profile (fast tasks) |
| `research.config.toml` | `~/.codex/research.config.toml` | Maximum depth profile (multi-session reasoning) |
| `requirements.toml` | `/etc/codex/requirements.toml` | Immutable sovereign floor (needs sudo) |
| `AGENTS_merged.md` | Optional: review before replacing `~/.codex/AGENTS.md` | Full merged constitution; do not overwrite the active base file until reviewed |

---

## Profile Switching

```bash
codex                          # uses ~/.codex/config.toml (your existing patched config)
codex --profile sovereign      # full stack, daemon active, all 111 tools
codex --profile stealth        # lean, fast, no daemon
codex --profile research       # deep mode, 24h subagent jobs, full distillation
```

---

## Novel Patterns Enabled

### 1. Pre-prompt intent classification (no model turn)
`UserPromptSubmit` → `session_start.py` loads `precomputed_briefing.json` written by the 45s Muaddib daemon tick. The model sees context it didn't have to ask for.

### 2. Autonomous reflection (no model turn)
`PostToolUse` → `auto_reflect.py` calls `bb7_exo_reflect` in Python after every tool call. Golden paths update without consuming a model turn.

### 3. Result rewrite surface
`PostToolUse` with `should_block: true` + `reason` REPLACES the tool result delivered to the model. `intelligent_output_hook.py` lives here — clean, signal-prioritize, layer Muaddib Q commentary. The raw result still writes to the distillation pipeline.

### 4. Daemon loop enforcement
`Stop` with `should_block: true` + `reason` forces another model turn. Use in `stop.py` for "keep going until X" patterns — the sovereign autonomy loop.

### 5. Per-subagent context injection
`SubagentStart` with per-subagent metadata → inject different sovereign context per subagent based on its task type. Multi-agent fanout becomes cognitively differentiated.

### 6. Compaction interception
`PreCompact` → `pre_compact.py` stores key facts to memory BEFORE Codex compacts, then injects a sovereign summary as `additional_context` for the compactor. You control what survives compaction.

### 7. OTLP full event stream
`[otel]` in sovereign/research profiles → every prompt, tool call, hook event, reasoning token streams to `http://localhost:4318/v1/logs`. Wire SovereignMCP as the OTLP receiver and you have a complete session forensics feed for distillation.

### 8. out-of-band turn-complete signal
`notify = ["/home/daeron/.codex/bin/notify_relay.py"]` → on every `agent-turn-complete`, SovereignMCP records a non-blocking JSONL event under `SOVEREIGN_DATA_DIR`. No hook needed. Pure signal feed.

---

## Hook Scripts Included

This staged package now includes the Python scripts referenced by `hooks.json`.
For staging tests, leave files in this directory and run hooks with:

```bash
CODEX_HOME=/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2 /bin/sh -c '<hook command from hooks.json>'
```

For later deployment, copy `bin/` to `~/.codex/bin/` before copying `hooks.json`
to `~/.codex/hooks.json`. Do not point deployed hooks at the staging directory.

```
/home/daeron/.codex/bin/hooks/
  session_start.py     → read precomputed_briefing.json, emit as additional_context
  user_prompt_submit.py → call bb7_lisan_intend + bb7_journal_surface_relevant
  pre_tool_use.py      → log tool call to events.jsonl
  post_tool_use.py     → async distillation event + bb7_exo_reflect for exec tools
  pre_compact.py       → bb7_memory_store, emit summary as additional_context
  post_compact.py      → capture compaction summary to distillation
  subagent_start.py    → inject per-subagent context
  subagent_stop.py     → harvest to Q-table + insights
  stop.py              → final bb7_exo_reflect, bb7_memory_store, golden path update
/home/daeron/.codex/bin/notify_relay.py → record agent-turn-complete signal
```

Each script reads JSON from stdin (Codex hook payload) and writes JSON to stdout (hook response).

---

## Real Hook Events (10 total — do not invent others)

| Event | What it actually does |
|-------|----------------------|
| `SessionStart` | Before any user prompt — inject preamble |
| `UserPromptSubmit` | Before LLM sees prompt — classify, prepend |
| `PreToolUse` | Before tool executes — block/pass only (cannot rewrite input) |
| `PermissionRequest` | Only Allow/Deny output — no context injection |
| `PostToolUse` | After tool runs — rewrite result, distill |
| `PreCompact` | Before Codex compacts — store facts, inject summary |
| `PostCompact` | After compaction — capture what survived |
| `SubagentStart` | Before subagent begins — per-subagent preamble |
| `SubagentStop` | After subagent ends — harvest output |
| `Stop` | After model stops — can force another turn |

**NOT real**: ModelTurnComplete, ContextWindowExceeded, TurnStart, TurnEnd.
Use `Stop` for turn-complete. Use `PreCompact` for context-exceeded equivalent.
