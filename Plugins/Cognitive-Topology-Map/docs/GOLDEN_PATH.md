# GOLDEN_PATH.md — The Orchestration Doctrine

**Authority**: This document governs how the CTMv3 orchestration layer thinks about
command sequencing, pre-chaining, and memory signal emission.

**Scope**: The `ctmv3 chain` subcommand, the `orchestration.py` module, and every
host adapter (Claude Code, Codex, opencode, Gemini CLI, Cursor) that consumes
golden-path signals.

---

## What the Golden Path Is

The golden path is not a flowchart. A flowchart implies that every branch is designed
in advance, that the orchestrator knows the destination, and that the agent's job is to
follow the arrows. That model breaks under real-world codebase conditions where the
cold-vs-warm branch is unknown at invocation time.

The golden path is a domino run. Each domino, when it falls, tips the next one. The
orchestration layer does not know in advance which domino is last — it only knows which
domino is next, derived from the one that just fell. When no next domino exists, the
chain is done.

This is the key distinction: pre-chain rules are *local*, not *global*. Each rule takes
`(current_command, exit_state)` and returns `Optional[next_command]`. The chain emerges
from the composition of local rules, not from a master plan.

Why this matters: it makes the chain robust to novel states. If `fingerprint` returns a
state I have never seen, the rule returns `None` (terminal) rather than routing blindly
into a wrong branch. Fail-safe by default.

---

## The Chain Spine

The canonical golden-path spine for a new or re-entered repo:

```
boot
  |
  |-- COLD_START --> activate --> fingerprint --> session-close
  |                                   |
  |                              drift_detected --> architecture-map --> session-close
  |
  |-- WARM_START --> warm --> fingerprint --> session-close
  |                               |
  |                          drift_detected --> architecture-map --> session-close
  |
  |-- PARTIAL --> activate --> fingerprint --> session-close
```

ASCII form of the full domino chain:

```
[boot]
   |
   | COLD_START
   v
[activate] ----success----> [fingerprint] ----no_drift----> [session-close]
                                  |
                            drift_detected
                                  |
                                  v
                          [architecture-map] --success--> [session-close]

[boot]
   |
   | WARM_START
   v
[warm] ----success----> [fingerprint] ----no_drift----> [session-close]
                               |
                         drift_detected
                               |
                               v
                       [architecture-map] --success--> [session-close]
```

The session-close domino is always terminal. It updates PROVENANCE.md and anchors
the session state. Nothing chains after it by design: closing the session is
the final write.

---

## Pre-Chain Rules

Pre-chain rules are pure functions. They take `(command: str, exit_state: str)` and
return `Optional[str]`. No I/O. No side effects. No model calls. This makes them fast
to evaluate and safe to call in any context.

The rules are encoded as a lookup table in `orchestration.py`. Key properties:

1. **Local**: each rule knows only the immediately completed command and its state.
2. **Conservative**: unknown `(command, exit_state)` pairs return `None` (terminal),
   not an arbitrary guess.
3. **Suggestive, not coercive**: the host adapter that reads the signal SHOULD follow
   the suggestion, but nothing forces it. An agent that ignores golden-path signals
   loses flow efficiency; it does not break.

The spine encoded in the current rule table:

| Current command    | Exit state      | Next suggested     |
|--------------------|-----------------|-------------------|
| boot               | COLD_START      | activate          |
| boot               | WARM_START      | warm              |
| boot               | PARTIAL         | activate          |
| boot               | success         | warm              |
| boot               | failure         | (terminal)        |
| activate           | success         | fingerprint       |
| activate           | failure         | (terminal)        |
| warm               | success         | fingerprint       |
| warm               | failure         | (terminal)        |
| fingerprint        | drift_detected  | architecture-map  |
| fingerprint        | no_drift        | session-close     |
| fingerprint        | success         | session-close     |
| fingerprint        | failure         | (terminal)        |
| architecture-map   | success         | session-close     |
| architecture-map   | skipped         | session-close     |
| architecture-map   | failure         | (terminal)        |
| session-close      | success         | (terminal)        |
| session-close      | failure         | (terminal)        |
| sovereign-init     | success         | dot-init          |
| sovereign-init     | failure         | (terminal)        |
| dot-init           | success         | fingerprint       |
| dot-init           | failure         | (terminal)        |
| status             | success         | (terminal)        |

---

## Memory Surfacing Tags

