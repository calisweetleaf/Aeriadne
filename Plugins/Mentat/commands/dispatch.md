---
description: Fan out parallel state-machine-aware sub-agents
argument-hint: "[workstream_hint]"
---

Invoke the `mentat-dispatch` skill. If the user supplied an argument, use it
as a workstream hint when selecting operators: $ARGUMENTS.

Procedure (defined fully in `skills/mentat-dispatch/SKILL.md`):

1. Read `${CLAUDE_PROJECT_DIR}/.mentat/scope.md` and
   `${CLAUDE_PROJECT_DIR}/PLAN.md` to establish the boundary.
2. Pick two-to-four operators whose workstreams do not overlap. Use named
   aliases — `Cartographer`, `Crucible`, `Scribe`, `Sentinel` — never
   "subagent 1/2/3".
3. Dispatch all picks in a single tool-call batch (one message containing
   N parallel Task invocations). Each prompt must restate the scope
   inclusions and exclusions verbatim and specify a per-operator deliverable
   file under `/agent/workspace/...`.
4. Tag each dispatch in the insight bus:
   `python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat note "dispatched: <op-name> for <workstream>"`.
5. After the operators return, run `/reflect` to synthesize their outputs
   into one forward decision.

Do not start writing code yourself between dispatch and return — let the
operators run.
