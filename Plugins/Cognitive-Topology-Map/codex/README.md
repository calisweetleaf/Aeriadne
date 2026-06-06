# CTMv3 Codex Adapter

CTMv3 is a workspace activation system that bootstraps a repo into a living,
agent-operable state. This package is the Codex CLI adapter for it.

---

## What CTMv3 Is (and Is Not)

CTMv3 is not a skill maker.

That framing is too small. CTMv3 enters a repo and makes it living for agents:

- Sets up `.sovereign/`, `.github/`, `.claude/`, `.codex/` directories
- Creates AGENTS.md, ARCHITECTURE_MAP.md, TOPOLOGY.md, FAILURE_GRAMMAR.md,
  PROVENANCE.md as navigable topology artifacts
- Wires in session hooks so agents can cold-start or warm-start correctly
- Leaves behind a state that any future agent can enter and immediately work

A skill may be one byproduct of this process. The repo itself is the real output.

See `skills/ctmv3/REFERENCES.md` -> `EXPLANATION.md` for the full framing.

---

## Why Is This a Codex Skill If It Is Not a Skill Maker?

The skill package is the cognitive layer and invocation surface. The Python engine
(`python3 -m ctmv3`) is the activation engine. Together they form the full system:

- The skill tells Codex when and how to invoke the activation engine
- The `ctmv3-architect` sub-agent (declared in `agents/openai.yaml`) can be invoked
  implicitly when Codex recognizes activation-pattern phrases
- The shell wrappers in `scripts/` are the bridge between Codex's skill body and
  the Python engine

This split matches the principle in EXPLANATION.md: plugin = activation engine,
skill/docs = cognitive layer. Neither is sufficient alone.

---

## Prerequisites

- Codex CLI installed (`~/.codex/` exists)
- Python 3.8+
- CTMv3 core engine installed (`python3 -c "import ctmv3"` succeeds)

To install the core engine (development path):
```
pip install -e /agent/workspace/ctmv3-plugin/
```

---

## Install

```bash
bash install.sh
```

The installer:
1. Checks that `~/.codex/` exists
2. Copies `skills/ctmv3/` to `~/.codex/skills/ctmv3/`
3. Sets `chmod +x` on all `scripts/*.sh`
4. Prints (does NOT auto-merge) the contents of `config-fragments/config.toml.fragment`
   and `config-fragments/hooks.json.fragment` with instructions for where to paste them
5. Checks that `python3 -c "import ctmv3"` succeeds and reports if not

Daeron's `config.toml` is never auto-modified. The merge is always manual.

---

## Manual Config Steps After Install

After running `install.sh`, complete two manual steps:

### 1. Merge into `~/.codex/config.toml`

Add the CTMv3 project doc settings:
```toml
project_doc_max_bytes = 131072
project_doc_fallback_filenames = ["AGENTS.override.md", "AGENTS.md"]
```

Full fragment with comments is in `config-fragments/config.toml.fragment`.

### 2. Merge into `~/.codex/hooks.json`

The `SessionStart` hook fires `python3 -m ctmv3 boot` at the start of every Codex
session, so the engine can report cold vs warm branch before the agent begins.

```json
{
  "SessionStart": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "python3 -m ctmv3 boot --json --project-root \"$CODEX_PROJECT_DIR\" 2>/dev/null || true"
        }
      ]
    }
  ]
}
```

If `hooks.json` already has a `SessionStart` key, add the hook entry to the existing
array. Do not replace the entire key.

Full fragment is in `config-fragments/hooks.json.fragment`.

---

## Invoking CTMv3 from Codex

### Via $ctmv3 mention

In any Codex chat, mention `$ctmv3` to load the skill:

```
$ctmv3 activate this repo
$ctmv3 cold start /path/to/my-project
$ctmv3 warm start session
$ctmv3 build architecture map
$ctmv3 set up agent hooks
```

### Implicit invocation

The `ctmv3-architect` sub-agent has `allow_implicit_invocation: true`. Codex will
route to it automatically when the session message matches activation-pattern phrases:

- "activate this repo"
- "cold start this codebase"
- "bring this codebase alive"
- "set up agent hooks"
- "build architecture map"
- "warm start session"

