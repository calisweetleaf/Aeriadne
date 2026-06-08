### Shell Tools (`shell_tool.py`)

`tools/shell_tool.py` is the BB7 system-shell capability surface for guarded host command execution, system inventory, process listing, and shell command history. It is still distinct from `vscode_terminal_tool.py`: shell owns lower-level host/system inspection and explicit command security prechecks, while terminal owns richer editor/workspace development context.

> **bb7_ Doctrine.** Every `bb7_*` method below is a compiled tool, not a raw function. The method body wraps host primitives (`subprocess.run`, `psutil`, platform/environment inspection) with `_check_command_security()`, bounded timeouts, stdout/stderr formatting, output/error analysis, performance insights, and actionable suggestions.

> **Pairing with VS Code Terminal Tools (`vscode_terminal_tool.py`).** Prefer `bb7_terminal_*` for workspace/editor development flows, tracked directory state, PATH/tool discovery, and terminal-history analytics. Use `shell_tool.py` for host/system-level execution, process/system inventory, explicit environment injection, and commands where its dangerous-pattern security gate is desired. `bb7_terminal_run_command` also executes host shell commands, but it does not apply `shell_tool.py`'s `_check_command_security()` gate.

#### Current shell endpoints

| Endpoint | Status | Contract |
|---|---|---|
| `bb7_run_command` | active | Executes a host shell command through `subprocess.run(shell=True)` after `_check_command_security()`, validates working directory, merges optional environment variables, captures output by default, records in in-memory command history, and returns output/error diagnostics. |
| `bb7_get_system_info` | active | Reports OS/platform/user/shell, CPU/memory, optional disk/network/process details, development tool detection, health issues, and performance recommendations. |
| `bb7_list_processes` | active | Lists running processes via `psutil`, supports filtering/sorting/limits, hides system users by default, detects high CPU/memory and development-related processes, and emits recommendations. |
| `bb7_get_command_history` | active | Displays in-memory `bb7_run_command` history with filtering, success-only mode, stats, most-used commands, slow commands, failures, and optimization suggestions. |

#### `bb7_run_command`

Execute shell commands with security precheck, working-directory validation, environment injection, bounded timeout, output/error analysis, and in-memory command history tracking.
**Internal Composition**: Uses `_check_command_security()`, `Path(...).resolve()`, `subprocess.run()`, `set_default_output()`, `_analyze_command_output()`, `_analyze_error_output()`, `_get_performance_insights()`, and `_get_command_suggestions()`.

- **Parameters**:
  - `command` (string, required): Shell command to execute.
  - `working_directory` (string, optional): Directory to run the command in (default: `.`).
  - `timeout` (integer, optional): Command timeout in seconds. Runtime caps it at `self.max_timeout` (300s).
  - `capture_output` (boolean, optional): Whether to capture command output (default: `true`).
  - `environment` (object, optional): Additional environment variables merged into the process environment.

#### `bb7_get_system_info`

Get comprehensive system information including OS/platform, environment, CPU/memory, disk usage, optional network/process details, development tool detection, health issues, and performance recommendations.
**Internal Composition**: Uses `_get_system_info()`, `psutil.cpu_percent()`, `psutil.virtual_memory()`, `psutil.disk_partitions()`, `psutil.disk_usage()`, `psutil.net_if_addrs()`, `psutil.net_io_counters()`, `psutil.process_iter()`, `_detect_development_tools()`, `_assess_system_health()`, and `_get_performance_recommendations()`.

- **Parameters**:
  - `include_processes` (boolean, optional): Include top process information (default: `false`).
  - `include_network` (boolean, optional): Include network interface/counter information (default: `false`).
  - `include_disk_usage` (boolean, optional): Include disk usage information (default: `true`).

#### `bb7_list_processes`

List and analyze running processes with filtering, sorting, resource metrics, development-process detection, and recommendations.
**Internal Composition**: Uses `psutil.process_iter()` over PID/name/CPU/memory/status/user fields, filters by name, optionally hides system users, computes memory/age metrics, sorts, and formats high-resource process diagnostics.

- **Parameters**:
  - `filter` (string, optional): Filter processes by name substring.
  - `sort_by` (string, optional): Sort processes by `cpu`, `memory`, `name`, `pid`, or `age` (default: `cpu`).
  - `limit` (integer, optional): Maximum number of processes to show (default: 20).
  - `show_system_processes` (boolean, optional): Include system/root processes in results (default: `false`).

#### `bb7_get_command_history`

View in-memory command execution history captured by this `ShellTool` instance with performance analysis, success rates, common commands, slow command detection, failures, and automation recommendations.
**Internal Composition**: Reads `self.command_history`, applies optional filters, sorts by timestamp, computes statistics/frequencies, and uses `_format_time_ago()` for recency formatting.

- **Parameters**:
  - `limit` (integer, optional): Maximum number of commands to show (default: 20).
  - `filter` (string, optional): Filter commands by substring.
  - `show_successful_only` (boolean, optional): Show only successful commands (default: `false`).
