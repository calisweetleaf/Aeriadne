### Code Analysis Tools (Legacy) (`code_analysis_tool.py`)

> **Doctrine.** This module is the **legacy** code-analysis surface, superseded
> by `tools/enhanced_code_analysis_tool.py` (`runtime-tools/enhanced-code-analysis-tool.md`).
> Both modules register a `CodeAnalysisTool` class with `get_tools()` under
> class-discovery priority 5, so the MCP server will load whichever sorts
> first in `inspect.getmembers` order — effectively non-deterministic on
> Python's member iteration. The two surfaces share `bb7_analyze_code` and
> `bb7_security_audit` names with **different** implementations; the legacy
> versions are simpler and lack RestrictedPython sandboxes, AST data-flow
> analysis, and resource limits.
>
> **Pairing.** Do not pair-call legacy `code_analysis_tool` with
> `enhanced_code_analysis_tool` — pick one. New agents should call the
> enhanced version. This file is documented for **archaeology and rotation
> purposes** so future agents know what these 4 tool names refer to when
> they appear in old session logs or thoughts.

| Subsystem / Class | Role |
|---|---|
| `CodeAnalysisTool` | Legacy façade. Owns the `get_tools()` registry. |
| `_analyze_code_overview` | Function/class/import counts. |
| `_calculate_quality_metrics` | Complexity, maintainability, density, comment ratio. |
| `_analyze_python_structure` | Python-specific AST walk. |
| `_analyze_code_patterns` | Design-pattern / anti-pattern detection. |
| `_analyze_dependencies` | Import + external-dependency mapping. |
| `_generate_improvement_suggestions` | Heuristic recommendations. |
| `_generate_overall_assessment` | Readability/maintainability/security score. |
| `_pre_execution_security_check` | Pre-exec static safety review. |
| `_analyze_execution_error` / `_analyze_execution_results` | Post-exec result analysis. |

---

#### `bb7_analyze_code`

Comprehensive static code analysis — AST parsing, complexity metrics,
security auditing, pattern detection, quality assessment. Accepts inline
code or reads from `file_path`.
**Internal Composition**: Calls `CodeAnalysisTool.bb7_analyze_code()`. Composes
`_analyze_code_overview` → `_calculate_quality_metrics` → security branch →
`_analyze_code_patterns` → `_analyze_dependencies` → `_generate_improvement_suggestions`
→ `_generate_overall_assessment`.

- **Parameters**:
  - `code` (string, optional): Inline source code.
  - `language` (string, optional): `python`, `javascript`, `typescript`, `java`, `cpp`, `c`, `go`, `rust` (default: `python`).
  - `include_security` (boolean, optional): Include security analysis (default: true).
  - `include_metrics` (boolean, optional): Include quality metrics (default: true).
  - `include_suggestions` (boolean, optional): Include improvement suggestions (default: true).
  - `file_path` (string, optional): Read code from this path if `code` is empty.

#### `bb7_code_suggestions`

Generate intelligent code improvement suggestions — refactoring, performance,
security, readability, maintainability — at a target skill level.
**Internal Composition**: Calls `CodeAnalysisTool.bb7_code_suggestions()`. Composes
`_generate_targeted_suggestions` against the focus area, then buckets the
results into Performance / Security / Readability / Maintainability / Best
Practices categories.

- **Parameters**:
  - `code` (string, required): Source code to analyse.
  - `language` (string, optional): Programming language (default: `python`).
  - `focus_area` (string, optional): `performance`, `security`, `readability`, `maintainability`, or `all` (default: `all`).
  - `skill_level` (string, optional): `beginner`, `intermediate`, or `advanced` (default: `intermediate`).

#### `bb7_security_audit`

Detailed security audit of code — vulnerability detection, unsafe pattern
identification, compliance checking, remediation guidance.
**Internal Composition**: Calls `CodeAnalysisTool.bb7_security_audit()`.
Composes `_analyze_code_patterns` (security branch) with the
`_security_patterns` and `_architecture_patterns` lookup tables, emits
issue list with line numbers and severity.

- **Parameters**:
  - `code` (string, required): Source code to audit.
  - `language` (string, optional): Programming language (default: `python`).

#### `bb7_execute_code_safely`

Execute code in a sandboxed environment with pre-execution security
checks and post-execution analysis. **No RestrictedPython** — uses basic
pre-exec static checks only.
**Internal Composition**: Calls `CodeAnalysisTool.bb7_execute_code_safely()`.
Composes `_pre_execution_security_check` → execution → `_analyze_execution_results`
→ `_analyze_performance` → `_generate_execution_suggestions`.

- **Parameters**:
  - `code` (string, required): Source code to execute.
  - `language` (string, optional): Programming language (default: `python`).
