---
description: Print the active scope.md, or replace it with new scope text
argument-hint: "[new_scope_text]"
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/bin/mentat*) Bash(cat ${CLAUDE_PROJECT_DIR}/.mentat/scope.md) Bash(mkdir -p ${CLAUDE_PROJECT_DIR}/.mentat) Bash(tee ${CLAUDE_PROJECT_DIR}/.mentat/scope.md)"
---

Current scope (from `${CLAUDE_PROJECT_DIR}/.mentat/scope.md`):

!`mkdir -p "${CLAUDE_PROJECT_DIR}/.mentat" && cat "${CLAUDE_PROJECT_DIR}/.mentat/scope.md" 2>/dev/null || echo "(no scope.md yet — invoke /plan to author one)"`

User argument: $ARGUMENTS

If the user passed scope text as the argument, treat that as the new scope.
Write it verbatim into `${CLAUDE_PROJECT_DIR}/.mentat/scope.md`, preserving
the `## In` / `## Out (deferred — DO NOT re-inject)` structure the drift
detector parses. If the argument is not already in that shape, ask the user
to confirm the inclusion / exclusion split before writing.

If the user passed no argument, just summarize the current scope:

- Which topics are in
- Which topics are deferred
- Last time scope.md was modified

Then emit a single NOTE insight recording the read:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/mentat" note "scope reviewed via /scope"
```

Never write scope.md without an explicit user instruction in $ARGUMENTS or
a confirming reply turn. Drift enforcement depends on scope.md being
human-authored ground truth.
