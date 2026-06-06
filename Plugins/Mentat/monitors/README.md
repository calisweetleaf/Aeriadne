# Mentat background monitors

Claude Code's plugin spec exposes a `monitors/monitors.json` surface: a manifest
of small commands that the platform runs on a fixed cadence, completely outside
the hot path of any active session. Mentat uses three of those slots — two
observer monitors that emit insights asynchronously, and one daily archivist
that rotates stale artifacts before the disk grows unbounded.

## What's here

```
monitors/
├── monitors.json        manifest read by Claude Code
├── entropy_watcher.py   60s cadence — flags stale EXECUTING sessions
├── drift_watcher.py     60s cadence — flags prolonged DRIFTING sessions
├── archivist.py         daily — gzip-rotates insights / handoff / sessions,
│                        and vacuums the Q-table of stale low-confidence rows
├── test_smoke.py        pure stdlib smoke test for all of the above
└── README.md            you are here
```

All four Python scripts are designed to be invoked once and exit. The cadence
loop lives in Claude Code's monitor system (or in your local cron / systemd
timer when you copy the recipe `bin/mentat-monitors schedule` prints). The
scripts never block, never spawn long-lived child processes, and never edit
state they did not create.

## How a monitor finds the active sessions

Every Mentat monitor reads `~/.mentat/sessions/<sid>.json` directly — that is
the canonical durable copy of every session's state machine. The watcher
scripts iterate the directory, parse each file with
`state_machine.session.Session.from_json`, and apply their predicate. There
is no separate "active sessions" registry to keep in sync.

## Idempotency contract

Both observer watchers (entropy and drift) are idempotent on a one-hour
window: each watcher records the last time it emitted an insight for a given
session in `~/.mentat/monitors/<watcher>_seen.json`. A second run within the
hour will find the same wedged session, decide the cooldown has not elapsed,
and skip it. That guarantees you can run the monitor every minute without
flooding the insight bus, and that a missed run (laptop closed for an hour)
does not produce a thundering-herd of duplicate insights on the next tick.

The archivist is naturally idempotent — a file that has already been moved
into the archive is no longer in the source directory, and the SQL vacuum
deletes rows whose predicate it would re-evaluate the same way on every run.

## Adding a new monitor

1. Drop a new Python file under `monitors/`. The script must:
   - Add the plugin root to `sys.path` so `state_machine.*` imports work.
   - Run a single pass and exit. No internal loop.
   - Be safe to invoke before any hook has fired (treat missing directories
     and missing SQLite schemas as no-ops).

2. Add a stanza to `monitors.json`:

   ```jsonc
   {
     "name": "your-monitor",
     "description": "What it does, plainly.",
     "command": "python3",
     "args": ["${CLAUDE_PLUGIN_ROOT}/monitors/your_monitor.py"],
     "interval": 300,
     "enabled": true
   }
   ```

3. If the monitor emits insights, give it an idempotency record path under
   `~/.mentat/monitors/` so re-runs do not duplicate.

4. Add a case to `test_smoke.py`.

## Running by hand

```bash
# Run one monitor right now (independent of cadence)
python3 plugin/bin/mentat-monitors run-once entropy-watcher

# Show last-run timestamps for every monitor
python3 plugin/bin/mentat-monitors status

# Emit copy-paste cron + systemd recipes
python3 plugin/bin/mentat-monitors schedule
```

`bin/mentat-monitors` is deliberately separate from `bin/mentat` so the
inspector CLI surface stays uncluttered and the monitor CLI stays composable
with `systemd-run` and `cron`.

## Why these three

- **entropy-watcher** — Catches the failure mode where the model has been in
  `EXECUTING` for a while, chained 8+ tool calls together, and gone silent.
  Either the user walked away, or the model is stuck in a retry loop that
  the hook layer can't see (because the hook only fires on a tool call,
  and the model isn't calling any). The watcher emits an
  `ENTROPY_SPIKE(tag="stale")` so the next `/reflect` surfaces it.
- **drift-watcher** — Once the FSA enters `DRIFTING`, only an explicit
  `PROMPT_SUBMIT` escapes. If the user ignores the banner the session can
  sit in `DRIFTING` indefinitely, silently poisoning every subsequent
  reflection. The watcher emits a `NOTE(tag="drift-stuck")` after thirty
  minutes so the next reflection has a clear reminder to either acknowledge
  or update `scope.md`.
- **archivist** — Insight JSONL files grow without bound. A long-running
  daily session can accumulate a few megabytes a week. The archivist
  gzip-compresses anything older than the retention window into a
  monthly bucket under `~/.mentat/insights.archive/`, then deletes the
  source. The Q-table vacuum removes rows that were touched once and never
  visited again — they bloat the table and skew Thompson sampling toward
  noisy estimates.

All three are stdlib-only Python ≥ 3.10. No new dependencies.
