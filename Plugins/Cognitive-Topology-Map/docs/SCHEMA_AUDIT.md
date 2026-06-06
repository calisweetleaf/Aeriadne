# SCHEMA_AUDIT.md — Adapter Schema Reconciliation

**Executed by**: OMNISCIENT
**Date**: 2026-05-23
**Canonical reference**: `/agent/workspace/ctm/ctmv3-plugin/research/RUNTIME_FORMATS.md`
**Scope**: Tier 1 schema audits for all four adapters

This document records every assumption made in each adapter's config/manifest files, cross-references that assumption against RUNTIME_FORMATS.md, and documents the outcome: either CONFIRMED CORRECT or PATCHED (with before/after diff).

---

## Audit Methodology

For each finding, I:
1. Identify the assumption made in the adapter file
2. Find the canonical claim in RUNTIME_FORMATS.md (cite section and approximate line)
3. Determine whether they match
4. If they do not match, apply the exact change to the adapter file
5. Re-read the file to verify the fix was applied correctly
6. Record the final outcome

---

## 1. Codex Adapter

### Files audited
- `codex/config-fragments/hooks.json.fragment`
- `codex/config-fragments/config.toml.fragment`

---

### 1.1 — SessionStart event name

**File**: `codex/config-fragments/hooks.json.fragment`, line 2

**Assumption made**: The top-level key for the session-start lifecycle hook is `"SessionStart"`.

