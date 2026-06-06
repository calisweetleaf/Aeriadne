# Mentat — live cognitive substrate for Claude Code

A Claude Code plugin that runs alongside a session and watches it the way
Muad'Dib watches a tool plane: explicit state machine, TD-learning Q-table
over `(state, tool)` pairs, structured insight bus, persistence across
compaction. The mirror, inside Claude Code, of the bb7 exoskeleton.

The user opens a session. Mentat decides the session is in PLANNING. The
user reads three files. Mentat watches and steps the FSA into EXPLORING. The
user edits one of them. EXECUTING. The user runs `pytest`. VERIFYING. The
user mentions a deferred topic from `.mentat/scope.md`. Mentat steps the FSA
into DRIFTING and the next attempt to write a file is denied at the hook
layer with a clear reason. The session compacts. Mentat snapshots state and
recent insights to disk. The post-compact session reads that snapshot back
in via additionalContext on its very first turn.

That's the shape. Below is what's in the box.

## Layout

```
mentat/
├── .claude-plugin/
│   └── plugin.json
├── mcp.json                       (rename to .mcp.json on install — see below)
├── hooks/
│   ├── _lib.py                    shared helpers (state, classify, decision JSON)
│   ├── hooks.json                 wires every event to its script
│   ├── session_start.py           load + handoff replay
│   ├── user_prompt_submit.py      drift detect + state-aware context
│   ├── pre_tool_use.py            classify + drift + DRIFTING guard
│   ├── post_tool_use.py           reward + Q-table + entropy spike
│   ├── subagent_start.py          dispatch tagging
│   ├── subagent_stop.py           return tagging
│   ├── pre_compact.py             handoff snapshot
│   ├── post_compact.py            FSA out of COMPACTING
│   ├── stop.py                    SESSION_END
│   └── stop_failure.py            rate-limit / auth-fail tagging
├── skills/
│   ├── mentat-reflect/SKILL.md    pause + synthesize live state
│   ├── mentat-plan/SKILL.md       author scope.md + PLAN.md
│   ├── mentat-dispatch/SKILL.md   parallel sub-agent fan-out
│   └── mentat-debrief/SKILL.md    end-of-session HTML insight report
├── agents/
│   ├── mentat-cartographer.md     read-only repo mapper
│   ├── mentat-crucible.md         red-team / pushback
│   ├── mentat-scribe.md           doc-only synthesizer (never writes code)
│   └── mentat-sentinel.md         scope-drift auditor
├── mcp_server/
│   ├── __init__.py
│   └── __main__.py                stdio MCP server (10 mentat_* tools)
├── state_machine/
│   ├── __init__.py
│   ├── machine.py                 8-state FSA + transition table
│   ├── q_table.py                 SQLite-backed TD-learning + Thompson sampling
│   ├── insights.py                JSONL insight bus
│   ├── session.py                 disk-backed session record
│   └── drift.py                   scope.md parser + phrase detector
└── bin/
    └── mentat                     CLI inspector
```

## Install

```bash
# 1. clone the plugin into a directory Claude Code can see
git clone <somewhere>/mentat ~/.claude/plugins/mentat

# 2. The package above ships an mcp.json file (the sandbox where this was
#    authored blocks dotfile names). Rename it on disk:
mv ~/.claude/plugins/mentat/mcp.json ~/.claude/plugins/mentat/.mcp.json

# 3. Tell Claude Code about it
claude --plugin-dir ~/.claude/plugins/mentat
# or for production:
claude plugin install ~/.claude/plugins/mentat
```

After install, every session writes to `~/.mentat/`:

```
~/.mentat/
├── q_table.sqlite                       persistent Q-table, cross-session
├── sessions/<session-id>.json           per-session FSA state
├── insights/<session-id>.jsonl          structured event bus
└── handoff/<session-id>.md              latest pre-compact snapshot
```

Per-project state lives under `${CLAUDE_PROJECT_DIR}/.mentat/`:

```
.mentat/
├── active_session.json                  pointer to current session
└── scope.md                             scope inclusions + deferred topics
```

## Authoring scope.md

Mentat's drift detection only works if `.mentat/scope.md` exists. Author it
manually or via the `mentat-plan` skill.

