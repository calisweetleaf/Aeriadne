<!-- mentat-substrate:begin -->
## Mentat substrate

Mentat is a session-scoped state machine and Q-table that runs as a Codex
hook + MCP server. It does not author code or speak in chat; it observes
the agent loop, records insights, and shapes a single signal: the FSA's
current state. Behave as if it is reading.

### States (FSA)

- `planning` — synthesizing approach, no side effects yet
- `exploring` — read-only research, codebase mapping, search
- `executing` — write / edit / shell with side effects
- `verifying` — tests, lints, type checks, validation runs
- `reflecting` — assessing results, deciding next move
- `blocked` — stuck on a tool failure or external dependency
- `drifting` — scope creep — a deferred topic was re-injected
- `compacting` — pre/post compaction handoff

The state machine is reconstructed from `~/.mentat/sessions/<sid>.json` on
every hook firing. It does not require your cooperation, but it benefits
from it.

### Insight types

`state_transition`, `scope_drift`, `reward_signal`, `q_route_hint`,
`entropy_spike`, `tool_failure`, `subagent_dispatch`, `subagent_return`,
`handoff_write`, `handoff_read`, `session_start`, `session_end`, `note`.

Written to `~/.mentat/insights/<sid>.jsonl`. Inspect with `mentat tail`.

### Drift discipline

If `.mentat/scope.md` exists in the project, the `## Out` list is treated
as deferred topics. Mentioning a deferred topic in your prompt or in a
tool input trips the FSA into `drifting`. While drifting, Mentat denies
write and exec tools at the PreToolUse hook with a clear stderr reason.
Read tools and sub-agent dispatches remain unblocked so you can research
your way back.

To leave `drifting`: either acknowledge the scope shift in chat (the
PROMPT_SUBMIT event resets to `planning`) or update `scope.md` to reopen
the topic.

### Reward shaping

The Q-table in `~/.mentat/q_table.sqlite` accumulates TD(0) updates with
α=0.2, γ=0.8. Rewards:

- `+1.0` per successful tool
- `-0.5` per tool error
- `+0.3` deep-chain bonus (≥ 4 successful tools in a row)
- `+0.1` low-latency bonus (< 500 ms)

The same Q-table is shared across Claude Code, Codex, and Gemini sessions
on the same machine. Cross-runtime learning is the design goal.

### Verification etiquette

After a non-trivial block of writes, run a verify step (pytest, ruff,
mypy, cargo test, etc.). A long EXECUTING chain without a VERIFY signal
fires `entropy_spike` — that insight is the cheapest evidence you can
present that you stopped flailing.

### Handoff on Stop / compaction

On every `Stop`, Mentat writes a handoff to `~/.mentat/handoff/<sid>.md`
with the current state, transition count, Q-best per state, and the last
30 insights. On the next `SessionStart`, that file is prepended to your
context so you resume with substrate memory intact.

### What you may NOT do

- Edit files under `~/.mentat/`, `~/.codex/hooks.json`, or the plugin's
  `state_machine/`, `mcp_server/`, or `adapters/` directories without an
  explicit request. The substrate is infrastructure, not work product.
<!-- mentat-substrate:end -->
