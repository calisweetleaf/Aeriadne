---
description: Run the mentat-sentinel sub-agent against arbitrary text or a plan
argument-hint: "[text_or_plan_path]"
---

Run an explicit drift audit against the supplied text or plan.

User argument: $ARGUMENTS

Procedure:

1. Read `${CLAUDE_PROJECT_DIR}/.mentat/scope.md` so the deferred-topic list
   is in context.

2. Dispatch the `mentat-sentinel` sub-agent with this exact instruction:

   > Audit the following input against every "Out" topic in
   > `${CLAUDE_PROJECT_DIR}/.mentat/scope.md`. Report Pass or Fail with a
   > per-hit detail block in the format specified in your skill prompt.
   > Input to audit:
   >
   > $ARGUMENTS

3. When Sentinel returns, surface its verdict verbatim. If the verdict is
   Fail, also recommend one of:

   - Acknowledge and revert
   - Update `.mentat/scope.md` to reopen the topic
   - Reword to remove the deferred-topic mention

4. Log the audit:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/bin/mentat" note "drift-check via /drift-check"
   ```

Never modify scope.md from this command — the user updates it by hand or via
`/plan`.
