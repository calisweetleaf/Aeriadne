---
description: Audit an existing agent constitution or system prompt — severity-ranked findings, scorecard, rewrite recommendations.
agent: aeriadne-cpf
subtask: true
---

Run the Constitutional Prompt Framework in Mode C (Audit).

Input (prompt file path or pasted content): $ARGUMENTS

1. If a file path is given, read the file.
2. If content is pasted inline, treat it as the subject.
3. Apply the CPF audit sequence:
   - Load `references/15-audit-checklist.md` for severity-ranked checks.
   - Load `references/16-evaluation-rubric.md` for the scorecard.
   - Load `references/17-red-team-suite.md` for adversarial probes.
4. Run `python3 skills/constitutional-prompt-framework/scripts/constitution_linter.py` if
   the subject is in a file.
5. Run `python3 skills/constitutional-prompt-framework/scripts/score_constitution.py` if
   the subject is in a file.

Return:
1. Severity-ranked findings with evidence snippets
2. Scorecard (rubric-based, 0-100)
3. Rewrite recommendations for each Critical/High finding
4. Patched sections or full rewrite if requested
