#!/usr/bin/env python3
"""
Unleashed File Tool - Unrestricted System-Wide File Operations
============================================================

Maximum capability file operations for Claude collaborative intelligence.
NO RESTRICTIONS, NO LIMITATIONS - Full system access for true partnership.

This tool provides unrestricted access to the entire file system with
intelligent analysis, bulk operations, and advanced file manipulation.
Designed for maximum power and flexibility in our AI lab environment.
"""

import os
import shutil
import stat
import time
import json
import ast
import difflib
import hashlib
import zipfile
import tarfile
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import mimetypes
import fnmatch
import threading
from concurrent.futures import ThreadPoolExecutor
import base64

# bb7_ direct tools "_.." tool server native enhancements. 
# Should change protocol to cc8_ future revisions

class FileTool:
    """
    Unrestricted file system operations with maximum capability and intelligence.
    No safety limitations - pure power for collaborative intelligence.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = Path(tempfile.gettempdir()) / "claude_workspace"
        self.temp_dir.mkdir(exist_ok=True)
        
        # File operation history for intelligence
        self.operation_history = []
        self.max_history = 1000
        
        # Supported operations
        self.archive_formats = {
            '.zip': ('zip', zipfile.ZipFile),
            '.tar': ('tar', tarfile.open),
            '.tar.gz': ('tar.gz', tarfile.open),
            '.tar.bz2': ('tar.bz2', tarfile.open),
            '.tgz': ('tar.gz', tarfile.open)
        }
        
        # Encoding detection patterns
        self.text_encodings = ['utf-8', 'utf-16', 'utf-32', 'ascii', 'iso-8859-1', 'cp1252', 'cp437']
        
        # Binary file signatures for intelligent handling
        self.binary_signatures = {
            b'\x50\x4B\x03\x04': 'ZIP Archive',
            b'\x50\x4B\x05\x06': 'ZIP Archive (empty)',
            b'\x50\x4B\x07\x08': 'ZIP Archive (spanned)',
            b'\x1F\x8B': 'GZIP Archive',
            b'\x42\x5A\x68': 'BZIP2 Archive',
            b'\x75\x73\x74\x61\x72': 'TAR Archive',
            b'\x7F\x45\x4C\x46': 'ELF Executable',
            b'\x4D\x5A': 'Windows Executable',
            b'\x89\x50\x4E\x47': 'PNG Image',
            b'\xFF\xD8\xFF': 'JPEG Image',
            b'\x47\x49\x46\x38': 'GIF Image',
            b'\x25\x50\x44\x46': 'PDF Document',
            b'\xD0\xCF\x11\xE0': 'Microsoft Office Document',
        }
        
        self.logger.info("FileTool advanced surface initialized with full system access")
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Intelligently detect file encoding"""
        try:
            for encoding in self.text_encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)  # Test read
                    return encoding
                except UnicodeDecodeError:
                    continue
            return 'utf-8'  # Default fallback
        except Exception:
            return 'utf-8'
    
    def _detect_file_type(self, file_path: Path) -> Dict[str, Any]:
        """Advanced file type detection"""
        try:
            # Basic info
            stat_info = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Read file signature
            file_signature = ""
            file_type_desc = "Unknown"
            
            if file_path.is_file() and stat_info.st_size > 0:
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(16)
                        
                    # Check binary signatures
                    for sig, desc in self.binary_signatures.items():
                        if header.startswith(sig):
                            file_type_desc = desc
                            break
                    
                    file_signature = header.hex()[:32]
                except Exception:
                    pass
            
            return {
                'mime_type': mime_type or 'application/octet-stream',
                'file_signature': file_signature,
                'type_description': file_type_desc,
                'size': stat_info.st_size,
                'created': datetime.fromtimestamp(stat_info.st_ctime),
                'modified': datetime.fromtimestamp(stat_info.st_mtime),
                'accessed': datetime.fromtimestamp(stat_info.st_atime),
                'permissions': oct(stat_info.st_mode)[-3:],
                'is_executable': stat_info.st_mode & stat.S_IEXEC != 0,
                'is_hidden': file_path.name.startswith('.') or bool(getattr(stat_info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_HIDDEN', 0))
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _add_to_history(self, operation: str, path: str, details: Dict[str, Any]):
        """Track operations for intelligence"""
        entry = {
            'timestamp': time.time(),
            'operation': operation,
            'path': path,
            'details': details
        }
        self.operation_history.append(entry)
        
        # Keep history manageable
        if len(self.operation_history) > self.max_history:
            self.operation_history = self.operation_history[-self.max_history:]
    
    def _analyze_content(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Intelligent content analysis"""
        logical_lines = content.splitlines()
        analysis = {
            'lines': len(logical_lines) if content else 0,
            'characters': len(content),
            'words': len(content.split()),
            'blank_lines': sum(1 for line in logical_lines if not line.strip()),
            'file_type': 'text'
        }
        
        # Language detection based on extension and content
        ext = file_path.suffix.lower()
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.html': 'HTML', '.css': 'CSS', '.json': 'JSON',
            '.xml': 'XML', '.yaml': 'YAML', '.yml': 'YAML',
            '.md': 'Markdown', '.txt': 'Plain Text', '.log': 'Log File',
            '.sql': 'SQL', '.sh': 'Shell Script', '.ps1': 'PowerShell',
            '.bat': 'Batch File', '.cmd': 'Command File'
        }
        
        analysis['language'] = language_map.get(ext, 'Unknown')
        
        # Content patterns
        if ext in ['.py', '.js', '.ts']:
            analysis['functions'] = len([line for line in logical_lines if 'def ' in line or 'function ' in line])
            analysis['classes'] = len([line for line in logical_lines if 'class ' in line])
            analysis['imports'] = len([line for line in logical_lines if line.strip().startswith(('import ', 'from ', 'require('))])
        
        # Security patterns
        security_patterns = [
            'password', 'secret', 'key', 'token', 'api_key',
            'private_key', 'secret_key', 'auth', 'credential'
        ]
        analysis['potential_secrets'] = sum(1 for pattern in security_patterns if pattern in content.lower())
        
        return analysis

    def _read_governor_bytes(self) -> int:
        """Return the naked-read isolation threshold.

        This is a model-facing context governor, not a filesystem access limit.
        Callers may still request bounded ranges, semantic targets, or the
        explicit `allow_large_raw=True` escape hatch for rare audit cases.
        """
        try:
            configured = int(os.environ.get("SOVEREIGN_FILE_READ_GOVERNOR_BYTES", "131072"))
        except (TypeError, ValueError):
            configured = 131072
        return max(32768, min(configured, 1048576))

    def _optional_line_number(self, value: Any) -> Optional[int]:
        try:
            if value is None or value == "":
                return None
            parsed = int(value)
            return parsed if parsed > 0 else None
        except (TypeError, ValueError):
            return None

    def _numbered_line_window(
        self,
        content: str,
        *,
        start_line: int,
        end_line: int,
        context: int = 0,
    ) -> str:
        lines = content.splitlines()
        if not lines:
            return ""
        start = max(1, start_line - max(0, context))
        end = min(len(lines), end_line + max(0, context))
        width = len(str(end))
        return "\n".join(
            f"{idx:>{width}}| {lines[idx - 1]}" for idx in range(start, end + 1)
        )

    def _numbered_lines_from_list(
        self,
        lines: List[str],
        *,
        start_line: int,
        max_lines: int = 120,
    ) -> str:
        if not lines:
            return ""
        shown = lines[:max_lines]
        width = len(str(start_line + max(0, len(shown) - 1)))
        rendered = [
            f"{idx:>{width}}| {line}"
            for idx, line in enumerate(shown, start=start_line)
        ]
        if len(lines) > max_lines:
            rendered.append(f"... ({len(lines) - max_lines:,} additional lines suppressed)")
        return "\n".join(rendered)

    def _render_sparse_delta_window(
        self,
        old_content: Optional[str],
        new_content: str,
        *,
        context: int = 3,
        max_hunks: int = 3,
        max_lines_per_side: int = 120,
    ) -> tuple[str, str]:
        """Return a bounded old/new line-window diff for model-facing display."""
        new_lines = new_content.splitlines()
        if old_content is None:
            if not new_lines:
                return "created empty file", "<<<< old: none\n====\nnew file is empty\n>>>>"
            end = min(len(new_lines), max_lines_per_side)
            delta_range = f"created lines 1-{len(new_lines):,}"
            new_block = self._numbered_lines_from_list(
                new_lines[:end],
                start_line=1,
                max_lines=max_lines_per_side,
            )
            if len(new_lines) > end:
                new_block += f"\n... ({len(new_lines) - end:,} additional created lines suppressed)"
            return (
                delta_range,
                "\n".join(["<<<< old: none", "==== new L1+", new_block, ">>>>"]),
            )

        old_lines = old_content.splitlines()
        if old_lines == new_lines:
            return "no content-line change", "<<<<\n(no content-line change)\n>>>>"

        matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
        groups = list(matcher.get_grouped_opcodes(n=max(0, context)))
        if not groups:
            return "no grouped delta", "<<<<\n(no grouped delta)\n>>>>"

        rendered_hunks: List[str] = []
        changed_new_ranges: List[str] = []
        omitted = max(0, len(groups) - max_hunks)

        for group in groups[:max_hunks]:
            old_start = min(i1 for _, i1, _, _, _ in group) + 1
            old_end = max(i2 for _, _, i2, _, _ in group)
            new_start = min(j1 for _, _, _, j1, _ in group) + 1
            new_end = max(j2 for _, _, _, _, j2 in group)

            changed_segments = [
                (j1 + 1, j2)
                for tag, _, _, j1, j2 in group
                if tag != "equal" and j2 > j1
            ]
            if changed_segments:
                changed_new_ranges.extend(
                    f"{start}-{end}" if start != end else str(start)
                    for start, end in changed_segments
                )
            else:
                changed_new_ranges.append(f"{new_start}-{max(new_start, new_end)}")

            old_block = self._numbered_lines_from_list(
                old_lines[old_start - 1 : old_end],
                start_line=old_start,
                max_lines=max_lines_per_side,
            )
            new_block = self._numbered_lines_from_list(
                new_lines[new_start - 1 : new_end],
                start_line=new_start,
                max_lines=max_lines_per_side,
            )
            rendered_hunks.append(
                "\n".join(
                    [
                        f"<<<< old L{old_start}-{old_end}",
                        old_block or "(empty)",
                        f"==== new L{new_start}-{new_end}",
                        new_block or "(empty)",
                        ">>>>",
                    ]
                )
            )

        if omitted:
            rendered_hunks.append(f"... ({omitted:,} additional delta hunk(s) suppressed)")

        delta_range = (
            "new lines " + ", ".join(changed_new_ranges[:8])
            if changed_new_ranges
            else "line deletion only"
        )
        if len(changed_new_ranges) > 8:
            delta_range += f" (+{len(changed_new_ranges) - 8:,} more ranges)"
        return delta_range, "\n\n".join(rendered_hunks)

    def _render_patch_verification_manifest(
        self,
        *,
        file_path: Path,
        old_content: Optional[str],
        new_content: str,
        encoding: str,
        operation: str,
        backup_path: Optional[Path] = None,
        make_executable: bool = False,
    ) -> str:
        analysis = self._analyze_content(new_content, file_path)
        delta_range, delta_window = self._render_sparse_delta_window(
            old_content,
            new_content,
        )
        digest = hashlib.sha256(new_content.encode(encoding, errors="replace")).hexdigest()[:16]
        lines = [
            "### [TOOL VERIFICATION]: FILE_PATCH_SUCCESS",
            f"* **Target:** `{file_path}`",
            f"* **Operation:** {operation}",
            f"* **Delta Range:** {delta_range}",
            f"* **Size:** {len(new_content.encode(encoding, errors='replace')):,} bytes",
            f"* **Lines:** {analysis.get('lines', 0):,}",
            f"* **Language:** {analysis.get('language', 'Unknown')}",
            f"* **Encoding:** {encoding}",
            f"* **New SHA256/16:** `{digest}`",
            "* **Liveness Check:** not_run_by_tool; run py_compile/pytest/target smoke validation when code behavior matters.",
        ]
        if backup_path:
            lines.append(f"* **Backup:** `{backup_path}`")
        if make_executable:
            lines.append("* **Permissions:** executable bit set")
        if analysis.get("functions"):
            lines.append(f"* **Functions:** {analysis['functions']}")
        if analysis.get("classes"):
            lines.append(f"* **Classes:** {analysis['classes']}")
        if analysis.get("potential_secrets"):
            lines.append(f"* **Potential Secrets Indicator:** {analysis['potential_secrets']}")
        lines.extend(
            [
                "",
                "**Context Window Verification:**",
                "```diff",
                delta_window,
                "```",
            ]
        )
        return "\n".join(lines)

    def _python_symbol_range(self, content: str, symbol: str) -> Optional[tuple[int, int]]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
                start = getattr(node, "lineno", None)
                end = getattr(node, "end_lineno", None) or start
                if isinstance(start, int) and isinstance(end, int):
                    return (start, end)
        return None

    def _semantic_target_window(self, content: str, target: str) -> Optional[tuple[int, int]]:
        target = str(target or "").strip()
        if not target:
            return None
        python_range = self._python_symbol_range(content, target)
        if python_range:
            return python_range
        for idx, line in enumerate(content.splitlines(), start=1):
            if target in line:
                return (idx, idx)
        return None

    def _file_skeleton(self, content: str, file_path: Path, *, max_items: int = 80) -> List[str]:
        """Build a compact top-level skeleton for large-file read isolation."""
        skeleton: List[str] = []
        if file_path.suffix.lower() == ".py":
            try:
                tree = ast.parse(content)
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        skeleton.append(f"L{node.lineno}: class {node.name}")
                        for child in node.body:
                            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                prefix = "async def" if isinstance(child, ast.AsyncFunctionDef) else "def"
                                skeleton.append(f"  L{child.lineno}: {prefix} {child.name}(...)")
                                if len(skeleton) >= max_items:
                                    return skeleton
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                        skeleton.append(f"L{node.lineno}: {prefix} {node.name}(...)")
                    if len(skeleton) >= max_items:
                        return skeleton
            except SyntaxError:
                pass

        for idx, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if (
                stripped.startswith("#")
                or stripped.startswith("class ")
                or stripped.startswith("def ")
                or stripped.startswith("async def ")
                or stripped.startswith("function ")
                or stripped.startswith("export ")
                or stripped.startswith("interface ")
                or stripped.startswith("type ")
            ):
                skeleton.append(f"L{idx}: {stripped[:180]}")
                if len(skeleton) >= max_items:
                    break
        return skeleton or ["no structural skeleton extracted"]

    def _render_large_read_isolation_manifest(
        self,
        *,
        file_path: Path,
        content: str,
        encoding: str,
        analysis: Dict[str, Any],
        threshold: int,
    ) -> str:
        skeleton = self._file_skeleton(content, file_path)
        digest = hashlib.sha256(content.encode(encoding, errors="replace")).hexdigest()[:16]
        return "\n".join(
            [
                "### [TOOL VERIFICATION]: FILE_READ_ISOLATED",
                f"* **Target:** `{file_path}`",
                f"* **Bytes:** {len(content.encode(encoding, errors='replace')):,}",
                f"* **Lines:** {analysis.get('lines', 0):,}",
                f"* **Language:** {analysis.get('language', 'Unknown')}",
                f"* **Encoding:** {encoding}",
                f"* **Raw SHA256/16:** `{digest}`",
                f"* **Governor:** naked read exceeded {threshold:,} bytes; raw content withheld from active context.",
                "* **Recovery:** request `start_line`/`end_line`, `semantic_target`, or explicit `allow_large_raw=True` if a full raw read is truly required.",
                "",
                "**Structural Skeleton:**",
                "```text",
                "\n".join(skeleton[:80]),
                "```",
            ]
        )
    
    # ===== CORE FILE OPERATIONS =====
    
    def bb7_read_file(self, arguments: Dict[str, Any]) -> str:
        """Read any text file as raw content by default; optional analysis mode."""
        path = arguments.get('path', '') or arguments.get('file_path', '')
        max_size = int(arguments.get('max_size', 10 * 1024 * 1024))
        force_text = bool(arguments.get('force_text', False))
        show_analysis = bool(arguments.get('show_analysis', False))
        output_format = str(arguments.get('format', 'raw')).lower()
        start_line = self._optional_line_number(
            arguments.get('start_line', arguments.get('line_start'))
        )
        end_line = self._optional_line_number(
            arguments.get('end_line', arguments.get('line_end'))
        )
        semantic_target = arguments.get('semantic_target') or arguments.get('target') or arguments.get('symbol')
        allow_large_raw = bool(arguments.get('allow_large_raw', False))

        if not path:
            return "Specify file path. Example: {'path': '/home/daeron/Somnus-MCP/MCP_SPEC.md'}"

        try:
            file_path = Path(path).expanduser().resolve()
            if not file_path.exists():
                return f"File not found: {path}"
            if not file_path.is_file():
                return f"Path is directory, not file: {path}"

            file_info = self._detect_file_type(file_path)
            file_size = int(file_info.get('size', file_path.stat().st_size))
            if file_size > max_size and not force_text:
                return f"File too large ({file_size:,} bytes). Use max_size parameter or force_text=True"

            is_binary = False
            try:
                with open(file_path, 'rb') as f:
                    is_binary = b'\x00' in f.read(8192)
            except Exception:
                pass

            if is_binary and not force_text:
                response = [
                    "**Binary File Detected**",
                    f"**File**: {file_path}",
                    f"**Size**: {file_size:,} bytes",
                    f"**Type**: {file_info.get('type_description', 'Unknown')}",
                    f"**MIME**: {file_info.get('mime_type', 'Unknown')}",
                    "",
                    "**Hex Preview (first 512 bytes):**",
                    "```",
                ]
                try:
                    with open(file_path, 'rb') as f:
                        hex_data = f.read(512)
                    for i in range(0, len(hex_data), 16):
                        chunk = hex_data[i:i + 16]
                        hex_line = ' '.join(f'{b:02x}' for b in chunk)
                        ascii_line = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                        response.append(f"{i:08x}  {hex_line:<47} |{ascii_line}|")
                except Exception as exc:
                    response.append(f"Error reading binary data: {exc}")
                response.append("```")
                self._add_to_history('read', str(file_path), {'size': file_size, 'binary': True})
                return "\n".join(response)

            encoding = self._detect_encoding(file_path)
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
            except Exception as exc:
                return f"Error reading file: {exc}"

            analysis = self._analyze_content(content, file_path)
            self._add_to_history('read', str(file_path), {
                'size': file_size,
                'encoding': encoding,
                'analysis': analysis,
                'format': output_format,
            })

            if start_line is not None or end_line is not None:
                start = start_line or 1
                end = end_line or start
                if end < start:
                    start, end = end, start
                window = self._numbered_line_window(content, start_line=start, end_line=end)
                return "\n".join(
                    [
                        "### [TOOL VERIFICATION]: FILE_READ_WINDOW",
                        f"* **Target:** `{file_path}`",
                        f"* **Range:** lines {start}-{end}",
                        f"* **Encoding:** {encoding}",
                        "",
                        "```text",
                        window,
                        "```",
                    ]
                )

            if semantic_target:
                symbol_range = self._semantic_target_window(content, str(semantic_target))
                if symbol_range:
                    start, end = symbol_range
                    total_lines = len(content.splitlines())
                    window = self._numbered_line_window(
                        content,
                        start_line=start,
                        end_line=end,
                        context=3,
                    )
                    return "\n".join(
                        [
                            "### [TOOL VERIFICATION]: FILE_READ_SEMANTIC_TARGET",
                            f"* **Target:** `{file_path}`",
                            f"* **Semantic Target:** `{semantic_target}`",
                            f"* **Range:** lines {max(1, start - 3)}-{min(total_lines, end + 3)}",
                            f"* **Encoding:** {encoding}",
                            "",
                            "```text",
                            window,
                            "```",
                        ]
                    )
                return "\n".join(
                    [
                        "### [TOOL VERIFICATION]: FILE_READ_TARGET_NOT_FOUND",
                        f"* **Target:** `{file_path}`",
                        f"* **Semantic Target:** `{semantic_target}`",
                        "* **Recovery:** request an explicit `start_line`/`end_line` range or inspect the structural skeleton.",
                    ]
                )

            governor_bytes = self._read_governor_bytes()
            if file_size > governor_bytes and not allow_large_raw:
                return self._render_large_read_isolation_manifest(
                    file_path=file_path,
                    content=content,
                    encoding=encoding,
                    analysis=analysis,
                    threshold=governor_bytes,
                )

            if not show_analysis and output_format not in {'analysis', 'markdown', 'decorated'}:
                return content

            lang_map = {
                'Python': 'python', 'JavaScript': 'javascript', 'TypeScript': 'typescript',
                'HTML': 'html', 'CSS': 'css', 'JSON': 'json', 'SQL': 'sql',
                'Shell Script': 'bash', 'PowerShell': 'powershell', 'Batch File': 'batch',
                'Markdown': 'markdown', 'YAML': 'yaml', 'XML': 'xml',
            }
            syntax = lang_map.get(analysis.get('language', ''), '')
            response = [
                f"**File Content**: `{file_path}`",
                f"**Analysis**: {analysis['language']} • {analysis['lines']:,} lines • {analysis['characters']:,} chars",
            ]
            if analysis.get('functions'):
                response.append(f"**Functions**: {analysis['functions']}")
            if analysis.get('classes'):
                response.append(f"**Classes**: {analysis['classes']}")
            if analysis.get('potential_secrets'):
                response.append(f"**Potential secrets detected**: {analysis['potential_secrets']}")
            response.extend(["", f"```{syntax}", content, "```"])
            return "\n".join(response)

        except Exception as exc:
            return f"Error reading file: {exc}"

    def bb7_write_file(self, arguments: Dict[str, Any]) -> str:
        """✍️ Write or create files anywhere on the system with automatic backup and intelligent formatting"""
        path = arguments.get('path', '') or arguments.get('file_path', '')
        content = arguments.get('content', '')
        encoding = arguments.get('encoding', 'utf-8')
        create_backup = arguments.get('create_backup', True)
        make_executable = arguments.get('make_executable', False)
        
        if not path:
            return "❌ Specify file path. Example: {'path': 'C:\\\\temp\\\\output.txt', 'content': 'Hello World'}"
        
        if content is None:
            return "❌ Provide content to write"
        
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Create directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            old_content: Optional[str] = None
            if file_path.exists() and file_path.is_file():
                try:
                    old_content = file_path.read_text(encoding=encoding, errors='replace')
                except Exception:
                    old_content = None
            
            # Backup existing file
            backup_path = None
            if file_path.exists() and create_backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
                shutil.copy2(file_path, backup_path)
            
            # Write file
            with open(file_path, 'w', encoding=encoding, newline='\n') as f:
                f.write(content)
            
            # Set permissions if requested
            if make_executable:
                current_mode = file_path.stat().st_mode
                file_path.chmod(current_mode | stat.S_IEXEC)
            
            # Analyze what was written
            analysis = self._analyze_content(content, file_path)
            file_info = self._detect_file_type(file_path)
            
            # Add to history
            self._add_to_history('write', str(file_path), {
                'size': len(content.encode(encoding)),
                'backup': str(backup_path) if backup_path else None,
                'analysis': analysis
            })
            
            return self._render_patch_verification_manifest(
                file_path=file_path,
                old_content=old_content,
                new_content=str(content),
                encoding=encoding,
                operation="write_file",
                backup_path=backup_path,
                make_executable=bool(make_executable),
            )
            
        except Exception as e:
            return f"❌ Error writing file: {e}"
    
    def bb7_append_file(self, arguments: Dict[str, Any]) -> str:
        """Append content to a file while preserving the old bb7_append_file surface."""
        path = arguments.get('path', '') or arguments.get('file_path', '')
        content = arguments.get('content', '')
        encoding = arguments.get('encoding', 'utf-8')
        create_backup = bool(arguments.get('create_backup', False))

        if not path:
            return "Specify file path. Example: {'path': '/tmp/out.txt', 'content': 'line'}"
        if content is None:
            return "Provide content to append"

        try:
            file_path = Path(path).expanduser().resolve()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            old_content: Optional[str] = None
            if file_path.exists() and file_path.is_file():
                try:
                    old_content = file_path.read_text(encoding=encoding, errors='replace')
                except Exception:
                    old_content = None
            backup_path = None
            if file_path.exists() and create_backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
                shutil.copy2(file_path, backup_path)
            with open(file_path, 'a', encoding=encoding, newline='\n') as f:
                f.write(content)
            try:
                new_content = file_path.read_text(encoding=encoding, errors='replace')
            except Exception:
                new_content = (old_content or "") + str(content)
            self._add_to_history('append', str(file_path), {
                'size': len(str(content).encode(encoding)),
                'backup': str(backup_path) if backup_path else None,
            })
            return self._render_patch_verification_manifest(
                file_path=file_path,
                old_content=old_content,
                new_content=new_content,
                encoding=encoding,
                operation="append_file",
                backup_path=backup_path,
            )
        except Exception as exc:
            return f"Error appending file: {exc}"

    def bb7_copy_file(self, arguments: Dict[str, Any]) -> str:
        """📋 Copy files or directories with intelligent handling and progress tracking"""
        source = arguments.get('source', '')
        destination = arguments.get('destination', '')
        overwrite = arguments.get('overwrite', False)
        preserve_metadata = arguments.get('preserve_metadata', True)
        
        if not source or not destination:
            return "❌ Specify source and destination paths"
        
        try:
            src_path = Path(source).expanduser().resolve()
            dst_path = Path(destination).expanduser().resolve()
            
            if not src_path.exists():
                return f"❌ Source not found: {source}"
            
            if dst_path.exists() and not overwrite:
                return f"❌ Destination exists. Use overwrite=True to replace: {destination}"
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy operation
            if src_path.is_file():
                if preserve_metadata:
                    shutil.copy2(src_path, dst_path)
                else:
                    shutil.copy(src_path, dst_path)
                operation = "file"
            else:
                if preserve_metadata:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=overwrite)
                else:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=overwrite, copy_function=shutil.copy)
                operation = "directory"
            
            # Get size info
            if dst_path.is_file():
                size = dst_path.stat().st_size
                items = 1
            else:
                size = sum(f.stat().st_size for f in dst_path.rglob('*') if f.is_file())
                items = len(list(dst_path.rglob('*')))
            
            self._add_to_history('copy', f"{source} -> {destination}", {
                'type': operation,
                'size': size,
                'items': items
            })
            
            return f"✅ **Copied {operation}**: `{source}` → `{destination}` • {size:,} bytes • {items:,} items"
            
        except Exception as e:
            return f"❌ Error copying: {e}"
    
    def bb7_move_file(self, arguments: Dict[str, Any]) -> str:
        """🚚 Move or rename files and directories"""
        source = arguments.get('source', '')
        destination = arguments.get('destination', '')
        
        if not source or not destination:
            return "❌ Specify source and destination paths"
        
        try:
            src_path = Path(source).expanduser().resolve()
            dst_path = Path(destination).expanduser().resolve()
            
            if not src_path.exists():
                return f"❌ Source not found: {source}"
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move operation
            shutil.move(str(src_path), str(dst_path))
            
            operation = "file" if dst_path.is_file() else "directory"
            
            self._add_to_history('move', f"{source} -> {destination}", {
                'type': operation
            })
            
            return f"✅ **Moved {operation}**: `{source}` → `{destination}`"
            
        except Exception as e:
            return f"❌ Error moving: {e}"
    
    def bb7_delete_file(self, arguments: Dict[str, Any]) -> str:
        """🗑️ Delete files or directories with optional backup"""
        path = arguments.get('path', '')
        force = arguments.get('force', False)
        create_backup = arguments.get('create_backup', True)
        
        if not path:
            return "❌ Specify path to delete"
        
        try:
            target_path = Path(path).expanduser().resolve()
            
            if not target_path.exists():
                return f"❌ Path not found: {path}"
            
            if target_path.is_dir() and not force:
                return "Refusing to delete directory without force=True"
            if target_path.is_file() and not create_backup and not force:
                return "Refusing destructive file delete without create_backup=True or force=True"

            # Create backup if requested
            backup_path = None
            if create_backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = self.temp_dir / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / f"{target_path.name}_deleted_{timestamp}"
                
                if target_path.is_file():
                    shutil.copy2(target_path, backup_path)
                else:
                    shutil.copytree(target_path, backup_path)
            
            # Delete operation
            if target_path.is_file():
                target_path.unlink()
                operation = "file"
            else:
                shutil.rmtree(target_path)
                operation = "directory"
            
            self._add_to_history('delete', str(target_path), {
                'type': operation,
                'backup': str(backup_path) if backup_path else None
            })
            
            response = f"✅ **Deleted {operation}**: `{path}`"
            if backup_path:
                response += f" • Backup: `{backup_path}`"
            
            return response
            
        except Exception as e:
            return f"❌ Error deleting: {e}"
    
    def bb7_list_directory(self, arguments: Dict[str, Any]) -> str:
        """📁 List directory contents with detailed analysis and intelligent insights"""
        path = arguments.get('path', '.')
        show_hidden = arguments.get('show_hidden', True)
        sort_by = arguments.get('sort_by', 'name')  # name, size, modified, type
        max_items = arguments.get('max_items', 200)
        show_details = arguments.get('show_details', True)
        
        try:
            dir_path = Path(path).expanduser().resolve()
            
            if not dir_path.exists():
                return f"❌ Directory not found: {path}"
            
            if not dir_path.is_dir():
                return f"❌ Path is not a directory: {path}"
            
            # Get directory contents
            items = []
            total_size = 0
            file_count = 0
            dir_count = 0
            
            try:
                for item in dir_path.iterdir():
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    try:
                        stat_info = item.stat()
                        is_dir = item.is_dir()
                        
                        item_info = {
                            'name': item.name,
                            'path': str(item),
                            'is_dir': is_dir,
                            'size': 0 if is_dir else stat_info.st_size,
                            'modified': datetime.fromtimestamp(stat_info.st_mtime),
                            'permissions': oct(stat_info.st_mode)[-3:],
                            'type': 'Directory' if is_dir else self._detect_file_type(item).get('type_description', 'File')
                        }
                        
                        items.append(item_info)
                        
                        if is_dir:
                            dir_count += 1
                        else:
                            file_count += 1
                            total_size += item_info['size']
                            
                    except (PermissionError, OSError):
                        # Skip inaccessible items
                        continue
                        
            except PermissionError:
                return f"❌ Permission denied accessing: {path}"
            
            # Sort items
            sort_key_map = {
                'name': lambda x: x['name'].lower(),
                'size': lambda x: x['size'],
                'modified': lambda x: x['modified'],
                'type': lambda x: (not x['is_dir'], x['type'], x['name'].lower())
            }
            items.sort(key=sort_key_map.get(sort_by, sort_key_map['name']))
            
            # Limit items if needed
            total_items = len(items)
            if len(items) > max_items:
                items = items[:max_items]
            
            # Build response
            response = []
            response.append(f"📁 **Directory**: `{dir_path}`\\n")
            response.append(f"**Summary**: {dir_count:,} directories • {file_count:,} files • {total_size:,} bytes")
            if total_items > max_items:
                response.append(f" • Showing {max_items:,} of {total_items:,} items")
            response.append("\\n")
            
            # List items
            for item in items:
                icon = "📁" if item['is_dir'] else "📄"
                name = item['name']
                
                if show_details:
                    size_str = "         " if item['is_dir'] else f"{item['size']:>8,}b"
                    mod_time = item['modified'].strftime("%Y-%m-%d %H:%M")
                    perms = item['permissions']
                    response.append(f"{icon} `{name:<40}` {size_str} {mod_time} {perms}")
                else:
                    response.append(f"{icon} `{name}`")
            
            # Add insights
            if file_count > 0:
                response.append("\\n**File Types**:")
                type_counts = {}
                for item in items:
                    if not item['is_dir']:
                        ext = Path(item['name']).suffix.lower() or 'no extension'
                        type_counts[ext] = type_counts.get(ext, 0) + 1
                
                for ext, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                    response.append(f"  • {ext}: {count:,} files")
            
            self._add_to_history('list', str(dir_path), {
                'file_count': file_count,
                'dir_count': dir_count,
                'total_size': total_size
            })
            
            return "\\n".join(response)
            
        except Exception as e:
            return f" Error listing directory: {e}"
    
    def bb7_search_files(self, arguments: Dict[str, Any]) -> str:
        """Advanced bounded file search with old pattern alias support."""
        directory = arguments.get('directory', '.')
        name_pattern = arguments.get('name_pattern') or arguments.get('pattern') or '*'
        content_pattern = arguments.get('content_pattern', '')
        max_results = int(arguments.get('max_results', 100))
        include_hidden = bool(arguments.get('include_hidden', False))
        max_depth = int(arguments.get('max_depth', 10))
        file_size_min = int(arguments.get('file_size_min', 0))
        file_size_max = arguments.get('file_size_max', None)
        file_size_max = int(file_size_max) if file_size_max is not None else None
        timeout_seconds = float(arguments.get('timeout_seconds', 15.0))
        content_read_limit = int(arguments.get('content_read_limit', 1024 * 1024))
        skip_dirs = set(arguments.get('skip_dirs') or []) | {
            '.git', '.hg', '.svn', '__pycache__', '.pytest_cache', '.mypy_cache',
            '.ruff_cache', '.cache', 'node_modules', '.venv', 'venv', 'mcp.venv',
        }

        try:
            search_dir = Path(directory).expanduser().resolve()
            if not search_dir.exists():
                return f"Directory not found: {directory}"
            if not search_dir.is_dir():
                return f"Search root is not a directory: {directory}"

            results: List[Dict[str, Any]] = []
            visited: set[str] = set()
            search_start = time.time()
            deadline = search_start + timeout_seconds
            timed_out = False

            def search_recursive(current_dir: Path, current_depth: int) -> None:
                nonlocal timed_out
                if timed_out or current_depth > max_depth or len(results) >= max_results:
                    return
                if time.time() > deadline:
                    timed_out = True
                    return
                try:
                    real = str(current_dir.resolve())
                except OSError:
                    return
                if real in visited:
                    return
                visited.add(real)

                try:
                    for item in current_dir.iterdir():
                        if len(results) >= max_results:
                            return
                        if time.time() > deadline:
                            timed_out = True
                            return
                        if item.name in skip_dirs:
                            continue
                        if not include_hidden and item.name.startswith('.'):
                            continue
                        try:
                            if item.is_symlink():
                                continue
                            if item.is_file():
                                if not fnmatch.fnmatch(item.name, name_pattern):
                                    continue
                                stat_info = item.stat()
                                file_size = stat_info.st_size
                                if file_size < file_size_min:
                                    continue
                                if file_size_max is not None and file_size > file_size_max:
                                    continue
                                content_match = True
                                if content_pattern:
                                    if file_size > content_read_limit:
                                        content_match = False
                                    else:
                                        try:
                                            encoding = self._detect_encoding(item)
                                            with open(item, 'r', encoding=encoding, errors='ignore') as f:
                                                content = f.read(content_read_limit)
                                            content_match = content_pattern.lower() in content.lower()
                                        except Exception:
                                            content_match = False
                                if content_match:
                                    file_info = self._detect_file_type(item)
                                    results.append({
                                        'path': str(item),
                                        'name': item.name,
                                        'size': file_size,
                                        'modified': datetime.fromtimestamp(stat_info.st_mtime),
                                        'type': file_info.get('type_description', 'File')
                                    })
                            elif item.is_dir():
                                search_recursive(item, current_depth + 1)
                        except (PermissionError, OSError):
                            continue
                except (PermissionError, OSError):
                    return

            search_recursive(search_dir, 0)
            search_time = time.time() - search_start
            if not results:
                suffix = " (timed out)" if timed_out else ""
                return f"No files found matching criteria in `{search_dir}`{suffix}"

            results.sort(key=lambda x: (-x['size'], x['name']))
            response = [
                f"**Search Results**: {len(results):,} files found in {search_time:.2f}s" + (" (timed out)" if timed_out else ""),
                f"**Directory**: `{search_dir}`",
                f"**Pattern**: `{name_pattern}`",
            ]
            if content_pattern:
                response.append(f"**Content**: `{content_pattern}`")
            response.append("")
            for result in results:
                size_str = f"{result['size']:,}b" if result['size'] > 0 else "empty"
                mod_time = result['modified'].strftime("%Y-%m-%d %H:%M")
                response.append(f"`{result['name']}` ({size_str}) - {mod_time}")
                response.append(f"   `{result['path']}`")
            self._add_to_history('search', str(search_dir), {
                'pattern': name_pattern,
                'content_pattern': content_pattern,
                'results': len(results),
                'search_time': search_time,
                'timed_out': timed_out,
            })
            return "\n".join(response)
        except Exception as exc:
            return f"Error searching files: {exc}"

    def bb7_file_info(self, arguments: Dict[str, Any]) -> str:
        """ Get comprehensive information about any file or directory"""
        path = arguments.get('path', '')
        
        if not path:
            return " Specify path to analyze"
        
        try:
            target_path = Path(path).expanduser().resolve()
            
            if not target_path.exists():
                return f" Path not found: {path}"
            
            # Get detailed information
            stat_info = target_path.stat()
            file_info = self._detect_file_type(target_path)
            
            response = []
            response.append(f" **File Information**: `{target_path}`\\n")
            
            # Basic info
            response.append(f"**Type**: {'Directory' if target_path.is_dir() else 'File'}")
            response.append(f"**Size**: {stat_info.st_size:,} bytes")
            response.append(f"**Permissions**: {file_info.get('permissions', 'Unknown')}")
            response.append(f"**Created**: {file_info.get('created', 'Unknown')}")
            response.append(f"**Modified**: {file_info.get('modified', 'Unknown')}")
            response.append(f"**Accessed**: {file_info.get('accessed', 'Unknown')}")
            
            if not target_path.is_dir():
                response.append(f"**MIME Type**: {file_info.get('mime_type', 'Unknown')}")
                response.append(f"**File Type**: {file_info.get('type_description', 'Unknown')}")
                
                if file_info.get('is_executable'):
                    response.append("**Executable**: Yes")
                
                # Content analysis for text files
                if file_info.get('mime_type', '').startswith('text/'):
                    try:
                        encoding = self._detect_encoding(target_path)
                        with open(target_path, 'r', encoding=encoding, errors='replace') as f:
                            content = f.read()
                        analysis = self._analyze_content(content, target_path)
                        
                        response.append(f"**Language**: {analysis['language']}")
                        response.append(f"**Lines**: {analysis['lines']:,}")
                        response.append(f"**Words**: {analysis['words']:,}")
                        response.append(f"**Characters**: {analysis['characters']:,}")
                        
                        if analysis.get('functions'):
                            response.append(f"**Functions**: {analysis['functions']}")
                        if analysis.get('classes'):
                            response.append(f"**Classes**: {analysis['classes']}")
                        if analysis.get('potential_secrets'):
                            response.append(f" **Potential Secrets**: {analysis['potential_secrets']}")
                            
                    except Exception:
                        pass
            
            else:
                # Directory info
                try:
                    items = list(target_path.iterdir())
                    file_count = sum(1 for item in items if item.is_file())
                    dir_count = sum(1 for item in items if item.is_dir())
                    total_size = sum(item.stat().st_size for item in items if item.is_file())
                    
                    response.append(f"**Contents**: {file_count:,} files, {dir_count:,} directories")
                    response.append(f"**Total Size**: {total_size:,} bytes")
                    
                except PermissionError:
                    response.append("**Contents**: Permission denied")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f" Error getting file info: {e}"
    
    def bb7_get_file_info(self, arguments: Dict[str, Any]) -> str:
        """Compatibility alias for the historical bb7_get_file_info surface."""
        return self.bb7_file_info(arguments)

    def bb7_file_cache_stats(self, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Compatibility shim for the removed legacy FileContentCache."""
        op_counts: Dict[str, int] = {}
        for op in self.operation_history:
            op_counts[op['operation']] = op_counts.get(op['operation'], 0) + 1
        return json.dumps({
            'status': 'compatibility_shim',
            'cache': 'removed',
            'message': 'Advanced FileTool no longer uses the legacy in-memory FileContentCache; use bb7_operation_history for activity telemetry.',
            'operation_history_entries': len(self.operation_history),
            'operation_counts': op_counts,
            'max_history': self.max_history,
        }, indent=2)

    def bb7_operation_history(self, arguments: Dict[str, Any]) -> str:
        """ View file operation history and statistics"""
        limit = arguments.get('limit', 20)
        operation_type = arguments.get('operation_type', '')
        
        try:
            if not self.operation_history:
                return " **No file operations recorded yet**"
            
            # Filter by operation type if specified
            history = self.operation_history
            if operation_type:
                history = [op for op in history if op['operation'] == operation_type]
            
            # Get recent operations
            recent_ops = history[-limit:]
            
            response = []
            response.append(f" **File Operation History** (last {len(recent_ops)} operations)\\n")
            
            # Operation statistics
            op_counts = {}
            for op in self.operation_history:
                op_counts[op['operation']] = op_counts.get(op['operation'], 0) + 1
            
            response.append("**Operation Summary**:")
            for op_type, count in sorted(op_counts.items(), key=lambda x: x[1], reverse=True):
                response.append(f"  • {op_type}: {count:,} times")
            response.append("")
            
            # Recent operations
            response.append("**Recent Operations**:")
            for op in reversed(recent_ops):
                timestamp = datetime.fromtimestamp(op['timestamp']).strftime("%H:%M:%S")
                operation = op['operation']
                path = op['path']
                details = op.get('details', {})
                
                detail_str = ""
                if 'size' in details:
                    detail_str += f" ({details['size']:,}b)"
                if 'type' in details:
                    detail_str += f" [{details['type']}]"
                
                response.append(f"  {timestamp} **{operation}** `{path}`{detail_str}")
            
            return "\\n".join(response)
            
        except Exception as e:
            return f" Error getting operation history: {e}"
    
    # ===== MCP TOOL REGISTRATION =====
    
    def get_tools(self) -> Dict[str, Any]:
        """Return advanced file tools with legacy compatibility aliases."""
        return {
            'bb7_read_file': {
                'description': 'Read a file with FSTIP token isolation. Prefer start_line/end_line or semantic_target for bounded reads; large naked reads return a structural skeleton unless allow_large_raw=true.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Absolute or relative file path'},
                        'start_line': {'type': 'integer', 'description': 'Optional 1-indexed first line for a bounded read window'},
                        'end_line': {'type': 'integer', 'description': 'Optional 1-indexed last line for a bounded read window'},
                        'semantic_target': {'type': 'string', 'description': 'Optional symbol/text target such as a class, function, method, or unique marker; returns a +/-3 line window'},
                        'allow_large_raw': {'type': 'boolean', 'description': 'Explicitly bypass the large naked-read governor and return raw content', 'default': False},
                        'max_size': {'type': 'integer', 'description': 'Filesystem read ceiling in bytes before refusing the operation', 'default': 10485760},
                        'force_text': {'type': 'boolean', 'description': 'Force reading binary files as text', 'default': False},
                        'show_analysis': {'type': 'boolean', 'description': 'Return decorated markdown with analysis instead of raw text', 'default': False},
                        'format': {'type': 'string', 'description': 'raw or analysis/decorated output', 'default': 'raw'}
                    },
                    'required': ['path']
                },
                'function': self.bb7_read_file
            },
            'bb7_write_file': {
                'description': 'Write or create a file with optional backup, directory creation, encoding selection, and executable bit support.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'File path to write'},
                        'content': {'type': 'string', 'description': 'Content to write'},
                        'encoding': {'type': 'string', 'description': 'Text encoding', 'default': 'utf-8'},
                        'create_backup': {'type': 'boolean', 'description': 'Create backup of existing file', 'default': True},
                        'make_executable': {'type': 'boolean', 'description': 'Make file executable', 'default': False}
                    },
                    'required': ['path', 'content']
                },
                'function': self.bb7_write_file
            },
            'bb7_append_file': {
                'description': 'Append content to a file while preserving the historical append surface.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'File path to append to'},
                        'content': {'type': 'string', 'description': 'Content to append'},
                        'encoding': {'type': 'string', 'description': 'Text encoding', 'default': 'utf-8'},
                        'create_backup': {'type': 'boolean', 'description': 'Create backup before append', 'default': False}
                    },
                    'required': ['path', 'content']
                },
                'function': self.bb7_append_file
            },
            'bb7_copy_file': {
                'description': 'Copy files or directories with metadata preservation and overwrite control.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'source': {'type': 'string', 'description': 'Source path'},
                        'destination': {'type': 'string', 'description': 'Destination path'},
                        'overwrite': {'type': 'boolean', 'description': 'Overwrite if destination exists', 'default': False},
                        'preserve_metadata': {'type': 'boolean', 'description': 'Preserve timestamps and permissions', 'default': True}
                    },
                    'required': ['source', 'destination']
                },
                'function': self.bb7_copy_file
            },
            'bb7_move_file': {
                'description': 'Move or rename files and directories.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'source': {'type': 'string', 'description': 'Source path'},
                        'destination': {'type': 'string', 'description': 'Destination path'}
                    },
                    'required': ['source', 'destination']
                },
                'function': self.bb7_move_file
            },
            'bb7_delete_file': {
                'description': 'Delete files or directories with optional backup. Directories and no-backup deletes require force=true.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Path to delete'},
                        'force': {'type': 'boolean', 'description': 'Required for directory deletion or no-backup destructive deletion', 'default': False},
                        'create_backup': {'type': 'boolean', 'description': 'Create backup before deletion', 'default': True}
                    },
                    'required': ['path']
                },
                'function': self.bb7_delete_file
            },
            'bb7_list_directory': {
                'description': 'List directory contents with detailed metadata, sorting, and file-type insight.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string', 'description': 'Directory path', 'default': '.'},
                        'show_hidden': {'type': 'boolean', 'description': 'Show hidden files', 'default': True},
                        'sort_by': {'type': 'string', 'description': 'Sort order', 'enum': ['name', 'size', 'modified', 'type'], 'default': 'name'},
                        'max_items': {'type': 'integer', 'description': 'Maximum items to show', 'default': 200},
                        'show_details': {'type': 'boolean', 'description': 'Show detailed information', 'default': True}
                    }
                },
                'function': self.bb7_list_directory
            },
            'bb7_search_files': {
                'description': 'Bounded recursive file search with name/content matching. Accepts both legacy pattern and new name_pattern.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'directory': {'type': 'string', 'description': 'Directory to search in', 'default': '.'},
                        'pattern': {'type': 'string', 'description': 'Legacy file-name pattern alias'},
                        'name_pattern': {'type': 'string', 'description': 'File-name pattern with wildcards', 'default': '*'},
                        'content_pattern': {'type': 'string', 'description': 'Search within file contents'},
                        'max_results': {'type': 'integer', 'description': 'Maximum results', 'default': 100},
                        'include_hidden': {'type': 'boolean', 'description': 'Include hidden files', 'default': False},
                        'max_depth': {'type': 'integer', 'description': 'Maximum directory depth', 'default': 10},
                        'file_size_min': {'type': 'integer', 'description': 'Minimum file size in bytes', 'default': 0},
                        'file_size_max': {'type': 'integer', 'description': 'Maximum file size in bytes'},
                        'timeout_seconds': {'type': 'number', 'description': 'Search deadline in seconds', 'default': 15.0},
                        'content_read_limit': {'type': 'integer', 'description': 'Maximum bytes read per file for content search', 'default': 1048576},
                        'skip_dirs': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Additional directory names to skip'}
                    }
                },
                'function': self.bb7_search_files
            },
            'bb7_file_info': {
                'description': 'Get comprehensive information about a file or directory.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {'path': {'type': 'string', 'description': 'Path to analyze'}},
                    'required': ['path']
                },
                'function': self.bb7_file_info
            },
            'bb7_get_file_info': {
                'description': 'Compatibility alias for bb7_file_info.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {'path': {'type': 'string', 'description': 'Path to analyze'}},
                    'required': ['path']
                },
                'function': self.bb7_get_file_info
            },
            'bb7_file_cache_stats': {
                'description': 'Compatibility shim for the removed legacy file content cache; reports operation-history state.',
                'inputSchema': {'type': 'object', 'properties': {}},
                'function': self.bb7_file_cache_stats
            },
            'bb7_operation_history': {
                'description': 'View file operation history, statistics, and patterns for workflow optimization.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'limit': {'type': 'integer', 'description': 'Number of recent operations to show', 'default': 20},
                        'operation_type': {'type': 'string', 'description': 'Filter by operation type'}
                    }
                },
                'function': self.bb7_operation_history
            }
        }


# Testing
if __name__ == "__main__":
    def test_unleashed_file():
        tool = FileTool()
        
        print("=== Testing Unleashed File Tool ===")
        
        # Test directory listing
        result = tool.bb7_list_directory({'path': '.'})
        print(f"Directory listing:\\n{result}\\n")
        
        # Test file info
        result = tool.bb7_file_info({'path': __file__})
        print(f"File info:\\n{result}\\n")
    
    test_unleashed_file()
