### Advanced File Capability Surface (`file_tool.py`)

> **bb7_ doctrine:** `bb7_` is not the tool — it compiles a smarter tool. The twelve `bb7_*` methods here are orchestrators over a small set of internal helpers: `_detect_encoding` (sequential try-decode across 7 encodings), `_detect_file_type` (extension + binary-signature sniffing against 13 magic-byte patterns), `_analyze_content` (Python/JS/HTML/JSON/SQL/etc. language detection + counts + secret-pattern scan), `_numbered_line_window` (bounded read window formatter), `_semantic_target_window` (symbol-text matcher), `_render_large_read_isolation_manifest` (token-density governor), `_render_patch_verification_manifest` (sparse write-back manifest), and `_add_to_history` (operation-history append). The `bb7_*` surface handles argument extraction, dual-key compat (`path`/`file_path`, `start_line`/`line_start`, `pattern`/`name_pattern`, `semantic_target`/`target`/`symbol`), and the response-shaping decisions. Callers can chain: `bb7_search_files` (find candidates) → `bb7_file_info` (size pre-check) → `bb7_read_file` (with `start_line`/`end_line` or `semantic_target`) → `bb7_write_file` (with `create_backup=true`).

> **Pairing: this file is the file-state backbone of the runtime.** Pairs with [`shell-tool`](shell-tool.md) for bulk shell-driven filesystem operations (copy/move/delete loops, large file system walks), [`enhanced-code-analysis-tool`](enhanced-code-analysis-tool.md) for the reverse size-gate (large Python files OOM the AST pass; this file's read window is the recovery path), [`project-context-tool`](project-context-tool.md) for project structure analysis, and [`auto-tool-module`](auto-tool-module.md) (this file's methods are not in the router's category map — the router treats them as a low-level surface for direct invocation rather than routing). The execution side has a parallel pair: `shell-tool` + `vscode-terminal-tool`. Pairs with [`thought-journal-tool`](thought_journal_tool.md) for persisting file-derived insights — `bb7_operation_history` is the in-memory buffer, not the journal.

> **Protocol migration note (source line 36-37):** Source comment reads `# bb7_ direct tools "_.." tool server native enhancements. Should change protocol to cc8_ future revisions`. The `bb7_` prefix is a legacy convenience; do not assume any future `cc8_` namespace exists yet. If a new namespace is introduced, the migration should preserve the existing 12 `bb7_*` method names as compatibility aliases for at least one release.

> **Token-density governor in action (read path).** `bb7_read_file` is the runtime's primary defense against context-compilation failures. The `_render_large_read_isolation_manifest` helper (line ~470) intercepts reads that exceed `_read_governor_bytes()` (default 10MB unless overridden) and returns a structural skeleton + SHA256/16 digest + recovery instructions (`start_line`/`end_line`, `semantic_target`, or `allow_large_raw=true`) instead of the raw file content. This is the read-side analog of the size-gate in `bb7_analyze_code_complete`. Naked reads of `MCP_SPEC.md`, `MEMORY.md`, or other large runtime docs **must** use `start_line`/`end_line` or `semantic_target`.

#### Class & Runtime Configuration

Single class `FileTool` (line 39) hosts all twelve `bb7_*` methods. Initialization (line 45) configures:

| Config | Value | Notes |
|---|---|---|
| `temp_dir` | `<tempfile.gettempdir()>/claude_workspace` | `mkdir(exist_ok=True)` on init. Used as the default destination for `bb7_delete_file.create_backup=true` backups. |
| `operation_history` | `list[dict]` (in-memory) | Appended on every read/write/copy/move/delete. Bounded by `max_history=1000` (FIFO eviction, not enforced in the read path here). |
| `max_history` | `1000` | Operations cap. |
| `archive_formats` | `dict[ext, (label, handler)]` | `.zip`→`zipfile.ZipFile`, `.tar`/`.tar.gz`/`.tar.bz2`/`.tgz`→`tarfile.open`. |
| `text_encodings` | `utf-8, utf-16, utf-32, ascii, iso-8859-1, cp1252, cp437` | Sequentially tried by `_detect_encoding` until one decodes the first 1024 bytes. |
| `binary_signatures` | 13 magic-byte prefixes → type label | ZIP (3), GZIP, BZIP2, TAR, ELF, Windows EXE, PNG, JPEG, GIF, PDF, Microsoft Office. |

> **Docstring vs. runtime contract.** The class docstring (line 39-43) declares "Unrestricted System-Wide File Operations. NO RESTRICTIONS, NO LIMITATIONS." This is historical marketing copy. The actual runtime contract enforces: `max_size` ceilings on `bb7_read_file` (default 10MB), `max_size` ceilings on `bb7_search_files` content reads (default 1MB), `force=true` gates for directory deletion and no-backup destructive deletion, `max_results=100` and `max_depth=10` and `timeout_seconds=15.0` on `bb7_search_files`, and `allow_large_raw` opt-in for the read governor. Do not treat the docstring as a safety waiver — the gates are enforced.

---

#### `bb7_read_file`

Read a file as raw text by default, with optional bounded windows (`start_line`/`end_line`), semantic target navigation (`semantic_target` returns ±3 line context), binary detection + hex preview, and large-read governor enforcement. Accepts `path` or `file_path`; `start_line` or `line_start`; `end_line` or `line_end`; `semantic_target` or `target` or `symbol`.

**Internal Composition**: Argument-extracts from dual-key aliases. Calls `_detect_file_type` then `Path.stat()` for size. If `size > max_size` and `force_text=False`, returns the "File too large" message. Sniffs first 8192 bytes for `b'\x00'` to detect binary; binary files get a 512-byte hex+ASCII preview and are recorded to history. Otherwise calls `_detect_encoding` (sequential try-decode) then `open(encoding=, errors='replace')`. If `start_line`/`end_line` set, emits `### [TOOL VERIFICATION]: FILE_READ_WINDOW` with the bounded window. If `semantic_target` set, calls `_semantic_target_window` to find the symbol span, then `_numbered_line_window` with `context=3`; emits `FILE_READ_SEMANTIC_TARGET` or `FILE_READ_TARGET_NOT_FOUND` with recovery instructions. If `size > _read_governor_bytes()` and `allow_large_raw=False`, calls `_render_large_read_isolation_manifest` which returns a structural skeleton + SHA256/16 digest + `Recovery: request start_line/end_line, semantic_target, or allow_large_raw=True`. Otherwise returns raw content (or decorated markdown if `show_analysis=true` or `format in {'analysis','markdown','decorated'}`).

- **Parameters**:
  - `path` or `file_path` (string, **required**): Absolute or relative path. Empty string returns "Specify file path."
  - `start_line` or `line_start` (integer, optional): 1-indexed first line of bounded read window.
  - `end_line` or `line_end` (integer, optional): 1-indexed last line of bounded read window.
  - `semantic_target` or `target` or `symbol` (string, optional): Symbol/text target (class/function/method/unique marker). Returns ±3 line context.
  - `max_size` (integer, optional, default `10485760` (10MB)): Filesystem read ceiling. Reads above this refuse without `force_text=true`.
  - `force_text` (boolean, optional, default `false`): Force reading binary files as text.
  - `show_analysis` (boolean, optional, default `false`): Return decorated markdown with language/line/char/function/class/secret analysis.
  - `format` (string, optional, default `raw`): `raw` returns content directly; `analysis` / `markdown` / `decorated` returns the show_analysis block.
  - `allow_large_raw` (boolean, optional, default `false`): Bypass the large-read governor and return raw content. Use with caution.

#### `bb7_write_file`

Write or create a file with parent directory creation, optional timestamped backup, encoding selection, and optional executable bit. Returns a patch verification manifest.

**Internal Composition**: Argument-extracts from `path`/`file_path`. `Path(path).expanduser().resolve()`, then `parent.mkdir(parents=True, exist_ok=True)`. If file exists and is a file, reads old content into `old_content`. If `create_backup=true`, calls `shutil.copy2(file_path, file_path.with_suffix(f".backup_{YYYYMMDD_HHMMSS}{file_path.suffix}"))`. Writes content with `open(..., 'w', encoding=encoding, newline='\n')`. If `make_executable=true`, ORs `S_IEXEC` into the current mode via `chmod`. Analyzes content via `_analyze_content` and detects file type via `_detect_file_type`. Appends to `operation_history` with size/backup-path/analysis. Returns `_render_patch_verification_manifest(..., operation="write_file", backup_path=..., make_executable=...)` which produces a sparse diff-style manifest (old vs new fingerprint, line counts, backup path) rather than the full file body.

- **Parameters**:
  - `path` or `file_path` (string, **required**): File path. Empty string returns "Specify file path."
  - `content` (string, **required**): Content to write. `None` returns "Provide content to write."
  - `encoding` (string, optional, default `utf-8`): File encoding.
  - `create_backup` (boolean, optional, default `true`): Create `<path>.backup_{YYYYMMDD_HHMMSS}<suffix>` if file exists.
  - `make_executable` (boolean, optional, default `false`): Set executable permissions via `chmod | S_IEXEC`.

#### `bb7_append_file`

Append text content to a file. Historical compatibility surface.

**Internal Composition**: Argument-extracts. Resolves path, creates parent directories. If file exists and `create_backup=true`, copies to backup. Opens in append mode, writes content, closes. Analyzes content + detects file type, appends to `operation_history` with `operation='append'`.

- **Parameters**:
  - `path` or `file_path` (string, **required**): File path to append to.
  - `content` (string, **required**): Content to append.
  - `encoding` (string, optional, default `utf-8`): File encoding.
  - `create_backup` (boolean, optional, default `false`): Backup before appending. Off by default (historical behavior).

#### `bb7_copy_file`

Copy a file or directory to a destination path.

**Internal Composition**: `shutil.copy2()` (preserves metadata) or `shutil.copytree()` for directories. Honors `overwrite` and `preserve_metadata` flags. Appends to `operation_history` with `operation='copy'`.

- **Parameters**:
  - `source` (string, **required**): Source path of file or directory.
  - `destination` (string, **required**): Destination path.
  - `overwrite` (boolean, optional, default `false`): Overwrite destination if it exists.
  - `preserve_metadata` (boolean, optional, default `true`): Preserve timestamps and permissions via `copy2`/`copy2`-equivalent.

#### `bb7_move_file`

Move or rename a file or directory.

**Internal Composition**: `shutil.move()` with overwrite-safe checks. Appends to `operation_history` with `operation='move'`.

- **Parameters**:
  - `source` (string, **required**): Source path.
  - `destination` (string, **required**): Destination path.

#### `bb7_delete_file`

Remove a file or directory. **Directory deletion, or any delete with `create_backup=false`, requires `force=true`.** This is the runtime's primary defense against accidental irreversible state loss.

**Internal Composition**: Argument-extracts path/force/create_backup. If `path` is a directory, requires `force=true`; else returns the directory-refusal error. If `create_backup=true`, copies the file to `temp_dir / claude_workspace` (timestamped) before deletion. Removes the file. Appends to `operation_history` with `operation='delete'` and the backup path.

- **Parameters**:
  - `path` (string, **required**): Path to delete.
  - `force` (boolean, optional, default `false`): Required for directory deletion or no-backup destructive deletion.
  - `create_backup` (boolean, optional, default `true`): Backup to `temp_dir/claude_workspace/` before deletion.

#### `bb7_list_directory`

List directory contents with metadata-rich metrics, sorting, and per-entry details.

**Internal Composition**: `Path(path).iterdir()` filtered by `show_hidden`. Sorts by `name`/`size`/`modified`/`type`. Caps at `max_items`. Per-entry details include size, modified timestamp, type, and permissions. Appends to `operation_history` with `operation='list'`.

- **Parameters**:
  - `path` (string, optional, default `.`): Directory to list.
  - `show_hidden` (boolean, optional, default `true`): Include dotfiles.
  - `sort_by` (string, optional, default `name`): `name` / `size` / `modified` / `type`.
  - `max_items` (integer, optional, default `200`): Cap on entry count.
  - `show_details` (boolean, optional, default `true`): Include size/timestamp/type/permissions.

#### `bb7_search_files`

Bounded recursive search by name pattern and/or content pattern. Skips symlink loops and heavy runtime directories.

**Internal Composition**: `Path(directory).rglob(pattern)` with `name_pattern`/`pattern` alias resolution. Skips `__pycache__`, `.git`, `node_modules`, `.venv`, `data/`, and any caller-supplied `skip_dirs` entries. Symlink loop detection. For each match, optionally reads up to `content_read_limit` bytes and runs the content regex. Capped at `max_results`. Bounded by `timeout_seconds` and `max_depth`.

- **Parameters**:
  - `directory` (string, optional, default `.`): Root directory to search.
  - `pattern` or `name_pattern` (string, optional, default `*`): Glob pattern (legacy `pattern` alias accepted).
  - `content_pattern` (string, optional): Regex/substring to search within file contents.
  - `max_results` (integer, optional, default `100`): Bounded result count.
  - `include_hidden` (boolean, optional, default `false`): Include hidden directories/files.
  - `max_depth` (integer, optional, default `10`): Recursion depth cap.
  - `file_size_min` (integer, optional, default `0`): Minimum file size in bytes.
  - `file_size_max` (integer, optional): Maximum file size in bytes.
  - `timeout_seconds` (number, optional, default `15.0`): Search deadline.
  - `content_read_limit` (integer, optional, default `1048576` (1MB)): Per-file content read cap.
  - `skip_dirs` (array of strings, optional): Additional directory names to skip.

#### `bb7_file_info`

Comprehensive file or directory metadata with Linux-safe stat handling. Canonical info surface.

**Internal Composition**: `Path(path).stat()` (Linux-safe: no Windows quirks). Computes size, modified/created/accessed timestamps, mode, owner (best-effort), and content-type via `_detect_file_type`. For directories, also computes entry count.

- **Parameters**:
  - `path` (string, **required**): Target file or directory.

#### `bb7_get_file_info`

**Compatibility alias** for `bb7_file_info`. Single-line forwarder.

**Internal Composition**: `return self.bb7_file_info(arguments)`.

- **Parameters**:
  - `path` (string, **required**): Target file or directory.

#### `bb7_file_cache_stats`

**Compatibility shim** for the removed legacy `FileContentCache`. Reports cache-removal status plus operation-history statistics. **Returns JSON, not human-readable text.**

**Internal Composition**: Iterates `self.operation_history` to build `op_counts` (`operation → count`). Returns `json.dumps({status: 'compatibility_shim', cache: 'removed', message: '...', operation_history_entries: N, operation_counts: {...}, max_history: 1000}, indent=2)`.

- **Parameters**: None.

#### `bb7_operation_history`

View recent file-operation history with summary statistics, optional `operation_type` filter, and bounded `limit`.

**Internal Composition**: Filters `self.operation_history` by `operation_type` (if supplied). Slices to last `limit` entries. Computes per-operation counts across the full history. Renders `📋 File Operation History` header, `Operation Summary` (per-type totals sorted by count desc), then `Recent Operations` (timestamp, operation, path, size, type) in reverse-chronological order.

- **Parameters**:
  - `limit` (integer, optional, default `20`): Max recent entries to return.
  - `operation_type` (string, optional): Filter to a single operation type (e.g., `read`, `write`, `copy`, `move`, `delete`, `append`, `list`).
