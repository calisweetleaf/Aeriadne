#!/usr/bin/env python3
"""Shared helpers for the Constitutional Prompt Framework scripts.

Standard library only. These checks are heuristic and intended to support review,
not replace expert judgment.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
REFERENCE_RE = re.compile(r"`((?:references|assets|scripts|tests|examples|agents)/[^`]+)`")
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
]

REQUIRED_CONSTITUTION_TERMS = {
    "mission_identity": ["identity", "mission"],
    "authority_governance": ["authority", "governance", "approval"],
    "rules_of_engagement": ["rules of engagement", "roe", "violation surface", "recovery"],
    "operating_doctrine": ["operating doctrine", "principle", "failure mode"],
    "persona": ["persona", "voice", "posture"],
    "capability": ["capability", "trigger", "fallback", "verification"],
    "memory": ["memory", "continuity", "remember"],
    "output_contracts": ["output", "contract", "format"],
    "evaluation": ["evaluation", "red-team", "score", "acceptance"],
    "living_status": ["living status", "version", "last updated"],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end():]
    data: Dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        data[key.strip()] = value
    return data, body


def find_references(text: str) -> List[str]:
    refs = []
    for match in REFERENCE_RE.finditer(text):
        ref = match.group(1).strip()
        if ref not in refs:
            refs.append(ref)
    return refs


def scan_for_secret_patterns(root: Path) -> List[str]:
    findings: List[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".zip", ".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(root).as_posix()
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(rel)
                break
    return findings


def term_present(text_l: str, terms: Iterable[str]) -> bool:
    return any(term.lower() in text_l for term in terms)


def constitution_heuristics(text: str) -> Dict[str, object]:
    text_l = text.lower()
    checks = {name: term_present(text_l, terms) for name, terms in REQUIRED_CONSTITUTION_TERMS.items()}
    roe_count = len(re.findall(r"(?im)^#{2,4}\s*(?:roe\b|.*rules? of engagement|.*\bROE\b)", text))
    tetrad_signals = sum(1 for term in ["principle:", "rationale:", "failure mode:", "required behavior:"] if term in text_l)
    approval_signals = len(re.findall(r"(?i)approval|approve|explicit approval", text))
    false_capability_signals = len(re.findall(r"(?i)actually ran|actually done|do not claim|truthful|unavailable|fallback", text))
    headings = len(re.findall(r"(?m)^#{1,4}\s+", text))
    word_count = len(re.findall(r"\b\w+\b", text))
    return {
        "checks": checks,
        "roe_heading_count": roe_count,
        "tetrad_signal_count": tetrad_signals,
        "approval_signal_count": approval_signals,
        "capability_truthfulness_signal_count": false_capability_signals,
        "heading_count": headings,
        "word_count": word_count,
    }


def score_constitution(text: str) -> Dict[str, object]:
    h = constitution_heuristics(text)
    checks = h["checks"]
    category_scores: Dict[str, int] = {}
    mapping = {
        "Mission and identity": "mission_identity",
        "Authority and governance": "authority_governance",
        "Rules of engagement": "rules_of_engagement",
        "Operating doctrine": "operating_doctrine",
        "Persona architecture": "persona",
        "Capability dispatch": "capability",
        "Memory and continuity": "memory",
        "Output contracts": "output_contracts",
        "Evaluation and maintenance": "evaluation",
        "Living status": "living_status",
    }
    for label, key in mapping.items():
        category_scores[label] = 8 if checks.get(key) else 2

    text_l = text.lower()
    if h["tetrad_signal_count"] >= 4:
        category_scores["Operating doctrine"] = min(10, category_scores["Operating doctrine"] + 2)
    if h["approval_signal_count"] >= 3:
        category_scores["Authority and governance"] = min(10, category_scores["Authority and governance"] + 1)
        category_scores["Rules of engagement"] = min(10, category_scores["Rules of engagement"] + 1)
    if "violation surface" in text_l and "recovery" in text_l:
        category_scores["Rules of engagement"] = min(10, category_scores["Rules of engagement"] + 1)
    if "fallback" in text_l and "verification" in text_l:
        category_scores["Capability dispatch"] = min(10, category_scores["Capability dispatch"] + 1)
    if "update-vs-create" in text_l or "update vs create" in text_l:
        category_scores["Memory and continuity"] = min(10, category_scores["Memory and continuity"] + 1)
    if "red-team" in text_l and "acceptance" in text_l:
        category_scores["Evaluation and maintenance"] = min(10, category_scores["Evaluation and maintenance"] + 1)

    total = sum(category_scores.values())
    caps: List[str] = []
    if not checks.get("authority_governance"):
        caps.append("No authority model: cap 70")
        total = min(total, 70)
    if "memory" in text_l and "fallback" not in text_l and "unavailable" not in text_l:
        caps.append("Memory mentioned without fallback: cap 80")
        total = min(total, 80)
    if "delete" in text_l and "approval" not in text_l:
        caps.append("Destructive action mentioned without approval: cap 70")
        total = min(total, 70)
    if "tool" in text_l and "fallback" not in text_l:
        caps.append("Capabilities mentioned without fallback: cap 80")
        total = min(total, 80)

    readiness = "fragile prompt"
    if total >= 90:
        readiness = "production ready"
    elif total >= 75:
        readiness = "production candidate"
    elif total >= 60:
        readiness = "hardened draft"
    elif total >= 40:
        readiness = "prototype"

    return {"total": total, "readiness": readiness, "category_scores": category_scores, "mandatory_caps": caps, "heuristics": h}


def load_json_compatible_yaml(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def print_json(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))
