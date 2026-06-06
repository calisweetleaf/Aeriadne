---
name: mentat-debrief
description: |
  Generate the modernized end-of-session insight report. Replaces and exceeds
  the stock session-report plugin: full state-machine timeline, Q-table delta,
  drift event log, contradiction map, source-grounding audit, sub-agent
  provenance, and a forward-motion next-actions list. Renders as a webpage
  artifact in the user's modernized aesthetic.
when_to_use: |
  Trigger phrases: "debrief", "session report", "wrap up", "end-of-session",
  "what did we do", "summarize the session", "session review". Fire on
  explicit request only — debrief is expensive and shouldn't auto-run.
disable-model-invocation: false
allowed-tools: "Read Write Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*)"
---

You are generating the session debrief. The renderer is canonical — you do
not author HTML. A deterministic Python script reads the insight bus + Q-table
+ session record off disk and produces the full multi-section artifact in
Daeron's modernized aesthetic.

Procedure:

1. Run the renderer:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/mentat-debrief/scripts/render.py \
     --session ${CLAUDE_SESSION_ID} \
     --out /tmp/mentat-debrief-${CLAUDE_SESSION_ID}.html
   ```

   The script prints the artifact path and a one-line size summary to stdout.

2. Surface the path to the user. The HTML is self-contained (Google Fonts +
   inline CSS/SVG only) — no follow-up rendering or styling required.

3. If a forward-action recommendation is missing or under-specified, you may
   add a one-paragraph qualitative narrative in your reply, but DO NOT
   regenerate the HTML — the renderer is canonical. Twelve sections are
   guaranteed to populate: banner, state timeline (Gantt), state machine
   graph (SVG with weighted edges + Gaussian glow on most-visited node),
   tool routing learned (Q-table top-3 per state), drift audit, sub-agent
   ledger, reward distribution (top/bottom sparkline bars), source-grounding
   score, contradiction map, entropy spikes, tool ledger, and three forward
   moves tied to state + insight evidence.
