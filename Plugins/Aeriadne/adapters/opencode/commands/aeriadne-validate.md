---
description: Run the full Aeriadne package validation gate sequence — JSON/TOML/YAML parse, skill frontmatter, secret scan, adapter drift, registry consistency. Use before promoting any package.
agent: aeriadne-release-sentinel
subtask: true
---

Run the Aeriadne release sentinel validation gate sequence.

Working directory: $ARGUMENTS
If no argument is given, use the current directory (run from the Aeriadne plugin root).

Execute every gate in order:
1. Root manifest parse: `python3 -m json.tool plugin.json`
2. TOML parse: `python3 -c "import pathlib,tomllib; tomllib.loads(pathlib.Path('plugin.toml').read_text())"`
3. Client manifests: `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`
4. Package structure: `python3 scripts/validate_package.py .`
5. Skill packages: validate each skill under `skills/`
6. Constitution linter on canonical example
7. Score check (>= 70 required)
8. Static evals
9. Secrets scan: `find . -name ".env" -o -name "*.sqlite" -o -name "oauth*" -o -name "*.log" -o -name "*.cache" -o -name "session*" -o -name "__pycache__" -o -name ".cache" | grep -v .git`

Return PROMOTION READY or BLOCKED with exact gate failures.
