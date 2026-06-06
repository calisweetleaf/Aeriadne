# JSON Tool-Output Hygiene

Use this when Daeron wants clean JSON tool outputs, Markdown reports, formatted manifests, or output cleanups after validation/tool runs.

## Goal

Turn noisy CLI/tool output into three layers:

1. **Human report**: short Markdown summary with exact pass/fail status and commands.
2. **Machine manifest**: JSON with timestamps, tool versions, commands, statuses, and redacted structured evidence.
3. **Raw evidence**: optional terminal snippets only where needed; avoid dumping huge tables, tokens, auth files, emails, or environment secrets.

## Hard gotcha: heredoc steals stdin

Bad pattern:

```bash
codex doctor --json | python3 - <<'PY'
import json, sys
print(json.load(sys.stdin))
PY
```

The heredoc supplies Python's stdin, so the pipe is not available to `json.load(sys.stdin)`. In this session that caused a JSON parse failure and a broken-pipe panic from the producer. Use one of the safe patterns below.

## Safe patterns

### Temp-file parse

```bash
tmp=$(mktemp)
codex doctor --json > "$tmp"
python3 -c 'import json,sys; obj=json.load(open(sys.argv[1])); print(obj.get("overallStatus"))' "$tmp"
rm -f "$tmp"
```

### Python `-c` pipe parse

```bash
codex mcp list --json | python3 -c 'import json,sys; obj=json.load(sys.stdin); print(type(obj).__name__)'
```

### `jq` parse

```bash
codex doctor --json | jq '{overallStatus, codexVersion, checks: (.checks | keys)}'
```

### Capture raw then summarize

```bash
out=$(codex features list)
printf '%s\n' "$out" | awk '$3 == "true" { print $1 }'
```

## Redaction rules

Do not print:

- `auth.json` contents;
- bearer tokens, OAuth tokens, API keys, refresh tokens, cookies;
- full environment dumps;
- private email/account identities unless Daeron explicitly asks and it is task-relevant;
- huge plugin marketplace tables unless filtered.

Prefer redacted summaries:

- server names and statuses, not env values;
- feature names and booleans, not unrelated internal noise;
- top-level doctor statuses, not entire raw reports;
- installed/enabled plugin names, not every marketplace candidate.

## Clean validation report shape

Markdown:

```markdown
# Validation Report — <task>

- Date: <iso8601>
- Host: <host/os>
- Codex: <version>
- Scope: <path>

## Commands

| Command | Status | Notes |
|---|---:|---|
| `codex doctor --json` | pass | overallStatus ok |

## Findings

- ...

## Follow-ups

- ...
```

JSON:

```json
{
  "schema": "codex-control-plane-audit-v1",
  "generated_at": "2026-06-04T03:00:00-05:00",
  "scope": "/home/daeron/.codex",
  "codex": {"version": "codex-cli 0.136.0", "doctor_status": "ok"},
  "commands": [
    {"command": "codex doctor --json", "status": "pass", "summary": "overallStatus ok"}
  ],
  "redaction": {"auth_files_printed": false, "env_values_printed": false}
}
```

## Use the packaged audit script

Run:

```bash
python3 /home/daeron/.codex/skills/custom/codex-config-topology/scripts/audit_codex_control_plane.py --markdown --prompt-audit
```

Default output is JSON. `--markdown` switches to a human report. `--prompt-audit` runs `codex debug prompt-input` and reports file-name hits only, not full prompt text.
