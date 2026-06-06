# CTMv3 — Gemini CLI Extension

CTMv3 workspace activation system for Gemini CLI. Bootstraps a repo into a
living, agent-operable workspace by creating `.sovereign/`, `AGENTS.md`,
`ARCHITECTURE_MAP.md`, `TOPOLOGY.md`, `FAILURE_GRAMMAR.md`, `PROVENANCE.md`,
and the `.claude/.codex/.github/` ecosystem artifacts.

CTMv3 is not a skill maker. It is a codebase onboarding and workspace
activation engine.

---

## Prerequisites

- Gemini CLI installed (`gemini --version` should work)
- Python 3.10+ available as `python3`
- CTMv3 engine installed: `pip install ctmv3` (or install from the
  `core/` directory of this repo)

Verify the engine is reachable before installing the extension:

```bash
python3 -m ctmv3 --help
```

---

## Install

Clone or download this repo, then run the installer from the `gemini-cli/`
directory:

```bash
cd path/to/ctmv3-plugin/gemini-cli
bash install.sh
```

The installer:
1. Copies `ctmv3/` to `~/.gemini/extensions/ctmv3/`
2. Sets execute permissions on the wrapper scripts
3. Checks that `python3 -m ctmv3` is reachable
4. Prints next steps

After install, **restart Gemini CLI** — extensions are loaded at startup.

Verify the extension is active:

```
/extensions list
```

---

## Update

To update to a newer version after pulling this repo:

```bash
bash install.sh
```

The installer removes the existing installation before copying the new version.

Alternatively, using Gemini CLI's built-in update (if installed from a GitHub
URL via `gemini extensions install`):

```bash
gemini extensions update ctmv3
```

---

## Uninstall

```bash
gemini extensions uninstall ctmv3
```

Or manually:

```bash
rm -rf ~/.gemini/extensions/ctmv3
```

---

## Usage

### Session bootstrap (always first)

At the start of every session in a repo, run boot discovery before answering
any architectural question:

```
/ctmv3:boot
```

This reports the signal inventory and determines the branch:
- `COLD_START` — no CTM artifacts found; activate the repo first
- `WARM_START` — CTM artifacts present, recent session, topology valid
- `PARTIAL` — some artifacts found; run targeted archaeology

### Available slash commands

| Command                     | What it does                                   |
|-----------------------------|------------------------------------------------|
| `/ctmv3:boot`               | Discover signal inventory, determine branch    |
| `/ctmv3:activate`           | Full Phase 0-5 cold-start activation           |
| `/ctmv3:warm`               | Warm-start diff check, three-question validity |
| `/ctmv3:architecture-map`   | Build or update ARCHITECTURE_MAP.md            |
| `/ctmv3:sovereign-init`     | Initialize `.sovereign/` directory             |
| `/ctmv3:dot-init`           | Scaffold `.claude/`, `.codex/`, `.github/`     |
| `/ctmv3:session-close`      | Close session, update PROVENANCE.md            |
| `/ctmv3:status`             | Print activation status and open tasks         |

Commands are namespaced under `ctmv3:` to avoid conflicts with user or project
commands. If a conflict occurs, Gemini CLI automatically prefixes the extension
name (e.g., `/ctmv3.boot`).

### Direct invocation

You can also invoke without slash commands by asking Gemini naturally:
- "run ctmv3 boot"
- "activate this repo with ctmv3"
- "what is the ctmv3 status"
- "close the ctmv3 session"

The GEMINI.md context file loaded by this extension tells Gemini how to
interpret these phrases and which shell commands to run.

### Set project root

The scripts read `CTMV3_PROJECT_ROOT` from the environment. Override if your
project root is not `$PWD`:

```bash
export CTMV3_PROJECT_ROOT="/path/to/my/project"
```

---

## Cold Start Workflow

A fresh repo with no CTM artifacts:

```
/ctmv3:boot          # verify branch = COLD_START
/ctmv3:activate      # run full Phase 0-5 activation
/ctmv3:status        # confirm artifacts were created
/ctmv3:session-close # close session cleanly before exiting
```

Phase 0-5 activation produces:

