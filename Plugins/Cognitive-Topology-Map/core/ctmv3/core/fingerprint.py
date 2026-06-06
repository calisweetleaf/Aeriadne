"""
CTMv3 Fingerprint — Topology Hash Computation and Verification
==============================================================
Provenance: CTMv3 Engine v1.1.0 — 2026-05-23
Author: Forge (activation engine builder)
Purpose: Computes and stores a SHA-256 hash of TOPOLOGY.md + ARCHITECTURE_MAP.md.
         Implements the topology_fingerprint.txt mechanism described in
         DOT_TOPOLOGY.md (.sovereign/ section) and BOOT_PROTOCOL.md Section 3.1.

The fingerprint is the verification anchor for warm-start validity. If the hash
stored in .sovereign/topology_fingerprint.txt differs from the current computed
hash, topology has drifted since the last session close.

Hardening notes (v1.1.0):
  - Structured logging via stdlib logging.
  - SHA-256 computation is now streaming (8 KiB chunks) — files are not loaded
    fully into memory. Safe for large TOPOLOGY.md or ARCHITECTURE_MAP.md files.
  - Swallowed OSError in compute() replaced with logged warning.
  - Input validation: project_root must exist and be a directory.
  - write() uses atomic write (write to .tmp then os.replace).
  - verify() and read_stored() log on read failures instead of silently returning.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)

FINGERPRINT_SOURCES: list[str] = ["TOPOLOGY.md", "ARCHITECTURE_MAP.md"]
FINGERPRINT_FILE: str = ".sovereign/topology_fingerprint.txt"
FINGERPRINT_PREFIX: str = "sha256:"

_CHUNK_SIZE: int = 8192  # 8 KiB streaming chunk size


def compute(project_root: Path) -> str:
    """
    Compute SHA-256 of TOPOLOGY.md + ARCHITECTURE_MAP.md concatenated.

    Files are read in a deterministic order (TOPOLOGY.md first, then
    ARCHITECTURE_MAP.md) in streaming 8 KiB chunks to avoid loading large
    files fully into memory. Missing files contribute an empty byte sequence
    so the hash is always computable regardless of which files exist.

    Args:
        project_root: Path to the project root directory. Must exist.

    Returns:
        A string like "sha256:abcdef1234..." (prefix + 64 hex digits).

    Raises:
        ValueError: If project_root does not exist or is not a directory.
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

    hasher = hashlib.sha256()

    for filename in FINGERPRINT_SOURCES:
        p = root / filename
        if p.exists():
            try:
                _stream_hash(p, hasher)
                logger.debug("compute: hashed %s", filename)
            except OSError as exc:
                # Unreadable file contributes zero bytes — log and continue.
                # The caller will see a different hash than if the file were readable,
                # which is the correct signal (the topology data is inaccessible).
                logger.warning(
                    "compute: cannot read %s, contributing zero bytes to hash: %s",
                    p,
                    exc,
                )
        else:
            logger.debug("compute: %s absent, contributing zero bytes", filename)
        # Missing or unreadable file contributes nothing (idempotent for absent files)

    digest = FINGERPRINT_PREFIX + hasher.hexdigest()
    logger.debug("compute: digest=%s", digest[:20])
    return digest


def _stream_hash(path: Path, hasher: "hashlib._Hash") -> None:
    """
    Read path in chunks and feed each chunk to hasher.

    Raises:
        OSError: If the file cannot be opened or read.
    """
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(_CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)


def write(project_root: Path) -> Path:
    """
    Compute the fingerprint and write it atomically to .sovereign/topology_fingerprint.txt.

    Creates .sovereign/ if it does not exist. Uses os.replace for atomic write.

    Args:
        project_root: Path to the project root directory. Must exist.

    Returns:
        The path to the written fingerprint file.

    Raises:
        ValueError: If project_root does not exist or is not a directory.
        OSError: If the .sovereign/ directory cannot be created or the file cannot be written.
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

    sovereign_dir = root / ".sovereign"
    sovereign_dir.mkdir(parents=True, exist_ok=True)

    hash_value = compute(root)
    fingerprint_path = sovereign_dir / "topology_fingerprint.txt"

    lines: list[str] = [
        f"{hash_value}",
        "",
        "Sources hashed (in order):",
    ]
    for src in FINGERPRINT_SOURCES:
        status = "present" if (root / src).exists() else "absent (contributed empty bytes)"
        lines.append(f"  {src}: {status}")

    sources_absent = [f for f in FINGERPRINT_SOURCES if not (root / f).exists()]
    if sources_absent:
        lines.append("")
        lines.append(
            "WARNING: Some source files were absent. Hash will change when they are created."
        )

    lines.append("")
    lines.append(
        "Regenerate with: python -m ctmv3 fingerprint --project-root <path>"
    )

    content = "\n".join(lines) + "\n"
    _atomic_write(fingerprint_path, content)
    logger.info("write: fingerprint written to %s", fingerprint_path)
    return fingerprint_path


def verify(project_root: Path) -> tuple[bool, str]:
    """
    Compare the stored fingerprint against the current computed hash.

    Returns (matches: bool, current_hash: str).
      matches=True  — stored hash equals current computed hash (no topology drift)
      matches=False — hashes differ, or fingerprint file is absent/unreadable

    The caller should not treat matches=False as an error; it is expected after
    any change to TOPOLOGY.md or ARCHITECTURE_MAP.md and is the intended drift signal.

    Args:
        project_root: Path to the project root directory. Must exist.

    Raises:
        ValueError: If project_root does not exist or is not a directory.
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

    current_hash = compute(root)
    fingerprint_path = root / FINGERPRINT_FILE

    if not fingerprint_path.exists():
        logger.debug("verify: fingerprint file absent; returning (False, current_hash)")
        return False, current_hash

    try:
        stored_content = fingerprint_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("verify: cannot read fingerprint file %s: %s", fingerprint_path, exc)
        return False, current_hash

    # First line of the fingerprint file is the hash value
    first_line = stored_content.splitlines()[0].strip() if stored_content.strip() else ""
    stored_hash = first_line

    matches = stored_hash == current_hash
    logger.debug(
        "verify: stored=%s current=%s matches=%s",
        stored_hash[:20] if stored_hash else "(empty)",
        current_hash[:20],
        matches,
    )
    return matches, current_hash


def read_stored(project_root: Path) -> Optional[str]:
    """
    Read the stored fingerprint hash from topology_fingerprint.txt.
    Returns None if the file does not exist or is unreadable.

    Args:
        project_root: Path to the project root directory.
    """
    root = Path(project_root).resolve()
    fingerprint_path = root / FINGERPRINT_FILE

    if not fingerprint_path.exists():
        return None

    try:
        content = fingerprint_path.read_text(encoding="utf-8")
        first_line = content.splitlines()[0].strip() if content.strip() else ""
        result = first_line if first_line.startswith(FINGERPRINT_PREFIX) else None
        logger.debug("read_stored: result=%s", result[:20] if result else None)
        return result
    except OSError as exc:
        logger.warning("read_stored: cannot read %s: %s", fingerprint_path, exc)
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
