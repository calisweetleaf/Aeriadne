# Mentat — Codex CLI adapter

The Codex CLI adapter ships Mentat's hook layer to OpenAI's `codex` runtime.
The substrate (state machine, Q-table, insight bus, MCP server) is shared
across all three runtimes Mentat targets; this adapter only carries the
thin Codex-flavored entry scripts and the wiring to register them.

## What it gives you

- The same six FSA states (planning, exploring, executing, verifying,
  reflecting, blocked, drifting, compacting) over Codex sessions.
- The same `~/.mentat/q_table.sqlite` accumulating rewards from your
  Claude Code and Gemini work — cross-runtime TD-learning.
- Drift detection against `.mentat/scope.md` with hard deny of write/exec
  tools while DRIFTING (via Codex's exit-2 + stderr deny path).
- Handoff written on every Stop and picked up on the next SessionStart,
  so resume preserves substrate memory.

## Codex events Mentat wires

| Codex event       | Hook script              | Purpose                              |
|-------------------|--------------------------|--------------------------------------|
| SessionStart      | session_start.py         | FSA boot + handoff replay            |
| UserPromptSubmit  | user_prompt_submit.py    | Drift check + Q-route hint           |
| PreToolUse        | pre_tool_use.py          | Classify + drift guard (deny on drift) |
| PermissionRequest | permission_request.py    | Tag escalations, emit Q-hint         |
| PostToolUse       | post_tool_use.py         | Reward + Q-update + entropy spike    |
| Stop              | stop.py                  | SESSION_END + handoff snapshot       |

Codex does not expose a separate PreCompact / PostCompact pair; the Stop
hook doubles as a cheap handoff write so resume is still seamless.

## Install (manual)

```bash
# 1. Put Mentat somewhere on disk (the install_universal.sh script will do this for you)
#    Pick a stable absolute path — Codex resolves command paths literally.
PLUGIN_ROOT=$HOME/.codex/plugins/mentat
mkdir -p "$PLUGIN_ROOT"
# rsync / cp the plugin tree into $PLUGIN_ROOT
# (skip if already done by the universal installer)

# 2. Enable the hooks feature flag and register the MCP server.
#    Splice adapters/codex/config.toml.snippet into ~/.codex/config.toml.
mkdir -p ~/.codex
test -f ~/.codex/config.toml || touch ~/.codex/config.toml
sed -i "s|\${CODEX_PLUGIN_ROOT}|$PLUGIN_ROOT|g" "$PLUGIN_ROOT/adapters/codex/config.toml.snippet"
cat "$PLUGIN_ROOT/adapters/codex/config.toml.snippet" >> ~/.codex/config.toml

# 3. Drop the hooks.json into ~/.codex/ (only ONE source per layer).
sed "s|\${CODEX_PLUGIN_ROOT}|$PLUGIN_ROOT|g" \
  "$PLUGIN_ROOT/adapters/codex/hooks.json" > ~/.codex/hooks.json

# 4. Make hook scripts executable (Codex invokes them via python3, but a
#    +x bit is still polite and helps if you ever swap to shebang dispatch).
chmod +x "$PLUGIN_ROOT/adapters/codex/hooks/"*.py

# 5. Add the substrate vocabulary to your AGENTS doc so the agent knows
#    Mentat exists. The snippet is bracketed; safe to re-run idempotently.
mkdir -p ~/.codex
test -f ~/.codex/AGENTS.md || touch ~/.codex/AGENTS.md
grep -q "mentat-substrate:begin" ~/.codex/AGENTS.md || \
  cat "$PLUGIN_ROOT/adapters/codex/AGENTS.snippet.md" >> ~/.codex/AGENTS.md
```

## Smoke test

```bash
# Start a Codex session in any project
cd ~/Projects/whatever
codex

# In another shell, watch the insight bus
$PLUGIN_ROOT/bin/mentat tail --n 5
# After the first prompt you should see SESSION_START + USER_PROMPT entries
# tagged with runtime=codex.

# Author a scope file and drift-test it
mkdir -p .mentat
cat > .mentat/scope.md <<'EOF'
# Scope — current task
## In
- whatever you're working on
## Out (deferred — DO NOT re-inject)
- inference
- model loading
EOF

# In the Codex chat, send a prompt that mentions "inference".
# Mentat should emit SCOPE_DRIFT in the bus and the next write/exec tool
# should be denied with a clear reason on stderr (visible in Codex's
# transcript).
```

## Troubleshooting

- **Hooks don't fire**: confirm `[features] codex_hooks = true` is in your
  `~/.codex/config.toml`. The feature flag is required.
- **`hooks.json` AND inline `[hooks]` both present**: Codex warns at
  startup and merges them. Pick one to avoid double-firing.
- **`MODULE NOT FOUND state_machine`**: set `CODEX_PLUGIN_ROOT` in your
  shell to the absolute plugin path, or rely on the adapter's parents[3]
  fallback (works when the hooks live inside the plugin tree).
- **Q-table doesn't share with Claude Code**: confirm `MENTAT_HOME` is
  unset (or set to the same path) in both Codex's and Claude Code's
  shells. The default is `~/.mentat` for both.

## Uninstall

```bash
# Remove the wiring (keeps the substrate state)
rm -f ~/.codex/hooks.json
# manually strip the [mcp_servers.mentat] and [features] blocks from
# ~/.codex/config.toml — or just revert from your dotfiles VCS.

# Optional — wipe substrate state too (this also wipes Claude/Gemini state)
rm -rf ~/.mentat
```
