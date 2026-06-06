# CHANGELOG

## v1.2.0 — 2026-05-24

SOTA++ Production Hardening Pass. Full engine maturity upgrade targeting monorepo support, robust parsing, logging, and comprehensive test coverage.

### Added
- Monorepo discovery: `boot.discover_all(project_root, max_depth)` implemented using `os.scandir` to find nested CTMv3 activations across complex repository structures.
- Structured logging (`logging.getLogger(__name__)`) added to `activate.py`, `dot_init.py`, and `architecture_map.py` to ensure all engine paths leave a trace.
- Session log rotation: `MAX_SESSION_LOG_ROWS = 500`. PROVENANCE.md session logs are now automatically rotated to `.sovereign/provenance_archive_{date}.md` when they grow too large, preventing unbounded file growth.
- 7 new test classes appended to `test_engine.py` (~500 new lines), pushing the test suite past 200 checks. Added CLI command tests, schema validations, and regression checks.
- Expanded GitHub Actions CI/CD matrix (`.github/workflows/validate.yml`) validating syntax, tests, test regression counts, and smoke tests across Python 3.10, 3.11, and 3.12.

### Changed
- `architecture_map.py` project name inference upgraded from naive line-scanner to `tomllib` (Python 3.11+) with optional `tomli` fallback (Python 3.10). Correctly parses complex `pyproject.toml` structures (Hatch, Poetry).
- Deprecated `datetime.utcnow()` removed across `boot.py`, `sovereign.py`, and `activate.py` in favor of timezone-aware `datetime.now(timezone.utc)` to support Python 3.12+ and 3.14 deprecation timelines.
- CLI exit codes formalized: `cmd_warm` now properly emits exit code 3 (missing prerequisite) on cold starts; `cmd_activate` emits exit code 2 on corrupt repo aborts; `cmd_fingerprint` exits 3 if run before topology exists.
- Claude Code `hooks.json` upgraded to handle exceptions explicitly rather than silently masking them with `2>/dev/null || true`.
- opencode plugin handler logic streamlined to natively use the `"session.created"` event key mapping.
- Engine version bumped to `1.2.0` in both `core/pyproject.toml` and `core/ctmv3/core/__init__.py`.

## v1.1.0 — 2026-05-23

Hardening pass. Tier 1 (schema reconciliation), Tier 3 (polish, docs, CI), and
Tier 4 (Cursor adapter, orchestration layer) shipped together.

### Added
- `core/ctmv3/core/orchestration.py` — golden-path routing layer. `GoldenPathSignal`
  dataclass, `pre_chain_rules` mapping (current_command, exit_state) to next
  suggested command, `memory_surface_tags` emitter, `emit_signal()` JSON-envelope
  sentinel writer (`[CTMV3_GOLDEN_PATH] {...}`), `chain()` domino executor
  bounded by `MAX_CHAIN_DEPTH = 5`. Stdlib only.
- `chain` CLI subcommand (`python -m ctmv3 chain --initial boot`) — walks the
  full domino chain from any initial command with a single invocation.
- `--no-golden-path` global flag — suppresses signal emission for environments
  that do not want it.
- Cursor adapter (`cursor/`) — Cursor Rules (`.mdc`), 10 slash commands, 10 bash
  wrappers, `install.sh`, `README.md`. Fifth supported runtime.
- `CODEBASE_INTELLIGENCE.md` — 15-section living architectural intelligence
  document (740 lines) covering executive summary, dependency graph, security
  assessment, technical debt register, recommended reading order, action items.
- `docs/SCHEMA_AUDIT.md` — adapter assumption-to-canonical reconciliation
  across all 5 adapters. Cites `research/RUNTIME_FORMATS.md` line by line.
- `docs/GOLDEN_PATH.md` — orchestration philosophy, chain spine ASCII diagram,
  pre-chain rules table, memory tags, signal envelope contract.
- `docs/interfaces/orchestration.md` — `GoldenPathSignal` schema, pre-chain
  rules table, memory tags table, sentinel spec, CLI usage, sample stdout.
- `examples/cold-start-trace.md` — fully annotated cold-start activation trace
  on a hypothetical Python+TS repo (646 lines, phases 0 through 5f).
- `LICENSE` — MIT, Copyright (c) 2026 Daeron.
- `CONTRIBUTING.md` — extension protocol (templates, commands, adapters,
  tests), style rules, commit conventions, PR review expectations.
- `.github/workflows/validate.yml` — matrix Python 3.10/3.11/3.12 running
  `tests/run-all.sh` on push and PR.
- `.github/workflows/schema-check.yml` — JSON syntax, TOML, bash, required-field
  validation for every adapter manifest.
- `.github/workflows/release.yml` — tag-triggered (`v*.*.*`) zip build and
  GitHub release artifact upload.
- `.github/workflows/topology-enforce.yml` — self-applied CTMv3 fingerprint
  drift check on the plugin's own critical docs.
- `extras/` — `README.md` and 4 worked reference templates
  (`AGENTS.example.md`, `golden_paths.example.json`,
  `topology-enforce.example.yml`, `CLAUDE.example.md`).
- 75 new unit tests covering hardening branches (50 → 125 tests).