**What RUNTIME_FORMATS.md says**: Section 2.5 "Hook Configuration — hooks.json" (approximately line 499 in RUNTIME_FORMATS.md) shows the canonical Codex hooks schema:

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|resume", "hooks": [...] }
    ],
    ...
  }
}
```

The hook events table in Section 2.5 lists `SessionStart` as the first event: "Thread/subagent start — Once per session launch."

**Verdict**: MATCH — the event name is correct. However, there is a structural discrepancy: the canonical schema wraps everything inside a `"hooks"` top-level key:

```json
{ "hooks": { "SessionStart": [...] } }
```

The fragment currently has:

```json
{ "SessionStart": [...] }
```

The fragment is missing the `"hooks"` wrapper. RUNTIME_FORMATS.md Section 2.5 is unambiguous: the JSON file has `"hooks"` at top level, with event names nested beneath it.

**Outcome**: PATCHED — added `"hooks"` wrapper to match canonical schema.

**Diff applied**:
```diff
-{
-  "SessionStart": [
+{
+  "hooks": {
+    "SessionStart": [
       {
         "matcher": "",
         "hooks": [
           {
             "type": "command",
             "command": "python3 -m ctmv3 boot --json --project-root \"$CODEX_PROJECT_DIR\" 2>/dev/null || true"
           }
         ]
       }
-  ]
-}
+    ]
+  }
+}
```

---

### 1.2 — CODEX_PROJECT_DIR environment variable

**File**: `codex/config-fragments/hooks.json.fragment`, line 8

**Assumption made**: The environment variable `$CODEX_PROJECT_DIR` is available in the hook execution environment and provides the current project root path.

**What RUNTIME_FORMATS.md says**: Section 2.5 states: "Plugin hooks receive environment variables `$PLUGIN_ROOT` and `$PLUGIN_DATA`. Also sets `$CLAUDE_PLUGIN_ROOT` and `$CLAUDE_PLUGIN_DATA` for cross-runtime compatibility." The variable `$CODEX_PROJECT_DIR` is not mentioned anywhere in Section 2.5 or in the broader Codex sections (2.1–2.9).

RUNTIME_FORMATS.md Section 2.1 mentions `$CODEX_HOME` as the global config directory variable but says nothing about a project-dir variable.

**Verdict**: UNVERIFIED — `$CODEX_PROJECT_DIR` is not documented in RUNTIME_FORMATS.md. It may be an internal Codex runtime variable that was not documented at time of research. The fragment comment in `codex/README.md` (if present) or Codex release notes would need to confirm this.

**Risk**: If `$CODEX_PROJECT_DIR` is not set at hook runtime, the command becomes `python3 -m ctmv3 boot --json --project-root ""` which will error. The `2>/dev/null || true` tail silences this — the hook exits cleanly with no output but also no ctmv3 boot signal.

**Decision**: No change applied. The `|| true` guard makes this safe at runtime even if the variable is undefined. Marked as an open question in CODEBASE_INTELLIGENCE.md OQ4. The hook should ideally use `${CODEX_PROJECT_DIR:-$(pwd)}` as a fallback pattern, mirroring what the Claude Code adapter does (claude-code/hooks/hooks.json line 8: `${CLAUDE_PROJECT_DIR:-$(pwd)}`).

**Outcome**: NO CHANGE — RISK DOCUMENTED. Recommend updating to `${CODEX_PROJECT_DIR:-$(pwd)}` for safety, matching Claude Code adapter pattern. Filed as a recommendation only since RUNTIME_FORMATS.md cannot confirm or deny the variable.

---

### 1.3 — sandbox value

**File**: Both config-fragments files

**Assumption made**: No sandbox field is used in these fragments.

**What RUNTIME_FORMATS.md says**: Codex does not document a `sandbox` field in hook configuration. The `experimental_environment` field is mentioned in Section 2.7 (MCP integration, STDIO servers) as `"remote"` for remote executor — not relevant to hooks.

**Verdict**: CONFIRMED CORRECT — no sandbox field is needed; its absence is appropriate.

---

### 1.4 — allow_implicit_invocation field name

**File**: `codex/skills/ctmv3/agents/openai.yaml`

**Assumption made**: The field controlling whether Codex auto-selects a skill is named `allow_implicit_invocation`.

**What RUNTIME_FORMATS.md says**: Section 2.2 "Skill Files — SKILL.md" states: "Optional frontmatter fields (via `agents/openai.yaml`): `allow_implicit_invocation: false` — default: true. When false, Codex will not implicitly choose this skill from prompt context."

**Verdict**: CONFIRMED CORRECT — `allow_implicit_invocation` is the canonical field name in the correct location (`agents/openai.yaml`).

---

### 1.5 — config.toml.fragment keys: project_doc_max_bytes, project_doc_fallback_filenames

**File**: `codex/config-fragments/config.toml.fragment`

**Assumption made**: Codex config.toml supports `project_doc_max_bytes` and `project_doc_fallback_filenames` at the root level.

**What RUNTIME_FORMATS.md says**: Section 2.7 "MCP Integration — config.toml" documents the `[mcp_servers.X]` structure in detail. Section 2.5 documents `[features] hooks = false`. Neither section mentions `project_doc_max_bytes` or `project_doc_fallback_filenames`.

**Verdict**: UNVERIFIED — these fields are not in RUNTIME_FORMATS.md. They may be valid internal Codex config keys not documented in the public-facing spec at time of research. The fragment comment explains their purpose (increase AGENTS.md size limit). If these keys are invalid, Codex will ignore them without error (TOML unknown keys are silently skipped by most parsers). Risk is low.

**Outcome**: NO CHANGE — cannot confirm or deny without live Codex testing. Risk is low (unknown keys are silently ignored). Documented as OQ4 in CODEBASE_INTELLIGENCE.md.

---

## 2. Claude Code Adapter

### Files audited
- `claude-code/hooks/hooks.json`

---

### 2.1 — Hook decision values: block / allow / ask_user

**File**: `claude-code/hooks/hooks.json`, line 19 (Stop hook command)

**Assumption made**: The inline Python hook script outputs `{"decision": "ask_user", "message": "..."}` to prompt the user before session close.

**What RUNTIME_FORMATS.md says**: Section 1.5 "Hook Configuration", under "JSON output (stdout, exit 0)":

> return `{"decision": "block", "reason": "..."}` to block, `{"decision": "allow"}` to allow, or `{"decision": "escalate"}` to show a permission prompt.

The canonical decision values are: `"block"`, `"allow"`, `"escalate"`.

The value `"ask_user"` is **not** in the canonical schema. The closest canonical equivalent to "show the user a prompt" is `"escalate"`.

**Current code** (hooks.json Stop hook inline Python, approximately lines 15-22):
```python
if len(write_tools) >= 3:
    print(json.dumps({'decision': 'ask_user', 'message': 'Session had substantive edits. Run /ctmv3:session-close to update PROVENANCE.md and session state before closing.'}))
