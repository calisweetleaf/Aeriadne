#!/usr/bin/env python3
"""Heuristic linter for agent constitutions."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _cpf_common import constitution_heuristics, print_json, read_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a constitution markdown file for structural signals.")
    parser.add_argument("path", help="Markdown constitution file")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    path = Path(args.path)
    text = read_text(path)
    h = constitution_heuristics(text)
    checks = h["checks"]
    missing = [name for name, ok in checks.items() if not ok]
    warnings = []
    if h["word_count"] < 1200:
        warnings.append("Very short for a production constitution; verify this is intentional.")
    if h["heading_count"] < 8:
        warnings.append("Few headings; long-context navigation may be weak.")
    if h["tetrad_signal_count"] < 3:
        warnings.append("Few tetrad signals; doctrine may lack rationale/failure-mode encoding.")
    if h["approval_signal_count"] < 2:
        warnings.append("Few approval signals; irreversible action gates may be weak.")

    report = {"path": str(path), "missing_structural_checks": missing, "warnings": warnings, "heuristics": h, "ok": not missing}
    if args.json:
        print_json(report)
    else:
        print(f"Lint report: {path}")
        print("Structural checks:")
        for name, ok in checks.items():
            print(f"  {'PASS' if ok else 'FAIL'} {name}")
        for warning in warnings:
            print(f"WARN: {warning}")
        print("RESULT:", "PASS" if not missing else "REVIEW")
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())
