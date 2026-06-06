# Mentat — Gemini CLI adapter

The Gemini CLI adapter ships Mentat's hook layer to Google's `gemini`
runtime (Antigravity, gemini-cli). The substrate (state machine, Q-table,
insight bus, MCP server) is shared across all three runtimes; this
adapter only carries the Gemini-flavored entry scripts and the manifest
to register them as a Gemini extension.

## What it gives you

- The same FSA states (planning, exploring, executing, verifying,
  reflecting, blocked, drifting, compacting) over Gemini sessions.
- The same `~/.mentat/q_table.sqlite` accumulating rewards from your
  Claude Code and Codex work — cross-runtime TD-learning.
- Drift detection against `.mentat/scope.md` with hard System Block of
  write/exec tools while DRIFTING (exit 2 + stderr reason).
- Handoff written on `PreCompress` and `SessionEnd` and picked up on the
  next `SessionStart`, so resume preserves substrate memory.

## Gemini events Mentat wires (11 total)

| Gemini event           | Hook script                  | Primary purpose                             |
|------------------------|------------------------------|---------------------------------------------|
| SessionStart           | session_start.py             | FSA boot + handoff replay                   |
| SessionEnd             | session_end.py               | SESSION_END + handoff write                 |
| BeforeAgent            | before_agent.py              | Drift check + Q-route hint on prompt        |
| AfterAgent             | after_agent.py               | Tag turn close                              |
| BeforeModel            | before_model.py              | Record model + state at model call          |
| AfterModel             | after_model.py               | Tag model response                          |
| BeforeToolSelection    | before_tool_selection.py     | Record Q-best alongside available tools     |
| BeforeTool             | before_tool.py               | Classify + drift guard (deny on drift)      |
| AfterTool              | after_tool.py                | Reward + Q-update + entropy spike           |
| PreCompress            | pre_compress.py              | Snapshot to handoff.md before compression   |
| Notification           | notification.py              | Tag system notifications                    |

**Primary verify trigger**: `AfterTool` on a `run_shell_command` whose
command starts with a known verify prefix (pytest / ruff / mypy / cargo
test / etc.) — the state-machine inside `state_machine/machine.py`
reclassifies it from `EXEC_TOOL` to `VERIFY_TOOL` automatically, so the
FSA transitions to `VERIFYING` without any extra hook logic.

## Install (manual)

```bash
# 1. Put Mentat somewhere stable on disk.
PLUGIN_ROOT=$HOME/.gemini/extensions/mentat
mkdir -p "$PLUGIN_ROOT"
# rsync / cp the plugin tree into $PLUGIN_ROOT
# (skip if already done by the universal installer)

# 2. The gemini-extension.json manifest is the canonical registration.
#    Gemini auto-discovers extensions in ~/.gemini/extensions/<name>/.
ls "$PLUGIN_ROOT/adapters/gemini/gemini-extension.json"
# If your Gemini build looks at the extension root directly, symlink:
ln -sf "$PLUGIN_ROOT/adapters/gemini/gemini-extension.json" \
       "$PLUGIN_ROOT/gemini-extension.json"

# 3. Wire the hooks into your settings.json (or let the extension
#    manifest reference handle it — Gemini supports $ref-style imports).
mkdir -p ~/.gemini
test -f ~/.gemini/settings.json || echo '{}' > ~/.gemini/settings.json
# The universal installer merges the hooks block automatically.

# 4. Append the substrate vocabulary to ~/.gemini/GEMINI.md.
test -f ~/.gemini/GEMINI.md || touch ~/.gemini/GEMINI.md
grep -q "mentat-substrate:begin" ~/.gemini/GEMINI.md || \
  cat "$PLUGIN_ROOT/adapters/gemini/GEMINI.snippet.md" >> ~/.gemini/GEMINI.md

# 5. Make hook scripts executable.
chmod +x "$PLUGIN_ROOT/adapters/gemini/hooks/"*.py
```

## Smoke test

```bash
# Start a Gemini session in any project
cd ~/Projects/whatever
gemini

# Watch the insight bus from another shell
$PLUGIN_ROOT/bin/mentat tail --n 5
# After the first prompt you should see SESSION_START + USER_PROMPT
# entries tagged with runtime=gemini.

# Drift-test it
mkdir -p .mentat
cat > .mentat/scope.md <<'EOF'
# Scope — current task
## In
- whatever you're working on
## Out (deferred — DO NOT re-inject)
- inference
- model loading
EOF

# In the Gemini chat, send a prompt that mentions "inference".
# Mentat should emit SCOPE_DRIFT and the next write_file / replace /
# run_shell_command should be denied with a System Block (exit 2 +
# stderr reason).
```

## Troubleshooting

- **Hooks don't fire**: confirm the `hooks` block is in your
  `~/.gemini/settings.json` AND that the extension is listed in
  `~/.gemini/extensions/`. Run `/hooks panel` in the Gemini CLI to see
  what it sees.
- **`stdout` parse failure**: Gemini is strict — stdout MUST be a
  single JSON object or empty. Any stray print() breaks the hook. All
  Mentat hooks route logs through stderr; if you see a parse error,
  check `~/.mentat/log/hook-errors.log` for the traceback.
- **`MODULE NOT FOUND state_machine`**: set `GEMINI_PLUGIN_ROOT` in your
  shell to the absolute plugin path, or rely on the adapter's
  `parents[3]` fallback (works when hooks live inside the plugin tree).
- **Project hooks untrusted**: Gemini fingerprints project hooks. If
  Mentat's hook command changes, you'll be warned before re-running.

## Uninstall

```bash
rm -rf "$HOME/.gemini/extensions/mentat"
# manually strip the hooks block from ~/.gemini/settings.json — or
# revert from your dotfiles VCS.

# Optional — wipe substrate state too (also affects Claude/Codex)
rm -rf ~/.mentat
```
