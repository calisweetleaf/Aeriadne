#!/usr/bin/env python3
"""Validate the Aeriadne private-v1 plugin package.

This is intentionally stdlib-only. It checks package shape, manifest parseability,
metadata mirror drift, skill frontmatter, declared path existence, stale canonical
paths, deleted-archive reappearance, and obvious secret/runtime-state/backup-churn
packaging mistakes. It does not install the plugin.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

REQUIRED_PATHS = [
    "plugin.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    "plugin.toml",
    "README.md",
    "MANIFEST.md",
    "MARKETPLACE_ROADMAP.md",
    "CHANGELOG.md",
    "LICENSE.md",
    "registry/aeriadne.plugin.json",
    "registry/plugins.yaml",
    "registry/skills.yaml",
    "registry/agents.yaml",
    "registry/mcp_servers.yaml",
    "skills/constitutional-prompt-framework/SKILL.md",
    "skills/aeriadne-marketplace-operator/SKILL.md",
    "agents/README.md",
    "agents/subagents/prompt-architect.md",
    "agents/subagents/package-cartographer.md",
    "agents/subagents/compatibility-auditor.md",
    "agents/subagents/registry-scribe.md",
    "agents/subagents/release-sentinel.md",
    "adapters/codex/README.md",
    "adapters/claude-code/README.md",
    "adapters/opencode/README.md",
    "mcp/README.md",
    "mcp/servers/sovereign-bb7.md",
    "mcp/contracts/tool-capabilities.yaml",
    "mcp/contracts/client-bindings.yaml",
    "marketplace/cards/aeriadne.plugin.md",
    "marketplace/cards/constitutional-prompt-framework.skill.md",
    "marketplace/cards/aeriadne-marketplace-operator.skill.md",
    "marketplace/cards/sovereign-bb7.mcp.md",
]

FORBIDDEN_NAME_PATTERNS = [
    re.compile(r"(^|/)auth\.json$"),
    re.compile(r"(^|/)installation_id$"),
    re.compile(r"\.(sqlite|sqlite3|db)$"),
    re.compile(r"(^|/)(sessions|logs|tmp|cache)(/|$)"),
    re.compile(r"(^|/)\.env($|\.)"),
    re.compile(r"backup_\d{8}_\d{6}"),
    re.compile(r"~$"),
    re.compile(r"(^|/)__pycache__(/|$)"),
    re.compile(r"\.pyc$"),
]

STALE_TEXT_PATTERNS = [
    "/home/daeron/Projects/" + "Modern-ML/Plugins/" + "Aeriadne",
    "Modern-ML/Plugins/" + "Aeriadne",
]

FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validator reports all parse failures.
        fail(errors, f"JSON parse failed: {path}: {exc}")
        return None


def check_skill_frontmatter(root: Path, rel: str, expected_name: str, errors: list[str]) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        fail(errors, f"missing YAML frontmatter: {rel}")
        return
    body = match.group("body")
    if f"name: {expected_name}" not in body:
        fail(errors, f"frontmatter name mismatch in {rel}; expected {expected_name}")
    if "description:" not in body:
        fail(errors, f"missing description in {rel}")


def check_forbidden_files(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        for pattern in FORBIDDEN_NAME_PATTERNS:
            if pattern.search(rel):
                fail(errors, f"forbidden package file detected: {rel}")


def check_stale_paths(root: Path, errors: list[str]) -> None:
    text_extensions = {".md", ".json", ".toml", ".yaml", ".yml", ".py"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in text_extensions:
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in STALE_TEXT_PATTERNS:
            if marker in text:
                fail(errors, f"stale Modern-ML Aeriadne path in {rel}: {marker}")


def check_deleted_archive_absent(root: Path, errors: list[str]) -> None:
    old_dir = root.parent / "old"
    if old_dir.exists():
        fail(errors, f"deleted legacy plugin archive reappeared: {old_dir}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Aeriadne plugin root")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    errors: list[str] = []

    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            fail(errors, f"missing required path: {rel}")

    root_manifest = load_json(root / "plugin.json", errors) if (root / "plugin.json").exists() else None
    codex_manifest = load_json(root / ".codex-plugin/plugin.json", errors) if (root / ".codex-plugin/plugin.json").exists() else None
    claude_manifest = load_json(root / ".claude-plugin/plugin.json", errors) if (root / ".claude-plugin/plugin.json").exists() else None
    registry_card = load_json(root / "registry/aeriadne.plugin.json", errors) if (root / "registry/aeriadne.plugin.json").exists() else None

    expected_homepage = root.as_uri()
    if isinstance(root_manifest, dict):
        if root_manifest.get("name") != "aeriadne":
            fail(errors, "plugin.json name must be aeriadne")
        if root_manifest.get("skills") != "./skills/":
            fail(errors, "plugin.json skills must be ./skills/")
        if root_manifest.get("homepage") != expected_homepage:
            fail(errors, f"plugin.json homepage must be {expected_homepage}")

    if root_manifest is not None and codex_manifest is not None and root_manifest != codex_manifest:
        fail(errors, "plugin.json and .codex-plugin/plugin.json drifted")
    if root_manifest is not None and claude_manifest is not None and root_manifest != claude_manifest:
        fail(errors, "plugin.json and .claude-plugin/plugin.json drifted")

    if registry_card and isinstance(registry_card, dict):
        if registry_card.get("canonical_path") != str(root):
            fail(errors, f"registry canonical_path must be {root}")
        includes = registry_card.get("includes", {})
        skills = set(includes.get("skills", [])) if isinstance(includes, dict) else set()
        for expected in {"constitutional-prompt-framework", "aeriadne-marketplace-operator"}:
            if expected not in skills:
                fail(errors, f"registry card missing skill include: {expected}")

    try:
        data = tomllib.loads((root / "plugin.toml").read_text(encoding="utf-8"))
        if data.get("id") != "aeriadne":
            fail(errors, "plugin.toml id must be aeriadne")
        if data.get("canonical_path") != str(root):
            fail(errors, f"plugin.toml canonical_path must be {root}")
        for skill in data.get("skills", []):
            path = skill.get("path")
            if path and not (root / path).exists():
                fail(errors, f"plugin.toml references missing skill path: {path}")
        for server in data.get("mcp_servers", []):
            path = server.get("path")
            if path and not (root / path).exists():
                fail(errors, f"plugin.toml references missing MCP path: {path}")
    except Exception as exc:  # noqa: BLE001
        fail(errors, f"TOML parse failed: plugin.toml: {exc}")

    if (root / "skills/constitutional-prompt-framework/SKILL.md").exists():
        check_skill_frontmatter(
            root,
            "skills/constitutional-prompt-framework/SKILL.md",
            "constitutional-prompt-framework",
            errors,
        )
    if (root / "skills/aeriadne-marketplace-operator/SKILL.md").exists():
        check_skill_frontmatter(
            root,
            "skills/aeriadne-marketplace-operator/SKILL.md",
            "aeriadne-marketplace-operator",
            errors,
        )

    check_forbidden_files(root, errors)
    check_stale_paths(root, errors)
    check_deleted_archive_absent(root, errors)

    if errors:
        print("Aeriadne package validation: FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("Aeriadne package validation: PASS")
    print(f"root={root}")
    print("skills=aeriadne-marketplace-operator, constitutional-prompt-framework")
    print("mcp=sovereign-bb7 canonical-reference")
    print("legacy_archive=deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
