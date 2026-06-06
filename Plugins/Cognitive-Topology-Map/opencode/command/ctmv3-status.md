---
description: Show current CTMv3 activation status for the project — what artifacts exist, session state, and health of the ecosystem.
agent: ctmv3-architect
subtask: true
---

Report the current CTMv3 activation status of the project. Shows which artifacts exist,
their approximate age, the last session state, and any health warnings. Read-only.

Use this to get a quick snapshot before starting work or to diagnose why a warm start
is failing.

## Invocation

```bash
python3 -m ctmv3 status --json --project-root "$PWD" $ARGUMENTS
```

## What gets reported

If engine is unavailable, run the checks manually:

```bash
# Tier 1 artifact presence
test -d .sovereign && echo ".sovereign: present" || echo ".sovereign: ABSENT"
test -f ARCHITECTURE_MAP.md && echo "ARCHITECTURE_MAP.md: present" || echo "ARCHITECTURE_MAP.md: ABSENT"
test -f AGENTS.md && echo "AGENTS.md: present" || echo "AGENTS.md: ABSENT"
test -f CLAUDE.md && echo "CLAUDE.md: present" || echo "CLAUDE.md: ABSENT"

# Tier 2 artifact presence
test -f TOPOLOGY.md && echo "TOPOLOGY.md: present" || echo "TOPOLOGY.md: ABSENT"
test -f FAILURE_GRAMMAR.md && echo "FAILURE_GRAMMAR.md: present" || echo "FAILURE_GRAMMAR.md: ABSENT"
test -f PROVENANCE.md && echo "PROVENANCE.md: present" || echo "PROVENANCE.md: ABSENT"

# Session state
cat .sovereign/session_state.json 2>/dev/null || echo "No session state"
```

## Status categories

FULLY_ACTIVATED — all Tier 1 artifacts present, session_state.json readable,
warm_start_valid = true, last session < 30 days.

ACTIVATED_STALE — Tier 1 artifacts present but session_state.json shows
warm_start_valid = false, or last session > 30 days. Recommend /ctmv3-warm.

PARTIAL — some Tier 1 artifacts present, others missing. List what is present
and absent. Recommend /ctmv3-activate --force to complete.

COLD — no Tier 1 artifacts. Recommend /ctmv3-activate.

CORRUPTED — Tier 1 artifacts present but session_state.json is malformed or
PROVENANCE.md Session Log is empty. Recommend /ctmv3-activate --force to reseed.

## Report back

State activation status in one line. List all artifacts found with presence/absence.
Summarize last session if available. Flag any health warnings. State the recommended
next command for the operator.
