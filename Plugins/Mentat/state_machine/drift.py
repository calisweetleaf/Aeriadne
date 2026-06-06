"""Scope-drift detector.

Reads ${CLAUDE_PROJECT_DIR}/.mentat/scope.md, which the user maintains by hand
or via the mentat:plan skill. Each scope file declares an inclusion lane and an
exclusion lane:

    # Scope
    ## In
    - UI/CSS porting
    - design tokens
    ## Out (deferred — DO NOT re-inject)
    - inference / model loading
    - safetensors backends
    - hardware constraints
    - AI/ML pipelines

The detector tokenizes the prompt and tool inputs against the deferred-topic
phrase list. A hit emits an InsightType.SCOPE_DRIFT and trips the state machine
into DRIFTING. The user gets a visible warning via the hook's stderr → fed back
to Claude as a deny-with-reason on PreToolUse, and as an acknowledgment-required
banner on UserPromptSubmit.

The phrase list supports multi-word phrases and case-insensitive matching.
False-positive rate matters — we only fire on full-phrase hits, never on
sub-tokens of a longer term.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DriftHit:
    topic: str
    matched_phrase: str
    snippet: str


def parse_scope(scope_path: Path) -> tuple[list[str], list[str]]:
    """Parse a scope.md, returning (in_topics, out_topics) lists."""
    if not scope_path.exists():
        return [], []
    text = scope_path.read_text(encoding="utf-8")
    in_topics: list[str] = []
    out_topics: list[str] = []
    bucket: Optional[list[str]] = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("## in"):
            bucket = in_topics
            continue
        if low.startswith("## out"):
            bucket = out_topics
            continue
        if line.startswith("#"):
            bucket = None
            continue
        if bucket is None:
            continue
        # Bullets like "- topic" or "* topic" → topic
        m = re.match(r"^[-*]\s+(.*)$", line)
        if m:
            bucket.append(m.group(1).strip().lower())
    return in_topics, out_topics


def detect_drift(text: str, deferred_topics: list[str]) -> Optional[DriftHit]:
    if not deferred_topics or not text:
        return None
    low = text.lower()
    for topic in deferred_topics:
        # Match the longest phrase from the topic line. Topic can be a comma-list.
        for phrase in (p.strip() for p in topic.split(",") if p.strip()):
            if not phrase:
                continue
            if re.search(rf"\b{re.escape(phrase)}\b", low):
                # Snippet: 60 chars centered on hit
                idx = low.find(phrase)
                start = max(0, idx - 30)
                end = min(len(low), idx + len(phrase) + 30)
                return DriftHit(topic=topic, matched_phrase=phrase, snippet=text[start:end])
    return None
