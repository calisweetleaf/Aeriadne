### Project Context Tools (`project_context_tool.py`)

> **Doctrine.** Project context is a derived view, not a source of truth. These tools
> introspect the workspace filesystem to surface structure, dependencies, recent git
> activity, and code metrics formatted for LLM context windows. They never modify
> project state and never claim ownership of any file. Treat their output as
> situational awareness to inform routing decisions in `auto_tool_module` and
> `exoskeleton_tool`, not as canonical memory.
>
> **Pairing.** Sits downstream of `file_tool` (filesystem reads are delegated when
> `read_file` already returns a snapshot) and `shell_tool` (git log + diff data
> rides through the sandbox). The three `(2026-04-10 ADDED)` entries that previously
> lived here — `bb7_workspace_context_loader`, `bb7_show_available_capabilities`,
> `bb7_intelligent_tool_guide` — were re-assigned to `auto_tool_module.py` because
> they are routing surfaces, not project-introspection surfaces. They have been
> removed from this file. See `runtime-tools/auto-tool-module.md`.
>
> **Deprecation note — `tools/project_context_tool (1).py`:** A duplicate
> source file exists with a different (`async`, SQLite-backed) implementation
> of the same 4 bb7_ names, plus 2 extras (`bb7_analyze_development_environment`,
> `bb7_security_audit`). Its `ProjectContextTool` class has **no `get_tools()`
> method**, so the MCP server's class-discovery loop at `mcp_server.py:4093`
> skips it — it is effectively dead code. Do not import from it. The 2 extra
> method names it declares are not exposed to MCP and should be migrated to
> this canonical file (or to `enhanced_code_analysis_tool.py`) before the
> duplicate is deleted.

| Subsystem / Class | Role |
|---|---|
| `ProjectContextTool` | Wraps every `bb7_*` method. |
| `_detect_project_type` | Heuristic detector (Python, Node, Rust, Go, mixed). |
| `_build_directory_tree` | Bounded tree walker with ignore list (`_get_ignored_dirs`). |
| `_parse_python_dependencies` | Reads `requirements.txt` / `pyproject.toml`. |
| `_parse_node_dependencies` | Reads `package.json` (incl. devDependencies). |
| `_format_*_for_llm` | Compacts raw analysis into the LLM context budget. |

**Ignores:** `__pycache__`, `.git`, `node_modules`, `.venv`, `mcp.venv`, `data/`,
`dist/`, `build/`, `.cache/`, `.tox/`, `.mypy_cache/`, `.pytest_cache/`,
`target/`, `.next/`, `.nuxt/`. Use `include_hidden=true` to opt in to dotfiles
on a per-call basis.

---

#### `bb7_analyze_project_structure`

Analyze and summarize project structure, detecting project types and technologies.
**Internal Composition**: Delegates to `ProjectContextTool.analyze_project_structure()`,
which calls `_detect_project_type`, `_build_directory_tree`, `_find_key_files`,
and `_format_analysis_for_llm`. Returns a Markdown tree with a header block.

- **Parameters**:
  - `max_depth` (number, optional): Maximum directory depth to walk (default: `3`).
  - `include_hidden` (boolean, optional): Include dotfiles / dot-directories (default: `false`).

#### `bb7_get_project_dependencies`

Extract and summarize project dependencies (Python `requirements.txt` /
`pyproject.toml`, Node `package.json`, etc.) in an LLM-friendly format.
**Internal Composition**: Maps to `ProjectContextTool.get_project_dependencies()`,
dispatching to `_parse_python_dependencies` or `_parse_node_dependencies`
based on the detected project type. Falls back to "no dependency files found"
if neither marker is present.

- **Parameters**: None.

#### `bb7_get_recent_changes`

Get recent Git changes (commits and modified files) to provide development
context. Calls `git log` and `git diff` via the process layer; returns
"not a git repository" if the workspace has no `.git/`.
**Internal Composition**: Delegates to `ProjectContextTool.get_recent_changes()`.

- **Parameters**:
  - `days` (number, optional): Look-back window in days (default: `7`).

#### `bb7_get_code_metrics`

Generate code metrics and statistics — total line count, language breakdown
(by extension), largest files, average file size — across the workspace.
**Internal Composition**: Maps to `ProjectContextTool.get_code_metrics()`,
which composes the metric summary in `_format_metrics_for_llm`.

- **Parameters**: None.
