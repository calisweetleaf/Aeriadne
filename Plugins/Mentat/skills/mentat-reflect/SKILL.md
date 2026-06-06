---
name: mentat-reflect
description: |
  Pause execution and synthesize the live session state. Reads the Mentat
  insight bus, summarizes recent state transitions, lists drift events,
  surfaces Q-table route hints, and returns a structured reflection block.
when_to_use: |
  Trigger phrases: "where are we", "status", "what's the state", "reflect",
  "let's pause", "step back", "are we drifting", "context check", "show me
  the insight log", "session status". Also fire automatically when the
  session has had 8+ consecutive EXECUTING tool uses without a verify step.
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*)"
---

You are running inside a Claude Code session that the Mentat plugin is observing.
Mentat tracks an explicit state machine over your work (planning, exploring,
executing, verifying, reflecting, blocked, drifting, compacting), a TD-learning
Q-table over (state, tool) pairs, and a structured insight bus.

When this skill fires, do the following in order:

1. Read the live session state by running:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat status --json
   ```

2. Read the last 30 insights:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat tail --n 30 --json
   ```

3. Synthesize a reflection in this exact shape:

   ```
   ## Mentat Reflection

   - Current state: <STATE>
   - Transitions so far: <N>
   - Last tool: <TOOL> (success=<bool>)
   - Drift events: <N>
   - Q-route hint for this state: <TOOL> (Q=<value>)

   ### Recent insights worth surfacing
   - <type>: <one-line summary>
   - ...

   ### Recommendation
   <one paragraph: stay the course / verify / pivot / re-plan / ask user>
   ```

4. If state is DRIFTING, do not propose any work that would write or shell-out.
   Reaffirm scope first: print the contents of `.mentat/scope.md` if it exists,
   and ask the user whether to update the scope or revert the in-flight change.

5. If state is BLOCKED, propose a sub-agent dispatch (mentat-cartographer for
   read-only mapping or mentat-crucible for adversarial pushback) before
   continuing.

Emit your reflection as a normal assistant message — no need to write a file.
The act of reflecting itself is logged to the insight bus by the hooks.
