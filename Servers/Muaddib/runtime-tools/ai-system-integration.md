### AI System Integration (`ai_system_integration_fixed.py`)

> **Doctrine.** The AI System Integration tool is a **host-level
> introspection** surface — it analyses the filesystem and the local
> hardware/software stack through two cooperating engines
> (`FileSystemIntelligence` and `SystemManagementEngine`) and exposes one
> umbrella `bb7_system_comprehensive_operation` tool that dispatches to
> four operation types. The filename suffix `_fixed` is a maintenance-tag
> marker; treat the file as the live surface unless AGENTS.md explicitly
> notes a successor.
>
> **Pairing.** Stands mostly alone — it does not delegate to any other
> `bb7_*` tool. It complements `file_tool` (which owns file reads/writes
> within the workspace) by providing **filesystem intelligence** (MIME
> detection, programming-language identification, PE/DLL analysis,
> file-relationship mapping) that `file_tool` does not expose. It also
> complements `shell_tool` for read-only system snapshots (CPU/memory
> percentages, software inventory, security posture).

| Subsystem / Class | Role |
|---|---|
| `FileSystemIntelligence` | Filesystem-side engine. Owns `advanced_file_analysis`, `intelligent_file_search`, `automated_file_organization`. |
| `_get_mime_type` / `_is_binary_file` / `_detect_programming_language` | File-classification helpers. |
| `_analyze_executable_file` / `_analyze_pe_file` / `_analyze_dll_file` | PE/DLL/EXE deep inspection. |
| `_analyze_file_security` / `_analyze_file_relationships` | Per-file security and link analysis. |
| `_search_by_content` / `_search_by_pattern` / `_search_by_relationship` / `_search_semantic` | Multi-strategy file search. |
| `_organize_by_type` / `_organize_by_date` / `_organize_by_project` / `_cleanup_duplicates` | File-organisation strategies. |
| `SystemManagementEngine` | Host-side engine. Owns `comprehensive_system_analysis` and the per-subsystem analyzers. |
| `_analyze_hardware` / `_analyze_software` / `_analyze_performance` / `_analyze_security` / `_analyze_network` / `_analyze_storage` / `_analyze_processes` | Per-subsystem analyzers. |
| `AISystemIntegrationTool` | Public façade. Composes both engines behind `bb7_system_comprehensive_operation`. |

---

#### `bb7_system_comprehensive_operation`

Comprehensive system operation with AI insights. The umbrella dispatch
tool — pass `operation_type` to choose the analysis path, plus any
operation-specific kwargs. Returns a JSON document with `success`, the
operation result, and a formatted Markdown `message` plus
`processing_time` (seconds).
**Internal Composition**: Calls `AISystemIntegrationTool.bb7_system_comprehensive_operation()`.
Dispatches on `operation_type`:
- `"file_analysis"` → `FileSystemIntelligence.advanced_file_analysis(file_path)` — MIME, language, size, security, relationships, AI recommendations.
- `"file_search"` → `FileSystemIntelligence.intelligent_file_search(query, search_path, search_type, max_results)` — content / pattern / relationship / semantic search.
- `"file_organization"` → `FileSystemIntelligence.automated_file_organization(directory, rules)` — organise by type, date, project, or deduplication.
- `"system_analysis"` → `SystemManagementEngine.comprehensive_system_analysis()` — hardware, software, performance, security, network, storage, processes.

- **Parameters**:
  - `operation_type` (string, required): One of `file_analysis`, `file_search`, `file_organization`, `system_analysis`.
  - **For `file_analysis`**:
    - `file_path` (string, required): Path to the file to analyse.
  - **For `file_search`**:
    - `query` (string, required): Search query.
    - `search_path` (string, optional): Root directory (default: `"."`).
    - `search_type` (string, optional): `content`, `pattern`, `relationship`, or `semantic` (default: `"content"`).
    - `max_results` (integer, optional): Max results to return (default: 50).
  - **For `file_organization`**:
    - `directory` (string, required): Root directory to organise.
    - `rules` (object, optional): Organisation rules (e.g. `{"by": "type", "target": "./Organized"}`).
  - **For `system_analysis`**: no additional parameters.

> **Internal helper note.** `bb7_generate_system_recommendations(analysis)`
> is a private method called from inside `bb7_system_comprehensive_operation`
> (it generates the AI recommendation list from the security/performance
> analysis). It is not registered in `get_tools()` and is not exposed
> via MCP. The single public surface for the AI System Integration tool
> is `bb7_system_comprehensive_operation`.
