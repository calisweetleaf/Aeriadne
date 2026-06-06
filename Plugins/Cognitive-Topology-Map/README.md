# CTMv3 Plugin — Cross-Runtime Workspace Activation System

**Version**: 1.2.0
**Operator**: Daeron
**Paradigm**: Workspace activation, not skill creation.
**Runtimes**: Claude Code, Codex, opencode, Gemini CLI, Cursor.

---

## What This Is

CTMv3 is **not a skill maker**. It is a **codebase activation system** whose
job is to enter a repo and make it living for agents — set up the topology,
install the agent-facing structure, create the right `.xyz` folders and files,
wire in hooks and workflow surfaces, establish memory/context/doctrine, and
leave the codebase in a state where an agent can actually work inside it
instead of guessing.

A skill may be one byproduct of a CTMv3 pass. The repo itself is the real output.

For the full philosophical framing read [`docs/EXPLANATION.md`](docs/EXPLANATION.md).

---

## What This Plugin Does (Operationally)

When invoked, the plugin runs the Python activation engine (`core/`) which:

1. **Inspects** the repo via the BOOT_PROTOCOL discovery sequence (read-only, <60s).
2. **Classifies** the boot state: COLD_START / WARM_START / PARTIAL.
3. **Builds** the missing CTMv3 artifacts: `TOPOLOGY.md`, `FAILURE_GRAMMAR.md`,
   `PROVENANCE.md`, `ARCHITECTURE_MAP.md`, `AGENTS.md`, `CLAUDE.md`.
4. **Scaffolds** the `.xyz` directories: `.sovereign/`, `.claude/`, `.codex/`,
   `.github/`.
5. **Seeds** golden paths in `.sovereign/golden_paths.json`.
6. **Fingerprints** `TOPOLOGY.md + ARCHITECTURE_MAP.md` via SHA-256 stored at
   `.sovereign/topology_fingerprint.txt` for drift detection.
7. **Logs** every action in `PROVENANCE.md` Session Log.

The cognitive layer (the CTMv3 source docs — BOOT_PROTOCOL, TOPOLOGY,
DOT_TOPOLOGY, FAILURE_GRAMMAR, etc.) ships with the plugin in `docs/` and
is referenced verbatim by each runtime adapter.

---

## Architecture

```
ctmv3-plugin/
├── core/                  Python activation engine (stdlib only)
│   ├── ctmv3/
│   │   ├── cli.py             python -m ctmv3 <command>
│   │   ├── boot.py            Discovery sequence
│   │   ├── activate.py        Cold-start orchestration
│   │   ├── fingerprint.py     SHA-256 drift detector
│   │   ├── sovereign.py       .sovereign/ management
│   │   ├── dot_init.py        .claude/, .codex/, .github/ scaffolders
│   │   ├── architecture_map.py
│   │   ├── templates.py       Template loader
│   │   └── orchestration.py   Golden-path routing layer (chain, pre-chain rules, memory tags)
│   └── tests/                 unittest suite (125 tests)
├── docs/                      Full CTMv3 cognitive doc set + GOLDEN_PATH.md + SCHEMA_AUDIT.md + interfaces/
├── claude-code/               Claude Code adapter (.claude-plugin/, commands/, hooks/, agents/, skills/)
├── codex/                     Codex adapter (skills/ctmv3/, config-fragments/, install.sh)
├── opencode/                  opencode adapter (agent/, command/, plugin/)
├── gemini-cli/                Gemini CLI adapter (ctmv3/gemini-extension.json, GEMINI.md)
├── cursor/                    Cursor adapter (.cursor/rules/ctmv3.mdc, .cursor/commands/, scripts/)
├── research/                  Cross-runtime format research (RUNTIME_FORMATS.md)
├── extras/                    Reference templates and worked examples
├── examples/                  Annotated traces (cold-start-trace.md, case_codebase_entry.md)
├── tests/                     End-to-end smoke tests
├── .github/workflows/         CI: validate, schema-check, release, topology-enforce
├── CODEBASE_INTELLIGENCE.md   Living architectural intelligence document
├── CONTRIBUTING.md            Extension protocol (templates, commands, adapters, tests)
└── LICENSE                    MIT
```

