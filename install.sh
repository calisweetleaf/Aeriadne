#!/usr/bin/env bash
# Aeriadne Marketplace Bootstrap
#
# This script initializes the Aeriadne marketplace on a local machine.
# It sets up the directory structure, validates the registry, and provides
# client-specific activation instructions.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/calisweetleaf/Aeriadne/main/install.sh | bash
#   (or local run)
#   bash install.sh

set -euo pipefail

# --- Configuration ---
REPO_NAME="Aeriadne"
REPO_URL="https://github.com/calisweetleaf/Aeriadne.git"
INSTALL_DIR="${HOME}/Repositories/Aeriadne"

echo "===================================================="
echo "   Aeriadne — Somnus Intelligence Marketplace"
echo "===================================================="
echo ""

# --- Discovery ---
if [ -d ".git" ] && [ "$(basename "$PWD")" == "${REPO_NAME}" ]; then
    echo "Running from within the Aeriadne repository."
    ROOT_DIR="$PWD"
else
    echo "Bootstrapping Aeriadne to ${INSTALL_DIR}..."
    if [ ! -d "${INSTALL_DIR}" ]; then
        git clone "${REPO_URL}" "${INSTALL_DIR}"
    else
        echo "Directory already exists, updating..."
        cd "${INSTALL_DIR}" && git pull
    fi
    ROOT_DIR="${INSTALL_DIR}"
fi

cd "${ROOT_DIR}"

# --- Structure Verification ---
echo "Verifying marketplace structure..."
for dir in Plugins Skills Agents Servers Registry Marketplace Core Docs; do
    if [ ! -d "$dir" ]; then
        echo "ERROR: Missing directory $dir"
        exit 1
    fi
done

# --- Aeriadne Package Validation ---
echo "Validating Aeriadne operator package..."
if python3 Plugins/Aeriadne/scripts/validate_package.py Plugins/Aeriadne >/dev/null; then
    echo "Aeriadne operator: VALID"
else
    echo "WARNING: Aeriadne operator package validation failed."
fi

# --- Client Activation ---

echo ""
echo "--- Activation Paths ---"

# 1. Codex
CODEX_PLUGINS_DIR="${HOME}/.codex/plugins"
if [ -d "${HOME}/.codex" ]; then
    echo "[Codex] detected at ${HOME}/.codex"
    mkdir -p "${CODEX_PLUGINS_DIR}"
    if [ ! -L "${CODEX_PLUGINS_DIR}/aeriadne" ]; then
        ln -s "${ROOT_DIR}/Plugins/Aeriadne" "${CODEX_PLUGINS_DIR}/aeriadne"
        echo "  - Aeriadne symlinked to Codex plugins."
    else
        echo "  - Aeriadne already symlinked to Codex."
    fi
fi

# 2. Gemini CLI Extension (CTMv3)
GEMINI_EXT_DIR="${HOME}/.gemini/extensions"
if [ -d "${HOME}/.gemini" ]; then
    echo "[Gemini CLI] detected at ${HOME}/.gemini"
    mkdir -p "${GEMINI_EXT_DIR}"
    if [ ! -d "${GEMINI_EXT_DIR}/ctmv3" ]; then
        cp -r "${ROOT_DIR}/Plugins/Cognitive-Topology-Map/gemini-cli/ctmv3" "${GEMINI_EXT_DIR}/ctmv3"
        echo "  - CTMv3 extension installed."
    else
        echo "  - CTMv3 extension already installed."
    fi
fi

echo ""
echo "===================================================="
echo "   Launch Complete — Aeriadne is Ready"
echo "===================================================="
echo ""
echo "Next steps:"
echo "  1. Restart your coding agent client."
echo "  2. Run 'Aeriadne' or 'CTMv3' commands."
echo "  3. Explore the registry: cat Registry/plugins.yaml"
echo ""
echo "For support: https://github.com/calisweetleaf/Aeriadne"
