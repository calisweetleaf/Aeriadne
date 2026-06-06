#!/usr/bin/env bash
# Mentat — universal cross-runtime installer.
#
# Installs Mentat's hook layer into one or more of:
#   - Claude Code   (~/.claude/plugins/mentat — v0.1 hook tree)
#   - Codex CLI     (~/.codex/hooks.json + ~/.codex/config.toml + MCP)
#   - Gemini CLI    (~/.gemini/extensions/mentat + settings.json hooks)
#
# Pattern adapted from klaudworks/universal-skills and
# sickn33/antigravity-awesome-skills: detect which runtimes the user has,
# install only those, leave the rest alone. The same ~/.mentat/q_table.sqlite
# accumulates rewards across whatever subset is installed.
#
# Usage:
#   ./install_universal.sh                   # auto-detect (any runtime dir present)
#   ./install_universal.sh --claude          # Claude Code only
#   ./install_universal.sh --codex           # Codex only
#   ./install_universal.sh --gemini          # Gemini only
#   ./install_universal.sh --all             # all three regardless of detection
#   ./install_universal.sh --dry-run         # print what would happen, don't touch disk
#   ./install_universal.sh --plugin-root /abs/path   # source tree (default: this dir's parent)

set -euo pipefail

# ---------- arg parsing ----------------------------------------------------
DRY_RUN=0
WANT_CLAUDE=0
WANT_CODEX=0
WANT_GEMINI=0
WANT_ALL=0
EXPLICIT_RUNTIMES=0
PLUGIN_ROOT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --claude) WANT_CLAUDE=1; EXPLICIT_RUNTIMES=1; shift ;;
        --codex)  WANT_CODEX=1;  EXPLICIT_RUNTIMES=1; shift ;;
        --gemini) WANT_GEMINI=1; EXPLICIT_RUNTIMES=1; shift ;;
        --all)    WANT_ALL=1;    EXPLICIT_RUNTIMES=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        --plugin-root)
            PLUGIN_ROOT="$2"; shift 2 ;;
        --plugin-root=*)
            PLUGIN_ROOT="${1#*=}"; shift ;;
        -h|--help)
            sed -n '2,/^set -euo pipefail/p' "$0" | sed 's/^# \{0,1\}//;/^set -euo pipefail/d'
            exit 0
            ;;
        *)
            echo "mentat:install: unknown flag '$1' (try --help)" >&2
            exit 2
            ;;
    esac
done

