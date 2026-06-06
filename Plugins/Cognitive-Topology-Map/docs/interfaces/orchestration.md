# Interface Reference: CTMv3 Orchestration Layer

**Module**: `ctmv3.core.orchestration`
**Path**: `core/ctmv3/core/orchestration.py`
**Dependencies**: Python stdlib only

This document is the technical contract for the golden-path orchestration layer.
For design philosophy and usage examples, see `docs/GOLDEN_PATH.md`.

---

## GoldenPathSignal Schema

```python
@dataclass
class GoldenPathSignal:
    command_name: str              # The CTMv3 subcommand that just completed
    command_status: str            # Semantic exit state (see Exit State Vocabulary)
    next_command_suggested: Optional[str]  # Next suggested command, or None if terminal
    memory_relevance_tags: List[str]       # Structured tags for memory system indexing
    payload: Dict                          # Command-output data; always JSON-serializable
    chain_depth: int               # Step index within chain() run (0 = initial command)
```

JSON envelope shape (as emitted by `emit_signal`):

```json
{
  "command_name": "boot",
  "command_status": "COLD_START",
  "next_command_suggested": "activate",
  "memory_relevance_tags": [
    "activation",
    "cold_start",
    "phase_0_required",
    "no_tier1_signals"
  ],
  "payload": {
    "project_root": "/path/to/repo",
    "branch": "COLD_START",
    "tier1_signals": [],
    "tier2_signals": [],
    "tier3_signals": ["pyproject.toml"],
    "provenance_present": false,
    "manifest_present": false,
    "last_session": null,
    "session_state_valid": false,
    "session_timestamp": null
  },
  "chain_depth": 0
}
```

---

## Exit State Vocabulary

Exit states are semantic tokens, not process exit codes. They are the values that
appear in `command_status` and drive `pre_chain_rules`.

| Exit State      | Produced by         | Meaning                                             |
|-----------------|---------------------|-----------------------------------------------------|
| COLD_START      | boot                | No Tier 1 CTMv3 signals found; full activation needed |
| WARM_START      | boot                | Tier 1 signals present; PROVENANCE.md readable      |
| PARTIAL         | boot                | Some Tier 1 signals present; PROVENANCE.md missing  |
| success         | activate, warm, sovereign-init, dot-init, session-close, status, fingerprint | Command completed without error |
| failure         | any                 | Command exited non-zero or threw                    |
| drift_detected  | fingerprint         | Stored hash differs from current computed hash      |
| no_drift        | fingerprint         | Stored hash matches current computed hash           |
| skipped         | architecture-map    | Existing ARCHITECTURE_MAP.md preserved (no --force) |

---

## Pre-Chain Rules Table

`pre_chain_rules(command: str, exit_state: str) -> Optional[str]`

| command          | exit_state      | next_command_suggested |
|------------------|-----------------|------------------------|
| boot             | COLD_START      | activate               |
| boot             | WARM_START      | warm                   |
| boot             | PARTIAL         | activate               |
| boot             | success         | warm                   |
| boot             | failure         | None (terminal)        |
| activate         | success         | fingerprint            |
| activate         | failure         | None (terminal)        |
| warm             | success         | fingerprint            |
| warm             | failure         | None (terminal)        |
| fingerprint      | drift_detected  | architecture-map       |
| fingerprint      | no_drift        | session-close          |
| fingerprint      | success         | session-close          |
| fingerprint      | failure         | None (terminal)        |
| architecture-map | success         | session-close          |
| architecture-map | skipped         | session-close          |
| architecture-map | failure         | None (terminal)        |
| session-close    | success         | None (terminal)        |
| session-close    | failure         | None (terminal)        |
| sovereign-init   | success         | dot-init               |
| sovereign-init   | failure         | None (terminal)        |
| dot-init         | success         | fingerprint            |
| dot-init         | failure         | None (terminal)        |
| status           | success         | None (terminal)        |
| status           | failure         | None (terminal)        |

Unknown `(command, exit_state)` pairs return `None` (terminal) without error.

---

## Memory Surface Tags by Command

`memory_surface_tags(command: str, exit_state: str, metadata: Optional[dict]) -> List[str]`

