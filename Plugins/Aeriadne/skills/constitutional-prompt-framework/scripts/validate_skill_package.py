#!/usr/bin/env python3
"""Validate a Constitutional Prompt Framework skill package."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _cpf_common import NAME_RE, find_references, parse_frontmatter, read_text, scan_for_secret_patterns


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate skill package structure and metadata.")
    parser.add_argument("root", nargs="?", default=".", help="Package root directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    errors = []
    warnings = []
    info = []

    skill_path = root / "SKILL.md"
    if not skill_path.exists():
        errors.append("Missing SKILL.md at package root.")
        frontmatter = {}
        body = ""
    else:
        text = read_text(skill_path)
        frontmatter, body = parse_frontmatter(text)
        if not frontmatter:
            errors.append("SKILL.md missing YAML frontmatter.")
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not name:
            errors.append("SKILL.md frontmatter missing name.")
        elif not NAME_RE.match(name):
            errors.append(f"Invalid skill name: {name!r}. Use lowercase letters, numbers, and hyphens.")
        if not description:
            errors.append("SKILL.md frontmatter missing description.")
        elif len(description) > 1024:
            errors.append(f"Description is {len(description)} chars; keep at or below 1024 for broad compatibility.")
        elif len(description) < 80:
            warnings.append("Description is short; skill discovery may be weaker.")
        info.append(f"Skill name: {name or '[missing]'}")
        info.append(f"Description length: {len(description)}")

        for ref in find_references(text):
            clean_ref = ref.split()[0].strip()
            if not (root / clean_ref).exists():
                errors.append(f"Referenced path does not exist: {clean_ref}")

    for expected_dir in ["references", "assets", "scripts", "tests", "examples", "agents"]:
        if not (root / expected_dir).exists():
            warnings.append(f"Optional directory missing: {expected_dir}")

    openai_yaml = root / "agents" / "openai.yaml"
    if openai_yaml.exists():
        text = read_text(openai_yaml)
        for required in ["interface:", "display_name:", "short_description:", "default_prompt:"]:
            if required not in text:
                warnings.append(f"agents/openai.yaml missing expected key: {required}")
    else:
        warnings.append("agents/openai.yaml not present. This is optional but recommended for OpenAI surfaces.")

    secret_hits = scan_for_secret_patterns(root)
    if secret_hits:
        errors.append("Potential secret-like pattern found in: " + ", ".join(secret_hits))

    report = {"root": str(root), "errors": errors, "warnings": warnings, "info": info, "ok": not errors}
    if args.json:
        import json
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Constitutional Prompt Framework package validation")
        for line in info:
            print(f"INFO: {line}")
        for line in warnings:
            print(f"WARN: {line}")
        for line in errors:
            print(f"ERROR: {line}")
        print("RESULT:", "PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
