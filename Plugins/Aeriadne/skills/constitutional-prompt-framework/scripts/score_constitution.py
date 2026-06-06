#!/usr/bin/env python3
"""Score an agent constitution using a heuristic mirror of the v10 rubric."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _cpf_common import print_json, read_text, score_constitution


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a constitution markdown file.")
    parser.add_argument("path", help="Markdown constitution file")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    path = Path(args.path)
    report = score_constitution(read_text(path))
    report["path"] = str(path)

    if args.json:
        print_json(report)
    else:
        print(f"Score report: {path}")
        print(f"Overall: {report['total']}/100")
        print(f"Readiness: {report['readiness']}")
        print("Category scores:")
        for label, score in report["category_scores"].items():
            print(f"  {label}: {score}/10")
        if report["mandatory_caps"]:
            print("Mandatory caps:")
            for cap in report["mandatory_caps"]:
                print(f"  - {cap}")
    return 0 if report["total"] >= 75 else 2


if __name__ == "__main__":
    sys.exit(main())
