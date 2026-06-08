#!/usr/bin/env python3
"""
Project Context Tool - bounded, production-grade project understanding for MCP clients.

Provides LLM-optimized project structure, dependency, Git activity, and code metric
summaries without unbounded filesystem walks or shell execution.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

import tomllib


class ProjectContextTool:
    """Enhanced project context analysis for MCP clients."""

    DEFAULT_MAX_DEPTH = 3
    MAX_DEPTH_LIMIT = 8
    MAX_DIR_SECONDS = 5.0
    MAX_FILES_PER_DIR = 50
    MAX_DIRS_PER_DIR = 20
    MAX_METRIC_FILES = 25000
    MAX_FILE_BYTES_FOR_LINE_COUNT = 2 * 1024 * 1024
    GIT_TIMEOUT_SECONDS = 8.0

    CODE_EXTENSIONS: Dict[str, str] = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".rb": "Ruby",
        ".go": "Go",
        ".rs": "Rust",
        ".php": "PHP",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".json": "JSON",
        ".xml": "XML",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".md": "Markdown",
        ".sh": "Shell",
    }

    PROJECT_INDICATORS: Dict[str, str] = {
        "package.json": "Node.js/JavaScript",
        "requirements.txt": "Python",
        "pyproject.toml": "Python (Modern)",
        "Pipfile": "Python/Pipenv",
        "environment.yml": "Python/Conda",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "pom.xml": "Java/Maven",
        "build.gradle": "Java/Gradle",
        "composer.json": "PHP",
        "deno.json": "Deno",
        "bun.lockb": "Bun",
    }

    KEY_PATTERNS: Tuple[str, ...] = (
        "README*",
        "LICENSE*",
        "CHANGELOG*",
        "CONTRIBUTING*",
        "AGENTS.md",
        "CLAUDE.md",
        "STYLE.md",
        "requirements.txt",
        "package.json",
        "pyproject.toml",
        "Cargo.toml",
        "go.mod",
        "Dockerfile",
        "docker-compose.yml",
        ".gitignore",
        "Makefile",
        "setup.py",
        "main.py",
        "index.js",
        "app.py",
    )

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.info("Project context tool initialized for MCP integration")

    def analyze_project_structure(
        self, max_depth: int = DEFAULT_MAX_DEPTH, include_hidden: bool = False
    ) -> str:
        """Analyze and summarize project structure for LLM consumption."""
        try:
            max_depth = self._coerce_int(
                max_depth, "max_depth", 0, self.MAX_DEPTH_LIMIT
            )
            include_hidden = self._coerce_bool(include_hidden)
            cwd = Path.cwd().resolve()
            self.logger.info(
                "Analyzing project structure from %s max_depth=%s include_hidden=%s",
                cwd,
                max_depth,
                include_hidden,
            )

            analysis: Dict[str, Any] = {
                "project_root": str(cwd),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "structure": self._build_directory_tree(cwd, max_depth, include_hidden),
                "key_files": self._find_key_files(cwd),
                "project_type": "Unknown",
                "technologies": [],
                "summary": "",
            }
            analysis.update(self._detect_project_type(cwd))
            analysis["summary"] = self._generate_project_summary(analysis)
            return self._format_analysis_for_llm(analysis)
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            self.logger.error("Error analyzing project structure: %s", exc)
            return f"Error analyzing project structure: {exc}"

    def get_project_dependencies(self) -> str:
        """Extract and summarize project dependencies in LLM-friendly format."""
        try:
            cwd = Path.cwd().resolve()
            dependencies: Dict[str, List[str]] = {"python": [], "node": [], "other": []}

            for req_name in (
                "requirements.txt",
                "pyproject.toml",
                "Pipfile",
                "environment.yml",
            ):
                req_path = cwd / req_name
                if req_path.is_file():
                    dependencies["python"].extend(
                        self._parse_python_dependencies(req_path)
                    )

            package_json = cwd / "package.json"
            if package_json.is_file():
                dependencies["node"].extend(self._parse_node_dependencies(package_json))

            for dep_file in (
                "Cargo.toml",
                "go.mod",
                "pom.xml",
                "build.gradle",
                "composer.json",
            ):
                dep_path = cwd / dep_file
                if dep_path.is_file():
                    dependencies["other"].append(f"{dep_file} found")

            dependencies["python"] = sorted(set(dependencies["python"]))
            dependencies["node"] = sorted(set(dependencies["node"]))
            dependencies["other"] = sorted(set(dependencies["other"]))
            return self._format_dependencies_for_llm(dependencies)
        except (
            OSError,
            json.JSONDecodeError,
            RuntimeError,
            ValueError,
            TypeError,
        ) as exc:
            self.logger.error("Error getting project dependencies: %s", exc)
            return f"Error getting project dependencies: {exc}"

    def get_recent_changes(self, days: int = 7) -> str:
        """Get recent Git changes in LLM-friendly format."""
        try:
            days = self._coerce_int(days, "days", 1, 365)
            cwd = Path.cwd().resolve()
            if not self._is_git_repository(cwd):
                return "This project is not a Git repository"
            if shutil.which("git") is None:
                return "Git not found - please ensure Git is installed and in PATH"

            since_arg = f"--since={days} days ago"
            commits_result = self._run_git(
                ["log", since_arg, "--oneline", "--no-merges", "--max-count=50"], cwd
            )
            commits = (
                commits_result.stdout.strip().splitlines()
                if commits_result.stdout.strip()
                else []
            )

            branch_result = self._run_git(["branch", "--show-current"], cwd)
            current_branch = branch_result.stdout.strip() or "detached-or-unknown"
            changed_files = self._recent_changed_files(cwd, since_arg)

            summary = f"Recent Git Activity (last {days} days):\n\n"
            summary += f"Current Branch: {current_branch}\n\n"
            if commits:
                summary += f"Recent Commits ({len(commits)} shown, max 50):\n"
                for commit in commits[:10]:
                    summary += f"  • {commit}\n"
                if len(commits) > 10:
                    summary += f"  ... and {len(commits) - 10} more commits\n"
            else:
                summary += "No commits in the specified timeframe\n"

            if changed_files:
                summary += (
                    f"\nRecently Changed Files ({len(changed_files)} shown, max 50):\n"
                )
                for file_name in changed_files[:15]:
                    summary += f"  • {file_name}\n"
                if len(changed_files) > 15:
                    summary += f"  ... and {len(changed_files) - 15} more files\n"
            return summary
        except subprocess.TimeoutExpired as exc:
            self.logger.error(
                "Git command timed out while getting recent changes: %s", exc
            )
            return "Git command timed out - repository may be too large or a Git process is hanging"
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            self.logger.error("Error getting recent changes: %s", exc)
            return f"Error getting recent changes: {exc}"

    def get_code_metrics(self) -> str:
        """Generate bounded code metrics and statistics in LLM-friendly format."""
        try:
            cwd = Path.cwd().resolve()
            metrics: Dict[str, Any] = {
                "total_files": 0,
                "code_files": 0,
                "total_lines": 0,
                "languages": {},
                "largest_files": [],
                "skipped_files": 0,
                "scan_limit_hit": False,
            }
            files_analyzed: List[Tuple[str, int]] = []
            scanned = 0

            for file_path in self._iter_project_files(cwd):
                scanned += 1
                if scanned > self.MAX_METRIC_FILES:
                    metrics["scan_limit_hit"] = True
                    break
                metrics["total_files"] += 1
                ext = file_path.suffix.lower()
                if ext not in self.CODE_EXTENSIONS:
                    continue
                try:
                    stat = file_path.stat()
                except OSError as exc:
                    metrics["skipped_files"] += 1
                    self.logger.debug(
                        "Skipping file stat failure for %s: %s", file_path, exc
                    )
                    continue
                if stat.st_size > self.MAX_FILE_BYTES_FOR_LINE_COUNT:
                    metrics["skipped_files"] += 1
                    continue

                line_count = self._count_lines(file_path)
                if line_count is None:
                    metrics["skipped_files"] += 1
                    continue

                lang = self.CODE_EXTENSIONS[ext]
                metrics["code_files"] += 1
                metrics["total_lines"] += line_count
                metrics["languages"].setdefault(lang, {"files": 0, "lines": 0})
                metrics["languages"][lang]["files"] += 1
                metrics["languages"][lang]["lines"] += line_count
                files_analyzed.append((str(file_path.relative_to(cwd)), line_count))

            files_analyzed.sort(key=lambda item: item[1], reverse=True)
            metrics["largest_files"] = files_analyzed[:10]
            return self._format_metrics_for_llm(metrics)
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            self.logger.error("Error calculating code metrics: %s", exc)
            return f"Error calculating code metrics: {exc}"

    def _detect_project_type(self, path: Path) -> Dict[str, Any]:
        technologies: List[str] = []
        project_type = "Unknown"
        for file_name, tech in self.PROJECT_INDICATORS.items():
            if (path / file_name).exists():
                technologies.append(tech)
                if project_type == "Unknown":
                    project_type = tech
        if (path / ".git").exists():
            technologies.append("Git Version Control")
        if (path / "docker-compose.yml").exists() or (path / "Dockerfile").exists():
            technologies.append("Docker")
        if (path / "mcp_server.py").exists():
            technologies.append("MCP/BB7 Runtime")
        return {"project_type": project_type, "technologies": sorted(set(technologies))}

    def _build_directory_tree(
        self, path: Path, max_depth: int, include_hidden: bool
    ) -> Dict[str, Any]:
        if max_depth < 0:
            return {
                "type": "directory",
                "name": path.name,
                "children": [],
                "depth_limit": True,
            }

        started_at = time.monotonic()
        result: Dict[str, Any] = {
            "type": "directory",
            "name": path.name,
            "children": [],
        }
        try:
            items = sorted(
                path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            )
        except PermissionError:
            return {
                "type": "directory",
                "name": path.name,
                "children": [],
                "error": "Permission denied",
            }
        except OSError as exc:
            return {
                "type": "directory",
                "name": path.name,
                "children": [],
                "error": str(exc)[:120],
            }

        file_count = 0
        dir_count = 0
        hidden_count = 0
        ignored_dirs = self._get_ignored_dirs()

        for item in items:
            if time.monotonic() - started_at > self.MAX_DIR_SECONDS:
                result["children"].append(
                    {
                        "type": "note",
                        "name": f"scan timeout after {self.MAX_DIR_SECONDS:.1f}s; partial results shown",
                    }
                )
                break
            if item.name.startswith(".") and not include_hidden:
                hidden_count += 1
                continue
            try:
                if item.is_dir():
                    if item.name in ignored_dirs:
                        result["children"].append(
                            {"type": "skipped_directory", "name": item.name}
                        )
                        continue
                    dir_count += 1
                    if dir_count <= self.MAX_DIRS_PER_DIR:
                        result["children"].append(
                            self._build_directory_tree(
                                item, max_depth - 1, include_hidden
                            )
                        )
                    elif dir_count == self.MAX_DIRS_PER_DIR + 1:
                        result["children"].append(
                            {"type": "note", "name": "additional directories omitted"}
                        )
                else:
                    file_count += 1
                    if file_count <= self.MAX_FILES_PER_DIR:
                        size = item.stat().st_size
                        result["children"].append(
                            {
                                "type": "file",
                                "name": item.name,
                                "size": self._format_size(size),
                                "extension": item.suffix.lower()[1:]
                                if item.suffix
                                else "",
                            }
                        )
                    elif file_count == self.MAX_FILES_PER_DIR + 1:
                        result["children"].append(
                            {"type": "note", "name": "additional files omitted"}
                        )
            except PermissionError:
                result["children"].append(
                    {"type": "error", "name": f"{item.name} (permission denied)"}
                )
            except OSError as exc:
                result["children"].append(
                    {"type": "error", "name": f"{item.name} ({str(exc)[:80]})"}
                )

        if hidden_count:
            result["hidden_skipped"] = hidden_count
        return result

    def _get_ignored_dirs(self) -> Set[str]:
        return {
            "node_modules",
            "__pycache__",
            ".git",
            ".vscode",
            "venv",
            "env",
            ".env",
            "virtualenv",
            "dist",
            "build",
            "target",
            "out",
            "bin",
            "obj",
            ".idea",
            ".gradle",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".next",
            "mcp.venv",
            "data",
        }

    def _iter_project_files(self, root: Path) -> Iterable[Path]:
        ignored = self._get_ignored_dirs()
        stack = [root]
        while stack:
            current = stack.pop()
            try:
                items = sorted(current.iterdir(), key=lambda p: p.name.lower())
            except (PermissionError, OSError) as exc:
                self.logger.debug(
                    "Skipping directory %s during metrics scan: %s", current, exc
                )
                continue
            for item in items:
                if item.name.startswith(".") and item.name not in {".gitignore"}:
                    continue
                if item.is_dir():
                    if item.name not in ignored:
                        stack.append(item)
                elif item.is_file() and not self._should_ignore_file(item):
                    yield item

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _find_key_files(self, path: Path) -> List[str]:
        found_files: List[str] = []
        for pattern in self.KEY_PATTERNS:
            for match in path.glob(pattern):
                if match.is_file():
                    found_files.append(str(match.relative_to(path)))
        return sorted(set(found_files))

    def _should_ignore_file(self, path: Path) -> bool:
        ignored = self._get_ignored_dirs()
        return any(part in ignored for part in path.parts)

    def _parse_python_dependencies(self, req_path: Path) -> List[str]:
        if req_path.name == "requirements.txt":
            return self._parse_requirements_txt(req_path)
        if req_path.name == "pyproject.toml":
            return self._parse_pyproject(req_path)
        if req_path.name == "Pipfile":
            return self._parse_pipfile(req_path)
        if req_path.name == "environment.yml":
            return self._parse_environment_yml(req_path)
        return []

    def _parse_requirements_txt(self, req_path: Path) -> List[str]:
        deps: List[str] = []
        for raw_line in req_path.read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            line = line.split("#", 1)[0].strip()
            package = re.split(r"\s*(?:==|>=|<=|~=|!=|>|<|\[)", line, maxsplit=1)[
                0
            ].strip()
            if package:
                deps.append(package)
        return deps

    def _parse_pyproject(self, req_path: Path) -> List[str]:
        with req_path.open("rb") as handle:
            pyproject = tomllib.load(handle)
        deps: List[str] = []
        project = pyproject.get("project", {})
        deps.extend(self._dependency_names(project.get("dependencies", [])))
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for values in optional.values():
                deps.extend(
                    self._dependency_names(values if isinstance(values, list) else [])
                )
        poetry = (
            pyproject.get("tool", {}).get("poetry", {})
            if isinstance(pyproject.get("tool"), dict)
            else {}
        )
        if isinstance(poetry, dict):
            for name in poetry.get("dependencies", {}).keys():
                if name.lower() != "python":
                    deps.append(str(name))
        return deps

    def _parse_pipfile(self, req_path: Path) -> List[str]:
        with req_path.open("rb") as handle:
            pipfile = tomllib.load(handle)
        deps: List[str] = []
        for section in ("packages", "dev-packages"):
            values = pipfile.get(section, {})
            if isinstance(values, dict):
                deps.extend(str(name) for name in values.keys())
        return deps

    def _parse_environment_yml(self, req_path: Path) -> List[str]:
        deps: List[str] = []
        in_deps = False
        for raw_line in req_path.read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if stripped == "dependencies:":
                in_deps = True
                continue
            if not in_deps or not stripped.startswith("-"):
                continue
            value = stripped[1:].strip()
            if not value or value.startswith("pip:"):
                continue
            deps.append(re.split(r"[=<> ]", value, maxsplit=1)[0])
        return deps

    @staticmethod
    def _dependency_names(values: List[Any]) -> List[str]:
        names: List[str] = []
        for value in values:
            if isinstance(value, str):
                package = re.split(r"\s*(?:==|>=|<=|~=|!=|>|<|\[)", value, maxsplit=1)[
                    0
                ].strip()
                if package:
                    names.append(package)
        return names

    def _parse_node_dependencies(self, package_path: Path) -> List[str]:
        with package_path.open("r", encoding="utf-8") as handle:
            package_data = json.load(handle)
        deps: List[str] = []
        for section in (
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        ):
            values = package_data.get(section, {})
            if isinstance(values, dict):
                deps.extend(str(name) for name in values.keys())
        return deps

    def _format_analysis_for_llm(self, analysis: Dict[str, Any]) -> str:
        output = "Project Structure Analysis\n"
        output += "========================\n\n"
        output += f"Project Root: {analysis['project_root']}\n"
        output += f"Analysis Time: {analysis['analysis_timestamp']}\n"
        output += f"Project Type: {analysis['project_type']}\n"
        technologies = analysis.get("technologies", [])
        output += f"Technologies: {', '.join(technologies) if technologies else 'None detected'}\n\n"
        if analysis["key_files"]:
            output += "Key Files Found:\n"
            for file_name in analysis["key_files"][:20]:
                output += f"  • {file_name}\n"
            if len(analysis["key_files"]) > 20:
                output += f"  ... and {len(analysis['key_files']) - 20} more\n"
            output += "\n"
        output += f"Summary: {analysis['summary']}\n"
        output += "\nTop-Level Structure:\n"
        output += self._format_tree(analysis["structure"], max_lines=120)
        return output

    def _format_tree(
        self, node: Dict[str, Any], *, indent: int = 0, max_lines: int = 120
    ) -> str:
        lines: List[str] = []

        def walk(current: Dict[str, Any], depth: int) -> None:
            if len(lines) >= max_lines:
                return
            prefix = "  " * depth
            marker = "/" if current.get("type") == "directory" else ""
            name = current.get("name", "unknown")
            extra = (
                f" [{current.get('type')}]"
                if current.get("type") not in {"directory", "file"}
                else ""
            )
            size = f" ({current.get('size')})" if current.get("size") else ""
            lines.append(f"{prefix}• {name}{marker}{size}{extra}")
            for child in current.get("children", []):
                if isinstance(child, dict):
                    walk(child, depth + 1)

        walk(node, indent)
        if len(lines) >= max_lines:
            lines.append("  ... structure output truncated")
        return "\n".join(lines)

    def _format_dependencies_for_llm(self, deps: Dict[str, List[str]]) -> str:
        output = "Project Dependencies\n"
        output += "===================\n\n"
        any_deps = False
        for label, key in (
            ("Python", "python"),
            ("Node.js", "node"),
            ("Other Dependency Files", "other"),
        ):
            values = deps.get(key, [])
            if not values:
                continue
            any_deps = True
            output += f"{label} ({len(values)}):\n"
            for dep in values[:30]:
                output += f"  • {dep}\n"
            if len(values) > 30:
                output += f"  ... and {len(values) - 30} more\n"
            output += "\n"
        if not any_deps:
            output += "No recognized dependency files found.\n"
        return output

    def _format_metrics_for_llm(self, metrics: Dict[str, Any]) -> str:
        output = "Code Metrics Summary\n"
        output += "===================\n\n"
        output += f"Total Files Scanned: {metrics['total_files']}\n"
        output += f"Code Files: {metrics['code_files']}\n"
        output += f"Total Lines of Code: {metrics['total_lines']}\n"
        output += f"Skipped Files: {metrics['skipped_files']}\n"
        if metrics.get("scan_limit_hit"):
            output += f"Scan Limit Hit: yes (max {self.MAX_METRIC_FILES} files)\n"
        output += "\n"
        if metrics["languages"]:
            output += "Languages Breakdown:\n"
            for lang, stats in sorted(
                metrics["languages"].items(),
                key=lambda item: item[1]["lines"],
                reverse=True,
            ):
                output += (
                    f"  • {lang}: {stats['files']} files, {stats['lines']} lines\n"
                )
            output += "\n"
        if metrics["largest_files"]:
            output += "Largest Files:\n"
            for file_name, lines in metrics["largest_files"][:10]:
                output += f"  • {file_name}: {lines} lines\n"
        return output

    @staticmethod
    def _generate_project_summary(analysis: Dict[str, Any]) -> str:
        project_type = analysis.get("project_type", "Unknown")
        technologies = analysis.get("technologies", [])
        tech_text = (
            ", ".join(technologies)
            if technologies
            else "no detected technology markers"
        )
        return f"This is a {project_type} project using {tech_text}."

    @staticmethod
    def _coerce_int(value: Any, field_name: str, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be an integer") from exc
        if not minimum <= parsed <= maximum:
            raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
        return parsed

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return bool(value)

    @staticmethod
    def _is_git_repository(path: Path) -> bool:
        return (path / ".git").exists()

    def _run_git(self, args: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        command = ["git", "--no-pager", *args]
        env = {**os.environ, "GIT_PAGER": "cat", "PAGER": "cat"}
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=self.GIT_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()[:500]
            raise RuntimeError(
                f"git {' '.join(args)} failed with exit {result.returncode}: {stderr}"
            )
        return result

    def _recent_changed_files(self, cwd: Path, since_arg: str) -> List[str]:
        commit_hashes = (
            self._run_git(
                ["log", since_arg, "--format=%H", "--no-merges", "--max-count=100"], cwd
            )
            .stdout.strip()
            .splitlines()
        )
        files: Set[str] = set()
        for commit_hash in commit_hashes[:100]:
            if not re.fullmatch(r"[0-9a-fA-F]{40}", commit_hash):
                continue
            result = self._run_git(
                ["show", "--name-only", "--format=", commit_hash], cwd
            )
            for line in result.stdout.splitlines():
                name = line.strip()
                if name:
                    files.add(name)
                if len(files) >= 50:
                    return sorted(files)
        return sorted(files)

    def _count_lines(self, file_path: Path) -> Optional[int]:
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
                return sum(1 for _ in handle)
        except (OSError, UnicodeError) as exc:
            self.logger.debug("Skipping unreadable file %s: %s", file_path, exc)
            return None

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return all available tool functions with bb7_ prefix for MCP consistency."""
        return {
            "bb7_analyze_project_structure": {
                "function": lambda max_depth=3, include_hidden=False: (
                    self.analyze_project_structure(max_depth, include_hidden)
                ),
                "description": "Analyze and summarize project structure in a bounded LLM-friendly format.",
                "parameters": [
                    {
                        "name": "max_depth",
                        "description": "Maximum directory depth to analyze (0-8).",
                        "type": "number",
                        "required": False,
                    },
                    {
                        "name": "include_hidden",
                        "description": "Whether to include hidden files/directories.",
                        "type": "boolean",
                        "required": False,
                    },
                ],
            },
            "bb7_get_project_dependencies": {
                "function": self.get_project_dependencies,
                "description": "Extract and summarize project dependencies in LLM-friendly format.",
                "parameters": [],
            },
            "bb7_get_recent_changes": {
                "function": lambda days=7: self.get_recent_changes(days),
                "description": "Get recent Git changes in LLM-friendly format.",
                "parameters": [
                    {
                        "name": "days",
                        "description": "Number of days to look back for changes (1-365).",
                        "type": "number",
                        "required": False,
                    }
                ],
            },
            "bb7_get_code_metrics": {
                "function": self.get_code_metrics,
                "description": "Generate bounded code metrics and statistics in LLM-friendly format.",
                "parameters": [],
            },
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tool = ProjectContextTool()
    print("=== Project Structure Analysis ===")
    print(tool.analyze_project_structure())
    print("\n=== Project Dependencies ===")
    print(tool.get_project_dependencies())
    print("\n=== Recent Changes ===")
    print(tool.get_recent_changes())
    print("\n=== Code Metrics ===")
    print(tool.get_code_metrics())
