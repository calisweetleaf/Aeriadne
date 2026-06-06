"""
CTMv3 Templates — Template Loader and Renderer
===============================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Provides load() and render() for all CTMv3 document templates.
         Templates live in the templates/ directory adjacent to this file,
         so Daeron can edit them without re-shipping code.

Template variables use {{VARIABLE_NAME}} syntax. render() substitutes all
provided context keys. Unmatched {{...}} placeholders are left in place so
the scaffolded document still shows what needs to be filled.

Available templates:
  TOPOLOGY.md.template
  FAILURE_GRAMMAR.md.template
  PROVENANCE.md.template
  ARCHITECTURE_MAP.md.template
  AGENTS.md.template
  CLAUDE.md.template
  copilot-instructions.md.template
  topology-enforce.yml.template

Hardening notes (v1.1.0):
  - Structured logging via stdlib logging.
  - Input validation: name must be a non-empty string and must not contain
    path traversal sequences (../ or absolute separators).
  - TemplateNotFoundError message now includes the resolved search path for
    easier debugging.
  - list_templates() logs a warning if _TEMPLATES_DIR does not exist rather
    than silently returning an empty list.
"""

from __future__ import annotations

import logging
from pathlib import Path


logger = logging.getLogger(__name__)

# Path to the templates/ directory relative to this file
_TEMPLATES_DIR: Path = Path(__file__).parent / "templates"


class TemplateNotFoundError(FileNotFoundError):
    """Raised when a requested template file cannot be found."""


def load(name: str) -> str:
    """
    Load a template by filename from the templates/ directory.

    Args:
        name: Template filename, e.g. "TOPOLOGY.md.template". Must be a
              plain filename with no directory separators or traversal sequences.

    Returns:
        Raw template text with {{VARIABLE}} placeholders intact.

    Raises:
        ValueError: If name is empty or contains path traversal sequences.
        TemplateNotFoundError: If the template file does not exist.
        OSError: If the template file exists but cannot be read.
    """
    if not name or not name.strip():
        raise ValueError(
            "Template name must be a non-empty string."
        )
    # Reject path traversal and absolute paths to prevent directory escape
    if ".." in name or name.startswith("/") or name.startswith("\\"):
        raise ValueError(
            f"Template name '{name}' contains path traversal or absolute path sequences. "
            "Pass a plain filename like 'TOPOLOGY.md.template'."
        )

    template_path = _TEMPLATES_DIR / name
    if not template_path.exists():
        available = [p.name for p in _TEMPLATES_DIR.glob("*.template")] if _TEMPLATES_DIR.exists() else []
        raise TemplateNotFoundError(
            f"Template '{name}' not found in {_TEMPLATES_DIR}. "
            f"Available: {sorted(available)}"
        )

    try:
        content = template_path.read_text(encoding="utf-8")
        logger.debug("load: loaded template %s (%d chars)", name, len(content))
        return content
    except OSError as exc:
        logger.error("load: cannot read template %s: %s", template_path, exc)
        raise


def render(name: str, **context: str) -> str:
    """
    Load a template and substitute {{KEY}} placeholders with context values.

    All keys in context are substituted. {{KEY}} patterns with no matching
    context key are left as-is (so partial renders work correctly).

    Args:
        name: Template filename, e.g. "TOPOLOGY.md.template"
        **context: Keyword arguments for substitution, e.g. PROJECT_NAME="myrepo"

    Returns:
        Rendered template string.

    Raises:
        ValueError: If name is invalid (see load()).
        TemplateNotFoundError: If the template does not exist.
        OSError: If the template cannot be read.

    Example:
        render("TOPOLOGY.md.template", PROJECT_NAME="myrepo", TODAY="2026-05-23")
    """
    text = load(name)
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", str(value))
    logger.debug("render: rendered %s with %d context keys", name, len(context))
    return text


def list_templates() -> list[str]:
    """
    Return the names of all available template files, sorted alphabetically.

    Returns an empty list if the templates/ directory does not exist.
    """
    if not _TEMPLATES_DIR.exists():
        logger.warning(
            "list_templates: templates directory not found at %s", _TEMPLATES_DIR
        )
        return []
    names = sorted(p.name for p in _TEMPLATES_DIR.glob("*.template"))
    logger.debug("list_templates: found %d templates", len(names))
    return names


