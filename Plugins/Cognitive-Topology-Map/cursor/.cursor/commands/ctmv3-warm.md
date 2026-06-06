---
description: Warm session resume — read PROVENANCE.md, validate topology currency, and run targeted archaeology on drifted areas. Use at the start of any session in an already-activated repo.
---

Warm session resume. Reads PROVENANCE.md, validates the topology fingerprint, and
reports whether the session state is valid for continuation. Does not rebuild from
scratch — targets the delta only.

Use this command at the start of any work session in a repo where CTMv3 has already
been run (i.e. `/ctmv3-boot` returned WARM_START).

## Invocation

```bash
python3 -m ctmv3 warm --json --project-root "$PWD"
```

## What the engine checks

1. Is the boot branch WARM_START? (Fails fast if COLD_START — recommends activate.)
2. Is session_state.json readable and not older than 30 days?
3. Does the stored fingerprint match the current TOPOLOGY.md + ARCHITECTURE_MAP.md?

## Interpreting the result

- `warm_valid: true`, `fingerprint_matches: true` — topology is current. Continue
  with the task. Load AGENTS.md and PROVENANCE.md Session Log for context.
- `warm_valid: true`, `fingerprint_matches: false` — topology has drifted since the
  last session. Run `/ctmv3-fingerprint` to capture the new hash, then investigate
  what changed in TOPOLOGY.md or ARCHITECTURE_MAP.md.
- `warm_valid: false` — session state is stale or missing. Run targeted archaeology
  per BOOT_PROTOCOL.md Section 3.2 before proceeding.

## After resuming

Read the last Session Log entry in PROVENANCE.md and the `open_tasks` list in
`.sovereign/session_state.json` to know exactly where the previous session ended.
