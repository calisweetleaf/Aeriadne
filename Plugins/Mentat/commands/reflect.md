---
description: Pause and synthesize live Mentat state
---

Invoke the `mentat-reflect` skill on the current Mentat session.

Read the live state machine, the last 30 insights from the insight bus, and
the persistent Q-table, then produce a structured reflection in the exact
shape the skill documents:

- Current state and transition count
- Last tool used (with success flag)
- Drift events so far
- Q-route hint for the active state
- A bulleted list of recent insights worth surfacing
- One paragraph of recommendation (stay the course / verify / pivot / re-plan / ask user)

If the active state is DRIFTING, do not propose any work that would write
files or shell out — print `.mentat/scope.md` first and ask the user how to
proceed. If the state is BLOCKED, propose a sub-agent dispatch
(`mentat-cartographer` or `mentat-crucible`) before continuing.

The reflection itself is logged to the insight bus by the post-tool-use hook.