```
[project-root]/
├── ARCHITECTURE_MAP.md   traversal map (question-oriented navigation for agents)
├── AGENTS.md             operational posture
├── CLAUDE.md             Claude-specific context (if Claude Code is primary)
├── TOPOLOGY.md           cognitive map of the domain
├── FAILURE_GRAMMAR.md    taxonomy of failure signatures
├── PROVENANCE.md         snapshot lineage + session log
├── .github/
│   ├── copilot-instructions.md
│   ├── instructions/
│   └── workflows/
├── .claude/
│   ├── settings.json
│   └── CLAUDE.md
├── .codex/skills/
└── .sovereign/
    ├── session_state.json
    ├── golden_paths.json
    └── PROVENANCE.md
```

---

## Warm Start Workflow

Resuming work in a repo that was previously activated:

```
/ctmv3:warm          # three-question validity check
                     # if all pass: continue from last session
                     # if any fail: partial archaeology on the delta
/ctmv3:status        # verify current state
...work...
/ctmv3:session-close # close cleanly
```

---

## Gemini CLI Extension Surface Caveats

### Custom commands use TOML, not Markdown

Gemini CLI extension commands are defined as TOML files in `commands/`. Each
file has a `prompt` field (required) and a `description` field (optional). The
`prompt` is sent to the model as a pre-defined template. This differs from
Claude Code's `.claude/commands/*.md` format and Codex's markdown-based command
files.

The command TOML files for this extension are at:
`ctmv3/commands/ctmv3/*.toml`

### No first-class session lifecycle hooks (as of v0.4.0)

Gemini CLI extensions support `hooks/hooks.json` for intercepting CLI lifecycle
events, but auto-running `ctmv3 boot` on every session start is not guaranteed
by the extension format. The `scripts/ctmv3-session-start.sh` script is
provided for manual or hook-based invocation, but you must run `/ctmv3:boot`
explicitly at session start.

If Gemini CLI adds session-start hooks in a future release, wire
`ctmv3-session-start.sh` into `hooks/hooks.json` as a `session_start` event.

### No `excludeTools` for `write_file` with wildcards

The `excludeTools` array in `gemini-extension.json` supports command-specific
restrictions for `run_shell_command` (e.g., `"run_shell_command(rm)"`), but
does not support wildcard path matching for `write_file`. The manifest entry
`"write_file(manifest.json)"` targets that exact filename only.

### Extension commands have lowest precedence

If your project or user commands define a command named `boot`, `activate`,
`warm`, etc., those will take precedence over `/ctmv3:boot`, `/ctmv3:activate`,
etc. Gemini CLI will rename the extension commands to `/ctmv3.boot`,
`/ctmv3.activate`, etc. (dot separator prefix) to resolve the conflict. The
extension GEMINI.md trigger phrases remain effective regardless.

### All extension changes require a CLI restart

Running `gemini extensions update ctmv3` or editing files in
`~/.gemini/extensions/ctmv3/` will not take effect until you restart the Gemini
CLI session. Use `/commands reload` after editing TOML files to pick up command
changes without a full restart.

### GEMINI.md is the primary command surface

For Gemini CLI, the GEMINI.md context file loaded into every session is the
most reliable way to ensure CTMv3 behavior. The slash commands are convenience
shortcuts. If slash commands are not working as expected, you can always invoke
CTMv3 operations directly by asking Gemini in natural language — the GEMINI.md
context teaches it how to respond.

---

## File Layout

```
gemini-cli/
├── install.sh                         installer
└── ctmv3/
    ├── gemini-extension.json          extension manifest
    ├── GEMINI.md                      context loaded on activation (200-400 lines)
    ├── commands/ctmv3/
    │   ├── boot.toml                  /ctmv3:boot
    │   ├── activate.toml              /ctmv3:activate
    │   ├── warm.toml                  /ctmv3:warm
    │   ├── architecture-map.toml      /ctmv3:architecture-map
    │   ├── sovereign-init.toml        /ctmv3:sovereign-init
    │   ├── dot-init.toml              /ctmv3:dot-init
    │   ├── session-close.toml         /ctmv3:session-close
    │   └── status.toml                /ctmv3:status
    └── scripts/
        ├── ctmv3-wrap.sh              generic wrapper: python3 -m ctmv3 <cmd>
        └── ctmv3-session-start.sh     boot runner for session-start hooks
```
