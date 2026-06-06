# SOVEREIGN_CODEX_V2-2 Staging Analysis

Generated: 2026-05-27 02:35 America/Chicago

## Scope

- Source ZIP: `/home/daeron/.codex/SOVEREIGN_CODEX_V2-2.zip`
- Staged directory: `/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2`
- Base overwrite performed: **no**

## Current config vs staged `config_patched.toml`

The staged patched config is now effectively the active `/home/daeron/.codex/config.toml` with one intentional active-value change and without stale trusted hook hashes.

### Intentional active change

- `features.plugins`: `true` in current base config → `false` in staged config, to disable plugin auto-surface while keeping local skills/tooling workflows.

### Deliberately omitted from staged config

- Existing `[hooks.state.*].trusted_hash` entries for the current Petdex hooks are omitted because they are hash bindings for the old `/home/daeron/.codex/hooks.json`, not for the staged Sovereign hooks.

### Preserved after rebase

- `features.external_migration = true`
- `features.mentions_v2 = true`

## Fixes applied inside staging only

1. Parsed and repaired all profile TOML files.
2. Converted invalid multiline inline `shell_environment_policy.set` blocks into valid `[shell_environment_policy.set]` subtables.
3. Removed duplicate feature keys that made TOML parsing fail.
4. Replaced invalid `[otel.exporter.otlp_http]` scalar/table conflict with `otlp_http_endpoint`.
5. Rewrote `hooks.json` to use `CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"; python3 "$CODEX_HOME/bin/hooks/<script>.py"`, so staging tests can use `CODEX_HOME=/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2` and later deployment can use `~/.codex/bin/hooks`.
6. Patched hook scripts to match the live SovereignMCP tool schemas surfaced in this session.
7. Added `bin/notify_relay.py` for the profile `notify` path.
8. Updated `README_DEPLOYMENT.md` so it no longer describes missing hook stubs as future work.

## Validation evidence

- TOML parse: **PASS** (`config_patched.toml`, `sovereign.config.toml`, `stealth.config.toml`, `research.config.toml`, `requirements.toml`)
- JSON parse: **PASS** (`hooks.json`)
- Python compile: **PASS** (`bin/hooks/*.py`, `bin/notify_relay.py`)
- Hook smoke via `/bin/sh -c` and `CODEX_HOME=/home/daeron/.codex/DESK/SOVEREIGN_CODEX_V2-2`: **PASS** for all 10 configured hook events.
  - Output discipline: stdout was empty or valid Codex hook JSON; stderr length was 0 in smoke tests.
- Base safety: **PASS** — no overwrite/copy into base config or base hooks was performed.

## Deployment notes for later

Do **not** deploy automatically from this report. When ready, the expected copy-out set is:

- `config_patched.toml` → `/home/daeron/.codex/config.toml`
- `hooks.json` → `/home/daeron/.codex/hooks.json`
- `bin/` → `/home/daeron/.codex/bin/`
- Optional profiles: `sovereign.config.toml`, `stealth.config.toml`, `research.config.toml` → `/home/daeron/.codex/`
- Do not deploy `requirements.toml` to `/etc/codex/requirements.toml` without explicit root/admin approval.

See `validation_manifest.json` for hashes and machine-readable validation status.
