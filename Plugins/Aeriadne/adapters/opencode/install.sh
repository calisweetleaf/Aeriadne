#!/usr/bin/env bash
# Aeriadne OpenCode adapter installer
#
# Usage:
#   bash install.sh            # project scope: installs to .opencode/ in $PWD
#   bash install.sh global     # global scope:  installs to ~/.config/opencode/
#
# What this installs:
#   agents/aeriadne-cpf.md                  — constitutional-prompt-framework subagent
#   agents/aeriadne-mop.md                  — aeriadne-marketplace-operator subagent
#   agents/aeriadne-prompt-architect.md     — prompt-architect subagent
#   agents/aeriadne-package-cartographer.md — package-cartographer subagent
#   agents/aeriadne-registry-scribe.md      — registry-scribe subagent
#   agents/aeriadne-release-sentinel.md     — release-sentinel subagent
#   agents/aeriadne-compatibility-auditor.md — compatibility-auditor subagent
#   commands/aeriadne-cpf.md               — /aeriadne-cpf slash command
#   commands/aeriadne-audit.md             — /aeriadne-audit slash command
#   commands/aeriadne-port.md              — /aeriadne-port slash command
#   commands/aeriadne-package.md           — /aeriadne-package slash command
#   commands/aeriadne-validate.md          — /aeriadne-validate slash command
#
# Canonical source: Plugins/Aeriadne/ in Somnus-Intellligence-Stack
# OpenCode does not consume plugin.json — projection is via agents/ and commands/.

set -euo pipefail

SCOPE="${1:-project}"

if [ "$SCOPE" = "global" ]; then
    TARGET="$HOME/.config/opencode"
else
    TARGET="$PWD/.opencode"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Aeriadne OpenCode adapter install"
echo "  scope  : $SCOPE"
echo "  target : $TARGET"
echo "  source : $SCRIPT_DIR"
echo ""

# Create target directories
mkdir -p "$TARGET/agents"
mkdir -p "$TARGET/commands"

# ── Agents ──────────────────────────────────────────────────────────────────

install_agent() {
    local src="$1"
    local name="$2"
    if [ ! -f "$src" ]; then
        echo "  ERROR: source file not found: $src" >&2
        exit 1
    fi
    echo "  -> agents/$name"
    cp "$src" "$TARGET/agents/$name"
}

install_agent "$SCRIPT_DIR/agents/aeriadne-cpf.md"                  "aeriadne-cpf.md"
install_agent "$SCRIPT_DIR/agents/aeriadne-mop.md"                  "aeriadne-mop.md"
install_agent "$SCRIPT_DIR/agents/aeriadne-prompt-architect.md"     "aeriadne-prompt-architect.md"
install_agent "$SCRIPT_DIR/agents/aeriadne-package-cartographer.md" "aeriadne-package-cartographer.md"
install_agent "$SCRIPT_DIR/agents/aeriadne-registry-scribe.md"      "aeriadne-registry-scribe.md"
install_agent "$SCRIPT_DIR/agents/aeriadne-release-sentinel.md"     "aeriadne-release-sentinel.md"
install_agent "$SCRIPT_DIR/agents/aeriadne-compatibility-auditor.md" "aeriadne-compatibility-auditor.md"

# ── Commands ─────────────────────────────────────────────────────────────────

install_cmd() {
    local src="$1"
    local name="$2"
    if [ ! -f "$src" ]; then
        echo "  ERROR: source file not found: $src" >&2
        exit 1
    fi
    echo "  -> commands/$name"
    cp "$src" "$TARGET/commands/$name"
}

install_cmd "$SCRIPT_DIR/commands/aeriadne-cpf.md"      "aeriadne-cpf.md"
install_cmd "$SCRIPT_DIR/commands/aeriadne-audit.md"    "aeriadne-audit.md"
install_cmd "$SCRIPT_DIR/commands/aeriadne-port.md"     "aeriadne-port.md"
install_cmd "$SCRIPT_DIR/commands/aeriadne-package.md"  "aeriadne-package.md"
install_cmd "$SCRIPT_DIR/commands/aeriadne-validate.md" "aeriadne-validate.md"

# ── Post-install verification ──────────────────────────────────────────────────

verify_installed() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo "  ERROR: missing after copy: $file" >&2
        exit 1
    fi
}

verify_installed "$TARGET/agents/aeriadne-cpf.md"
verify_installed "$TARGET/agents/aeriadne-mop.md"
verify_installed "$TARGET/commands/aeriadne-cpf.md"
verify_installed "$TARGET/commands/aeriadne-audit.md"

echo "  Verification passed — all checked files present."
echo ""
echo "Installation complete."
echo ""
echo "Restart OpenCode to load the new agents and commands."
echo ""
echo "Verification:"
echo "  In OpenCode TUI, type @ and confirm aeriadne-cpf and aeriadne-mop appear."
echo "  In OpenCode TUI, type / and confirm /aeriadne-cpf and /aeriadne-audit appear."
echo ""
echo "Canonical source (do not edit installed files directly):"
echo "  $SCRIPT_DIR"
