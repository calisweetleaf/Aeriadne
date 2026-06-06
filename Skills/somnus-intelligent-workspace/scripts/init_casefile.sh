#!/bin/bash
# SSDS Casefile Initialization Script
# Usage: ./init_casefile.sh [DATE] [TARGET_ID]
# Example: ./init_casefile.sh 20260510 XZ_BACKDOOR
#
# Creates the full casefile directory structure for a new investigation.
# Can be run by any agent via bash tool, or manually by the operator.

set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Usage: $0 <DATE_YYYYMMDD> <TARGET_ID>"
    echo "Example: $0 20260510 XZ_BACKDOOR"
    exit 1
fi

DATE="$1"
TARGET="$2"
CASE_ID="SSDS-SIC-${DATE}-${TARGET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
CASE_DIR="${WORKSPACE_DIR}/casefiles/${CASE_ID}"

if [ -d "$CASE_DIR" ]; then
    echo "[ERROR] Casefile already exists: ${CASE_DIR}"
    echo "        Use a different TARGET_ID or check existing casefiles."
    exit 1
fi

echo "[SSDS] Initializing casefile: ${CASE_ID}"
echo "[SSDS] Location: ${CASE_DIR}"

# Create directory structure
mkdir -p "${CASE_DIR}/evidence/artifacts"
mkdir -p "${CASE_DIR}/evidence/screenshots"
mkdir -p "${CASE_DIR}/evidence/transcripts"
mkdir -p "${CASE_DIR}/analysis"
mkdir -p "${CASE_DIR}/sources"

# Copy SIC template
if [ -f "${WORKSPACE_DIR}/assets/ssds_sic_template.md" ]; then
    cp "${WORKSPACE_DIR}/assets/ssds_sic_template.md" "${CASE_DIR}/SIC.md"
    # Stamp the case ID and timestamps
    sed -i "s/\[YYYYMMDD\]-\[TARGET_ID\]/${DATE}-${TARGET}/g" "${CASE_DIR}/SIC.md"
    sed -i "s/\[UTC_DATETIME\]/$(date -u '+%Y-%m-%d %H:%M:%S UTC')/g" "${CASE_DIR}/SIC.md"
    echo "[SSDS] SIC template initialized: SIC.md"
else
    echo "[WARN] SIC template not found at ${WORKSPACE_DIR}/assets/ssds_sic_template.md"
    echo "       SIC.md will need to be created manually."
fi

# Initialize evidence hash manifest
echo "# SSDS Evidence Hash Manifest — ${CASE_ID}" > "${CASE_DIR}/evidence/hashes.sha256"
echo "# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "${CASE_DIR}/evidence/hashes.sha256"
echo "# Format: SHA256_HASH  FILENAME" >> "${CASE_DIR}/evidence/hashes.sha256"
echo "" >> "${CASE_DIR}/evidence/hashes.sha256"
echo "[SSDS] Evidence manifest initialized: evidence/hashes.sha256"

# Initialize source matrix
cat > "${CASE_DIR}/sources/source_matrix.md" << 'EOF'
# SOURCE MATRIX — Admiralty Code Grading

| SOURCE ID | DESCRIPTION | RELIABILITY (A-F) | CREDIBILITY (1-6) | CONFLICT? | NOTES |
|:---|:---|:---|:---|:---|:---|
| | | | | | |
EOF
echo "[SSDS] Source matrix initialized: sources/source_matrix.md"

# Initialize analysis stubs
echo "# Temporal Intelligence Matrix (TIM) — ${CASE_ID}" > "${CASE_DIR}/analysis/tim.md"
echo "# Information Topology Map — ${CASE_ID}" > "${CASE_DIR}/analysis/topology.md"
echo "# Threat Actor Profile — ${CASE_ID}" > "${CASE_DIR}/analysis/actor_profile.md"
echo "# Incentive Matrix (Cui Bono) — ${CASE_ID}" > "${CASE_DIR}/analysis/incentive_matrix.md"
echo "# Contradiction Log — ${CASE_ID}" > "${CASE_DIR}/analysis/contradiction_log.md"
echo "# Scenario Analysis (Alpha/Beta/Gamma) — ${CASE_ID}" > "${CASE_DIR}/analysis/scenarios.md"
echo "[SSDS] Analysis stubs initialized."

# Initialize collection gaps
echo "# Collection Gaps & Open Intelligence Requirements — ${CASE_ID}" > "${CASE_DIR}/collection_gaps.md"
echo "" >> "${CASE_DIR}/collection_gaps.md"
echo "## Tool/Capability Limitations" >> "${CASE_DIR}/collection_gaps.md"
echo "" >> "${CASE_DIR}/collection_gaps.md"
echo "## Open Intelligence Requirements (OIRs)" >> "${CASE_DIR}/collection_gaps.md"
echo "" >> "${CASE_DIR}/collection_gaps.md"
echo "1. *OIR-1:* [Pending]" >> "${CASE_DIR}/collection_gaps.md"
echo "[SSDS] Collection gaps register initialized."

echo ""
echo "[SSDS] ══════════════════════════════════════════════"
echo "[SSDS] Casefile ${CASE_ID} initialized successfully."
echo "[SSDS] ══════════════════════════════════════════════"
echo ""
echo "Structure:"
find "${CASE_DIR}" -type f | sort | sed "s|${CASE_DIR}/|  |"