| command / state              | Tags                                                             |
|------------------------------|------------------------------------------------------------------|
| boot / COLD_START            | activation, cold_start, phase_0_required, no_tier1_signals      |
| boot / WARM_START            | activation, warm_start, tier1_signals_present, provenance_valid  |
| boot / PARTIAL               | activation, partial_state, tier1_incomplete, archaeology_needed  |
| boot / success               | activation, boot_complete                                        |
| boot / failure               | activation, boot_failed, diagnostic_needed                       |
| activate / success           | activation, phase_0_5_complete, all_artifacts_written, repo_live |
| activate / failure           | activation, activate_failed, artifact_incomplete                 |
| warm / success               | warm_start, topology_current, session_resumed                    |
| warm / failure               | warm_start, warm_invalid, partial_archaeology_needed             |
| fingerprint / drift_detected | topology, fingerprint_drift, architecture_map_stale              |
| fingerprint / no_drift       | topology, fingerprint_stable, no_drift                           |
| fingerprint / success        | topology, fingerprint_written                                    |
| fingerprint / failure        | topology, fingerprint_failed                                     |
| architecture-map / success   | architecture, map_updated, topology_traversal_ready              |
| architecture-map / skipped   | architecture, map_skipped, existing_preserved                    |
| architecture-map / failure   | architecture, map_failed                                         |
| session-close / success      | session, close_complete, provenance_updated, state_anchored      |
| session-close / failure      | session, close_failed, state_potentially_stale                   |
| sovereign-init / success     | sovereign, initialized, session_anchor_ready                     |
| sovereign-init / failure     | sovereign, init_failed                                           |
| dot-init / success           | ecosystem, dot_dirs_initialized, adapters_ready                  |
| dot-init / failure           | ecosystem, dot_init_failed                                       |
| status / success             | diagnostic, status_read, signal_inventory_current                |
| status / failure             | diagnostic, status_failed                                        |

Metadata-derived enrichment tags (appended if `metadata` is non-null):

- `project_<name>` — if `metadata["project_name"]` is present (lowercased, spaces to underscores)
- `fingerprint_<first16>` — if `metadata["fingerprint"]` is present (first 16 chars of hash)
- `has_errors` — if `metadata["errors"]` is a non-empty list

---

## Sentinel Prefix Specification

```
SIGNAL_SENTINEL = "[CTMV3_GOLDEN_PATH]"
```

Emission format:

```
[CTMV3_GOLDEN_PATH] <compact-json-no-spaces>
```

Rules:
- Single line terminated by newline.
- Compact JSON: `json.dumps(envelope, separators=(',', ':'))`. No indentation, no spaces.
- Emitted to stdout (not stderr) after all other stdout output for the command.
- Only one signal per command invocation.
- Suppressed when `--no-golden-path` is passed.

Extraction recipe (bash):

```bash
python3 -m ctmv3 boot --json --project-root "$PWD" \
  | grep '^\[CTMV3_GOLDEN_PATH\]' \
  | sed 's/^\[CTMV3_GOLDEN_PATH\] //' \
  | python3 -m json.tool
```

Extraction recipe (Python):

```python
SENTINEL = "[CTMV3_GOLDEN_PATH]"
signals = [
    json.loads(line[len(SENTINEL):].strip())
    for line in output.splitlines()
    if line.startswith(SENTINEL)
]
```

---

## CLI Usage

### Single command with golden-path signal

```bash
python3 -m ctmv3 boot --json --project-root /path/to/repo
```

Stderr: human-readable discovery output.
Stdout: JSON signal inventory + one sentinel line at the end.

### Chain: full domino run from boot

```bash
python3 -m ctmv3 chain --initial boot --project-root /path/to/repo
```

Stdout: JSON array of all GoldenPathSignal dicts, one per step.
Each step also emits a sentinel line as it completes.

### Suppress signal emission

```bash
python3 -m ctmv3 boot --json --project-root /path/to/repo --no-golden-path
```

No sentinel line emitted. Use in pipelines or environments that parse stdout strictly.

---

## Sample stdout: full chain run

