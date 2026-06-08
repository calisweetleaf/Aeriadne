### Code Analysis & Secure Python Execution Tools (`enhanced_code_analysis_tool.py`)

> **bb7_ doctrine:** `bb7_` is not the tool — it compiles a smarter tool. The four `bb7_*` methods here are thin orchestrators on top of three heavy subsystems (`AdvancedCodeAnalyzer`, `SecurePythonInterpreter`, `SecurityAuditor`). The `bb7_*` surface handles argument extraction, size-gate deflection, error framing, and human-readable formatting; the actual CFA/DFA/type-inference/sandboxed-execution work is delegated to subsystems. Callers can chain: `bb7_analyze_code_complete` → `bb7_security_audit` (faster re-audit focused on issues) → `bb7_get_execution_audit` (verify no regressions in the audit log).

> **Pairing: shell-tool + this file is a deflection pair.** The size gates in `bb7_analyze_code_complete` (60,000 bytes / 800 lines) and `bb7_security_audit` (60,000 bytes) deflect oversized Python files to `bb7_shell_execute` (or `bb7_run_command`) with pre-built `grep`/`wc`/`py_compile` commands. Do not attempt to bypass the size gate by chunking — the AST pass requires the full source in memory. Pair with `thought-journal-tool` for storing analysis results; the execution audit log here is independent and not journaled by the MCP server.

#### Subsystem Inventory

The `bb7_*` surface delegates to these subsystem classes (defined in the same file, lines 75-1499):

| Class | Lines | Role |
|---|---|---|
| `CodeLocation` (dataclass) | 75 | Source position record: file/line/column + optional end positions. |
| `Variable` (dataclass) | 85 | Variable record: name, type hint, inferred type, scope, definitions/usages, parameter/global flags. |
| `Function` (dataclass) | 100 | Function record: params, return type, complexity, calls/called_by, locals, security issues, CFG node/edge counts. |
| `ControlFlowNode` (dataclass) | 115 | CFG node: id, type (`entry`/`exit`/`statement`/`condition`/`loop`/`exception`), code, location, predecessor/successor/dominator/post-dominator sets, reaching defs, live vars. |
| `DataFlowFact` (dataclass) | 130 | DFA fact: variable, definition line, reaching definitions, live variables. |
| `SecurityAuditor` | 139 | Pattern + AST security scanner. Five pattern families (`sql_injection`, `command_injection`, `path_traversal`, `hardcoded_secrets`, `dangerous_imports`) plus a `dangerous_functions` blocklist. |
| `AdvancedCodeAnalyzer` | (in same file, pre-1500) | Composes CFA (dominance), DFA (reaching-defs + live-vars), type inference (constraint solving), and security — all behind a single `analyze_file(path, include_cfa, include_dfa, include_types, include_security)` entry point. |
| `SecurePythonInterpreter` | (in same file, pre-1500) | Hardened Python execution using `RestrictedPython.compile_restricted` + `safe_globals`/`safe_builtins`/`limited_builtins` + `PrintCollector`. Resource-limit gated via the optional `resource` stdlib module (Linux/macOS only). |
| `_FallbackPrintCollector` | 58 | Minimal drop-in for `RestrictedPython.PrintCollector` when RestrictedPython is not importable. |
| `CodeAnalysisTool` (the `bb7_*` host) | 1500 | The MCP wrapper. Owns one `AdvancedCodeAnalyzer` and one `SecurePythonInterpreter`; no per-call reinit. |

**RestrictedPython soft-degrade**: Lines 43-55 set `RESTRICTED_PYTHON_AVAILABLE` and provide fallback empty dicts. If RestrictedPython cannot be imported, the interpreter falls back to the basic `_FallbackPrintCollector` for `_print_` and disables the `_getattr_` / `_getitem_` / `_write_` guards. **Fail LOUD**: import-time warnings are emitted to the logger; the interpreter does not silently execute un-sandboxed code unless RestrictedPython is missing.

**Size gate doctrine**: Both `bb7_analyze_code_complete` and `bb7_security_audit` check `os.stat().st_size > 60_000 bytes` (`bb7_analyze_code_complete` also re-counts lines and checks `> 800` lines) and deflect with a pre-built `bb7_shell_execute` recipe. This prevents OOM during full-source AST analysis. The deflection message names the alternative tool, not just the file path.

---

#### `bb7_analyze_code_complete`

Complete code analysis with all AST/CFA/DFA/type/security passes enabled. For non-Python files, returns a basic size/lines/extension summary. For oversized Python files, deflects to `bb7_shell_execute`.

