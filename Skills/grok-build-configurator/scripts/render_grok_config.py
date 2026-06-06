#!/usr/bin/env python3
"""Render Grok Build setup templates for common profiles.

This script writes files into an output directory for review. It does not edit
~/.grok or the current repository unless the caller chooses that output path.
"""
from __future__ import annotations

import argparse
import shutil
import stat
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / "assets" / "templates"

PROFILES = {
    "daily": [
        ("config.daily.toml", "global/config.toml"),
        ("pager.tui.toml", "global/pager.toml"),
        ("AGENTS.grok-project.md", "project/AGENTS.md"),
        ("project.grok.config.mcp.toml", "project/.grok/config.toml"),
    ],
    "ci-safe": [
        ("config.ci-safe.toml", "global/config.toml"),
        ("headless-ci-review.sh", "ci/headless-ci-review.sh"),
        ("hooks/git-gh-only/git-gh-only.json", "hooks/git-gh-only/git-gh-only.json"),
        ("hooks/git-gh-only/git-gh-only.sh", "hooks/git-gh-only/git-gh-only.sh"),
    ],
    "enterprise-oidc": [
        ("config.enterprise-oidc.toml", "global/config.toml"),
        ("pager.tui.toml", "global/pager.toml"),
        ("project.grok.config.mcp.toml", "project/.grok/config.toml"),
    ],
    "project-mcp": [
        ("project.grok.config.mcp.toml", "project/.grok/config.toml"),
        ("AGENTS.grok-project.md", "project/AGENTS.md"),
    ],
    "hardened": [
        ("config.ci-safe.toml", "global/config.toml"),
        ("sandbox.toml", "project/.grok/sandbox.toml"),
        ("hooks/git-gh-only/git-gh-only.json", "hooks/git-gh-only/git-gh-only.json"),
        ("hooks/git-gh-only/git-gh-only.sh", "hooks/git-gh-only/git-gh-only.sh"),
        ("headless-ci-review.sh", "ci/headless-ci-review.sh"),
    ],
}


def copy_template(src_rel: str, dst: Path, force: bool) -> None:
    src = TEMPLATES / src_rel
    if not src.exists():
        raise FileNotFoundError(src)
    if dst.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {dst}. Pass --force to replace it.")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if src.suffix == ".sh":
        dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Grok Build config templates.")
    parser.add_argument("profile", choices=sorted(PROFILES), help="Setup profile to render.")
    parser.add_argument("--out", default="./grok-build-rendered-config", help="Output directory. Default: ./grok-build-rendered-config")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files in output directory.")
    args = parser.parse_args()

    out = Path(args.out).expanduser().resolve()
    written: list[Path] = []
    for src_rel, dst_rel in PROFILES[args.profile]:
        dst = out / dst_rel
        copy_template(src_rel, dst, args.force)
        written.append(dst)

    print(f"Rendered Grok Build profile '{args.profile}' into {out}")
    for p in written:
        print(f"- {p}")
    print()
    print("Review the files before copying them into ~/.grok or a repository.")
    print("Run `python3 scripts/grok_build_doctor.py --project <repo>` after applying changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
