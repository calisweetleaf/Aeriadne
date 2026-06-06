---
description: Recompute topology_fingerprint.txt — the SHA-256 hash of TOPOLOGY.md + ARCHITECTURE_MAP.md. Detects topology drift since the last session close.
---

Recompute and write `.sovereign/topology_fingerprint.txt`.

The fingerprint is the SHA-256 hash of TOPOLOGY.md + ARCHITECTURE_MAP.md concatenated.
It is the verification anchor for warm-start validity: if the stored hash differs from
the current hash at session start, topology has drifted and the architecture map may
be stale.

## Invocation

```bash
python3 -m ctmv3 fingerprint --json --project-root "$PWD"
```

## Interpreting the result

- `drift_detected: false` — topology matches the last session. No update needed.
- `drift_detected: true` — topology has changed since last session close. Review
  TOPOLOGY.md and ARCHITECTURE_MAP.md changes. Consider running `/ctmv3-architecture-map`
  to update the traversal map.

## When to run this

- After `/ctmv3-activate` completes the topology build.
- After any edit to TOPOLOGY.md or ARCHITECTURE_MAP.md.
- After `/ctmv3-warm` reports `fingerprint_matches: false`.
- As part of `/ctmv3-session-close` (the close command runs fingerprint automatically).

The golden-path chain runs this step automatically after activate or warm.
