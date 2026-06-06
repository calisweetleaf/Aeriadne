#!/usr/bin/env python3
"""
Project Context Tool - Enhanced project understanding for MCP clients

Provides intelligent project analysis and context retrieval specifically 
designed for optimal LLM consumption, following MCP best practices.
"""

import json
import logging
import os
import re
import subprocess
import time
import platform
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional, Set, Tuple
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Callable
import time


class ProjectContextTool:
    """Enhanced project context analysis for MCP clients"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Project context tool initialized for MCP integration")
    
    def analyze_project_structure(self, max_depth: int = 3, include_hidden: bool = False) -> str:
        """
        Analyze and summarize project structure in a format optimized for LLM understanding.
        Perfect for helping MCP clients understand your codebase organization.
        
        Args:
            max_depth: Maximum directory depth to analyze (default: 3)
            include_hidden: Whether to include hidden files/directories (default: False)
        """
        try:
            cwd = Path.cwd()
            self.logger.info(f"Analyzing project structure from: {cwd}")
            
            analysis = {
                "project_root": str(cwd),
                "analysis_timestamp": time.ctime(),
                "structure": {},
                "key_files": [],
                "project_type": "unknown",
                "technologies": [],
                "summary": ""
            }
            
            # Detect project type and technologies
            analysis.update(self._detect_project_type(cwd))
            
            # Build directory tree
            analysis["structure"] = self._build_directory_tree(cwd, max_depth, include_hidden)
            
            # Find key configuration and documentation files
            analysis["key_files"] = self._find_key_files(cwd)
            
            # Generate LLM-friendly summary
            analysis["summary"] = self._generate_project_summary(analysis)
            
            # Format for LLM consumption
            return self._format_analysis_for_llm(analysis)
            
        except Exception as e:
            self.logger.error(f"Error analyzing project structure: {e}")
            return f"Error analyzing project structure: {str(e)}"
    
    def get_project_dependencies(self) -> str:
        """
        Extract and summarize project dependencies in LLM-friendly format.
        Helps MCP clients understand what libraries and frameworks are available.
        """
        try:
            cwd = Path.cwd()
            dependencies = {
                "python": [],
                "node": [],
                "other": []
            }
            
            # Python dependencies
            req_files = ["requirements.txt", "pyproject.toml", "Pipfile", "environment.yml"]
            for req_file in req_files:
                req_path = cwd / req_file
                if req_path.exists():
                    deps = self._parse_python_dependencies(req_path)
                    dependencies["python"].extend(deps)
            
            # Node.js dependencies
            package_json = cwd / "package.json"
            if package_json.exists():
                dependencies["node"] = self._parse_node_dependencies(package_json)
            
            # Other dependency files
            other_files = ["Cargo.toml", "go.mod", "pom.xml", "build.gradle"]
            for dep_file in other_files:
                dep_path = cwd / dep_file
                if dep_path.exists():
                    dependencies["other"].append(f"{dep_file} found")
            
            return self._format_dependencies_for_llm(dependencies)
            
        except Exception as e:
            self.logger.error(f"Error getting project dependencies: {e}")
            return f"Error getting project dependencies: {str(e)}"
    
    def get_recent_changes(self, days: int = 7) -> str:
        """
        Get recent Git changes in LLM-friendly format.
        Helps MCP clients understand recent development activity and context.
        
        Args:
            days: Number of days to look back for changes (default: 7)
        """
        try:
            # Check if we're in a git repository
            if not (Path.cwd() / ".git").exists():
                return "This project is not a Git repository"
            
            # Get recent commits with improved error handling
            cmd = ["git", "log", f"--since={days} days ago", "--oneline", "--no-merges"]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode != 0:
                    return f"Git command failed: {result.stderr}"
                
                commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            except subprocess.TimeoutExpired:
                return "Git log command timed out - repository may be too large or hanging"
            except FileNotFoundError:
                return "Git not found - please ensure Git is installed and in PATH"
            except Exception as e:
                return f"Error running git log: {str(e)}"
            
            # Get changed files with improved error handling
            cmd_files = ["git", "diff", f"--since={days} days ago", "--name-only"]
            try:
                result_files = subprocess.run(cmd_files, capture_output=True, text=True, timeout=5)
                changed_files = result_files.stdout.strip().split('\n') if result_files.stdout.strip() else []
            except subprocess.TimeoutExpired:
                changed_files = []
                self.logger.warning("Git diff command timed out")
            except Exception as e:
                changed_files = []
                self.logger.warning(f"Error getting changed files: {e}")
            
            # Get current branch with improved error handling
            cmd_branch = ["git", "branch", "--show-current"]
            try:
                result_branch = subprocess.run(cmd_branch, capture_output=True, text=True, timeout=2)
                current_branch = result_branch.stdout.strip() if result_branch.returncode == 0 else "unknown"
            except subprocess.TimeoutExpired:
                current_branch = "unknown (timeout)"
            except Exception as e:
                current_branch = f"unknown (error: {str(e)[:30]})"
            
            # Format for LLM
            summary = f"Recent Git Activity (last {days} days):\n\n"
            summary += f"Current Branch: {current_branch}\n\n"
            
            if commits:
                summary += f"Recent Commits ({len(commits)}):\n"
                for commit in commits[:10]:  # Limit to 10 most recent
                    summary += f"  • {commit}\n"
                if len(commits) > 10:
                    summary += f"  ... and {len(commits) - 10} more commits\n"
            else:
                summary += "No commits in the specified timeframe\n"
            
            if changed_files:
                summary += f"\nRecently Modified Files ({len(changed_files)}):\n"
                for file in changed_files[:15]:  # Limit to 15 files
                    summary += f"  • {file}\n"
                if len(changed_files) > 15:
                    summary += f"  ... and {len(changed_files) - 15} more files\n"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting recent changes: {e}")
            return f"Error getting recent changes: {str(e)}"
    
    def get_code_metrics(self) -> str:
        """
        Generate code metrics and statistics in LLM-friendly format.
        Helps MCP clients understand codebase size and complexity.
        """
        try:
            cwd = Path.cwd()
            metrics = {
                "total_files": 0,
                "code_files": 0,
                "total_lines": 0,
                "languages": {},
                "largest_files": []
            }
            
            # Code file extensions to analyze
            code_extensions = {
                '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
                '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#',
                '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust', '.php': 'PHP',
                '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
                '.json': 'JSON', '.xml': 'XML', '.yaml': 'YAML', '.yml': 'YAML'
            }
            
            files_analyzed = []
            
            # Walk through project files
            for file_path in cwd.rglob('*'):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    metrics["total_files"] += 1
                    
                    ext = file_path.suffix.lower()
                    if ext in code_extensions:
                        metrics["code_files"] += 1
                        lang = code_extensions[ext]
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                                metrics["total_lines"] += lines
                                
                                if lang not in metrics["languages"]:
                                    metrics["languages"][lang] = {"files": 0, "lines": 0}
                                
                                metrics["languages"][lang]["files"] += 1
                                metrics["languages"][lang]["lines"] += lines
                                
                                files_analyzed.append((str(file_path.relative_to(cwd)), lines))
                        except:
                            continue
            
            # Find largest files
            files_analyzed.sort(key=lambda x: x[1], reverse=True)
            metrics["largest_files"] = files_analyzed[:10]
            
            return self._format_metrics_for_llm(metrics)
            
        except Exception as e:
            self.logger.error(f"Error calculating code metrics: {e}")
            return f"Error calculating code metrics: {str(e)}"
    
    def _detect_project_type(self, path: Path) -> Dict[str, Any]:
        """Detect project type and technologies"""
        project_indicators = {
            "package.json": "Node.js/JavaScript",
            "requirements.txt": "Python",
            "pyproject.toml": "Python (Modern)",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java/Maven",
            "build.gradle": "Java/Gradle",
            ".sln": "C#/.NET",
            "composer.json": "PHP"
        }
        
        technologies = []
        project_type = "Unknown"
        
        for file, tech in project_indicators.items():
            if (path / file).exists():
                technologies.append(tech)
                if project_type == "Unknown":
                    project_type = tech
        
        # Check for frameworks
        if (path / "node_modules").exists():
            technologies.append("Node.js Runtime")
        if (path / ".git").exists():
            technologies.append("Git Version Control")
        if (path / "docker-compose.yml").exists() or (path / "Dockerfile").exists():
            technologies.append("Docker")
        
        return {
            "project_type": project_type,
            "technologies": technologies
        }
    
    def _build_directory_tree(self, path: Path, max_depth: int, include_hidden: bool) -> Dict[str, Any]:
        """Build directory tree structure with configurable depth and hidden file handling"""
        if max_depth < 0:
            return {"type": "directory", "name": path.name}
        
        result = {
            "type": "directory",
            "name": path.name,
            "children": []
        }
        
        try:
            # Use a timeout to prevent hanging on large directories with lots of files
            # We'll use a simple implementation rather than a subprocess call
            start_time = time.time()
            max_time = 3.0  # 3 second timeout for directory operations (reduced from 5s for better responsiveness)
            
            items = list(path.iterdir())
            
            file_count = 0
            dir_count = 0
            hidden_count = 0
            
            for item in items:
                # Check timeout
                if time.time() - start_time > max_time:
                    result["children"].append({
                        "type": "note",
                        "name": f"⚠️ Directory scan timeout - showing partial results ({len(result['children'])} of {len(items)} items)"
                    })
                    break
                
                # Skip hidden files/dirs if not included
                if item.name.startswith('.') and not include_hidden:
                    hidden_count += 1
                    continue
                
                # Skip common large directories that aren't useful for context
                if item.is_dir() and item.name in self._get_ignored_dirs():
                    result["children"].append({
                        "type": "skipped_directory", 
                        "name": item.name
                    })
                    continue
                
                try:
                    if item.is_dir():
                        dir_count += 1
                        # Recurse with decreased max_depth
                        if dir_count <= 20:  # Limit number of directories to process at each level
                            child = self._build_directory_tree(item, max_depth - 1, include_hidden)
                            result["children"].append(child)
                        else:
                            result["children"].append({
                                "type": "note",
                                "name": f"... {dir_count - 20} more directories (omitted for brevity)"
                            })
                    else:
                        file_count += 1
                        # Only include up to 50 files per directory to avoid overwhelming context
                        if file_count <= 50:
                            size = item.stat().st_size
                            result["children"].append({
                                "type": "file",
                                "name": item.name,
                                "size": self._format_size(size),
                                "extension": item.suffix.lower()[1:] if item.suffix else ""
                            })
                        
                        # After 50 files, provide a summary instead
                        if file_count == 51:
                            result["children"].append({
                                "type": "note",
                                "name": "... additional files omitted for brevity"
                            })
                except PermissionError:
                    result["children"].append({
                        "type": "error",
                        "name": f"{item.name} (permission denied)"
                    })
                except Exception as e:
                    result["children"].append({
                        "type": "error",
                        "name": f"{item.name} (error: {str(e)[:30]})"
                    })
            
            # Add info about skipped hidden files
            if hidden_count > 0:
                result["hidden_skipped"] = hidden_count
            
            return result
            
        except PermissionError:
            return {
                "type": "directory",
                "name": path.name,
                "error": "Permission denied"
            }
        except Exception as e:
            return {
                "type": "directory",
                "name": path.name,
                "error": str(e)[:50]
            }
    
    def _get_ignored_dirs(self) -> Set[str]:
        """Get set of directory names that should be ignored in analysis"""
        return {
            "node_modules", "__pycache__", ".git", ".vscode",
            "venv", "env", ".env", "virtualenv", "dist",
            "build", "target", "out", "bin", "obj",
            ".idea", ".gradle", ".pytest_cache", ".next"
        }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def _find_key_files(self, path: Path) -> List[str]:
        """Find key project files"""
        key_patterns = [
            "README*", "LICENSE*", "CHANGELOG*", "CONTRIBUTING*",
            "requirements.txt", "package.json", "pyproject.toml",
            "Dockerfile", "docker-compose.yml", ".gitignore",
            "Makefile", "setup.py", "main.py", "index.js", "app.py"
        ]
        
        found_files = []
        for pattern in key_patterns:
            matches = list(path.glob(pattern))
            found_files.extend([str(f.relative_to(path)) for f in matches])
        
        return found_files
    
    def _should_ignore_file(self, path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            "node_modules", "__pycache__", ".git", ".vscode",
            "venv", "env", ".env", "dist", "build", "target",
            ".pytest_cache", ".coverage", "*.pyc", "*.pyo"
        ]
        
        path_str = str(path)
        return any(pattern in path_str for pattern in ignore_patterns)
    
    def _parse_python_dependencies(self, req_path: Path) -> List[str]:
        """Parse Python dependencies"""
        try:
            if req_path.name == "requirements.txt":
                with open(req_path, 'r') as f:
                    lines = f.readlines()
                    deps = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Extract package name (before version specifiers)
                            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].split('>')[0].split('<')[0]
                            deps.append(pkg_name.strip())
                    return deps
            # Add more parsers for pyproject.toml, etc. as needed
        except Exception:
            pass
        return []
    
    def _parse_node_dependencies(self, package_path: Path) -> List[str]:
        """Parse Node.js dependencies"""
        try:
            with open(package_path, 'r') as f:
                package_data = json.load(f)
                deps = []
                deps.extend(package_data.get('dependencies', {}).keys())
                deps.extend(package_data.get('devDependencies', {}).keys())
                return deps
        except Exception:
            pass
        return []
    
    def _format_analysis_for_llm(self, analysis: Dict[str, Any]) -> str:
        """Format analysis in LLM-friendly way"""
        output = f"Project Structure Analysis\n"
        output += f"========================\n\n"
        output += f"Project Root: {analysis['project_root']}\n"
        output += f"Project Type: {analysis['project_type']}\n"
        output += f"Technologies: {', '.join(analysis['technologies'])}\n\n"
        
        if analysis['key_files']:
            output += f"Key Files Found:\n"
            for file in analysis['key_files'][:10]:
                output += f"  • {file}\n"
            if len(analysis['key_files']) > 10:
                output += f"  ... and {len(analysis['key_files']) - 10} more\n"
            output += "\n"
        
        output += f"Summary: {analysis['summary']}\n"
        return output
    
    def _format_dependencies_for_llm(self, deps: Dict[str, List]) -> str:
        """Format dependencies for LLM consumption"""
        output = "Project Dependencies\n"
        output += "===================\n\n"
        
        if deps['python']:
            output += f"Python Dependencies ({len(deps['python'])}):\n"
            for dep in deps['python'][:15]:
                output += f"  • {dep}\n"
            if len(deps['python']) > 15:
                output += f"  ... and {len(deps['python']) - 15} more\n"
            output += "\n"
        
        if deps['node']:
            output += f"Node.js Dependencies ({len(deps['node'])}):\n"
            for dep in deps['node'][:15]:
                output += f"  • {dep}\n"
            if len(deps['node']) > 15:
                output += f"  ... and {len(deps['node']) - 15} more\n"
            output += "\n"
        
        if deps['other']:
            output += f"Other Dependency Files:\n"
            for dep in deps['other']:
                output += f"  • {dep}\n"
        
        return output
    
    def _format_metrics_for_llm(self, metrics: Dict[str, Any]) -> str:
        """Format code metrics for LLM consumption"""
        output = "Code Metrics Summary\n"
        output += "===================\n\n"
        output += f"Total Files: {metrics['total_files']}\n"
        output += f"Code Files: {metrics['code_files']}\n"
        output += f"Total Lines of Code: {metrics['total_lines']}\n\n"
        
        if metrics['languages']:
            output += "Languages Breakdown:\n"
            for lang, stats in sorted(metrics['languages'].items(), 
                                    key=lambda x: x[1]['lines'], reverse=True):
                output += f"  • {lang}: {stats['files']} files, {stats['lines']} lines\n"
            output += "\n"
        
        if metrics['largest_files']:
            output += "Largest Files:\n"
            for file, lines in metrics['largest_files'][:5]:
                output += f"  • {file}: {lines} lines\n"
        
        return output
    
    def _generate_project_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate intelligent project summary"""
        project_type = analysis['project_type']
        technologies = analysis['technologies']
        
        if 'Python' in project_type:
            return f"This is a Python project using {', '.join(technologies)}. "
        elif 'Node.js' in project_type or 'JavaScript' in project_type:
            return f"This is a JavaScript/Node.js project using {', '.join(technologies)}. "
        else:
            return f"This is a {project_type} project using {', '.join(technologies)}. "
    
    def get_tools(self) -> Dict[str, Callable]:
        """Return all available tool functions with bb7_ prefix for MCP consistency"""
        return {
            # Use bb7_ prefix for all tools to maintain consistency with MCP naming conventions
            'bb7_analyze_project_structure': {
                "function": lambda max_depth=3, include_hidden=False: 
                    self.analyze_project_structure(max_depth, include_hidden),
                "description": "Analyze and summarize project structure in a format optimized for LLM understanding.",
                "parameters": [
                    {"name": "max_depth", "description": "Maximum directory depth to analyze.", "type": "number", "required": False},
                    {"name": "include_hidden", "description": "Whether to include hidden files/directories.", "type": "boolean", "required": False}
                ]
            },
            'bb7_get_project_dependencies': {
                "function": self.get_project_dependencies,
                "description": "Extract and summarize project dependencies in LLM-friendly format.",
                "parameters": []
            },
            'bb7_get_recent_changes': {
                "function": lambda days=7: self.get_recent_changes(days),
                "description": "Get recent Git changes in LLM-friendly format.",
                "parameters": [
                    {"name": "days", "description": "Number of days to look back for changes.", "type": "number", "required": False}
                ]
            },
            'bb7_get_code_metrics': {
                "function": self.get_code_metrics,
                "description": "Generate code metrics and statistics in LLM-friendly format.",
                "parameters": []
            }
        }


# For standalone testing
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