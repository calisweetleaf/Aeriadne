### VS Code Terminal Integration Tools (`vscode_terminal_tool.py`)

`tools/vscode_terminal_tool.py` is a BB7 developer-terminal capability surface. Despite the name, it is **not limited to a VS Code extension API**: `bb7_terminal_run_command` executes host commands with `subprocess.run(..., shell=True)` from the MCP process environment. The VS Code layer is context intelligence — detecting editor/workspace signals, tracking a session `cwd`, analyzing PATH/tool availability, inferring command intent, and diagnosing output/errors.

> **bb7_ Doctrine.** Every `bb7_*` method below is a compiled tool, not a raw function. The method body wraps host primitives (`subprocess.run`, `shutil.which`, `os.chdir`, `os.environ`, `psutil`, filesystem/project scans) with VS Code context detection, session-persistent directory state, project-type fingerprinting, PATH/tool analysis, command-intent inference, history analytics, and error-diagnosis heuristics.

> **Pairing with Shell Tools (`shell_tool.py`).** Prefer `bb7_terminal_*` for editor/workspace development workflows because it tracks directory state and gives richer dev-context analysis. Keep `shell_tool.py` for lower-level host/system operations, process/system inventory, environment-injected command execution, and commands where its explicit `_check_command_security()` gate matters. `bb7_terminal_run_command` has timeout/output capture and diagnostics but does not apply the same dangerous-command precheck as `bb7_run_command`.

#### Current terminal endpoints

| Endpoint | Status | Contract |
|---|---|---|
| `bb7_terminal_status` | active | Reports VS Code detection, shell/platform/user, current directory, development context, environment summary, integrations, performance history, dev processes, capabilities, and recommendations. |
| `bb7_terminal_run_command` | active | Executes a host shell command from the tracked terminal directory, records in in-memory terminal history, analyzes stdout/stderr, detects environment changes, and suggests next steps. |
| `bb7_terminal_environment` | active | Analyzes shell/platform, development toolchain, PATH health, environment variables, shell config, optimization suggestions, VS Code tips, and quick diagnostics. |
| `bb7_terminal_history` | active | Displays in-memory terminal command history with filtering, analytics, performance trends, pattern detection, workflow insights, error analysis, and automation opportunities. |
| `bb7_terminal_cd` | active | Updates tracked terminal directory and process cwd with project/context detection, directory preview, development hints, navigation history, and smart suggestions. |
| `bb7_terminal_which` | active | Locates executables via PATH, reports file/version/PATH context, alternatives, related commands, installation suggestions, and environment notes. |

#### `bb7_terminal_status`

Get comprehensive terminal status, VS Code detection state, shell type, current directory, development context, environment summary, terminal integrations, and recent command metrics.
**Internal Composition**: Uses `_detect_vscode_context()`, `_detect_shell_type()`, `_get_system_info()`, `_detect_workspace_path()`, `_analyze_development_context()`, `_detect_terminal_integrations()`, `_get_development_processes()`, `_analyze_terminal_capabilities()`, and `_generate_terminal_recommendations()`.

- **Parameters**:
  - `include_environment` (boolean, optional): Include filtered environment variable summary and PATH count (default: `true`).
  - `include_integrations` (boolean, optional): Include terminal integration/tool availability checks (default: `true`).
  - `include_performance` (boolean, optional): Include recent in-memory command performance metrics (default: `true`).

#### `bb7_terminal_run_command`

Execute a command in the tracked terminal context with host `subprocess.run(shell=True)`, output/error analysis, command-intent inference, history capture, environment-change detection, and next-step suggestions.
**Internal Composition**: Uses `_analyze_command_intent()`, `subprocess.run()`, `_update_current_directory()`, `_analyze_command_output()`, `_analyze_command_error()`, `_get_command_suggestions()`, `_detect_environment_changes()`, `_get_command_performance_insights()`, and `_suggest_next_steps()`.

- **Parameters**:
  - `command` (string, required): Command to execute in the host shell.
  - `change_directory` (boolean, optional): Use and update the tracked terminal directory when possible (default: `true`).
  - `timeout` (integer, optional): Command timeout in seconds (default: 30).
  - `capture_environment` (boolean, optional): Detect environment changes after execution (default: `true`).

#### `bb7_terminal_environment`

Analyze the terminal environment, development toolchain, PATH configuration, environment variables, shell configuration, and setup health.
**Internal Composition**: Uses `_detect_development_environment()`, `_analyze_path_environment()`, `_check_development_tools()`, `_analyze_environment_variables()`, `_analyze_shell_configuration()`, `_generate_environment_suggestions()`, `_get_vscode_terminal_tips()`, and `_run_environment_diagnostics()`.

- **Parameters**:
  - `include_paths` (boolean, optional): Include detailed PATH analysis (default: `true`).
  - `include_tools` (boolean, optional): Check development tool availability and versions (default: `true`).
  - `include_suggestions` (boolean, optional): Include optimization suggestions (default: `true`).

#### `bb7_terminal_history`

Review and analyze in-memory terminal command history with usage analytics, performance trends, workflow pattern detection, error analysis, and automation suggestions.
**Internal Composition**: Reads `self.terminal_history` and uses `_analyze_command_history()`, `_format_time_ago()`, `_analyze_performance_trends()`, `_detect_command_patterns()`, `_analyze_workflow_patterns()`, and `_suggest_automation_opportunities()`.

- **Parameters**:
  - `limit` (integer, optional): Maximum number of commands to show (default: 20).
  - `filter` (string, optional): Filter command history by substring.
  - `include_analytics` (boolean, optional): Include usage and success analytics (default: `true`).
  - `show_performance` (boolean, optional): Include performance trend analysis (default: `true`).

#### `bb7_terminal_cd`

Navigate directories with tracked terminal state, process cwd mutation, project detection, directory preview, development context analysis, navigation history, and smart suggestions.
**Internal Composition**: Uses path normalization, `os.chdir()`, `_analyze_directory_context()`, `_find_similar_directories()`, `_detect_project_info()`, `_get_directory_preview()`, `_detect_directory_dev_context()`, and `_get_directory_suggestions()`.

- **Parameters**:
  - `path` (string, optional): Directory path to navigate to. If omitted, reports the current tracked directory.
  - `analyze_context` (boolean, optional): Analyze target directory context, contents, and project info (default: `true`).
  - `track_session` (boolean, optional): Track navigation in in-memory session history (default: `true`).

#### `bb7_terminal_which`

Locate executables and analyze command availability with PATH context, version detection, alternatives, related commands, installation suggestions, and environment-specific notes.
**Internal Composition**: Uses `shutil.which()`, `_get_command_version()`, `_analyze_command_path_context()`, `_find_command_alternatives()`, `_find_similar_commands()`, `_get_installation_suggestions()`, `_get_command_usage_context()`, `_get_related_commands()`, and `_get_environment_specific_notes()`.

- **Parameters**:
  - `command` (string, required): Command name to locate.
  - `show_alternatives` (boolean, optional): Show alternative locations in PATH (default: `true`).
  - `include_version` (boolean, optional): Detect command version information (default: `true`).
  - `analyze_path` (boolean, optional): Analyze PATH context for the command (default: `true`).
