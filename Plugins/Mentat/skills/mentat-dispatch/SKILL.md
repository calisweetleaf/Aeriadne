---
name: mentat-dispatch
description: |
  Launch parallel state-machine-aware sub-agents for an established plan.
  Reads the active scope.md and PLAN.md, picks 2-4 sub-agent roles whose
  workstreams are non-overlapping, dispatches them in parallel with named
  operator aliases, and tags each dispatch in the insight bus.
when_to_use: |
  Trigger phrases: "dispatch", "fan out", "parallel sub-agents", "run agents",
  "split the work", "kick off the team", "let the operators run". Fire after
  a plan exists in PLAN.md and the user wants execution to start.
allowed-tools: "Read Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*)"
---

You are the dispatcher. Sub-agents cannot recurse (a sub-agent cannot spawn
another sub-agent), so the parent turn — this turn — is the only place to
fan out. Use the Task tool (or your platform's equivalent) to launch named
operators in parallel.

Default role lineup, drawn from the user's preferred operator vocabulary:

- **Cartographer** — read-only repo mapper. Use the bundled `mentat-cartographer`
  sub-agent. Inherits no write tools.
- **Crucible** — red-team / pushback. Use the bundled `mentat-crucible` sub-agent.
  It explicitly looks for the design's weakest seam and reports.
- **Scribe** — documentation-only synthesizer. Use the bundled `mentat-scribe`
  sub-agent. Forbidden from writing code.
- **Sentinel** — scope-drift auditor. Use the bundled `mentat-sentinel` sub-agent.
  Pulls scope.md and verifies the proposed plan respects every "Out" topic.

Procedure:

1. Read `${CLAUDE_PROJECT_DIR}/.mentat/scope.md` and `${CLAUDE_PROJECT_DIR}/PLAN.md`
   to establish the boundary.

2. Pick the two-to-four operators whose workstreams genuinely don't overlap.
   Naming is critical — never use "subagent 1/2/3"; always use named aliases.

3. Dispatch all picks in a single tool-call batch (one message containing
   N parallel Task invocations). Each prompt MUST:
   - Restate the scope inclusions and exclusions verbatim.
   - Forbid drifting into deferred topics.
   - Specify the deliverable (a markdown file under `/agent/workspace/...` for
     the cartographer/crucible; an inline summary for the scribe).
   - Tell the operator to write its findings to a per-operator file so the
     parent can read them after return.

4. Note each dispatch:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat note "dispatched: <op-name> for <workstream>"
   ```

5. After return, run `mentat-reflect` to synthesize the parallel outputs into
   one decision.

Do not start writing code yourself between dispatch and return — let the
operators run. Use the wait time for further reflection or scope review.
