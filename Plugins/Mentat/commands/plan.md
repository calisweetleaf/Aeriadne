---
description: Author or revise the state-machine-aware plan and scope
argument-hint: "[plan_topic]"
---

Invoke the `mentat-plan` skill. If the user supplied an argument, treat it
as the plan topic and pass it through verbatim: $ARGUMENTS.

Procedure (defined fully in `skills/mentat-plan/SKILL.md`):

1. Restate the request, declaring what is in scope and what is deferred.
2. Write `${CLAUDE_PROJECT_DIR}/.mentat/scope.md` with the exact `## In` and
   `## Out (deferred — DO NOT re-inject)` structure that the drift detector
   parses on every turn.
3. Write `${CLAUDE_PROJECT_DIR}/PLAN.md` with plain-prose checkbox tasks.
4. Reset Mentat's chain depth and emit a `NOTE` insight tagging the fresh
   plan: `python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat note "plan authored: <name>"`.
5. Suggest a starting sub-agent dispatch if the work has natural parallel
   workstreams — do not dispatch from this command, the user invokes
   `/dispatch` separately.

Output a one-paragraph summary of the plan, explicitly listing the deferred
topics so they are visible before the first tool call.