The plugin separates **knowledge** (docs/, extras/) from **execution**
(core/) from **adapters** (claude-code/, codex/, opencode/, gemini-cli/, cursor/).
Each adapter is a thin shim over `python3 -m ctmv3`. The orchestration layer
(`core/ctmv3/core/orchestration.py`) lets any adapter chain commands as
dominoes (boot → activate → fingerprint → architecture-map → session-close)
and emits memory-relevance signals on stdout under a sentinel prefix.

---

## Install

### 1. Install the engine (all runtimes need this)

```bash
# Option A: pip install from a checkout
cd ctmv3-plugin/core
pip install --user .

# Option B: add to PYTHONPATH
export PYTHONPATH="$PWD/ctmv3-plugin/core:$PYTHONPATH"

# Verify:
python3 -m ctmv3 version
```

### 2. Install one or more runtime adapters

See per-runtime install docs:

- **Claude Code**: [`claude-code/README.md`](claude-code/README.md)
- **Codex**: [`codex/README.md`](codex/README.md)
- **opencode**: [`opencode/README.md`](opencode/README.md)
- **Gemini CLI**: [`gemini-cli/README.md`](gemini-cli/README.md)
- **Cursor**: [`cursor/README.md`](cursor/README.md)

You can install multiple adapters side-by-side. They all delegate to the same
engine, so commands stay consistent across runtimes.

---

## Cross-Runtime Command Surface

| Command | Claude Code | Codex | opencode | Gemini CLI | Cursor |
|---------|-------------|-------|----------|------------|--------|
| Discovery scan | `/ctmv3:boot` | `$ctmv3 boot` | `/ctmv3-boot` | `ctmv3 boot` (via GEMINI.md trigger) | `/ctmv3-boot` |
| Cold-start activation | `/ctmv3:activate` | `$ctmv3 activate` | `/ctmv3-activate` | `ctmv3 activate` | `/ctmv3-activate` |
| Warm continue | `/ctmv3:warm` | `$ctmv3 warm` | `/ctmv3-warm` | `ctmv3 warm` | `/ctmv3-warm` |
| Build architecture map | `/ctmv3:architecture-map` | `$ctmv3 architecture-map` | `/ctmv3-architecture-map` | `ctmv3 architecture-map` | `/ctmv3-architecture-map` |
| Create .sovereign/ | `/ctmv3:sovereign-init` | `$ctmv3 sovereign-init` | `/ctmv3-sovereign-init` | `ctmv3 sovereign-init` | `/ctmv3-sovereign-init` |
| Create .xyz dirs | `/ctmv3:dot-init` | `$ctmv3 dot-init` | `/ctmv3-dot-init` | `ctmv3 dot-init` | `/ctmv3-dot-init` |
| Recompute fingerprint | `/ctmv3:fingerprint` | `$ctmv3 fingerprint` | `/ctmv3-fingerprint` | `ctmv3 fingerprint` | `/ctmv3-fingerprint` |
| Session close | `/ctmv3:session-close` | `$ctmv3 session-close` | `/ctmv3-session-close` | `ctmv3 session-close` | `/ctmv3-session-close` |
| Status snapshot | `/ctmv3:status` | `$ctmv3 status` | `/ctmv3-status` | `ctmv3 status` | `/ctmv3-status` |
| Golden-path chain | `/ctmv3:chain` | `$ctmv3 chain` | `/ctmv3-chain` | `ctmv3 chain` | `/ctmv3-chain` |

Under the hood, every invocation is `python3 -m ctmv3 <command> --project-root "$PWD"`.
The `chain` command walks the domino chain end-to-end with a single invocation
(see [`docs/GOLDEN_PATH.md`](docs/GOLDEN_PATH.md)).

---

## The Eight CTMv3 Outputs

A completed CTMv3 pass produces:

