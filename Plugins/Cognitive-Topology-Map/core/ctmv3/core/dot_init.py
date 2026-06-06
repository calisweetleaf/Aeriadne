"""
CTMv3 Dot Init — .xyz Directory Scaffolding
============================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Scaffolds .claude/, .codex/skills/, and .github/ directories with their
         CTM artifact files, per DOT_TOPOLOGY.md.

Each init function is idempotent by default — existing files are not overwritten
unless force=True is passed. This protects prior agent work.

Targets:
  claude   -- .claude/settings.json + .claude/CLAUDE.md (skips CLAUDE.md if exists at root)
  codex    -- .codex/skills/ directory scaffold
  github   -- .github/copilot-instructions.md, instructions/, workflows/topology-enforce.yml
  all      -- all three targets

Hardening notes (v1.1.0):
  - Structured logging via stdlib logging.
  - All file writes are atomic (write to .tmp then os.replace) via _atomic_write_if_absent.
  - Fixed _write_if_absent status logic: status is determined BEFORE writing, not after.
  - Input validation: project_name must be non-empty; target must be one of the known literals.
  - init_target raises ValueError with a message that names valid targets.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Literal

from ctmv3.core import templates as tmpl


logger = logging.getLogger(__name__)

TargetType = Literal["claude", "codex", "github", "all"]

CLAUDE_SETTINGS_DEFAULT: dict = {
    "permissions": {
        "allow": [
            "Bash(python:*)",
            "Bash(go build:*)",
            "Read(*)",
            "Write(src/**)",
            "Write(tests/**)",
        ],
        "deny": [
            "Bash(rm -rf:*)",
            "Write(manifest.json)",
        ],
    },
    "env": {
        "SOVEREIGN_DATA_DIR": "./data",
        "SOVEREIGN_DISTILLATION_ENABLED": "0",
    },
}


def init_claude(
    project_root: Path,
    project_name: str,
    force: bool = False,
) -> dict[str, str]:
    """
    Scaffold .claude/ directory.

    Creates:
      .claude/settings.json   -- permissions and env config
      .claude/CLAUDE.md       -- Claude Code operational context (if not at root)

    Args:
        project_root: Path to the project root directory.
        project_name: Human-readable project name. Must be non-empty.
        force: If True, overwrite existing files.

    Returns:
        A dict mapping file path -> "created" | "skipped" | "force-overwritten".

    Raises:
        ValueError: If project_name is empty.
        OSError: If directory creation or file write fails.
    """
    if not project_name or not project_name.strip():
        raise ValueError(
            "project_name must be a non-empty string."
        )

    root = Path(project_root).resolve()
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("init_claude: scaffolding %s", claude_dir)

    results: dict[str, str] = {}

    # settings.json
    settings_path = claude_dir / "settings.json"
    results[str(settings_path)] = _write_if_absent(
        settings_path,
        json.dumps(CLAUDE_SETTINGS_DEFAULT, indent=2) + "\n",
        force=force,
    )

    # CLAUDE.md — write to .claude/ unless a root CLAUDE.md already exists
    root_claude = root / "CLAUDE.md"
    claude_md_path = claude_dir / "CLAUDE.md"

    if root_claude.exists() and not force:
        results[str(claude_md_path)] = "skipped (root CLAUDE.md exists)"
        logger.debug("init_claude: skipping .claude/CLAUDE.md (root CLAUDE.md present)")
    else:
        content = tmpl.render_claude_md(project_name)
        results[str(claude_md_path)] = _write_if_absent(claude_md_path, content, force=force)

    logger.info("init_claude: done; results=%s", list(results.values()))
    return results


def init_codex(
    project_root: Path,
    force: bool = False,
) -> dict[str, str]:
    """
    Scaffold .codex/ directory.

    Creates:
      .codex/skills/          -- directory for per-repo CTM skill installs
      .codex/session/         -- directory for Codex session state
      .codex/skills/.gitkeep  -- placeholder so skills/ is tracked

    Returns a dict mapping file path -> "created" | "skipped".

    Raises:
        OSError: If directory creation or file write fails.
    """
    root = Path(project_root).resolve()
    results: dict[str, str] = {}

    skills_dir = root / ".codex" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    results[str(skills_dir)] = "created"
    logger.debug("init_codex: created %s", skills_dir)

    session_dir = root / ".codex" / "session"
    session_dir.mkdir(parents=True, exist_ok=True)
    results[str(session_dir)] = "created"
    logger.debug("init_codex: created %s", session_dir)

    gitkeep = skills_dir / ".gitkeep"
    results[str(gitkeep)] = _write_if_absent(
        gitkeep,
        "# This file keeps the skills/ directory tracked by git.\n",
        force=force,
    )

    logger.info("init_codex: done; results=%s", list(results.values()))
    return results


def init_github(
    project_root: Path,
    project_name: str,
    force: bool = False,
) -> dict[str, str]:
    """
    Scaffold .github/ directory.

    Creates:
      .github/copilot-instructions.md     -- repo-wide agent context
      .github/instructions/               -- per-path context directory
      .github/workflows/topology-enforce.yml -- CTM topology enforcement CI gate

    Args:
        project_root: Path to the project root directory.
        project_name: Human-readable project name. Must be non-empty.
        force: If True, overwrite existing files.

    Returns:
        A dict mapping file path -> "created" | "skipped" | "force-overwritten".

    Raises:
        ValueError: If project_name is empty.
        OSError: If directory creation or file write fails.
    """
    if not project_name or not project_name.strip():
        raise ValueError(
            "project_name must be a non-empty string."
        )

    root = Path(project_root).resolve()
    results: dict[str, str] = {}

    github_dir = root / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)

    instructions_dir = github_dir / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    results[str(instructions_dir)] = "created"

    workflows_dir = github_dir / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    results[str(workflows_dir)] = "created"

    # copilot-instructions.md
    copilot_path = github_dir / "copilot-instructions.md"
    content = tmpl.render_copilot_instructions(project_name)
    results[str(copilot_path)] = _write_if_absent(copilot_path, content, force=force)

    # topology-enforce.yml
    enforce_path = workflows_dir / "topology-enforce.yml"
    yml_content = tmpl.render_topology_enforce_yml(project_name)
    results[str(enforce_path)] = _write_if_absent(enforce_path, yml_content, force=force)

    # instructions placeholder README
    instructions_readme = instructions_dir / "README.md"
    instructions_content = (
        "# .github/instructions/\n\n"
        "Place per-path agent context files here following the GitHub Copilot model.\n"
        "Example: `backend.instructions.md` for context injected when working in /backend/.\n\n"
        "See DOT_TOPOLOGY.md for the full encoding doctrine.\n"
    )
    results[str(instructions_readme)] = _write_if_absent(
        instructions_readme, instructions_content, force=force
    )

    logger.info("init_github: done; results=%s", list(results.values()))
    return results


def init_all(
    project_root: Path,
    project_name: str,
    force: bool = False,
) -> dict[str, str]:
    """
    Run init_claude, init_codex, and init_github in sequence.

    Returns merged results dict.

    Raises:
        ValueError: If project_name is empty.
        OSError: If any directory creation or file write fails.
    """
    if not project_name or not project_name.strip():
        raise ValueError(
            "project_name must be a non-empty string."
        )

    results: dict[str, str] = {}
    results.update(init_claude(project_root, project_name, force=force))
    results.update(init_codex(project_root, force=force))
    results.update(init_github(project_root, project_name, force=force))
    return results


def init_target(
    target: TargetType,
    project_root: Path,
    project_name: str,
    force: bool = False,
) -> dict[str, str]:
    """
    Dispatch to the appropriate init function based on target string.

    Args:
        target: One of "claude", "codex", "github", "all"
        project_root: Absolute path to the project root
        project_name: Human-readable project name used in template substitution
        force: If True, overwrite existing files

    Returns:
        Results dict mapping file paths to their write outcome.

    Raises:
        ValueError: If target is not a recognized value, or project_name is empty.
        OSError: If directory creation or file write fails.
    """
    _valid = {"claude", "codex", "github", "all"}
    if target not in _valid:
        raise ValueError(
            f"Unknown target '{target}'. Valid targets: {sorted(_valid)}"
        )

    logger.debug("init_target: target=%s project_name=%s force=%s", target, project_name, force)

    if target == "claude":
        return init_claude(project_root, project_name, force=force)
    elif target == "codex":
        return init_codex(project_root, force=force)
    elif target == "github":
        return init_github(project_root, project_name, force=force)
    else:  # target == "all"
        return init_all(project_root, project_name, force=force)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _write_if_absent(path: Path, content: str, force: bool = False) -> str:
    """
    Write content to path if it does not exist, or if force=True.

    Uses atomic write (write to .tmp then os.replace) to avoid partial-write
    corruption on crash.

    Returns a status string: "created", "skipped", or "force-overwritten".

    Raises:
        OSError: If the write or rename fails.
    """
    if path.exists() and not force:
        logger.debug("_write_if_absent: skipped (exists, no force) %s", path)
        return "skipped"

    # Determine status BEFORE writing (path.exists() is accurate at this point)
    status = "force-overwritten" if path.exists() else "created"

    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, content)
    logger.debug("_write_if_absent: %s %s", status, path)
    return status


def _atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write content to path atomically via a .tmp intermediate file.

    Raises:
        OSError: If the write or rename fails.
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding=encoding)
        os.replace(str(tmp_path), str(path))
    except OSError:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