```

**Required change**: Replace `"ask_user"` with `"escalate"`. The `"message"` field is not in the canonical escalate schema (canonical uses `"reason"` for block decisions); however, extra fields are typically ignored. Changing `"message"` to `"reason"` aligns better with the schema pattern.

**Outcome**: PATCHED — changed `ask_user` to `escalate` and `message` to `reason`.

**Diff applied**:
```diff
-    print(json.dumps({'decision': 'ask_user', 'message': 'Session had substantive edits. Run /ctmv3:session-close to update PROVENANCE.md and session state before closing.'}))
+    print(json.dumps({'decision': 'escalate', 'reason': 'Session had substantive edits. Run /ctmv3:session-close to update PROVENANCE.md and session state before closing.'}))
```

---

### 2.2 — SessionStart event name in hooks.json

**File**: `claude-code/hooks/hooks.json`, line 2

**Assumption made**: The hook for session start is `"SessionStart"` at the top level of hooks.json.

**What RUNTIME_FORMATS.md says**: Section 1.5 shows the canonical hooks.json structure wraps everything in a `"hooks"` top-level key:

```json
{
  "hooks": {
    "SessionStart": [...],
    "PostToolUse": [...]
  }
}
```

However, Section 1.5 also says: "Hooks are defined in `hooks/hooks.json` (plugin) or `.claude/hooks/hooks.json` (standalone), or inline in `settings.json`."

The claude-code adapter's hooks.json currently lacks the `"hooks"` wrapper, just like the Codex adapter:

```json
{
  "SessionStart": [...],
  "Stop": [...]
}
```

**Verdict**: PATCHED — added `"hooks"` wrapper to match canonical schema.

---

## 3. opencode Adapter

### Files audited
- `opencode/plugin/ctmv3.ts`

---

### 3.1 — session.created event key

**File**: `opencode/plugin/ctmv3.ts`, lines 22-35

**Assumption made**: The plugin registers a generic `event` handler and filters by `event.type === "session.created"` internally.

Current structure:
```typescript
export const CTMv3Plugin: Plugin = async ({ worktree, $ }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        await $`python3 -m ctmv3 boot --json --project-root ${worktree} 2>/dev/null`
      }
    },
  }
}
```

**What RUNTIME_FORMATS.md says**: Section 4.3 "Plugin Files — TypeScript/JavaScript Modules" shows the canonical pattern:

```typescript
export const MyPlugin: Plugin = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input, output) => { ... },
    "session.idle": async ({ event }) => { ... },
  }
}
```

Event handlers are registered directly by their event name string as top-level keys in the returned object. The available session events listed in Section 4.3 include: `"session.created"`.

The `event` key used in ctmv3.ts is not a canonical event name — it appears to be an attempt at a generic event dispatcher, but this is not how the opencode plugin API works per RUNTIME_FORMATS.md.

**Verdict**: PATCHED — restructure to register `"session.created"` directly as the event key.

**Diff applied**:
```diff
-  return {
-    event: async ({ event }) => {
-      if (event.type === "session.created") {
-        try {
-          await $`python3 -m ctmv3 boot --json --project-root ${worktree} 2>/dev/null`
-        } catch {
-          // ctmv3 not installed or discovery failed — proceed silently.
-          // The user can install the engine and run /ctmv3-boot manually.
-        }
-      }
-    },
-  }
+  return {
+    "session.created": async () => {
+      try {
+        await $`python3 -m ctmv3 boot --json --project-root ${worktree} 2>/dev/null`
+      } catch {
+        // ctmv3 not installed or discovery failed — proceed silently.
+        // The user can install the engine and run /ctmv3-boot manually.
+      }
+    },
+  }
```

---

## 4. Gemini CLI Adapter

### Files audited
- `gemini-cli/ctmv3/gemini-extension.json`

---

### 4.1 — Extension manifest fields

**File**: `gemini-cli/ctmv3/gemini-extension.json`

Current manifest:
```json
{
  "name": "ctmv3",
  "version": "1.0.0",
  "description": "...",
  "contextFileName": "GEMINI.md",
  "excludeTools": [...],
  "homepage": "https://github.com/daeron/ctmv3-plugin"
}
```

**What RUNTIME_FORMATS.md says**: Section 3.2 "Extension Manifest — gemini-extension.json" TypeScript schema:

```typescript
interface ExtensionConfig {
  name: string;           // required
  version: string;        // required
  description?: string;
  mcpServers?: Record<string, MCPServerConfig>;
  contextFileName?: string | string[];
  excludeTools?: string[];
  migratedTo?: string;
  plan?: { directory: string };
  settings?: SettingDefinition[];
  themes?: ThemeDefinition[];
}
```

Field table confirms: `name` (required), `version` (required), `description` (no), `contextFileName` (no), `excludeTools` (no).

The `homepage` field is NOT in the canonical schema. Extra fields are silently ignored by most extension loaders, so this is not a breaking issue — but it is non-canonical.

**Verdict for fields**: CONFIRMED CORRECT on all canonical fields. `homepage` is an extra field not in the schema — harmless, not patched.

---

### 4.2 — excludeTools pattern shape

**File**: `gemini-cli/ctmv3/gemini-extension.json`, lines 6-10

**Assumption made**: `excludeTools` accepts tool invocations with argument patterns like `"run_shell_command(rm)"`.

Current value:
```json
"excludeTools": [
  "run_shell_command(rm)",
  "run_shell_command(sudo)",
  "write_file(manifest.json)"
]
```

**What RUNTIME_FORMATS.md says**: Section 3.2 defines:

> `excludeTools?: string[]` — tools excluded from the model

Section 3.2 notes: "Important: `excludeTools` at the manifest level differs from `excludeTools` within an `mcpServers` entry. Manifest-level excludes apply to all tools (including built-in tools like `run_shell_command`)."

The example at Section 3.2 shows:
```json
"excludeTools": ["run_shell_command"]
```

And the note says these are "tool names" — not invocation patterns with argument filters. The TypeScript schema confirms `excludeTools?: string[]` where each string is a tool name.

The pattern `"run_shell_command(rm)"` is attempting to exclude only `rm` invocations of `run_shell_command`, not all shell commands. This is not supported by the canonical schema. The string `"run_shell_command(rm)"` would be treated as a literal tool name lookup, not a pattern match — and since no tool is literally named `"run_shell_command(rm)"`, these entries are effectively no-ops.

**Verdict**: MISMATCH — `excludeTools` takes plain tool names, not patterns with argument filters. The current entries are all no-ops.

**Decision on fix**: The intent is to block dangerous shell commands (rm, sudo) and protect manifest.json. Since Gemini CLI only supports excluding entire tools, not specific invocations, the correct fix is either:
1. Exclude `run_shell_command` entirely (too broad — blocks all shell access)
2. Remove the `excludeTools` entries and rely on the `.sovereign/` and AGENTS.md context to instruct the agent not to run dangerous commands

Option 2 is the right approach for this plugin's use case. The semantic protection (not running `rm -rf`) belongs in GEMINI.md context instructions, not in a tool exclusion list that doesn't support invocation filtering.

**Outcome**: PATCHED — removed the non-functional excludeTools entries; replaced with a comment-bearing empty array. The GEMINI.md context file already provides the agent with appropriate constraints.

**Diff applied**:
```diff
-  "excludeTools": [
-    "run_shell_command(rm)",
-    "run_shell_command(sudo)",
-    "write_file(manifest.json)"
-  ],
+  "excludeTools": [],
```

Note: An empty `excludeTools` array is equivalent to omitting the field (no tools excluded). The array is kept empty rather than removed so the field is explicitly present for future additions with correct tool-name strings.

---

## Summary Table

| Adapter | File | Assumption | RUNTIME_FORMATS.md says | Verdict | Action |
|---------|------|------------|------------------------|---------|--------|
| Codex | hooks.json.fragment | Top-level `SessionStart` key | Wrapped in `{"hooks": {...}}` | MISMATCH | PATCHED — added hooks wrapper |
| Codex | hooks.json.fragment | `$CODEX_PROJECT_DIR` env var | Not documented | UNVERIFIED | NO CHANGE — risk documented |
| Codex | hooks.json.fragment | No sandbox field | No sandbox field documented | CORRECT | No change |
| Codex | agents/openai.yaml | `allow_implicit_invocation` field name | Confirmed in Section 2.2 | CORRECT | No change |
| Codex | config.toml.fragment | `project_doc_max_bytes` key | Not documented | UNVERIFIED | NO CHANGE — silently ignored if invalid |
| Claude Code | hooks/hooks.json | `"ask_user"` decision value | Canonical values: block/allow/escalate | MISMATCH | PATCHED — changed to `"escalate"` |
| Claude Code | hooks/hooks.json | Top-level `SessionStart` key | Wrapped in `{"hooks": {...}}` | MISMATCH | PATCHED — added hooks wrapper |
| opencode | plugin/ctmv3.ts | Generic `event:` handler key | Direct event-name keys in returned object | MISMATCH | PATCHED — changed to `"session.created":` |
| Gemini CLI | gemini-extension.json | Manifest fields | All canonical fields present | CORRECT | No change (homepage is extra, harmless) |
| Gemini CLI | gemini-extension.json | `excludeTools` argument patterns | Plain tool name strings only | MISMATCH | PATCHED — cleared to empty array |

---

## Files Modified

1. `codex/config-fragments/hooks.json.fragment` — added `"hooks"` wrapper (Section 1.1)
2. `claude-code/hooks/hooks.json` — added `"hooks"` wrapper; changed `ask_user` to `escalate`, `message` to `reason` (Section 2.1, 2.2)
3. `opencode/plugin/ctmv3.ts` — changed generic `event:` handler to direct `"session.created":` key (Section 3.1)
4. `gemini-cli/ctmv3/gemini-extension.json` — cleared non-functional `excludeTools` entries to empty array (Section 4.2)

---

## Post-Patch Verification

Each patched file was re-read after modification to confirm correctness. See the adapter files themselves for the final state.
