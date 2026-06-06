---
name: mentat-plan
description: |
  Generate or revise a state-machine-aware plan for the current task. Writes
  plan tasks into the project's PLAN.md (or .mentat/active_plan.md if no PLAN
  is conventional), declares scope inclusions and exclusions in scope.md, and
  initializes the Mentat session in PLANNING.
when_to_use: |
  Trigger phrases: "let's plan", "make a plan", "scope this", "what's the
  approach", "before we start", "PLAN.md", "set scope", "draft a plan".
  Also fire when the user gives a high-level multi-step request that would
  benefit from explicit decomposition before execution.
allowed-tools: "Read Write Edit Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*)"
---

You are about to author a plan. Mentat will use the resulting `.mentat/scope.md`
file as ground-truth for drift detection on every subsequent turn — this is
the contract that lets the user push back hard on scope creep and have the
plugin actually enforce it.

Steps:

1. Restate the user's request in your own words. Confirm what's in scope and
   what's explicitly deferred.

2. Write `${CLAUDE_PROJECT_DIR}/.mentat/scope.md` with this exact structure:

   ```markdown
   # Scope — <task name>

   ## In
   - <topic 1>
   - <topic 2>

   ## Out (deferred — DO NOT re-inject)
   - <deferred topic 1>
   - <deferred topic 2>
   ```

   Be specific. "Don't worry about inference" becomes:
   `inference, model loading, safetensors, AI/ML pipelines, hardware constraints`
   so the drift detector can match every variant phrase.

3. Write the plan itself to `${CLAUDE_PROJECT_DIR}/PLAN.md` (overwrite the
   "Plan Tasks" section if it exists, otherwise create the file). Use plain
   prose checkbox tasks — no bold, no inline code, no links inside the
   checkbox lines:

   ```markdown
   - [ ] First concrete action
   - [ ] Second concrete action
   ```

4. Reset Mentat's chain depth to 0 and emit a NOTE insight tagging this as
   a fresh plan:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat note "plan authored: <task name>"
   ```

5. Recommend a starting subagent dispatch if the work has natural parallel
   workstreams (audit + red-team + scribe). Do not dispatch from here — the
   user will trigger the dispatch via mentat-dispatch.

Output a one-paragraph summary of the plan and explicitly list the deferred
topics so they're visible to the user before the first tool call.
