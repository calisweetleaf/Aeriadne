# Mentat — Helpers

Three sub-agents that compose with Mentat itself. Drop these into
`~/.claude/agents/` (user scope, not plugin scope — they need hooks /
mcpServers / permissionMode that plugin-scoped agents lose):

```bash
cp /agent/workspace/mentat/helpers/*.md ~/.claude/agents/
```

After install, they're available as `subagent_type` values when dispatching
via the Task tool, or auto-attach via their `description` retrieval signal.

| Helper                | Job                                                    | Tools                              |
|-----------------------|--------------------------------------------------------|------------------------------------|
| `mentat-medic`        | Diagnose plugin issues, parse hook-errors.log, triage  | Read, Grep, Glob, LS, Bash         |
| `mentat-quartermaster`| Validate, smoke, build tarball, sha-checksum, release  | Read, Write, Edit, Glob, Grep, Bash|
| `mentat-conductor`    | Meta: decompose features into parallel operator lanes  | Read, Glob, Grep, LS, Task, Bash   |

## Why these three

You said *"start making u some helpers please too"* — these are the helpers
**I (Artificer) need** when working on Mentat for you ongoing:

1. **mentat-medic** runs whenever a Mentat user reports anything wrong.
   It's the triage front-line — it never patches, it just finds.

2. **mentat-quartermaster** runs whenever I'm about to ship a Mentat release.
   It enforces the smoke-must-be-green rule, computes checksums, writes the
   release notes. Stops me from shipping broken builds.

3. **mentat-conductor** is the meta-orchestrator I use to spin up parallel
   operator dispatches for v0.3+ work. It encodes the lane-discipline
   pattern (named operators, disjoint file ownership, no rewrites,
   completion-note shape) so I don't reinvent the playbook each time.

## Why not more

Resist the temptation to add a helper for every Mentat workflow. The four
sub-agents already in `plugin/agents/` (`cartographer`, `crucible`, `scribe`,
`sentinel`) are the **user-facing** operators — they ship in the plugin.
The three helpers in `/helpers/` are the **operator-grade** sub-agents I
use when I'm working on Mentat itself. That separation matters.

If you need a fourth helper, my candidates would be:

- `mentat-archeologist` — combs `~/.mentat/handoff/` and
  `~/.mentat/insights.archive/` for cross-session patterns. Useful once
  you've accumulated weeks of session data.
- `mentat-cartographer-v2` — extends the plugin-scoped cartographer with
  Q-table delta analysis (compare two Q-tables and surface divergence).

Both are easy adds when you actually want them — don't pre-bake.
