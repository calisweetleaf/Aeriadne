# Mentat slash commands

Claude Code's TUI maps every `.md` file under a plugin's `commands/` directory
to a slash command. The filename, minus the `.md` extension, is the slash
invocation: `commands/reflect.md` becomes `/reflect`. The frontmatter
declares the command's metadata (description, argument hint, allowed-tools
scope); the body becomes the prompt Claude reads when the user runs the
command.

## The surface

| Slash command   | Effect |
| --------------- | ------ |
| `/status`       | Prepends `mentat status` output as additional context and asks Claude to interpret it (state, transitions, last tool, Q-best). |
| `/reflect`      | Invokes the `mentat-reflect` skill: pause execution, synthesize the live state + last 30 insights + Q-table into a structured reflection. |
| `/plan`         | Invokes the `mentat-plan` skill: author `.mentat/scope.md` and `PLAN.md`. Argument is the plan topic. |
| `/dispatch`     | Invokes the `mentat-dispatch` skill: fan out two-to-four named sub-agents in parallel against the active scope. |
| `/debrief`      | Invokes the `mentat-debrief` skill: generate the modernized end-of-session HTML insight report. |
| `/scope`        | Prints `.mentat/scope.md`. With an argument, proposes a scope rewrite (gated on a confirming reply). |
| `/qtable`       | Dumps the persistent Q-table grouped by state; asks Claude to interpret routing intuition. |
| `/tail`         | Shows the last 30 insights; asks Claude to walk the timeline. |
| `/drift-check`  | Dispatches the `mentat-sentinel` sub-agent against text or a plan, audits it for deferred-topic hits. |

## Convention notes

- **Frontmatter** — every file declares at minimum a `description`. Commands
  that take an argument also declare an `argument-hint` (rendered in the TUI
  picker). Commands that need to shell out declare `allowed-tools` so
  Claude Code does not prompt for confirmation on every invocation.
- **`!``bash`` injection** — `/status`, `/scope`, `/tail`, and `/qtable` all
  embed live shell output by writing a `!` `` `command` `` block in the
  body. Claude Code executes the block before the prompt is sent, so the
  output is part of the prompt and the model has the fresh data.
- **`$ARGUMENTS`** — passed straight into the prompt as the user's
  free-form argument. Commands that don't take arguments simply omit it.
- **Skill invocation** — the four "skill" commands (`/reflect`, `/plan`,
  `/dispatch`, `/debrief`) explicitly reference the corresponding
  `skills/<name>/SKILL.md` file so the model loads the full procedure when
  it executes the slash command. The skill prompts remain the
  authoritative source of truth — these command files are just the bound
  TUI entry points.
- **Sub-agent dispatch** — `/drift-check` is the only command that
  dispatches a named sub-agent (`mentat-sentinel`) directly rather than
  invoking a skill. That keeps Sentinel cheap to call ad-hoc, without the
  ceremony of authoring a plan first.

## Resolving `${CLAUDE_PLUGIN_ROOT}`

Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` with the absolute path of
the plugin root before executing any `!` bash block. So every command that
needs to call `bin/mentat` writes the path as
`"${CLAUDE_PLUGIN_ROOT}/bin/mentat"` and survives every install location.

## Adding a new command

1. Create `commands/<name>.md`. Put `description:` in the frontmatter at
   minimum.
2. If it needs an argument, add `argument-hint: "[label]"` and reference
   `$ARGUMENTS` in the body.
3. If it shells out, add an `allowed-tools` line scoped to the exact
   binaries it calls — keep the scope narrow, never wildcard `Bash(*)`.
4. Use `!` `` `command` `` blocks for any live data you want injected
   before Claude reads the prompt.

The TUI picker re-reads the directory on every invocation, so a new command
is live immediately after the file is saved — no plugin reload needed.
