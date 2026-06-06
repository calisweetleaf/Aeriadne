---
description: Show the last 30 insights from the active Mentat session
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*)"
---

Last 30 insights on the active session:

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/mentat" tail --n 30`

Walk through the timeline above. Group by:

- State transitions: which states the FSA touched and what triggered each
- Reward signals: which tools earned positive vs negative reward
- Drift events: any SCOPE_DRIFT hits, with their snippets
- Entropy spikes or stale-watcher emissions: indicators of stuck execution
- Sub-agent dispatches and returns

Close with a one-sentence read on the session's rhythm: tight verify loop,
exploring deep, drifting into deferred work, blocked on a tool failure, etc.
