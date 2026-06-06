# INSTALL — CTMv3 Plugin

This document explains how to install the CTMv3 cross-runtime plugin on a fresh
machine. The plugin has two layers:

1. **Engine** — the Python activation engine in `core/`. Required for all
   runtimes.
2. **Adapter(s)** — one or more runtime-specific shims in `claude-code/`,
   `codex/`, `opencode/`, `gemini-cli/`. Install whichever you actually use.

---

## Prerequisites

- Python 3.10 or newer (stdlib only — no external deps)
- bash 4+ (for installer scripts)
- A target runtime you intend to use (Claude Code, Codex, opencode, or
  Gemini CLI). Multiple runtimes can be installed side-by-side.

---

## Step 1: Install the Engine

The engine lives at `core/` and exposes the command-line interface
`python3 -m ctmv3`. Pick one install path:

### Option A: pip install (recommended)

```bash
cd core
pip install --user .
# Or for a virtualenv:
pip install .
```

After install, verify:

```bash
python3 -m ctmv3 version
# Expected: ctmv3 3.0.0
```

### Option B: PYTHONPATH (no install required)

```bash
export PYTHONPATH="/path/to/ctmv3-plugin/core:$PYTHONPATH"
python3 -m ctmv3 version
```

Add the export to your shell rc file (`~/.bashrc`, `~/.zshrc`) to persist.

### Option C: Symlink to ~/.local/bin

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/ctmv3 <<'EOF'
#!/usr/bin/env bash
exec python3 -m ctmv3 "$@"
EOF
chmod +x ~/.local/bin/ctmv3
```

Now `ctmv3 <command>` works directly (assuming `~/.local/bin` is on `$PATH`).

---

## Step 2: Install a Runtime Adapter

Pick one or more:

### Claude Code

```bash
# Project-scoped (recommended for testing):
# Copy the plugin to your project's .claude/ directory
cp -r claude-code/. .claude/

# Or install as a global plugin via marketplace once published:
# (see claude-code/README.md for the up-to-date install command)
```

### Codex

```bash
cd codex
bash install.sh
# This copies skills/ctmv3/ to ~/.codex/skills/ctmv3/ and prints the
# config.toml + hooks.json snippets to paste into your ~/.codex/ config.
```

### opencode

```bash
cd opencode
# Project-scoped:
bash install.sh
# Global:
bash install.sh global
```

### Gemini CLI

```bash
cd gemini-cli
bash install.sh
# Then enable in Gemini CLI:
gemini extensions enable ctmv3
```

---

## Step 3: Verify

In any repo you want to activate, run:

```bash
python3 -m ctmv3 boot --json
```

You should see a signal inventory JSON with `branch: COLD_START` (if the repo
has no prior CTMv3 artifacts) or `WARM_START` (if it does).

To do a full cold-start activation:

```bash
python3 -m ctmv3 activate
```

This builds the full CTMv3 artifact set. After it completes, your repo should
have:

```
TOPOLOGY.md
FAILURE_GRAMMAR.md
PROVENANCE.md
ARCHITECTURE_MAP.md
AGENTS.md
CLAUDE.md  (only if --target-runtime includes claude-code)
.sovereign/
  session_state.json
  topology_fingerprint.txt
  golden_paths.json
.claude/   (only if --target-runtime includes claude-code)
  settings.json
.codex/    (only if --target-runtime includes codex)
  skills/
.github/   (optional, only if --target-runtime includes github)
  copilot-instructions.md
  workflows/topology-enforce.yml
```

---

## Step 4: Phase 0 Archaeology

The scaffold is just structure. Your agent (or you) must now run Phase 0
archaeology to fill the templates with real findings:

- Read every Tier 3 config file (`pyproject.toml`, `go.mod`, `package.json`,
  `Cargo.toml`).
- Read the load-bearing source modules.
- Fill `TOPOLOGY.md` Load-Bearing Concepts with real concepts (not placeholders).
- Fill `ARCHITECTURE_MAP.md` branches with real `file:line` anchors.
- Update `PROVENANCE.md` Session Log with the archaeology pass.

This is where the cognitive layer takes over. The plugin scaffolds the
container; the agent fills the contents.

---

## Uninstall

### Engine

```bash
pip uninstall ctmv3
# Or remove the PYTHONPATH export
# Or rm ~/.local/bin/ctmv3
```

### Per-runtime

- Claude Code: remove `.claude/` from your project, or use the marketplace
  uninstall command if installed globally.
- Codex: `rm -rf ~/.codex/skills/ctmv3` and remove the config.toml /
  hooks.json fragments you pasted.
- opencode: remove `.opencode/agent/ctmv3-architect.md`,
  `.opencode/command/ctmv3-*.md`, `.opencode/plugin/ctmv3.ts`.
- Gemini CLI: `gemini extensions disable ctmv3 && rm -rf ~/.gemini/extensions/ctmv3`.

---

## Troubleshooting

### `python3 -m ctmv3` says "No module named ctmv3"

The engine is not on the Python path. Either run `pip install` from `core/`,
or set `PYTHONPATH` to include `core/` (see Step 1).

### Claude Code slash commands don't appear

Confirm `.claude/.claude-plugin/plugin.json` is valid JSON. Run:

```bash
python3 -c "import json; json.load(open('.claude/.claude-plugin/plugin.json'))"
```

If it errors, the manifest is malformed.

### `boot` returns an unexpected branch

Run `python3 -m ctmv3 status` to see the full signal inventory. If signals
exist but the branch is `COLD_START`, you may have a tier 1 artifact (e.g.
`AGENTS.md`) that is empty or trivially short — the boot protocol treats
zero-content artifacts as absent.

### topology_fingerprint.txt drifts on every commit

This is normal if you are actively editing `TOPOLOGY.md` or
`ARCHITECTURE_MAP.md`. Run `python3 -m ctmv3 fingerprint` at session close
to re-anchor.
