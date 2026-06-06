# CONTRIBUTING

I write this guide in the same voice as the rest of the project: first-person, no filler,
no aspirational language. Everything here describes what the code actually does, not what
I hope it will do.

---

## How to extend with a new template

Templates live in `core/ctmv3/core/templates/`. Each template is a plain text file named
`<ARTIFACT_NAME>.md.template` (or `.yml.template` for workflow files). The naming convention
is strict: the extension must be `.template` so that `templates.list_templates()` discovers
it via the `*.template` glob.

Template variables use `{{VARIABLE_NAME}}` syntax. The `templates.render()` function
substitutes every `{{KEY}}` it finds a matching keyword argument for. Unmatched placeholders
are left as-is so partial renders produce instructive scaffolding rather than blank fields.

To add a new template:

1. Create `core/ctmv3/core/templates/MY_ARTIFACT.md.template` with `{{VARIABLE_NAME}}`
   placeholders for any context the engine should inject.
2. Add a convenience renderer in `core/ctmv3/core/templates.py` following the pattern of the
   existing `render_topology()`, `render_provenance()`, etc. functions. Validate that any
   required parameters (like `project_name`) are non-empty before calling `render()`.
3. Call your renderer from `activate.py` in the appropriate phase if the artifact belongs
   to the cold-start sequence, or expose it as a standalone subcommand in `cli.py` if it
   is optional.
4. Add a unit test in `core/ctmv3/tests/test_engine.py` in the `TestTemplates` or
   `TestTemplatesHardening` class that verifies the template loads, that key context
   variables are substituted, and that empty project names are rejected.

The `templates.load()` function validates against path traversal sequences before
constructing the file path, so template names must be plain filenames with no directory
separators.

---

## How to add a new CLI command

The CLI entry point is `core/ctmv3/core/cli.py`, which belongs to the
golden-path-architect peer on this project. I do not own `cli.py` and do not modify it.
If you are adding a new subcommand:

1. Implement the business logic as a function in the appropriate engine module under
   `core/ctmv3/core/`. The function should return a structured dict (JSON-serializable)
   so the CLI can emit `--json` output consistently.
2. Wire the subcommand in `cli.py` using the existing pattern: each subcommand is a
   `argparse` sub-parser with `--project-root` and `--json` flags. The handler calls
   the engine function and either pretty-prints or JSON-dumps the result.
3. The expected function signature for a new engine entry point is:
   ```python
   def run(project_root: Path, **kwargs) -> dict[str, Any]:
       ...
   ```
   where `kwargs` carries any subcommand-specific flags.