def render_topology(
    project_name: str,
    today: str,
    language: str = "unknown",
    **config_flags: str,
) -> str:
    """
    Convenience renderer for TOPOLOGY.md.template.

    Args:
        project_name: Project name to substitute. Must be non-empty.
        today: ISO date string (YYYY-MM-DD).
        language: Detected primary language (e.g., "python", "go", "unknown").
        **config_flags: Optional flags: HAS_PYPROJECT, HAS_GOMOD, HAS_CARGO,
                        HAS_PACKAGEJSON, HAS_MANIFEST, HAS_AGENTS, HAS_CLAUDE,
                        HAS_SOVEREIGN, HAS_GITHUB — each "yes" or "no".

    Raises:
        ValueError: If project_name is empty.
    """
    if not project_name or not project_name.strip():
        raise ValueError("project_name must be non-empty.")

    ctx = {
        "PROJECT_NAME": project_name,
        "TODAY": today,
        "LANGUAGE": language,
        "HAS_PYPROJECT": "no",
        "HAS_GOMOD": "no",
        "HAS_CARGO": "no",
        "HAS_PACKAGEJSON": "no",
        "HAS_MANIFEST": "no",
        "HAS_AGENTS": "no",
        "HAS_CLAUDE": "no",
        "HAS_SOVEREIGN": "no",
        "HAS_GITHUB": "no",
    }
    ctx.update(config_flags)
    return render("TOPOLOGY.md.template", **ctx)


def render_provenance(project_name: str, today: str) -> str:
    """
    Convenience renderer for PROVENANCE.md.template.

    Raises:
        ValueError: If project_name is empty.
    """
    if not project_name or not project_name.strip():
        raise ValueError("project_name must be non-empty.")
    return render("PROVENANCE.md.template", PROJECT_NAME=project_name, TODAY=today)


def render_failure_grammar(project_name: str, today: str) -> str:
    """
    Convenience renderer for FAILURE_GRAMMAR.md.template.

    Raises:
        ValueError: If project_name is empty.
    """
    if not project_name or not project_name.strip():
        raise ValueError("project_name must be non-empty.")
    return render("FAILURE_GRAMMAR.md.template", PROJECT_NAME=project_name, TODAY=today)


def render_architecture_map(project_name: str) -> str:
    """
    Convenience renderer for ARCHITECTURE_MAP.md.template.

    Raises:
        ValueError: If project_name is empty.
    """
    if not project_name or not project_name.strip():
        raise ValueError("project_name must be non-empty.")
    return render("ARCHITECTURE_MAP.md.template", PROJECT_NAME=project_name)


def render_agents_md(project_name: str) -> str:
    """
    Convenience renderer for AGENTS.md.template.

    Raises:
        ValueError: If project_name is empty.
    """
    if not project_name or not project_name.strip():
        raise ValueError("project_name must be non-empty.")
    return render("AGENTS.md.template", PROJECT_NAME=project_name)


def render_claude_md(project_name: str) -> str:
    """
    Convenience renderer for CLAUDE.md.template.

    Raises:
        ValueError: If project_name is empty.
    """
    if not project_name or not project_name.strip():
        raise ValueError("project_name must be non-empty.")
    return render("CLAUDE.md.template", PROJECT_NAME=project_name)


def render_copilot_instructions(project_name: str) -> str:
    """
    Convenience renderer for copilot-instructions.md.template.

    Raises:
        ValueError: If project_name is empty.
    """
    if not project_name or not project_name.strip():
        raise ValueError("project_name must be non-empty.")
    return render("copilot-instructions.md.template", PROJECT_NAME=project_name)


def render_topology_enforce_yml(project_name: str = "") -> str:
    """
    Convenience renderer for topology-enforce.yml.template.

    project_name is accepted for API consistency but this template has no
    {{PROJECT_NAME}} placeholder.
    """
    return render("topology-enforce.yml.template", PROJECT_NAME=project_name)
