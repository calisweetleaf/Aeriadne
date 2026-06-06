---
description: Show the current Mentat session state, transitions, and Q-best tool
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*)"
---

Live Mentat status (prepended as additional context for this turn):

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/mentat" status`

Use the block above to answer the user's question. Cover at minimum:

- Current FSA state and how long the session has been in it
- Transition count and chain depth
- Last tool used and whether it succeeded
- Q-table best tool for the current state, with its Q-value

If the state is DRIFTING or BLOCKED, surface that prominently and recommend
the corresponding recovery action (acknowledge drift, dispatch a
cartographer, etc.). If chain_depth is approaching 8 and there have been no
VERIFYING transitions, recommend a verify step before more execution.
