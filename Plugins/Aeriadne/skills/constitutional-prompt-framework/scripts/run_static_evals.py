#!/usr/bin/env python3
"""Validate and summarize static red-team eval probes.

This runner does not call a model. It validates the eval file and prints coverage.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from _cpf_common import load_json_compatible_yaml, print_json

REQUIRED = {"id", "title", "prompt", "expected_layers", "pass_signals"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate static eval probe file.")
    parser.add_argument("eval_file", help="JSON-compatible YAML eval file")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    path = Path(args.eval_file)
    cases = load_json_compatible_yaml(path)
    errors = []
    coverage = Counter()
    ids = set()

    if not isinstance(cases, list):
        errors.append("Eval file must contain a list of cases.")
        cases = []

    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"Case {i} is not an object.")
            continue
        missing = REQUIRED - set(case)
        if missing:
            errors.append(f"Case {i} missing keys: {sorted(missing)}")
        cid = case.get("id")
        if cid in ids:
            errors.append(f"Duplicate case id: {cid}")
        ids.add(cid)
        for layer in case.get("expected_layers", []):
            coverage[layer] += 1
        if len(case.get("prompt", "")) < 20:
            errors.append(f"Case {cid} prompt is too short to be useful.")
        if not case.get("pass_signals"):
            errors.append(f"Case {cid} has no pass signals.")

    report = {"path": str(path), "case_count": len(cases), "coverage": dict(sorted(coverage.items())), "errors": errors, "ok": not errors}
    if args.json:
        print_json(report)
    else:
        print(f"Static eval report: {path}")
        print(f"Cases: {len(cases)}")
        print("Layer coverage:")
        for layer, count in sorted(coverage.items()):
            print(f"  {layer}: {count}")
        for error in errors:
            print(f"ERROR: {error}")
        print("RESULT:", "PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
