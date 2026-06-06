---
description: Show CTMv3 activation status — signal inventory, boot branch, fingerprint match, last session, open tasks, and recommended next command. Read-only.
---

Show the current CTMv3 state for the repo. Read-only — writes nothing.

Useful as a diagnostic at any point in a session. Reports everything needed to
decide what CTMv3 action (if any) is appropriate next.

## Invocation

```bash
python3 -m ctmv3 status --json --project-root "$PWD"
```

## Output fields

- `branch`: COLD_START | WARM_START | PARTIAL
- `warm_valid`: whether the session state is within the 30-day warm window
- `fingerprint_matches`: whether TOPOLOGY.md + ARCHITECTURE_MAP.md match the stored hash
- `tier1_signals`: list of Tier 1 CTMv3 artifacts present
- `tier2_signals`: list of Tier 2 artifacts present
- `tier3_signals`: list of config spine files present
- `last_agent`: agent from the last session close
- `last_action`: action from the last session close
- `last_timestamp`: ISO timestamp of the last session close
- `open_tasks`: list of tasks flagged as open at the last session close

## Reading the status output

- COLD_START: no CTMv3 artifacts. Run `/ctmv3-activate`.
- WARM_START, warm_valid=true, fingerprint_matches=true: repo is fully current. Continue.
- WARM_START, fingerprint_matches=false: topology may have drifted. Run `/ctmv3-fingerprint`.
- WARM_START, warm_valid=false: session is stale. Run targeted archaeology or `/ctmv3-activate --force`.
- PARTIAL: incomplete artifact set. Run `/ctmv3-activate` to complete.
