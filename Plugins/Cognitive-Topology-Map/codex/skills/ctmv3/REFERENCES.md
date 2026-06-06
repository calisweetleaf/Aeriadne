# REFERENCES.md — CTMv3 Cognitive Document Pointers

This skill package is the Codex adapter layer for CTMv3. The full cognitive documentation
set lives in the shared templates directory of the plugin and in the original source.

---

## Where the Full CTMv3 Docs Live

### Plugin templates (canonical for this installation)

```
/agent/workspace/ctmv3-plugin/core/templates/
+-- TOPOLOGY.md.template           <- Domain topology construction template
+-- FAILURE_GRAMMAR.md.template    <- Failure taxonomy template
+-- ARCHITECTURE_MAP.md.template   <- Traversal map construction template
+-- PROVENANCE.md.template         <- Decision log and session log template
+-- AGENTS.md.template             <- Agent operational posture template
+-- CLAUDE.md.template             <- Claude Code context template
```

Post-install, these templates are also available via:
```
~/.codex/skills/ctmv3/../../../  (if installed globally)
```

### Source docs (authoritative originals)

The CTMv3 source documentation is at `/agent/workspace/ctmv3-source/` (development path)
or wherever the ctmv3 package was cloned. Key files:

| File | Purpose |
|------|---------|
| `EXPLANATION.md` | What CTMv3 actually is (not a skill maker) |
| `SKILL.md` | The sovereign-skill-architect entry point and semantic router |
| `BOOT_PROTOCOL.md` | Session state machine: cold vs warm entry |
| `DOT_TOPOLOGY.md` | .xyz directories as topology signals |
| `AGENTS_ADDENDUM.md` | How to integrate CTMv3 into AGENTS.md |
| `TOPOLOGY.md` | Domain topology template and construction guide |
| `FAILURE_GRAMMAR.md` | Failure taxonomy template |
| `CONSTITUTION.md` | Development philosophy layer |
| `STYLE.md` | Code standards layer |
| `ARCHITECTURE_MAP_TEMPLATE.md` | Traversal map construction protocol |
| `PROVENANCE.md` | Decision log template |

---

## Document Load Order (Quick Reference)

For any repo entry task, load in this order:

1. BOOT_PROTOCOL.md -- always first, determines cold vs warm branch
2. If cold: TOPOLOGY.md, then FAILURE_GRAMMAR.md, then ARCHITECTURE_MAP_TEMPLATE.md
3. If warm: PROVENANCE.md (Session Log), then TOPOLOGY.md for the relevant section
4. DOT_TOPOLOGY.md -- when .xyz directory work is in scope
5. AGENTS_ADDENDUM.md -- when building AGENTS.md or Codex onboarding artifacts

Never load all documents upfront. The semantic router in SKILL.md governs which
documents are relevant to the current task type.

---

## Installed Skill Location

After running `install.sh`, this skill lives at:

```
~/.codex/skills/ctmv3/
+-- SKILL.md
+-- REFERENCES.md        <- this file
+-- agents/
|   +-- openai.yaml
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

The Python engine (`python3 -m ctmv3`) must be installed separately.
See the main README.md for install instructions.
