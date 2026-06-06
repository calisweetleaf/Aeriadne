---
description: Walk the CTMv3 golden-path domino chain from an initial command. Executes commands in sequence per pre-chain rules until terminal. Output is a JSON array of GoldenPathSignal envelopes. One call handles the full boot-to-close run.
---

Walk the full golden-path domino chain starting from an initial command.

This is the entry point for fully autonomous repo onboarding. One call handles
the full run: boot determines cold vs warm, routes to activate or warm, fingerprint
detects drift, architecture-map updates if needed, session-close anchors the state.

## Invocation

```bash
# Full chain from boot (most common usage)
python3 -m ctmv3 chain --initial boot --project-root "$PWD"

# Start from activate (if boot state is already known to be COLD_START)
python3 -m ctmv3 chain --initial activate --project-root "$PWD"

# Start from warm (if boot state is already known to be WARM_START)
python3 -m ctmv3 chain --initial warm --project-root "$PWD"
```

## Output

Stdout is a JSON array of GoldenPathSignal envelopes — one per step:

```json
[
  {
    "command_name": "boot",
    "command_status": "COLD_START",
    "next_command_suggested": "activate",
    "memory_relevance_tags": ["activation", "cold_start", "phase_0_required"],
    "payload": { "branch": "COLD_START", ... },
    "chain_depth": 0
  },
  {
    "command_name": "activate",
    "command_status": "success",
    "next_command_suggested": "fingerprint",
    ...
    "chain_depth": 1
  },
  ...
]
```

As each step completes, a golden-path signal line is also emitted to stdout
under the `[CTMV3_GOLDEN_PATH]` sentinel prefix.

## Chain depth limit

The chain runs a maximum of 5 steps (MAX_CHAIN_DEPTH). The canonical cold-start
chain (boot → activate → fingerprint → architecture-map → session-close) is exactly
5 steps. The warm chain (boot → warm → fingerprint → session-close) is 4 steps.

If the chain exceeds 5 steps, ChainTooLongError is raised and the command exits
with code 2. This prevents cycles in the pre-chain rules from running indefinitely.

## Signal envelope contract

Each step emits a line to stdout:
```
[CTMV3_GOLDEN_PATH] {"command_name":"boot","command_status":"COLD_START",...}
```

External tools grep for `[CTMV3_GOLDEN_PATH]` to extract signals. The final JSON
array (the last thing written to stdout) is consumed by programmatic callers.