Every `GoldenPathSignal` carries a `memory_relevance_tags` list. These tags are
emitted at the moment a command completes, before any memory system has been consulted.
They are derived purely from `(command, exit_state)` — no file reads, no model calls.

What they enable:

- A memory system operating outside the subprocess boundary can index the command
  output by listening for the signal envelope on stdout.
- Retrieval systems can use the tags to decide whether a past activation is relevant
  to the current session without re-running the command.
- Agents can weight their context window by tag density: a signal tagged with both
  `cold_start` and `phase_0_required` is higher priority than one tagged with only
  `session_resumed`.

Example tags for the most common states:

| Command + state              | Tags                                                      |
|------------------------------|-----------------------------------------------------------|
| boot / COLD_START            | activation, cold_start, phase_0_required, no_tier1_signals |
| boot / WARM_START            | activation, warm_start, tier1_signals_present, provenance_valid |
| activate / success           | activation, phase_0_5_complete, all_artifacts_written, repo_live |
| fingerprint / drift_detected | topology, fingerprint_drift, architecture_map_stale       |
| fingerprint / no_drift       | topology, fingerprint_stable, no_drift                    |
| session-close / success      | session, close_complete, provenance_updated, state_anchored |

The full table is in `docs/interfaces/orchestration.md`.

---

## The Signal Envelope Contract

Every subcommand emits exactly one signal to stdout after completing. The format is
a single line beginning with the sentinel prefix:

```
[CTMV3_GOLDEN_PATH] {"command_name":"boot","command_status":"COLD_START","next_command_suggested":"activate","memory_relevance_tags":["activation","cold_start","phase_0_required","no_tier1_signals"],"payload":{...},"chain_depth":0}
```

Properties of the envelope:
- Single line: grep-safe in all shell environments.
- Compact JSON (no pretty-printing): minimal stdout pollution.
- Sentinel prefix: unambiguous extraction by `grep '[CTMV3_GOLDEN_PATH]'`.
- Emitted after all human-readable output (which goes to stderr): the two streams
  do not interleave under normal operation.
- Suppressed by `--no-golden-path`: escape hatch for environments that do not want
  the envelope (e.g. nested subprocess calls during `ctmv3 chain`).

The full JSON schema is in `docs/interfaces/orchestration.md`.

---

## How an Orchestrator Should Consume Signals

For external orchestrators (Claude Code, Codex, opencode, Gemini CLI, Cursor):

1. Invoke `ctmv3 <command> --json` and capture stdout.
2. Split stdout lines. Any line beginning with `[CTMV3_GOLDEN_PATH]` is a signal
   envelope. Strip the prefix and parse as JSON.
3. All other stdout lines are the machine-readable command output (`--json` mode).
4. Read `next_command_suggested`. If non-null, consider running that command next
   with the same `--project-root`. This is a suggestion, not a requirement.
5. Use `memory_relevance_tags` to decide whether to surface this output into the
   model's memory context.
6. For the `ctmv3 chain` subcommand, stdout is a JSON array of all signals from
   the full chain run. Each element is a signal dict with `chain_depth` indicating
   its step index.

Pseudocode:

```python
import subprocess, json

lines = subprocess.check_output(["python3", "-m", "ctmv3", "boot", "--json",
                                  "--project-root", "/path/to/repo"]).decode().splitlines()
SENTINEL = "[CTMV3_GOLDEN_PATH]"
signals = []
json_lines = []
for line in lines:
    if line.startswith(SENTINEL):
        signals.append(json.loads(line[len(SENTINEL):].strip()))
    else:
        json_lines.append(line)

signal = signals[0] if signals else None
if signal and signal["next_command_suggested"]:
    print(f"Orchestrator: suggested next command is {signal['next_command_suggested']!r}")
```

For the full chain in one call:

```bash
python3 -m ctmv3 chain --initial boot --project-root /path/to/repo
```

Stdout is a JSON array. Each element is one step. Signals are also emitted
individually as the chain progresses (under the sentinel prefix, one per step).

---

## Safety Properties

- `MAX_CHAIN_DEPTH = 5` prevents cycles from running indefinitely.
- `ChainTooLongError` is raised if the limit is hit; it is never silently swallowed.
- Each step in `chain()` runs as a separate subprocess. A failing step does not
  crash the chain runner — it produces a `failure` exit state and the chain
  terminates naturally (because no rule chains off failure for most commands).
- `--no-golden-path` suppresses all signal emission for the invocation. Used
  internally by `chain()` to prevent subprocess steps from double-emitting signals.
