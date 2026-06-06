"""
CTMv3 Architecture Map — ARCHITECTURE_MAP.md Scaffolding
=========================================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Scaffolds ARCHITECTURE_MAP.md from the template. Does not fabricate
         content — leaves [TODO: ...] markers for the agent or operator to fill.
         The document structure (ROOT / BRANCH A / BRANCH B / Quick Reference)
         is always present after scaffolding.

Per ARCHITECTURE_MAP_TEMPLATE.md: the map is a traversal map, not a summary.
Each node answers one question and points to file:line anchors. The scaffold
provides the shape; the agent fills the line anchors after reading the repo.

Also provides from_topology() which injects project name derived from TOPOLOGY.md
if that file is present.

Hardening notes (v1.1.0):
  - Structured logging via stdlib logging.
  - All file writes are atomic (write to .tmp then os.replace).
  - Fixed scaffold() status logic: determined BEFORE writing, not after.
  - Input validation: project_root must exist; project_name, if provided, must be non-empty.
  - All OSError paths in name-extraction helpers are logged.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from ctmv3.core import templates as tmpl


logger = logging.getLogger(__name__)

ARCHITECTURE_MAP_FILENAME: str = "ARCHITECTURE_MAP.md"


def scaffold(
    project_root: Path,
    project_name: Optional[str] = None,
    force: bool = False,
) -> tuple[Path, str]:
    """
    Scaffold ARCHITECTURE_MAP.md at project_root.

    Does not overwrite an existing file unless force=True.
    Write is atomic (write to .tmp then os.replace).

    Args:
        project_root: Absolute path to the project root. Must exist.
        project_name: Human-readable project name. If None, inferred from
                      TOPOLOGY.md header or from the directory name. If provided,
                      must be non-empty.
        force: If True, overwrite an existing ARCHITECTURE_MAP.md

    Returns:
        (path, status) where status is "created", "skipped", or "force-overwritten".

    Raises:
        ValueError: If project_root does not exist, is not a directory, or
                    project_name is provided but is empty.
        OSError: If the file cannot be written.
    """
    root = Path(project_root).resolve()
    if not root.exists():
        raise ValueError(
            f"project_root does not exist: {root}. Pass an existing directory."
        )
    if not root.is_dir():
        raise ValueError(
            f"project_root is not a directory: {root}."
        )
    if project_name is not None and not project_name.strip():
        raise ValueError(
            "project_name must be non-empty when provided. "
            "Pass None to infer from the project root."
        )

    map_path = root / ARCHITECTURE_MAP_FILENAME

    if map_path.exists() and not force:
        logger.debug("scaffold: skipped (exists, no force) %s", map_path)
        return map_path, "skipped"

    # Determine status BEFORE writing
    status = "force-overwritten" if map_path.exists() else "created"

    name = project_name or _infer_project_name(root)
    content = tmpl.render_architecture_map(name)
    _atomic_write(map_path, content)
    logger.info("scaffold: %s %s (project_name=%s)", status, map_path, name)
    return map_path, status


def from_topology(
    project_root: Path,
    force: bool = False,
) -> tuple[Path, str]:
    """
    Scaffold ARCHITECTURE_MAP.md, extracting the project name from TOPOLOGY.md
    if that file is present.

    This is the --from-topology variant of the architecture-map subcommand.
    It reads the first H1 heading from TOPOLOGY.md to derive the project name.

    Returns (path, status) same as scaffold().

    Raises:
        ValueError: If project_root does not exist or is not a directory.
        OSError: If the file cannot be written.
    """
    root = Path(project_root).resolve()
    if not root.exists():
        raise ValueError(
            f"project_root does not exist: {root}. Pass an existing directory."
        )
    if not root.is_dir():
        raise ValueError(
            f"project_root is not a directory: {root}."
        )

    topology_path = root / "TOPOLOGY.md"
    project_name: Optional[str] = None
    if topology_path.exists():
        project_name = _extract_project_name_from_topology(topology_path)
        if project_name:
            logger.debug("from_topology: extracted project_name=%s from %s", project_name, topology_path)
        else:
            logger.debug("from_topology: could not extract project_name from %s; will infer", topology_path)

    return scaffold(root, project_name=project_name, force=force)


def _infer_project_name(project_root: Path) -> str:
    """
    Infer the project name from available signals, in priority order:
    1. TOPOLOGY.md first H1 heading
    2. pyproject.toml [project] name field
    3. package.json name field
    4. go.mod module path (last segment)
    5. Directory name as fallback
    """
    topo = project_root / "TOPOLOGY.md"
    if topo.exists():
        name = _extract_project_name_from_topology(topo)
        if name:
            return name

    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        name = _extract_from_pyproject(pyproject)
        if name:
            return name

    package_json = project_root / "package.json"
    if package_json.exists():
        name = _extract_from_package_json(package_json)
        if name:
            return name

    gomod = project_root / "go.mod"
    if gomod.exists():
        name = _extract_from_gomod(gomod)
        if name:
            return name

    return project_root.name


def _extract_project_name_from_topology(topology_path: Path) -> Optional[str]:
    """Extract project name from the first H1 or H2 heading in TOPOLOGY.md."""
    try:
        text = topology_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning(
            "_extract_project_name_from_topology: cannot read %s: %s", topology_path, exc
        )
        return None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# TOPOLOGY"):
            # "# TOPOLOGY — Domain Name" or "# TOPOLOGY — [Domain Name]"
            parts = stripped.replace("# TOPOLOGY", "").strip()
            if parts.startswith("—") or parts.startswith("-"):
                name = parts.lstrip("—- ").strip()
                if name and not name.startswith("["):
                    return name
        elif stripped.startswith("# "):
            name = stripped[2:].strip()
            if name and not name.lower().startswith("topology"):
                return name

    return None


def _extract_from_pyproject(pyproject_path: Path) -> Optional[str]:
    """Extract project name from pyproject.toml.

    Attempts tomllib (Python 3.11+) then tomli (optional 3.10 shim)
    then falls back to naive line scanner. Never raises on parse errors.
    """
    # Try stdlib tomllib (Python 3.11+)
    _tomllib: Any = None
    try:
        import tomllib as _tomllib  # type: ignore[import-not-found]
    except ImportError:
        # Try optional tomli package (3.10 shim)
        try:
            import tomli as _tomllib  # type: ignore[import-not-found,no-redef]
        except ImportError:
            _tomllib = None

    if _tomllib is not None:
        result = _extract_from_pyproject_tomllib(pyproject_path, _tomllib)
        if result:
            return result

    # Fallback to naive scanner
    return _extract_from_pyproject_naive(pyproject_path)


def _extract_from_pyproject_tomllib(pyproject_path: Path, tomllib: Any) -> Optional[str]:
    """Extract project name using a TOML library (tomllib or tomli)."""
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, Exception) as exc:
        logger.debug(
            "_extract_from_pyproject_tomllib: parse failed for %s: %s", pyproject_path, exc
        )
        return None

    # PEP 517/518: [project].name
    name = data.get("project", {}).get("name")
    if name and isinstance(name, str):
        logger.debug(
            "_extract_from_pyproject_tomllib: found [project].name = %r", name
        )
        return name.strip()

    # Poetry: [tool.poetry].name
    name = data.get("tool", {}).get("poetry", {}).get("name")
    if name and isinstance(name, str):
        logger.debug(
            "_extract_from_pyproject_tomllib: found [tool.poetry].name = %r", name
        )
        return name.strip()

    logger.debug(
        "_extract_from_pyproject_tomllib: no name field found in %s", pyproject_path
    )
    return None


def _extract_from_pyproject_naive(pyproject_path: Path) -> Optional[str]:
    """Extract name from [project] or [tool.poetry] section in pyproject.toml.

    Naive line-by-line scanner used as a fallback when tomllib/tomli is unavailable.
    Handles simple `name = "value"` patterns. Does not handle multi-line TOML values.
    """
    try:
        text = pyproject_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning(
            "_extract_from_pyproject: cannot read %s: %s", pyproject_path, exc
        )
        return None

    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in ("[project]", "[tool.poetry]"):
            in_project = True
            continue
        if stripped.startswith("[") and stripped not in ("[project]", "[tool.poetry]"):
            in_project = False
        if in_project and stripped.startswith("name"):
            parts = stripped.split("=", 1)
            if len(parts) == 2:
                return parts[1].strip().strip('"').strip("'")

    return None


def _extract_from_package_json(package_json_path: Path) -> Optional[str]:
    """Extract name from package.json."""
    try:
        raw = package_json_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return data.get("name") or None
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "_extract_from_package_json: cannot parse %s: %s", package_json_path, exc
        )
        return None


def _extract_from_gomod(gomod_path: Path) -> Optional[str]:
    """Extract module name (last path segment) from go.mod."""
    try:
        text = gomod_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning(
            "_extract_from_gomod: cannot read %s: %s", gomod_path, exc
        )
        return None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("module "):
            module_path = stripped[len("module "):].strip()
            return module_path.split("/")[-1] if "/" in module_path else module_path

    return None


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