1. Agent can answer without asking: What are the 3 things I cannot get wrong?
2. Agent can recognize failure before it's provable.
3. Agent knows what was already rejected.
4. Agent knows where complexity concentrates.
5. Agent knows its entry vector.
6. Agent knows the boot state in <60 seconds.
7. Agent has a traversal map (ARCHITECTURE_MAP.md).
8. Codebase enforces itself via `.github/`, `.sovereign/`, AGENTS.md.

If any of these eight outputs is missing, the activation is incomplete.

---

## Constraints

- **Python 3.10+ stdlib only.** No external deps. Runs on Ryzen 5 12GB no-GPU
  consumer hardware. No GPU required, no cloud calls, no network.
- **Idempotent.** Running `activate` twice on the same repo does not corrupt
  state. Existing artifacts are preserved unless `--force` is passed.
- **No emojis** in any generated artifact.
- **First-person no-emoji documentation style** for all generated docs (per
  Daeron's standard).

---

## Documentation

- [`docs/EXPLANATION.md`](docs/EXPLANATION.md) — What CTMv3 actually is
- [`docs/SKILL.md`](docs/SKILL.md) — Semantic router and phase protocol
- [`docs/BOOT_PROTOCOL.md`](docs/BOOT_PROTOCOL.md) — State machine
- [`docs/TOPOLOGY.md`](docs/TOPOLOGY.md) — 7+1 nodes of domain topology
- [`docs/DOT_TOPOLOGY.md`](docs/DOT_TOPOLOGY.md) — `.xyz` directory encoding
- [`docs/ARCHITECTURE_MAP_TEMPLATE.md`](docs/ARCHITECTURE_MAP_TEMPLATE.md) — Traversal map protocol
- [`docs/FAILURE_GRAMMAR.md`](docs/FAILURE_GRAMMAR.md) — Failure taxonomy
- [`docs/PROVENANCE.md`](docs/PROVENANCE.md) — Decision log doctrine
- [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md) — Development philosophy
- [`docs/AGENTS_ADDENDUM.md`](docs/AGENTS_ADDENDUM.md) — Integration with AGENTS.md
- [`docs/GOLDEN_PATH.md`](docs/GOLDEN_PATH.md) — Orchestration spine and signal envelope contract
- [`docs/SCHEMA_AUDIT.md`](docs/SCHEMA_AUDIT.md) — Adapter assumption-to-canonical reconciliation
- [`docs/interfaces/orchestration.md`](docs/interfaces/orchestration.md) — Orchestration module interface reference
- [`docs/interfaces/python.md`](docs/interfaces/python.md) — Python engine interface reference
- [`research/RUNTIME_FORMATS.md`](research/RUNTIME_FORMATS.md) — Cross-runtime plugin format reference
- [`CODEBASE_INTELLIGENCE.md`](CODEBASE_INTELLIGENCE.md) — Living architectural intelligence document
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — How to extend templates, commands, adapters, tests
- [`examples/cold-start-trace.md`](examples/cold-start-trace.md) — Annotated cold-start activation walkthrough

---

## Lineage

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-08 | Initial CTM paradigm (TOPOLOGY, FAILURE_GRAMMAR, PROVENANCE, CONSTITUTION) |
| v2.0 | 2026-03-08 | Packaged multi-doc skill |
| v3.0 | 2026-05-11 | BOOT_PROTOCOL, DOT_TOPOLOGY, ARCHITECTURE_MAP_TEMPLATE; config spine; ecosystem failures |
| v3.0-plugin | 2026-05-23 | Cross-runtime plugin form (4 adapters) |
| v3.1-plugin | 2026-05-23 | Hardening pass: orchestration layer, Cursor adapter, schema audit, MIT LICENSE, CI workflows, codebase intelligence doc, engine hardening (logging, atomic writes, streaming SHA-256, scan bounds), 125-test suite |
| v1.2.0 | 2026-05-24 | SOTA++ Hardening Pass: Monorepo discovery, PROVENANCE.md log rotation, Python 3.12+ `datetime` compatibility, `tomllib` integration, 200+ tests, production CI matrix |

---

## License

MIT License. Copyright (c) 2026 Daeron. See [LICENSE](LICENSE) for the full text.