### Changed
- Engine hardening pass across all 7 core modules (`activate.py`, `boot.py`,
  `fingerprint.py`, `sovereign.py`, `dot_init.py`, `architecture_map.py`,
  `templates.py`):
  - Structured stdlib `logging` throughout.
  - All file writes are atomic (write to `.tmp` then `os.replace`).
  - Input validation at every public boundary with `ValueError` carrying
    actionable context.
  - `fingerprint.compute` uses streaming SHA-256 (8 KiB chunks) instead of
    loading whole files into memory.
  - `boot.discover` enforces `MAX_SCAN_DEPTH` and `MAX_FILE_COUNT` bounds so
    runaway scans on giant repos cannot hang.
  - Specific exception types instead of bare `except Exception`; broad
    catches log with context and re-raise wrapped.
  - Fixed status-logic bug in `_scaffold_protected` and `_write_if_absent`.
  - Fixed separator-row detection bug in `_extract_last_session`.
  - `_detect_language` no longer returns a TODO string fallback.
- CLI handlers emit a `GoldenPathSignal` to stdout after each subcommand
  completes. Existing human-readable output is preserved unchanged above
  the sentinel line.
- `cmd_fingerprint` captures pre-write hash to derive `drift_detected` vs
  `no_drift` exit state for chain routing.
- `cmd_activate` emits a failure signal before `sys.exit(1)` on abort so
  chains can read the state instead of guessing from exit code alone.
- Tier 1 adapter schema reconciliation applied:
  - `claude-code/hooks/hooks.json` — added `"hooks"` wrapper; renamed
    `"ask_user"` → `"escalate"` and `"message"` → `"reason"` per canonical
    schema in `research/RUNTIME_FORMATS.md`.
  - `codex/config-fragments/hooks.json.fragment` — added `"hooks"` wrapper
    around `SessionStart` event array.
  - `opencode/plugin/ctmv3.ts` — changed generic `event:` key to direct
    `"session.created":` event name per current opencode plugin API.
  - `gemini-cli/ctmv3/gemini-extension.json` — cleared non-functional
    argument-pattern `excludeTools` entries (canonical schema only accepts
    plain tool names).
- `__init__.py` and `core/pyproject.toml` version bumped to 1.1.0.
- `README.md` — Cursor added to architecture diagram, install section, and
  cross-runtime command surface table; new documentation links added;
  License section now points to MIT LICENSE.

### Validation
- 125/125 unit tests green.
- 8/8 smoke tests green.
- All 5 JSON manifest files syntactically valid.
- 26 bash scripts syntactically valid.
- 8 TOML command files structurally valid.
- 152 total files, 4891 Python engine LOC, 15 doc files, 4162 adapter LOC.

## v1.0.0 — 2026-05-23

Initial cross-runtime plugin release.

### Added
- Python activation engine (`core/`) with stdlib-only implementation
- CLI surface: `boot`, `activate`, `warm`, `architecture-map`, `sovereign-init`,
  `dot-init`, `fingerprint`, `session-close`, `status`, `version`
- Templates for all CTMv3 artifacts: `TOPOLOGY.md`, `FAILURE_GRAMMAR.md`,
  `PROVENANCE.md`, `ARCHITECTURE_MAP.md`, `AGENTS.md`, `CLAUDE.md`,
  `copilot-instructions.md`, `topology-enforce.yml`, `session_state.json`,
  `golden_paths.json`, `.claude/settings.json`, `.pre-commit-config.yaml`
- Claude Code adapter (`claude-code/`): `.claude-plugin/plugin.json`,
  `settings.json`, slash commands (`commands/*.md`), hooks (`hooks/hooks.json`),
  subagent (`agents/ctmv3-architect.md`), skill (`skills/ctmv3/SKILL.md`)
- Codex adapter (`codex/`): skill (`skills/ctmv3/`), config fragments
  (`config-fragments/`), shell wrappers, `install.sh`
- opencode adapter (`opencode/`): subagent (`agent/ctmv3-architect.md`),
  commands (`command/ctmv3-*.md`), TypeScript plugin (`plugin/ctmv3.ts`),
  `install.sh`
- Gemini CLI adapter (`gemini-cli/`): `gemini-extension.json`, `GEMINI.md`,
  TOML slash commands (`commands/ctmv3/*.toml`), `install.sh`
- Full CTMv3 cognitive doc set in `docs/` (verbatim from source)
- Runtime format research at `research/RUNTIME_FORMATS.md`

### Notes
- Engine uses Python stdlib only. No external dependencies.
- Idempotent: `activate` preserves existing artifacts unless `--force`.
- All four runtime adapters delegate to the same engine — command semantics
  stay consistent across hosts.

## v3.0 (skill form) — 2026-05-11

- BOOT_PROTOCOL.md, DOT_TOPOLOGY.md, ARCHITECTURE_MAP_TEMPLATE.md added
- TOPOLOGY.md Node 8 (config spine)
- FAILURE_GRAMMAR.md Category 5 (ecosystem failures)
- SKILL.md semantic router expanded with COLD_START_REPO, WARM_START_REPO,
  BUILD_ARCHITECTURE_MAP, INTEGRATE_AGENT_ECOSYSTEM task types

## v2.0 (skill form) — 2026-03-08

- Packaged as `sovereign-skill-operator.zip`
- First full multi-doc skill package

## v1.0 (skill form) — 2026-03-08

- Initial CTM paradigm: TOPOLOGY, FAILURE_GRAMMAR, PROVENANCE, CONSTITUTION,
  python.md, case_codebase_entry.md, AGENTS_ADDENDUM
