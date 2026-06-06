---
description: Generate the modernized end-of-session insight report
---

Invoke the `mentat-debrief` skill. This is the modernized replacement for
the stock session-report plugin — multi-section HTML artifact with full
state-machine timeline, Q-table delta, drift event log, contradiction map,
sub-agent provenance, and forward-motion next actions.

Procedure (defined fully in `skills/mentat-debrief/SKILL.md`):

1. Pull the data:
   - `python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat status --json`
   - `python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat tail --n 500 --json`
   - `python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat q-table --json`

2. Compute aggregates from the insight stream:
   state-time histogram, transition graph, drift events with full snippets,
   reward distribution, sub-agent provenance, source-grounding ratio,
   entropy spike count, contradiction map.

3. Author an HTML artifact at `/agent/workspace/mentat-debrief-<sid>.html`
   using the modernized aesthetic: inline SVG headers with feGaussianBlur
   glow, traffic-light chrome on terminal blocks, animated state diagram
   with current-state pulse, dark canvas with the
   `linear-gradient(135deg, #3b82f6, #8b5cf6)` brand gradient.

4. Emit the artifact path as a link in the final assistant message.

Debrief is expensive — only fire on explicit user request.