# Resolve source plugin root (the dir containing state_machine/, mcp_server/, adapters/)
if [[ -z "$PLUGIN_ROOT" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

if [[ ! -d "$PLUGIN_ROOT/state_machine" ]]; then
    echo "mentat:install: --plugin-root '$PLUGIN_ROOT' does not contain state_machine/" >&2
    echo "                 (expected layout: <root>/state_machine/, <root>/mcp_server/, <root>/adapters/)" >&2
    exit 2
fi

# ---------- auto-detect runtimes (only if no explicit flags) ---------------
if [[ $EXPLICIT_RUNTIMES -eq 0 ]]; then
    [[ -d "$HOME/.claude" ]] && WANT_CLAUDE=1
    [[ -d "$HOME/.codex"  ]] && WANT_CODEX=1
    [[ -d "$HOME/.gemini" ]] && WANT_GEMINI=1
fi

if [[ $WANT_ALL -eq 1 ]]; then
    WANT_CLAUDE=1; WANT_CODEX=1; WANT_GEMINI=1
fi

if [[ $WANT_CLAUDE -eq 0 && $WANT_CODEX -eq 0 && $WANT_GEMINI -eq 0 ]]; then
    echo "mentat:install: no runtime selected and none auto-detected." >&2
    echo "                 pass --claude, --codex, --gemini, or --all" >&2
    exit 2
fi

# ---------- helpers --------------------------------------------------------
say() { echo "mentat:install: $*"; }
do_run() {
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  [dry-run] $*"
    else
        eval "$@"
    fi
}
ensure_dir() {
    [[ -d "$1" ]] && return 0
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  [dry-run] mkdir -p $1"
    else
        mkdir -p "$1"
    fi
}
copy_tree() {
    local src="$1" dst="$2"
    ensure_dir "$dst"
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  [dry-run] cp -r $src/ -> $dst/"
    else
        # rsync if available (preserves perms + skips unchanged), tar fallback
        if command -v rsync >/dev/null 2>&1; then
            rsync -a --exclude='__pycache__' --exclude='.git' "$src"/ "$dst"/
        else
            (cd "$src" && tar cf - --exclude='__pycache__' --exclude='.git' .) | (cd "$dst" && tar xf -)
        fi
    fi
}
append_if_missing() {
    local file="$1" marker="$2" payload="$3"
    if [[ -f "$file" ]] && grep -q "$marker" "$file" 2>/dev/null; then
        say "  (skip) $file already contains $marker"
        return 0
    fi
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  [dry-run] append snippet (marker '$marker') >> $file"
    else
        ensure_dir "$(dirname "$file")"
        [[ -f "$file" ]] || touch "$file"
        printf "\n" >> "$file"
        cat "$payload" >> "$file"
    fi
}
substitute_root() {
    # Read a template, substitute ${RUNTIME_PLUGIN_ROOT} → actual path.
    local template="$1" output="$2" var="$3" root="$4"
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "  [dry-run] render $template -> $output (replace \${$var} with $root)"
    else
        ensure_dir "$(dirname "$output")"
        sed "s|\${$var}|$root|g" "$template" > "$output"
    fi
}

say "source plugin root: $PLUGIN_ROOT"
say "dry-run: $DRY_RUN"

# ---------- Claude Code ----------------------------------------------------
if [[ $WANT_CLAUDE -eq 1 ]]; then
    CLAUDE_DEST="$HOME/.claude/plugins/mentat"
    say "[claude] installing into $CLAUDE_DEST"
    copy_tree "$PLUGIN_ROOT" "$CLAUDE_DEST"

    # The mcp.json -> .mcp.json rename (HyperAgent sandbox blocked the dotfile
    # name during authoring; the actual install path expects the leading dot).
    if [[ -f "$CLAUDE_DEST/mcp.json" && ! -f "$CLAUDE_DEST/.mcp.json" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  [dry-run] mv $CLAUDE_DEST/mcp.json -> $CLAUDE_DEST/.mcp.json"
        else
            mv "$CLAUDE_DEST/mcp.json" "$CLAUDE_DEST/.mcp.json"
        fi
    fi

    say "[claude] done. next: 'claude plugin marketplace add file://$CLAUDE_DEST'"
fi

# ---------- Codex ----------------------------------------------------------
if [[ $WANT_CODEX -eq 1 ]]; then
    CODEX_DEST="$HOME/.codex/plugins/mentat"
    say "[codex] installing plugin into $CODEX_DEST"
    copy_tree "$PLUGIN_ROOT" "$CODEX_DEST"

    # mcp.json -> .mcp.json (same as Claude — Codex doesn't care about the
    # name, but consistency helps when both runtimes share the install path).
    if [[ -f "$CODEX_DEST/mcp.json" && ! -f "$CODEX_DEST/.mcp.json" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  [dry-run] mv $CODEX_DEST/mcp.json -> $CODEX_DEST/.mcp.json"
        else
            mv "$CODEX_DEST/mcp.json" "$CODEX_DEST/.mcp.json"
        fi
    fi

    # Render hooks.json with the absolute plugin root substituted.
    say "[codex] rendering ~/.codex/hooks.json"
    substitute_root \
        "$CODEX_DEST/adapters/codex/hooks.json" \
        "$HOME/.codex/hooks.json" \
        "CODEX_PLUGIN_ROOT" \
        "$CODEX_DEST"

    # Render the config.toml.snippet and APPEND to ~/.codex/config.toml,
    # but only if Mentat isn't already wired (idempotent re-runs).
    if [[ -f "$HOME/.codex/config.toml" ]] && grep -q '\[mcp_servers.mentat\]' "$HOME/.codex/config.toml" 2>/dev/null; then
        say "[codex]   (skip) ~/.codex/config.toml already references [mcp_servers.mentat]"
    else
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  [dry-run] render config.toml.snippet -> append to ~/.codex/config.toml"
        else
            ensure_dir "$HOME/.codex"
            [[ -f "$HOME/.codex/config.toml" ]] || touch "$HOME/.codex/config.toml"
            sed "s|\${CODEX_PLUGIN_ROOT}|$CODEX_DEST|g" \
                "$CODEX_DEST/adapters/codex/config.toml.snippet" \
                >> "$HOME/.codex/config.toml"
        fi
    fi

    # Append AGENTS.snippet.md (idempotent via marker).
    append_if_missing "$HOME/.codex/AGENTS.md" \
        "mentat-substrate:begin" \
        "$CODEX_DEST/adapters/codex/AGENTS.snippet.md"

    chmod +x "$CODEX_DEST/adapters/codex/hooks/"*.py 2>/dev/null || true
    say "[codex] done. next: launch codex and confirm '[features] codex_hooks = true' in ~/.codex/config.toml"
fi

# ---------- Gemini ---------------------------------------------------------
if [[ $WANT_GEMINI -eq 1 ]]; then
    GEMINI_DEST="$HOME/.gemini/extensions/mentat"
    say "[gemini] installing extension into $GEMINI_DEST"
    copy_tree "$PLUGIN_ROOT" "$GEMINI_DEST"

    # mcp.json -> .mcp.json (same rationale).
    if [[ -f "$GEMINI_DEST/mcp.json" && ! -f "$GEMINI_DEST/.mcp.json" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  [dry-run] mv $GEMINI_DEST/mcp.json -> $GEMINI_DEST/.mcp.json"
        else
            mv "$GEMINI_DEST/mcp.json" "$GEMINI_DEST/.mcp.json"
        fi
    fi

    # Symlink the extension manifest so Gemini's discovery finds it at the root.
    if [[ ! -e "$GEMINI_DEST/gemini-extension.json" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "  [dry-run] symlink adapters/gemini/gemini-extension.json -> $GEMINI_DEST/gemini-extension.json"
        else
            # Inline the manifest with substitutions instead of symlinking, so
            # ${GEMINI_PLUGIN_ROOT} is resolved at install time.
            sed "s|\${GEMINI_PLUGIN_ROOT}|$GEMINI_DEST|g" \
                "$GEMINI_DEST/adapters/gemini/gemini-extension.json" \
                > "$GEMINI_DEST/gemini-extension.json"
        fi
    fi

    # Render hooks.json with the absolute extension root substituted.
    say "[gemini] rendering ~/.gemini/extensions/mentat/hooks.json"
    substitute_root \
        "$GEMINI_DEST/adapters/gemini/hooks/hooks.json" \
        "$GEMINI_DEST/hooks.json" \
        "GEMINI_PLUGIN_ROOT" \
        "$GEMINI_DEST"

    # Append GEMINI.snippet.md to ~/.gemini/GEMINI.md (idempotent).
    append_if_missing "$HOME/.gemini/GEMINI.md" \
        "mentat-substrate:begin" \
        "$GEMINI_DEST/adapters/gemini/GEMINI.snippet.md"

    chmod +x "$GEMINI_DEST/adapters/gemini/hooks/"*.py 2>/dev/null || true
    say "[gemini] done. next: launch gemini-cli and run '/hooks panel' to confirm Mentat is wired"
fi

# ---------- final ----------------------------------------------------------
say "----"
say "all selected runtimes installed."
say "shared substrate state will live at: \$HOME/.mentat/ (Q-table, sessions, insights, handoff)"
say "inspect with: $PLUGIN_ROOT/bin/mentat tail --n 5"
if [[ $DRY_RUN -eq 1 ]]; then
    say "DRY-RUN — nothing was actually written."
fi