**Internal Composition**: Argument-extracts `file_path` and `include_all` (default `True`). On non-`.py` files, returns `os.stat` + `f.read().splitlines()` summary without invoking the analyzer. On `.py` files > 60,000 bytes or > 800 lines, emits a deflection message with pre-built `grep -n`/`wc -l`/`python3 -m py_compile` commands. Otherwise calls `self.analyzer.analyze_file(file_path, include_cfa=include_all, include_dfa=include_all, include_types=include_all, include_security=include_all)` and pipes the dict through `_format_complete_analysis` which renders metrics, CFA per-function (nodes/edges/cyclomatic complexity), DFA per-function (unused-variable counts), type coverage percentage, and security by-severity counts.

- **Parameters**:
  - `file_path` (string, **required**): Absolute or relative path. Existence and `.py` extension are enforced. Non-`.py` files get a basic summary; missing files return `❌ File not found`.
  - `include_all` (boolean, optional, default `true`): Toggle for CFA, DFA, types, and security passes. All four are coupled; there is no per-pass selector at this surface.

#### `bb7_python_execute_secure`

Execute a Python code snippet inside the `SecurePythonInterpreter` sandbox with optional input injection, stateless mode, and a dry-run security scan.

**Internal Composition**: Argument-extracts `code`, `input_data` (parsed via `json.loads` if string, otherwise passed through), `stateless` (default `True`), `dry_run` (default `False`). Parses input JSON before passing to interpreter. Calls `self.interpreter.execute_code(code, input_data=parsed_input, stateless=stateless, dry_run=dry_run)` and pipes through `_format_execution_result` which renders: `🛡️ DRY RUN` for dry runs, `🚫 EXECUTION BLOCKED - Security Issues` (first 3) for security blocks, `✅ Python Execution Successful` with execution_id, timing, memory, stdout, stderr, and `variables_created` for success paths.

- **Parameters**:
  - `code` (string, **required**): Python source. Empty string returns `❌ code is required`.
  - `input_data` (string, optional): JSON string parsed into a Python object. Invalid JSON returns `❌ Invalid input data JSON format`.
  - `stateless` (boolean, optional, default `true`): When `true`, no variable persistence between calls.
  - `dry_run` (boolean, optional, default `false`): Security-scan only, do not execute. Returns `🛡️ DRY RUN - Code passed security scan` plus an execution_id.

#### `bb7_security_audit`

Run only the security pass (`include_security=True`, all other passes off) for a faster, focused vulnerability scan. Same size gate as `bb7_analyze_code_complete`.

**Internal Composition**: Argument-extracts `file_path`. Enforces `.py` extension (non-`.py` files return a "Security audit is only available for Python files" notice). Enforces `os.stat().st_size <= 60_000 bytes` (deflection message points at `bb7_shell_execute` with `grep -n 'eval\|exec\|__import__\|subprocess\|os\.system'` and `grep -n 'pickle\|yaml\.load\|input('` recipes). Calls `self.analyzer.analyze_file(file_path, include_cfa=False, include_dfa=False, include_types=False, include_security=True)`, extracts `result["security_analysis"]`, and pipes through `_format_security_audit` which renders `🚨 Found N security issues` plus per-severity groups (`HIGH`/`MEDIUM`/`LOW` with red/yellow/green dots, first 5 issues per severity with line + description + 50-char code preview, "... and N more" overflow).

- **Parameters**:
  - `file_path` (string, **required**): Path to a `.py` file. Missing files return `❌ File not found`.

#### `bb7_get_execution_audit`

Retrieve the audit log of recent `bb7_python_execute_secure` calls. Read-only access to the interpreter's in-memory audit buffer.

**Internal Composition**: Argument-extracts `limit` (default `20` if not in the dict, else caller value). Calls `self.interpreter.get_audit_log(limit)` and pipes through `_format_audit_log` which renders: `📋 No execution history` for empty logs, or `📋 Python Execution Audit Log (N entries)` with the **last 10** entries (note: last 10, not last `limit`) showing per-entry: success emoji + timestamp (`HH:MM:SS`) + execution_id + 50-char code preview, then optional security-scan summary (`Security: N issues found`) and resource usage (`Resources: T.TTTs, X.XXMB`).

- **Parameters**:
  - `limit` (number, optional, default `20`): Maximum number of audit entries to fetch from the interpreter. The formatter caps the rendered output at 10 entries regardless of `limit`.