4. Register the new subcommand name in the adapter `scripts/` directories (Codex's
   `scripts/ctmv3-*.sh`, Gemini CLI's `ctmv3.*.toml`, etc.) if the command is intended
   to be surface-exposed in those runtimes. Adapter files belong to the OMNISCIENT peer.

The `golden_path_signal` JSON envelope that cli.py emits after each command is handled
by the CLI layer, not the engine. Your engine function does not need to emit it.

---

## How to add a new runtime adapter

The four existing adapters — `claude-code/`, `codex/`, `opencode/`, `gemini-cli/` — each
follow the same directory structure. Mirror it exactly:

```
<runtime-name>/
  README.md                  -- what this adapter does, install steps, uninstall steps
  install.sh                 -- idempotent install script (see install.sh pattern below)
  <runtime-config-dir>/      -- runtime-specific config directory (e.g. .cursor/rules/)
    ctmv3.<extension>        -- the hook/rule/extension file that triggers the engine
  scripts/                   -- optional: bash wrappers that invoke `python3 -m ctmv3`
    ctmv3-boot.sh
    ctmv3-activate.sh
    ctmv3-fingerprint.sh
    ctmv3-session-close.sh
    ctmv3-status.sh
```

`install.sh` pattern: every install script must be idempotent. Use `cp -n` (no-clobber)
or an existence check before copying config files. Never overwrite user config silently.
Create the target directory with `mkdir -p` before placing files. Provide a corresponding
`uninstall` section (or a separate `uninstall.sh`) that removes only the files the script
placed, not the runtime's entire config directory.

The manifest format for a new adapter's primary config file must conform to
`research/RUNTIME_FORMATS.md`. Before writing the manifest, read `RUNTIME_FORMATS.md`
and `docs/SCHEMA_AUDIT.md` to understand which fields are required, which are canonical
keys (not invented ones), and which event names the runtime actually emits. Do not invent
field names; use the exact keys the runtime documents.

---

## Testing protocol

### Running the full suite

From the plugin root:

```bash
bash tests/run-all.sh
```

`run-all.sh` runs six phases in sequence:

1. **Engine unit tests** — `python3 -m unittest discover -s core/ctmv3/tests -v`. Covers
   all engine modules with 125+ assertions.
2. **End-to-end smoke test** — `bash tests/smoke.sh`. Spins up a temp repo, runs a full
   cold-start activate, verifies all expected artifacts appear, checks fingerprint
   stability, tests idempotency, and verifies session-close.
3. **JSON syntax** — validates all adapter manifest/hook/config JSON files parse cleanly.
4. **Bash script syntax** — runs `bash -n` over every `.sh` file in the plugin.
5. **TOML structural check** — verifies every Gemini CLI command TOML has `description`
   and `prompt` fields.
6. **File inventory** — prints a summary (total files, engine LOC, doc count). Does not
   fail unless earlier phases did.

All six phases must pass before merging. A PR that breaks any phase is not ready.

### Adding new unit tests

Unit tests live in `core/ctmv3/tests/test_engine.py`. The file is organized into test
classes, one per module, each with an `Original suite` section and a `Hardening tests`
section. Add new tests to the appropriate hardening class (e.g., `TestBootHardening`,
`TestFingerprintHardening`).

Each test class has a `setUp` that calls `_tmp_root()` to create a fresh temporary
directory, and a `tearDown` that calls `_cleanup()` to remove it. Use this pattern for
any test that writes to disk.

Tests must be self-contained: no mocking of external systems, no network calls, no
reliance on test ordering. The engine is stdlib-only; tests should be too, except that
`unittest.mock.patch` is allowed where simulating a crash requires intercepting an
OS-level call.

Name test methods descriptively: `test_<what>_<expected_behavior>`. The docstring is
the assertion statement in plain English. If the test covers a branch added during
hardening (input validation, atomic write, error path), mark it with a comment
`# v1.1.0 hardening` so future readers can identify when it was added.

---

## Style rules

I follow these rules in every file I write for this project. New contributions must
match them:

- **First-person, no emojis.** Documentation and commit messages are written in
  first-person declarative ("I implement...", "This function validates...", not "Let's
  add..." or "This PR introduces emojis as a feature").
- **No placeholders, no TODOs in engine code.** Every function in `core/ctmv3/core/`
  must be fully functional and immediately executable. The CONSTITUTION.md Prime Axiom
  applies: the file tree is the executable codebase. A stub is a split.
- **stdlib only.** The engine (`core/ctmv3/core/*.py`) must import nothing outside the
  Python standard library. No `requests`, no `pyyaml`, no `toml`, no third-party
  packages. If you need TOML parsing, parse it line-by-line as the existing
  `_extract_from_pyproject()` does.
- **Atomic writes.** Every file write in engine code uses the `_atomic_write()` helper
  (write to `.tmp`, then `os.replace`). Direct `path.write_text()` is acceptable in test
  code and in doc files, but not in engine modules.
- **Idempotent operations.** If a function can run twice, the second run must not corrupt
  state. Use existence checks and `exist_ok=True` on `mkdir`. Return status strings
  ("skipped", "created", "force-overwritten") so callers can see what happened.
- **Input validation at boundaries.** Every public function that accepts `project_root`,
  `project_name`, `last_agent`, or `last_action` must validate those inputs before use.
  `ValueError` with an actionable message is the correct exception type.
- **Structured logging.** Every module has `logger = logging.getLogger(__name__)` at
  module level. Use DEBUG for per-file trace, INFO for phase completion, WARNING for
  recoverable anomalies, ERROR for failures. Never log secrets or credentials.

---

## Commit message convention

I follow the style in `CHANGELOG.md`. The convention is:

```
<verb>: <subject> (<scope if not obvious>)

<body if needed — what changed and why, not how>
```

Verbs I use:

- `add` — a wholly new file or feature that did not exist
- `update` — an enhancement to an existing feature
- `fix` — a bug correction
- `harden` — production reliability improvements (logging, validation, atomic writes)
- `refactor` — code restructuring with no behavior change
- `test` — adding or fixing tests only
- `docs` — documentation only

Examples from this project's style:

```
harden: atomic writes and input validation across engine modules (v1.1.0)

fix: separator row detection in _extract_last_session

add: CONTRIBUTING.md, LICENSE, .github/workflows/

test: extend test_engine.py to 125 assertions covering hardening branches
```

One subject line, imperative mood, 72 characters or fewer. Body is optional and explains
the why, not the what.

---

## PR review expectations

Before opening a PR, verify all of the following manually:

1. `bash tests/run-all.sh` exits 0 from the plugin root.
2. No new external dependencies have been added to the engine. If `core/ctmv3/core/*.py`
   imports anything outside stdlib, the PR is not ready.
3. Any new adapter manifest field has been traced to `research/RUNTIME_FORMATS.md` and
   cross-referenced in `docs/SCHEMA_AUDIT.md`. If you are adding a field that is not in
   `RUNTIME_FORMATS.md`, you must update `RUNTIME_FORMATS.md` first and reference the
   update in your PR description.
4. All new public functions have docstrings that describe arguments, return values, and
   which exceptions they raise. The docstring is not optional.
5. All file writes in engine code are atomic. If a reviewer sees a bare `path.write_text()`
   in `core/ctmv3/core/`, it will be flagged.
6. The PR title matches the commit message convention above.
7. If the PR touches adapter files (`claude-code/`, `codex/`, `opencode/`, `gemini-cli/`),
   the schema reconciliation must be traced to `RUNTIME_FORMATS.md` in the PR description.
   Quoting the relevant lines from `RUNTIME_FORMATS.md` is the expected format.
