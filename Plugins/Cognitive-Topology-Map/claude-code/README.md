# CTMv3 Workspace Activator — Claude Code Plugin

CTMv3 is a workspace activation system. It enters a repo and makes it living for agents.

It is not a skill maker. It is not a documentation generator. It is not a README helper.

After a proper CTMv3 pass, a repo has enough structure that any agent can enter it and
immediately know: what this codebase is, how it is organized, what has already been
decided, where the risk is, and how to continue work without re-deriving the entire
topology from scratch.

Requirements: Python 3.10+, stdlib only.

---

## What CTMv3 IS

- Workspace activation: `.sovereign/`, `AGENTS.md`, `ARCHITECTURE_MAP.md`, `TOPOLOGY.md`,
  `PROVENANCE.md`, `.claude/`, `.codex/`, `.github/` — all built from actual repo inspection.
- Session state machine: cold start vs. warm start, determined in < 60 seconds.
- Topology enforcement: `.github/` CI gates and pre-commit hooks that enforce structural
  invariants encoded in TOPOLOGY.md.
- Agent-operable output: after activation, any agent can enter the repo on a warm start
  without re-discovering context that already exists.

## What CTMv3 IS NOT

- A skill maker (that is one possible byproduct, not the purpose)
- A README generator
- A code documentation tool
- A workflow template pack
- A replacement for reading the code

---

## Install

**Local install (development or personal use):**

```bash
claude plugin install /path/to/ctmv3-plugin/claude-code
```

**From git (when published):**

```bash
claude plugin install https://github.com/daeron/ctmv3-plugin#claude-code
```

**Test without installing (--plugin-dir flag):**

```bash
claude --plugin-dir /path/to/ctmv3-plugin/claude-code
```

After installation, skills are namespaced as `/ctmv3-workspace-activator:<command>`.
Reload changes without restarting with `/reload-plugins`.

---

## Usage

All commands accept `--project-root PATH` to target a repo other than the current directory.

### /ctmv3-workspace-activator:activate

Full cold start. Runs Phase 0-5 archaeology and produces the complete artifact set.
Use this on repos that have never been CTMv3-activated.

```
/ctmv3-workspace-activator:activate
/ctmv3-workspace-activator:activate --force          # overwrite existing artifacts
/ctmv3-workspace-activator:activate --project-root /path/to/repo
```

### /ctmv3-workspace-activator:boot

Boot state check. Read-only. Determines in < 60 seconds whether the repo is COLD, WARM,
or PARTIAL. Run this at the start of any session before doing anything else.

```
/ctmv3-workspace-activator:boot
```

### /ctmv3-workspace-activator:warm

Warm session resume. Reads PROVENANCE.md, checks topology validity, runs targeted
archaeology on changed areas if drift is detected. Use instead of :activate on repos
that have already been activated.

```
/ctmv3-workspace-activator:warm
/ctmv3-workspace-activator:warm --force-full         # rebuild from scratch even if warm
```

### /ctmv3-workspace-activator:architecture-map

Build or rebuild ARCHITECTURE_MAP.md — the agent-navigable traversal map.
Requires TOPOLOGY.md to exist first.

```
/ctmv3-workspace-activator:architecture-map
/ctmv3-workspace-activator:architecture-map --force
```

### /ctmv3-workspace-activator:sovereign-init

Initialize or repair the .sovereign/ directory: session_state.json,
topology_fingerprint.txt, golden_paths.json. Requires TOPOLOGY.md and ARCHITECTURE_MAP.md
to exist first.

```
/ctmv3-workspace-activator:sovereign-init
/ctmv3-workspace-activator:sovereign-init --repair   # reseed malformed files only
```

### /ctmv3-workspace-activator:dot-init

Build the .xyz directory ecosystem: .claude/settings.json, CLAUDE.md,
.github/copilot-instructions.md, per-path instruction files for DENSE topology nodes,
and CI enforcement workflows.

```
/ctmv3-workspace-activator:dot-init
/ctmv3-workspace-activator:dot-init --skip-github    # skip .github/ creation
/ctmv3-workspace-activator:dot-init --force          # overwrite existing files
```

### /ctmv3-workspace-activator:session-close

Clean session close. Updates PROVENANCE.md Session Log, refreshes session_state.json,
recomputes topology fingerprint if TOPOLOGY.md was modified. Run at end of every session.

```
/ctmv3-workspace-activator:session-close
/ctmv3-workspace-activator:session-close --last-action "built TOPOLOGY.md LBC section"
```

### /ctmv3-workspace-activator:status

Read-only workspace status report. Artifact inventory, session state, boot state,
completeness score (0-8), topology drift detection.

```
/ctmv3-workspace-activator:status
```

---

## Lifecycle hooks

The plugin installs two automatic hooks:

**SessionStart**: runs `python3 -m ctmv3 boot --json` on every session start so Claude
immediately knows the boot state (COLD/WARM/PARTIAL) without requiring a manual command.
Runs quietly — if the engine is absent, the hook exits cleanly.

**Stop**: checks at session end whether there were substantive writes. If so, prompts
the operator to run /ctmv3:session-close before exiting. Corrupted session state is the
primary source of broken warm starts.

---

## Subagent: ctmv3-architect

The plugin includes a specialized subagent at `agents/ctmv3-architect.md`. It can be
invoked to run the full Phase 0-5 activation in an isolated subagent context, keeping
the main conversation clean.

The architect subagent will not produce placeholders. It reads the actual repo and builds
topology, failure grammar, traversal map, and ecosystem artifacts from real findings.

---

## Session workflow

Typical session in a new repo:
```
1. /ctmv3:boot                       <- determine state (30 seconds)
2. /ctmv3:activate                   <- if COLD: full activation
3. (do work)
4. /ctmv3:session-close              <- clean close, update provenance
```

Typical session in an already-activated repo:
```
1. /ctmv3:boot                       <- confirm WARM state
2. /ctmv3:warm                       <- load session context, check for drift
3. (do work)
4. /ctmv3:session-close
```

---

## Python engine

All commands shell out to `python3 -m ctmv3 <subcommand> --json`. The engine lives at
`ctmv3-plugin/core/` and requires Python 3.10+, stdlib only. Install it in your Python
path before using the plugin, or place it on PATH as a module.

If the engine is absent, each command includes a manual fallback that reads the CTMv3
artifacts directly.

---

## Hardware note

The CTMv3 architecture is designed for Daeron's primary system: Ryzen 5 2400G / 12GB RAM,
no discrete GPU. The engine and all templates respect this constraint. No model-heavy
operations are performed locally. All inference is handled by Claude Code's existing API
connection.