```
[CTMV3_GOLDEN_PATH] {"command_name":"boot","command_status":"COLD_START","next_command_suggested":"activate","memory_relevance_tags":["activation","cold_start","phase_0_required","no_tier1_signals"],"payload":{"project_root":"/tmp/my-repo","branch":"COLD_START","tier1_signals":[],"tier2_signals":[],"tier3_signals":["pyproject.toml"],"provenance_present":false,"manifest_present":false,"last_session":null,"config_spine":{"pyproject.toml":true},"session_state_valid":false,"session_timestamp":null,"returncode":0},"chain_depth":0}
[CTMV3_GOLDEN_PATH] {"command_name":"activate","command_status":"success","next_command_suggested":"fingerprint","memory_relevance_tags":["activation","phase_0_5_complete","all_artifacts_written","repo_live"],"payload":{"project_name":"my-repo","phase":"complete","fingerprint":"sha256:abc123...","files_written":{"AGENTS.md":"written","ARCHITECTURE_MAP.md":"written"},"errors":[],"returncode":0},"chain_depth":1}
[CTMV3_GOLDEN_PATH] {"command_name":"fingerprint","command_status":"no_drift","next_command_suggested":"session-close","memory_relevance_tags":["topology","fingerprint_stable","no_drift"],"payload":{"fingerprint_path":"/tmp/my-repo/.sovereign/topology_fingerprint.txt","hash":"sha256:abc123...","matches":true,"drift_detected":false,"returncode":0},"chain_depth":2}
[CTMV3_GOLDEN_PATH] {"command_name":"session-close","command_status":"success","next_command_suggested":null,"memory_relevance_tags":["session","close_complete","provenance_updated","state_anchored"],"payload":{"agent":"unknown","action":"session close","topology_drift":false,"fingerprint":"sha256:abc123...","provenance_updated":true,"session_state_updated":true,"returncode":0},"chain_depth":3}
[
  {
    "command_name": "boot",
    "command_status": "COLD_START",
    ...
  },
  ...
]
```

(The sentinel lines are emitted one per step as each subprocess completes. The final JSON array is the stdout of `ctmv3 chain`.)

---

## How to Write a New Pre-Chain Rule

1. Identify the new `(command, exit_state)` pair you want to route.
2. Add an entry to `_CHAIN_TABLE` in `orchestration.py`:

```python
("my-command", "my-exit-state"): "next-command-name",
```

3. If the new exit state is terminal:

```python
("my-command", "my-exit-state"): None,
```

4. Update the pre-chain rules table in this document.
5. Write a test that calls `pre_chain_rules("my-command", "my-exit-state")` and asserts
   the expected return value.

No other changes are needed. `pre_chain_rules` is a pure lookup — adding a table entry
is sufficient.

---

## How to Add a New Memory Tag

1. Add an entry to `_MEMORY_TAG_TABLE` in `orchestration.py`:

```python
("my-command", "my-exit-state"): ["tag_a", "tag_b", "tag_c"],
```

2. Tag convention: `category_dimension_value`, all lowercase, underscores for spaces.
   Examples: `activation`, `cold_start`, `phase_0_required`, `fingerprint_stable`.

3. Update the memory surface tags table in this document.

4. Tags are appended (not replaced) with metadata-derived enrichment if `metadata` is
   provided. Enrichment logic lives in `memory_surface_tags()`. To add a new enrichment
   pattern, add a conditional block after the base tag lookup.

---

## ChainTooLongError

```python
class ChainTooLongError(Exception):
    depth: int        # The step count when the error was raised
    last_command: str # The command that would have been step depth+1
```

Raised by `chain()` when `depth >= MAX_CHAIN_DEPTH`. Indicates either a cycle in
the pre-chain rules or a workflow that genuinely requires more than 5 steps.

To increase the limit:
```python
import ctmv3.core.orchestration as orch
orch.MAX_CHAIN_DEPTH = 8
```

This is a module-level integer; setting it before calling `chain()` takes effect
immediately. The default of 5 covers the full canonical spine (boot → activate →
fingerprint → architecture-map → session-close) with one step to spare.

---

## Constants

| Name            | Value                 | Purpose                                              |
|-----------------|----------------------|------------------------------------------------------|
| MAX_CHAIN_DEPTH | 5                    | Maximum steps before ChainTooLongError is raised     |
| SIGNAL_SENTINEL | `[CTMV3_GOLDEN_PATH]` | Prefix for golden-path signal lines on stdout        |