### Direct script invocation

The scripts in `~/.codex/skills/ctmv3/scripts/` can be called directly from any
shell or from inside a Codex skill body:

```bash
# Check current boot state and signal inventory
bash ~/.codex/skills/ctmv3/scripts/ctmv3-status.sh

# Full activation of a specific repo
bash ~/.codex/skills/ctmv3/scripts/ctmv3-activate.sh /path/to/repo

# Boot discovery only (outputs JSON signal inventory)
bash ~/.codex/skills/ctmv3/scripts/ctmv3-boot.sh /path/to/repo --json

# Warm start -- diff provenance and continue
bash ~/.codex/skills/ctmv3/scripts/ctmv3-warm.sh /path/to/repo

# Build or update ARCHITECTURE_MAP.md
bash ~/.codex/skills/ctmv3/scripts/ctmv3-architecture-map.sh /path/to/repo

# Initialize .sovereign/ (run after topology artifacts are complete)
bash ~/.codex/skills/ctmv3/scripts/ctmv3-sovereign-init.sh /path/to/repo

# Initialize .github/, .claude/, .codex/ (run after TOPOLOGY.md is complete)
bash ~/.codex/skills/ctmv3/scripts/ctmv3-dot-init.sh /path/to/repo

# Close session cleanly (update PROVENANCE.md + session_state.json)
bash ~/.codex/skills/ctmv3/scripts/ctmv3-session-close.sh /path/to/repo
```

All scripts accept `PROJECT_ROOT` as the first argument (defaults to `$PWD`) and
pass any additional arguments through to the Python engine.

---

## Per-Command Reference

| Script | CTMv3 command | When to use |
|--------|--------------|-------------|
| `ctmv3-boot.sh` | `boot` | First thing every session. Determines cold vs warm branch. |
| `ctmv3-activate.sh` | `activate` | Cold entry: full Phase 0-5 pass on a new or unencoded repo. |
| `ctmv3-warm.sh` | `warm` | Warm entry: diff provenance, continue from last session. |
| `ctmv3-architecture-map.sh` | `architecture-map` | Build or refresh ARCHITECTURE_MAP.md from TOPOLOGY.md. |
| `ctmv3-sovereign-init.sh` | `sovereign-init` | Initialize .sovereign/ after topology artifacts exist. |
| `ctmv3-dot-init.sh` | `dot-init` | Initialize .github/, .claude/, .codex/ after TOPOLOGY.md. |
| `ctmv3-session-close.sh` | `session-close` | Mandatory at session end. Updates PROVENANCE.md + state. |
| `ctmv3-status.sh` | `status` | Inspect signal inventory and current boot state anytime. |

---

## Installed File Layout

```
~/.codex/skills/ctmv3/
+-- SKILL.md                   <- Entry point and semantic router (read first)
+-- REFERENCES.md              <- Pointers to full CTMv3 cognitive doc set
+-- agents/
|   +-- openai.yaml            <- ctmv3-architect sub-agent declaration
+-- scripts/
    +-- ctmv3-boot.sh
    +-- ctmv3-activate.sh
    +-- ctmv3-warm.sh
    +-- ctmv3-architecture-map.sh
    +-- ctmv3-sovereign-init.sh
    +-- ctmv3-dot-init.sh
    +-- ctmv3-session-close.sh
    +-- ctmv3-status.sh
```

---

## Troubleshooting

**"ctmv3 Python package not found"**
The core engine is not installed. Run:
```
pip install -e /agent/workspace/ctmv3-plugin/
```
or check the install path of the core engine.

**"~/.codex/ does not exist"**
Codex CLI is not installed. The skill cannot be installed without it.

**Scripts run but nothing happens in the repo**
Run `ctmv3-status.sh` first to check the signal inventory. If all tiers are absent,
the repo has no CTM artifacts and needs a cold start via `ctmv3-activate.sh`.

**AGENTS.md is not being loaded by Codex**
Check that `project_doc_fallback_filenames` is set correctly in `~/.codex/config.toml`
(see config-fragments/config.toml.fragment). Codex looks for `AGENTS.override.md`
then `AGENTS.md` in that order.
