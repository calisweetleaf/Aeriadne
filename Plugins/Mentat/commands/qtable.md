---
description: Dump the persistent Mentat Q-table grouped by state
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*)"
---

Persistent Q-table (TD(0), α=0.2, γ=0.8, learned across all sessions):

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/mentat" q-table`

Interpret the dump for the user. Cover:

- Top-three tools per state, with Q-values and visit counts
- Any state with thin coverage (every Q-value near 0 or every visit count
  in single digits) — those states are still being explored and Thompson
  sampling will weight exploration more heavily there
- The lowest-Q tools — those are the routes the table has learned to avoid

Keep the language descriptive, not algorithmic. The user wants the live
routing intuition the table encodes, not a textbook on TD-learning.
