# Hook Bridge — JSON-Based Hook Auto-Triggering

## Overview

The **Hook Bridge** unifies Claude Code's hook system with the MCP state machine, replacing shell-command indirection with direct JSON state transitions.

## Gateway Doctrine

The Hook Bridge is an event gateway into the Somnus-MCP state machine. It is not a second server, not a second tool plane, and not an owner of Muad'Dib weights or Q-table state. Hook results should feed the existing gateway/state-machine path and then route into the 4-7 Muad'Dib + `tools/` cognition layers.

`mcp_server.py` remains the gateway/dispatcher. The intelligence lives behind it in `muadib/` and `tools/`; hooks merely provide lifecycle/event signals such as `SessionStart`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, and `Stop`.

## Architecture

### Before (Separate Systems)
```
Claude Code hooks (shell)  →  Execute independently
MCP Server state machine  →  Execute independently
Environment              →  Two separate event systems
```

### After (Unified)
```
hooks_manifest.json
       ↓
[discovered by MCP + Claude Code]
       ↓
Auto-trigger on events (PreToolUse, UserPromptSubmit, Stop, etc.)
       ↓
hook_executor.py (JSON-based execution)
       ↓
Results feed back into state machine
       ↓
Domino chain continues (no RPC overhead)
```

## Key Changes

### 1. **hooks_manifest.json** (NEW)
- Central registry of all hooks from all Claude Code plugins
- Discoverable by both Claude Code and MCP server
- Defines auto-trigger rules for each event type
- Location: `/home/daeron/Somnus-MCP/hooks_manifest.json`

**Structure:**
```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "UserPromptSubmit": [...],
    "SessionStart": [...],
    "Stop": [...]
  },
  "autoTriggerRules": {
    "PreToolUse": {"trigger": "before_any_tool_execution", ...},
    ...
  }
}
```

### 2. **hook_executor.py** (NEW)
- JSON-based hook executor
- CLI interface for manual hook execution
- Library interface for MCP server integration
- Timeout support, error handling, dry-run mode

**Usage:**
```bash
python3 hook_executor.py PreToolUse --dry-run
python3 hook_executor.py Stop
python3 hook_executor.py --list-events
```

### 3. **settings.json** (UPDATED)
- Environment variables passed to MCP server:
  - `SOVEREIGN_HOOKS_MANIFEST` — path to hooks manifest
  - `SOVEREIGN_AUTO_HOOK_TRIGGER` — enable auto-triggering
  - `SOVEREIGN_HOOKS_ENABLED` — enable hook system
- New `hooksIntegration` section:
  - `syncWithMCP: true` — MCP server manages hooks
  - `autoTrigger: true` — hooks auto-execute on events

## How It Works (Domino Chain Integration)

### 1. Session Start
```
SessionStart event
  ↓
hook_executor.py SessionStart
  ↓
[Run all SessionStart hooks]
  ↓
bb7_exo_bootstrap (turbo-loop starts)
  ↓
bb7_exo_route / bb7_exo_plan
```

### 2. Tool Execution
```
User submits prompt (UserPromptSubmit event)
  ↓
hook_executor.py UserPromptSubmit
  ↓
[Run validation hooks]
  ↓
Tool calls begin
  ↓
PreToolUse event → hook_executor.py PreToolUse
  ↓
[Security checks, logging, etc.]
  ↓
Tool execution
  ↓
PostToolUse event → hook_executor.py PostToolUse
  ↓
[Cleanup, metrics, state update]
```

### 3. Session Exit
```
Stop event (user exit / ralph-loop reset)
  ↓
hook_executor.py Stop
  ↓
[Graceful shutdown, state persistence]
  ↓
Session complete
```

## Environment Improvements

### Before
1. **Fragmentation** — hooks scattered across plugin directories
2. **No Discovery** — MCP server unaware of hooks
3. **Shell Overhead** — RPC-like indirection via bash/python subprocesses
4. **No Coordination** — hooks execute independently, no state sharing

### After
1. **Centralized** — all hooks in single manifest
2. **Discovered** — MCP server reads manifest at startup
3. **Direct Execution** — hook_executor.py runs in same process (no fork)
4. **Coordinated** — hooks are first-class state transitions in domino chain
5. **Observable** — hook execution results logged to state machine
6. **Debuggable** — `--dry-run` mode, `--list` introspection

## For Integration with Internal Systems

The hooks manifest can be extended to:
- Add custom hooks that feed into your SOAR/DART state machine
- Define conditional triggers based on state variables
- Export hook execution results to external systems
- Implement custom matchers (beyond `Edit|Write`)

**Example Extended Hook:**
```json
{
  "plugin": "custom-internal",
  "name": "push_to_state_machine",
  "command": "python3 /path/to/internal/state_pusher.py",
  "condition": "event_type == 'UserPromptSubmit' AND workspace_changed == true",
  "export_result": true,
  "target_system": "SOAR_DART"
}
```

## Testing

### List all hooks
```bash
python3 /home/daeron/Somnus-MCP/hook_executor.py --list
```

### Dry-run a hook type
```bash
python3 /home/daeron/Somnus-MCP/hook_executor.py PreToolUse --dry-run
```

### Execute hooks for an event
```bash
python3 /home/daeron/Somnus-MCP/hook_executor.py Stop
```

## Next Steps

1. **MCP Integration** — Add hook executor as a native bb7_ tool in mcp_server.py
2. **Auto-Trigger Wiring** — Hook claude-code harness events to auto-call hook_executor
3. **State Persistence** — Log hook results to state machine database
4. **Custom Hooks** — Define hooks for internal systems integration
