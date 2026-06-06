#!/usr/bin/env python3
"""Render a Markdown constitution from a JSON constitution spec.

The renderer is intentionally conservative. It creates a complete structural draft,
then humans or agents should refine the prose and run lint/scoring.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def bullets(items: Iterable[str]) -> str:
    items = list(items or [])
    if not items:
        return "- [none specified]"
    return "\n".join(f"- {item}" for item in items)


def numbered(items: Iterable[str]) -> str:
    items = list(items or [])
    if not items:
        return "1. [none specified]"
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


def render_rule(rule: Mapping[str, str]) -> str:
    return f"""### ROE: {rule.get('name', '[unnamed rule]')}

- Trigger: {rule.get('trigger', '[missing]')}
- Rule: {rule.get('rule', '[missing]')}
- Rationale: {rule.get('rationale', '[missing]')}
- Violation surface: {rule.get('violation_surface', '[missing]')}
- Recovery: {rule.get('recovery', '[missing]')}
""".strip()


def render_principle(item: Mapping[str, str]) -> str:
    return f"""### {item.get('name', '[unnamed principle]')}

- Principle: {item.get('principle', '[missing]')}
- Rationale: {item.get('rationale', '[missing]')}
- Failure mode: {item.get('failure_mode', '[missing]')}
- Required behavior: {item.get('required_behavior', '[missing]')}
""".strip()


def render_capability(cap: Mapping[str, str]) -> str:
    return "| {name} | {trigger} | {use} | {do_not_use} | {verification} | {approval_gate} | {fallback} |".format(
        name=cap.get("name", "[missing]"),
        trigger=cap.get("trigger", "[missing]"),
        use=cap.get("use", "[missing]"),
        do_not_use=cap.get("do_not_use", "[missing]"),
        verification=cap.get("verification", "[missing]"),
        approval_gate=cap.get("approval_gate", "[missing]"),
        fallback=cap.get("fallback", "[missing]"),
    )


def render(spec: Mapping[str, object]) -> str:
    identity = spec.get("identity", {})
    authority = spec.get("authority", {})
    persona = spec.get("persona", {})
    domain = spec.get("domain", {})
    memory = spec.get("memory", {})
    outputs = spec.get("outputs", {})
    evaluation = spec.get("evaluation", {})
    status = spec.get("status", {})

    agent_name = identity.get("agent_name", "[Agent Name]")
    roe = spec.get("roe", []) or []
    doctrine = spec.get("doctrine", []) or []
    capabilities = spec.get("capabilities", []) or []
    glossary = domain.get("glossary", {}) if isinstance(domain, dict) else {}

    lines = []
    lines.append(f"# {agent_name} Constitution")
    lines.append("\n## 0. Mission bootloader\n")
    lines.append(f"{agent_name} is a {identity.get('agent_type', '[agent type]')}. It exists to {identity.get('mission', '[mission]')}")
    lines.append("\n## 1. Identity and mission\n")
    lines.append(f"### Identity\n\n{identity.get('agent_type', '[agent type]')}")
    lines.append(f"\n### Mission\n\n{identity.get('mission', '[mission]')}")
    lines.append(f"\n### Scope\n\n{bullets(identity.get('scope', []))}")
    lines.append(f"\n### Non-goals\n\n{bullets(identity.get('non_goals', []))}")
    lines.append(f"\n### Success conditions\n\n{bullets(identity.get('success_conditions', []))}")
    lines.append("\n## 2. Authority and governance\n")
    lines.append(f"### Authority hierarchy\n\n{numbered(authority.get('hierarchy', []))}")
    lines.append(f"\n### Approval gates\n\n{bullets(authority.get('approval_gates', []))}")
    lines.append(f"\n### Conflict handling\n\n{authority.get('conflict_handling', '[missing]')}")
    lines.append(f"\n### Refusal behavior\n\n{authority.get('refusal_behavior', '[missing]')}")
    lines.append("\n## 3. Rules of engagement\n")
    lines.append("\n\n".join(render_rule(rule) for rule in roe) or "[No rules specified]")
    lines.append("\n## 4. Operating doctrine\n")
    lines.append("\n\n".join(render_principle(item) for item in doctrine) or "[No doctrine specified]")
    lines.append("\n## 5. Persona architecture\n")
    lines.append(f"### Archetype\n\n{persona.get('archetype', '[none specified]')}")
    lines.append(f"\n### Voice\n\n{bullets(persona.get('voice', []))}")
    lines.append(f"\n### Posture\n\n{bullets(persona.get('posture', []))}")
    lines.append(f"\n### Behavioral defaults\n\n{bullets(persona.get('behavioral_defaults', []))}")
    lines.append("\n## 6. Capability posture\n")
    lines.append("| Capability | Trigger | Use | Do not use | Verification | Approval gate | Fallback |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append("\n".join(render_capability(cap) for cap in capabilities) or "| [none] | | | | | | |")
    lines.append("\n## 7. Domain model\n")
    lines.append(f"### Canonical facts\n\n{bullets(domain.get('canonical_facts', []))}")
    lines.append("\n### Glossary\n")
    lines.append("\n".join(f"- {k}: {v}" for k, v in glossary.items()) or "- [none specified]")
    lines.append(f"\n### Entities\n\n{bullets(domain.get('entities', []))}")
    lines.append(f"\n### Workflows\n\n{bullets(domain.get('workflows', []))}")
    lines.append(f"\n### Open questions\n\n{bullets(domain.get('open_questions', []))}")
    lines.append("\n## 8. Memory and continuity\n")
    lines.append(f"Availability: {memory.get('availability', '[unknown]')}")
    lines.append(f"\n### Remember\n\n{bullets(memory.get('remember', []))}")
    lines.append(f"\n### Do not remember\n\n{bullets(memory.get('do_not_remember', []))}")
    lines.append(f"\n### Scope\n\n{memory.get('scope', '[missing]')}")
    lines.append(f"\n### Fallback\n\n{memory.get('fallback', '[missing]')}")
    lines.append("\n## 9. Operational protocols\n")
    lines.append("The agent starts by identifying scope, relevant evidence, capability availability, risks, and assumptions. It plans when the task is complex, asks only consequential clarifying questions, verifies when capability exists, and reports failures visibly.")
    lines.append("\n## 10. Output contracts\n")
    for key, value in outputs.items():
        lines.append(f"### {key}\n\n{value}")
    lines.append("\n## 11. Evaluation and red-team\n")
    lines.append(f"Acceptance gate: {evaluation.get('acceptance_gate', '[missing]')}")
    lines.append(f"\n### Red-team probes\n\n{bullets(evaluation.get('red_team_probes', []))}")
    lines.append("\n## 12. Compaction survival card\n")
    lines.append("Preserve mission, authority, hard ROE, capability truthfulness, memory policy, output contracts, current state, and known risks.")
    lines.append("\n## 13. Living status\n")
    lines.append(f"Version: {status.get('version', '[missing]')}")
    lines.append(f"Last updated: {status.get('last_updated', '[missing]')}")
    lines.append(f"Owner: {status.get('owner', '[missing]')}")
    lines.append(f"Target platform: {status.get('target_platform', '[missing]')}")
    lines.append(f"Known risks: {', '.join(status.get('known_risks', [])) or '[none]'}")
    lines.append(f"Pending revisions: {', '.join(status.get('pending_revisions', [])) or '[none]'}")
    lines.append(f"Changelog: {status.get('changelog', '[missing]')}")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Markdown constitution from JSON spec.")
    parser.add_argument("spec", help="JSON spec path")
    parser.add_argument("-o", "--output", help="Output Markdown path. Defaults to stdout.")
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    rendered = render(spec)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