```markdown
# Scope — Forge UI port

## In
- UI / CSS porting from Somnus chat library
- design tokens
- @layer cascade integration

## Out (deferred — DO NOT re-inject)
- inference, model loading, safetensors
- AI/ML pipelines
- hardware constraints, Ryzen, VRAM
- backend, FastAPI, Docker
```

The detector matches **whole phrases** (case-insensitive, word-boundary).
A line under `## Out` can be a comma-separated phrase list — every comma-split
fragment is its own match.

## CLI

```
mentat status                      current state, Q-best, drift count
mentat tail --n 50                 last 50 insights with timestamps
mentat q-table                     dump (state, tool, value, visits) per state
mentat insights --type DECISION    filter by insight type
mentat note "<text>"               emit a NOTE insight from the shell
mentat drift "<text>"              run drift check ad-hoc
mentat scope                       print active scope.md
mentat replay <session-id>         show state-transition timeline for a past session
mentat reset                       wipe session state (keeps Q-table)
```

Add `--json` to any subcommand for machine-readable output.

## MCP

The bundled stdio MCP server exposes ten tools to the live Claude Code turn.
The model can introspect its own session mid-turn — the Mentat equivalent of
calling `bb7_state_get` from inside Muad'Dib.

| Tool                  | Purpose                                            |
|-----------------------|----------------------------------------------------|
| `mentat_state_get`    | Snapshot of current state, transitions, last tool  |
| `mentat_state_set`    | Manual transition (declare REFLECTING explicitly)  |
| `mentat_insight_emit` | Push a structured insight (DECISION, NOTE, ...)    |
| `mentat_insight_query`| Filter the bus by type and/or state                |
| `mentat_insight_tail` | Last N insights                                    |
| `mentat_q_route`      | Thompson recommendation for current state          |
| `mentat_q_table`      | Full Q-table dump                                  |
| `mentat_handoff_read` | Read latest pre-compact handoff                    |
| `mentat_handoff_write`| Manual handoff snapshot                            |
| `mentat_drift_check`  | Run drift detection against arbitrary text         |

## State machine

```
PLANNING ──read/agent──► EXPLORING ──write/exec──► EXECUTING ──verify──► VERIFYING
   ▲                          │                       │                      │
   │                          ▼                       ▼                      ▼
   └─prompt──REFLECTING ◄──subagent_return       error──► BLOCKED        success──► REFLECTING
                                                            │
                                                          retry─────► EXECUTING

Any state ──scope_drift──► DRIFTING ──prompt──► PLANNING
Any state ──pre_compact──► COMPACTING ──post_compact──► REFLECTING
```

The transitions are listed exhaustively in `state_machine/machine.py`. The FSA
is deterministic; non-determinism lives in the Q-table.

## Reward constants

The TD(0) update uses the same constants as Muad'Dib:

```
REWARD_SUCCESS    = +1.0
REWARD_ERROR      = -0.5
DEEP_CHAIN_BONUS  = +0.3   (≥ 4 successful tool uses in a row)
LOW_LATENCY_BONUS = +0.1   (tool returned in < 500 ms)
ALPHA             = 0.2
GAMMA             = 0.8
```

Recommendation uses Thompson sampling with variance shrinking by `1/sqrt(visits+1)`
so high-value-but-rarely-visited tools still get exploration weight.

## What Mentat does not try to do

- It does not replace `serena` or any LSP-driven semantic-code-intel plugin.
- It does not replace `ralph-loop`'s explicit loop orchestration. Ralph
  forces a hard plan-execute-verify cycle; Mentat tracks the cycle as it
  unfolds organically. They compose well.
- It does not replace the stock `session-report` plugin's CLI export — its
  debrief is a higher-density visual artifact, not a CSV.
- It does not assume bb7 / Muad'Dib is installed. It mirrors the pattern but
  is fully standalone. If bb7 is present, both can run in parallel — the
  Mentat MCP server lives in its own namespace.

## License

MIT (matches the user's OSS-friendly stance for this kind of tooling).

## Author note

This is a private lab tool. The README assumes you (Daeron) are the operator.
Treat anything that says "the user" or "the operator" as you. Drop the
public-distribution framing if and when you want to ship.
