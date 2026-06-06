#!/usr/bin/env python3
"""
Thought Journal Tool — Structured Reasoning & Decision Provenance System

Captures the *reasoning* behind actions, not just the actions themselves.
Answers "why did we make this decision?", "what alternatives were considered?",
and "what actually happened?" — enabling future AI sessions to inherit
accumulated wisdom from prior work.

This tool solves the core "AI amnesia" problem: each new session starts cold
without knowing *why* previous decisions were made. The Thought Journal
creates a durable reasoning provenance trail that survives session boundaries.

Data Model:
  ThoughtEntry  — thoughts, insights, hypotheses, observations, questions
  DecisionEntry — decisions with full rationale, alternatives, constraints,
                  risk assessment, success criteria, and outcome tracking

Storage:
  data/thought_journal.json  — main entry store
  data/journal_index.json    — BM25 inverted index for fast search

BM25 Implementation:
  Self-contained (no circular dependency on memory_interconnect).
  k1=1.5, b=0.75 — standard Okapi BM25 parameters.
"""

import json
import logging
import math
import os
import re
import threading
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Sovereign Data Directory — single source of truth for all persistent state.
# Set SOVEREIGN_DATA_DIR env var to override; falls back to canonical MCP path.
# ---------------------------------------------------------------------------
_SOVEREIGN_DATA_DIR: Path = Path(
    os.environ.get("SOVEREIGN_DATA_DIR", r"/home/daeron/Projects/mcp_server/data")
)

# ---------------------------------------------------------------------------
# Tokenisation (self-contained, mirrors memory_interconnect)
# ---------------------------------------------------------------------------

_STOPWORDS: Set[str] = {
    "a",
    "an",
    "the",
    "this",
    "that",
    "these",
    "those",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "up",
    "about",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "than",
    "too",
    "very",
    "just",
    "now",
    "then",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "both",
    "either",
    "neither",
    "one",
    "two",
    "also",
    "back",
    "well",
    "way",
    "he",
    "she",
    "it",
    "they",
    "we",
    "you",
    "i",
    "me",
    "my",
    "his",
    "her",
    "its",
    "our",
    "your",
    "their",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "must",
    "shall",
    "need",
    "get",
    "got",
    "go",
    "going",
    "gone",
    "make",
    "made",
    "put",
    "say",
    "said",
    "see",
    "set",
    "take",
    "try",
    "use",
    "want",
    "work",
    "know",
    "think",
    "come",
    "look",
    "also",
    "really",
    "actually",
    "basically",
    "simply",
    "maybe",
    "perhaps",
    "return",
    "import",
    "class",
    "self",
    "true",
    "false",
    "none",
    "null",
    "type",
    "value",
    "string",
    "list",
    "dict",
    "object",
    "item",
    "data",
}

_STEM_RULES: List[Tuple[str, str]] = [
    ("ations", ""),
    ("nesses", ""),
    ("ments", ""),
    ("tions", ""),
    ("ation", ""),
    ("ness", ""),
    ("ment", ""),
    ("tion", ""),
    ("ings", ""),
    ("edly", ""),
    ("ably", ""),
    ("ible", ""),
    ("able", ""),
    ("ful", ""),
    ("ous", ""),
    ("ive", ""),
    ("ing", ""),
    ("ess", ""),
    ("est", ""),
    ("ies", "y"),
    ("ied", "y"),
    ("ed", ""),
    ("er", ""),
    ("ly", ""),
    ("es", ""),
    ("s", ""),
]


def _stem(word: str) -> str:
    for suffix, repl in _STEM_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)] + repl
    return word


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    text_lower = str(text).lower()
    raw = re.findall(r"[a-z][a-z0-9_']*", text_lower)
    result = []
    for tok in raw:
        parts = tok.split("_") if "_" in tok else [tok]
        for part in parts:
            part = part.strip("'")
            if len(part) < 3 or part in _STOPWORDS:
                continue
            stemmed = _stem(part)
            if len(stemmed) >= 3 and stemmed not in _STOPWORDS:
                result.append(stemmed)
    return result


# ---------------------------------------------------------------------------
# Minimal BM25 Engine (self-contained)
# ---------------------------------------------------------------------------


class _BM25Index:
    """
    Lightweight in-process BM25 index for journal entries.
    Persisted to journal_index.json.
    """

    K1 = 1.5
    B = 0.75

    def __init__(self) -> None:
        self.doc_term_freq: Dict[str, Dict[str, int]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.doc_frequency: Dict[str, int] = {}
        self.total_docs: int = 0
        self.avg_doc_length: float = 0.0
        self._idf_cache: Dict[str, float] = {}
        self._idf_dirty: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_term_freq": self.doc_term_freq,
            "doc_lengths": self.doc_lengths,
            "doc_frequency": self.doc_frequency,
            "total_docs": self.total_docs,
            "avg_doc_length": self.avg_doc_length,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "_BM25Index":
        idx = cls()
        idx.doc_term_freq = d.get("doc_term_freq", {})
        idx.doc_lengths = d.get("doc_lengths", {})
        idx.doc_frequency = d.get("doc_frequency", {})
        idx.total_docs = d.get("total_docs", 0)
        idx.avg_doc_length = d.get("avg_doc_length", 0.0)
        idx._idf_dirty = True
        return idx

    def add_or_update(self, doc_id: str, text: str) -> None:
        tokens = _tokenize(text)
        old_tf = self.doc_term_freq.get(doc_id, {})

        # Decrement old doc_frequency
        if old_tf:
            self.total_docs = max(self.total_docs - 1, 0)
            for term in old_tf:
                self.doc_frequency[term] = max(self.doc_frequency.get(term, 1) - 1, 0)
                if self.doc_frequency[term] == 0:
                    del self.doc_frequency[term]

        # Compute new TF
        tf: Dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1

        self.doc_term_freq[doc_id] = tf
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1

        for term in tf:
            self.doc_frequency[term] = self.doc_frequency.get(term, 0) + 1

        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)

        self._idf_dirty = True

    def remove(self, doc_id: str) -> None:
        old_tf = self.doc_term_freq.pop(doc_id, {})
        if old_tf:
            self.total_docs = max(self.total_docs - 1, 0)
            for term in old_tf:
                self.doc_frequency[term] = max(self.doc_frequency.get(term, 1) - 1, 0)
                if self.doc_frequency[term] == 0:
                    del self.doc_frequency[term]
        self.doc_lengths.pop(doc_id, None)
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)
        else:
            self.avg_doc_length = 0.0
        self._idf_dirty = True

    def _idf(self, term: str) -> float:
        if self._idf_dirty:
            n = max(self.total_docs, 1)
            self._idf_cache = {
                t: math.log((n - df + 0.5) / (df + 0.5) + 1)
                for t, df in self.doc_frequency.items()
            }
            self._idf_dirty = False
        return self._idf_cache.get(term, 0.0)

    def score(self, doc_id: str, query_tokens: List[str]) -> float:
        doc_tf = self.doc_term_freq.get(doc_id, {})
        if not doc_tf or not query_tokens:
            return 0.0
        doc_len = self.doc_lengths.get(doc_id, 0)
        avgdl = max(self.avg_doc_length, 1.0)
        k1, b = self.K1, self.B
        s = 0.0
        for term in query_tokens:
            tf = doc_tf.get(term, 0)
            if tf == 0:
                continue
            idf_val = self._idf(term)
            num = tf * (k1 + 1)
            den = tf + k1 * (1 - b + b * doc_len / avgdl)
            s += idf_val * (num / den)
        return s

    def search(
        self,
        query: str,
        max_results: int = 10,
        filter_ids: Optional[Set[str]] = None,
    ) -> List[Tuple[str, float]]:
        tokens = _tokenize(query)
        if not tokens:
            return []
        candidates = filter_ids if filter_ids else set(self.doc_term_freq.keys())
        scored = [(doc_id, self.score(doc_id, tokens)) for doc_id in candidates]
        scored = [(d, s) for d, s in scored if s > 0.0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:max_results]


# ---------------------------------------------------------------------------
# Negation word detection for conflict detection
# ---------------------------------------------------------------------------

_NEGATION_PHRASES = {
    "do not",
    "don't",
    "avoid",
    "never",
    "should not",
    "shouldn't",
    "must not",
    "mustn't",
    "cannot",
    "can't",
    "won't",
    "will not",
    "refrain from",
    "stay away",
    "not use",
    "not recommended",
    "instead of",
    "rather than",
    "oppose",
    "reject",
    "refuse",
}


def _has_negation(text: str) -> bool:
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in _NEGATION_PHRASES)


# ---------------------------------------------------------------------------
# ThoughtJournalTool
# ---------------------------------------------------------------------------


class ThoughtJournalTool:
    """
    Structured Reasoning & Decision Provenance System.

    Records the *why* behind decisions and insights, enabling reasoning chains
    to be reconstructed across sessions. Links entries to memory keys and file
    paths for full contextual traceability.
    """

    THOUGHT_TYPES = {"thought", "insight", "hypothesis", "observation", "question"}
    DECISION_STATUSES = {"active", "validated", "invalidated", "superseded"}

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            data_dir = str(_SOVEREIGN_DATA_DIR)

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.journal_file = self.data_dir / "thought_journal.json"
        self.index_file = self.data_dir / "journal_index.json"
        self.reverse_map_file = self.data_dir / "journal_memory_index.json"

        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

        self._bm25 = _BM25Index()
        self._reverse_map: Dict[str, List[str]] = {}  # memory_key → [entry_ids]
        self._load()
        self.logger.info(
            f"ThoughtJournalTool initialised — "
            f"{len(self._journal)} entries, store: {self.journal_file}"
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load journal entries, BM25 index, and reverse map from disk."""
        try:
            if self.journal_file.exists():
                with open(self.journal_file, "r", encoding="utf-8") as f:
                    self._journal: Dict[str, Any] = json.load(f)
            else:
                self._journal = {}

            if self.index_file.exists():
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self._bm25 = _BM25Index.from_dict(json.load(f))
            else:
                # Rebuild index from existing entries
                self._bm25 = _BM25Index()
                for entry_id, entry in self._journal.items():
                    self._bm25.add_or_update(entry_id, self._entry_text(entry))

            # Load or rebuild reverse map (memory_key → [entry_ids])
            if self.reverse_map_file.exists():
                with open(self.reverse_map_file, "r", encoding="utf-8") as f:
                    self._reverse_map = json.load(f)
            else:
                self._rebuild_reverse_map()

        except Exception as e:
            self.logger.error(f"Failed to load journal: {e}. Starting empty.")
            self._journal = {}
            self._bm25 = _BM25Index()
            self._reverse_map = {}

    def _save(self) -> None:
        """Atomically persist journal, BM25 index, and reverse map. Caller must hold _lock."""

        def _atomic(path: Path, obj: Any) -> None:
            serialized = json.dumps(obj, indent=2, ensure_ascii=False)
            last_error: Optional[Exception] = None

            for attempt in range(8):
                tmp = path.with_name(
                    f"{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
                )
                try:
                    with open(tmp, "w", encoding="utf-8") as f:
                        f.write(serialized)
                    os.replace(tmp, path)
                    return
                except Exception as exc:
                    last_error = exc
                    try:
                        if tmp.exists():
                            tmp.unlink()
                    except OSError:
                        pass

                    winerror = getattr(exc, "winerror", None)
                    if isinstance(exc, PermissionError) or winerror in {5, 32}:
                        time.sleep(0.05 * (attempt + 1))
                        continue
                    raise

            if last_error is not None:
                raise last_error

        try:
            _atomic(self.journal_file, self._journal)
            _atomic(self.index_file, self._bm25.to_dict())
            _atomic(self.reverse_map_file, self._reverse_map)
        except Exception as e:
            self.logger.error(f"Failed to save journal: {e}")

    def _rebuild_reverse_map(self) -> None:
        """Reconstruct the memory_key → [entry_ids] reverse map from scratch."""
        self._reverse_map = {}
        for entry_id, entry in self._journal.items():
            for mem_key in entry.get("linked_memories", []):
                self._reverse_map.setdefault(mem_key, [])
                if entry_id not in self._reverse_map[mem_key]:
                    self._reverse_map[mem_key].append(entry_id)

    def _update_reverse_map(self, entry_id: str, linked_memories: List[str]) -> None:
        """Update the reverse map for a single entry. Caller must hold _lock."""
        for mem_key in linked_memories:
            self._reverse_map.setdefault(mem_key, [])
            if entry_id not in self._reverse_map[mem_key]:
                self._reverse_map[mem_key].append(entry_id)

    def _entry_text(self, entry: Dict[str, Any]) -> str:
        """Concatenate all searchable text fields for BM25 indexing."""
        parts = [
            entry.get("content", ""),
            entry.get("context", ""),
            entry.get("decision", ""),
            entry.get("rationale", ""),
            entry.get("risk_assessment", ""),
            entry.get("success_criteria", ""),
            entry.get("outcome", "") or "",
            " ".join(entry.get("alternatives", [])),
            " ".join(entry.get("constraints", [])),
            " ".join(entry.get("tags", [])),
        ]
        return " ".join(p for p in parts if p)

    @staticmethod
    def _short_id() -> str:
        """Generate a short unique ID (8 hex chars)."""
        return uuid.uuid4().hex[:8]

    # ------------------------------------------------------------------
    # Tool 1: Record thought
    # ------------------------------------------------------------------

    def bb7_journal_record_thought(
        self,
        content: str,
        type: str = "thought",
        context: str = "",
        confidence: float = 0.7,
        tags: Optional[List[str]] = None,
        linked_memories: Optional[List[str]] = None,
        linked_files: Optional[List[str]] = None,
    ) -> str:
        """
        Record a thought, insight, hypothesis, observation, or question.

        Args:
            content: The thought/reasoning content.
            type: One of thought|insight|hypothesis|observation|question.
            context: Situational context that prompted this thought.
            confidence: Confidence level 0.0-1.0 (default 0.7).
            tags: Optional classification tags.
            linked_memories: Keys from memory_tool to link to this thought.
            linked_files: File paths relevant to this thought.

        Returns:
            Confirmation string with assigned entry ID.
        """
        if not content or not isinstance(content, str):
            return "Error: 'content' must be a non-empty string."

        type = str(type).strip().lower()
        if type not in self.THOUGHT_TYPES:
            return (
                f"Error: Invalid type '{type}'. "
                f"Choose from: {', '.join(sorted(self.THOUGHT_TYPES))}"
            )

        confidence = round(max(0.0, min(1.0, float(confidence))), 3)
        entry_id = self._short_id()
        now = time.time()

        entry: Dict[str, Any] = {
            "id": entry_id,
            "type": type,
            "content": content.strip(),
            "context": str(context).strip(),
            "confidence": confidence,
            "tags": [str(t).strip() for t in (tags or [])],
            "linked_memories": [str(k) for k in (linked_memories or [])],
            "linked_files": [str(f) for f in (linked_files or [])],
            "linked_entries": [],
            "outcome": None,
            "outcome_validated": None,
            "created": now,
            "updated": now,
        }

        with self._lock:
            self._journal[entry_id] = entry
            self._bm25.add_or_update(entry_id, self._entry_text(entry))
            self._update_reverse_map(entry_id, entry.get("linked_memories", []))
            self._save()

        self.logger.info(f"Journal: recorded {type} [{entry_id}]")

        parts = [
            f"Recorded {type} [id: {entry_id}]",
            f"  Type: {type} | Confidence: {confidence:.0%}",
        ]
        if context:
            parts.append(f"  Context: {context[:120]}")
        if linked_memories:
            parts.append(f"  Linked memories: {', '.join(linked_memories[:5])}")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Tool 2: Capture decision
    # ------------------------------------------------------------------

    def bb7_journal_capture_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: Optional[str] = None,
        constraints: Optional[str] = None,
        risk_assessment: str = "",
        success_criteria: str = "",
        linked_memories: Optional[List[str]] = None,
        linked_files: Optional[List[str]] = None,
    ) -> str:
        """
        Record a decision with full provenance: rationale, alternatives considered,
        constraints, risk assessment, and success criteria.

        Args:
            decision: What was decided.
            rationale: Why this decision was made.
            alternatives: Comma-separated or JSON array of alternatives considered.
            constraints: Comma-separated or JSON array of constraints that shaped this.
            risk_assessment: What could go wrong with this decision.
            success_criteria: How to know if this decision was correct.
            linked_memories: Memory keys relevant to this decision.
            linked_files: File paths relevant to this decision.

        Returns:
            Confirmation string with decision summary and entry ID.
        """
        if not decision or not isinstance(decision, str):
            return "Error: 'decision' must be a non-empty string."
        if not rationale or not isinstance(rationale, str):
            return "Error: 'rationale' must be a non-empty string."

        def _parse_list(val: Optional[str]) -> List[str]:
            if not val:
                return []
            if isinstance(val, list):
                return [str(v).strip() for v in val if str(v).strip()]
            s = str(val).strip()
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(v).strip() for v in parsed if str(v).strip()]
                except json.JSONDecodeError:
                    pass
            return [part.strip() for part in s.split(",") if part.strip()]

        alt_list = _parse_list(alternatives)
        con_list = _parse_list(constraints)
        entry_id = self._short_id()
        now = time.time()

        entry: Dict[str, Any] = {
            "id": entry_id,
            "type": "decision",
            "decision": decision.strip(),
            "rationale": rationale.strip(),
            "alternatives": alt_list,
            "constraints": con_list,
            "risk_assessment": str(risk_assessment).strip(),
            "success_criteria": str(success_criteria).strip(),
            "status": "active",
            "linked_thoughts": [],
            "linked_memories": [str(k) for k in (linked_memories or [])],
            "linked_files": [str(f) for f in (linked_files or [])],
            "outcome": None,
            "superseded_by": None,
            "created": now,
            "updated": now,
        }

        with self._lock:
            self._journal[entry_id] = entry
            self._bm25.add_or_update(entry_id, self._entry_text(entry))
            self._update_reverse_map(entry_id, entry.get("linked_memories", []))
            self._save()

        self.logger.info(f"Journal: captured decision [{entry_id}]: {decision[:60]}")

        parts = [
            f"Decision recorded [id: {entry_id}]",
            f"  Decision: {decision[:120]}",
            f"  Rationale: {rationale[:120]}",
            f"  Alternatives considered: {len(alt_list)}"
            + (f" ({', '.join(alt_list[:3])})" if alt_list else ""),
            f"  Constraints: {len(con_list)}"
            + (f" ({', '.join(con_list[:3])})" if con_list else ""),
        ]
        if risk_assessment:
            parts.append(f"  Risk: {risk_assessment[:100]}")
        if success_criteria:
            parts.append(f"  Success criteria: {success_criteria[:100]}")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Tool 3: Add outcome
    # ------------------------------------------------------------------

    def bb7_journal_add_outcome(
        self,
        entry_id: str,
        outcome: str,
        validated: Optional[bool] = None,
    ) -> str:
        """
        Retrospectively record what happened as a result of a thought or decision.
        For decisions, sets status to 'validated' or 'invalidated'.

        Args:
            entry_id: Journal entry ID (8-char hex from prior record/capture call).
            outcome: Description of what actually happened.
            validated: True=confirmed correct, False=was wrong, None=unknown yet.

        Returns:
            Confirmation with updated status.
        """
        if not entry_id:
            return "Error: 'entry_id' must be a non-empty string."
        if not outcome:
            return "Error: 'outcome' must be a non-empty string."

        with self._lock:
            entry = self._journal.get(str(entry_id).strip())
            if not entry:
                return f"Error: Entry '{entry_id}' not found in journal."

            entry["outcome"] = str(outcome).strip()
            entry["updated"] = time.time()

            if validated is not None:
                entry["outcome_validated"] = bool(validated)
                if entry.get("type") == "decision":
                    entry["status"] = "validated" if validated else "invalidated"

            self._bm25.add_or_update(entry_id, self._entry_text(entry))
            self._save()

        entry_type = entry.get("type", "entry")
        status = entry.get("status", "")
        status_str = f" | Status: {status}" if status else ""
        validated_str = ""
        if validated is not None:
            validated_str = (
                " | Validated: ✓" if validated else " | Validated: ✗ (invalidated)"
            )

        return (
            f"Outcome recorded for {entry_type} [{entry_id}]{status_str}{validated_str}\n"
            f"  Outcome: {outcome[:200]}"
        )

    # ------------------------------------------------------------------
    # Tool 4: Search
    # ------------------------------------------------------------------

    def bb7_journal_search(
        self,
        query: str,
        max_results: int = 5,
        entry_type: Optional[str] = None,
    ) -> str:
        """
        BM25-ranked full-text search across all journal entries.

        Args:
            query: Search query.
            max_results: Maximum results to return (default 5).
            entry_type: Filter by type: thought|insight|hypothesis|observation|question|decision

        Returns:
            Formatted ranked result list.
        """
        if not query:
            return "Error: 'query' must be a non-empty string."

        max_results = max(1, min(int(max_results), 50))

        with self._lock:
            journal_snapshot = dict(self._journal)

        # Optionally restrict to a subset of IDs
        filter_ids: Optional[Set[str]] = None
        if entry_type:
            entry_type = str(entry_type).strip().lower()
            filter_ids = {
                eid
                for eid, e in journal_snapshot.items()
                if e.get("type") == entry_type
            }
            if not filter_ids:
                return f"No journal entries of type '{entry_type}' found."

        with self._lock:
            results = self._bm25.search(
                query, max_results=max_results * 2, filter_ids=filter_ids
            )

        if not results:
            type_note = f" of type '{entry_type}'" if entry_type else ""
            return f"No journal entries{type_note} matching '{query}'."

        lines = [f"Journal search for '{query}' ({len(results)} matches):\n"]
        for i, (eid, score) in enumerate(results[:max_results], 1):
            entry = journal_snapshot.get(eid, {})
            etype = entry.get("type", "unknown")
            snippet = self._entry_snippet(entry)
            created = datetime.fromtimestamp(entry.get("created", 0)).strftime(
                "%Y-%m-%d"
            )
            has_outcome = "✓" if entry.get("outcome") else "○"

            if etype == "decision":
                status = entry.get("status", "active")
                lines.append(
                    f"{i:2d}. [{eid}] decision ({status}) {has_outcome}  "
                    f"score={score:.3f}  {created}"
                )
            else:
                conf = entry.get("confidence", 0.0)
                lines.append(
                    f"{i:2d}. [{eid}] {etype} (conf={conf:.0%}) {has_outcome}  "
                    f"score={score:.3f}  {created}"
                )
            lines.append(f"      {snippet}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool 5: Decision trail
    # ------------------------------------------------------------------

    def bb7_journal_get_decision_trail(
        self,
        topic: str,
        days: int = 90,
    ) -> str:
        """
        Get the chronological decision history for a topic.
        Uses BM25 to find relevant decisions, then orders them by creation time.

        Args:
            topic: Topic or keyword to trace decisions for.
            days: Look-back window in days (default 90).

        Returns:
            Chronological narrative of decisions, status, and outcomes.
        """
        if not topic:
            return "Error: 'topic' must be a non-empty string."

        days = max(1, min(int(days), 3650))
        cutoff = time.time() - (days * 86400)

        with self._lock:
            journal_snapshot = dict(self._journal)

        decision_ids = {
            eid
            for eid, e in journal_snapshot.items()
            if e.get("type") == "decision" and e.get("created", 0) >= cutoff
        }

        if not decision_ids:
            return f"No decisions found in the last {days} days."

        with self._lock:
            results = self._bm25.search(topic, max_results=20, filter_ids=decision_ids)

        if not results:
            return f"No decisions related to '{topic}' found in the last {days} days."

        # Sort chronologically
        decisions = [
            (eid, score, journal_snapshot[eid])
            for eid, score in results
            if eid in journal_snapshot
        ]
        decisions.sort(key=lambda x: x[2].get("created", 0))

        lines = [
            f"Decision Trail for '{topic}' — last {days} days ({len(decisions)} decisions):\n"
        ]
        conflict_flags: List[Tuple[str, str]] = []  # pairs of conflicting decision IDs

        for i, (eid, score, entry) in enumerate(decisions, 1):
            created = datetime.fromtimestamp(entry.get("created", 0)).strftime(
                "%Y-%m-%d %H:%M"
            )
            decision_text = entry.get("decision", "")
            rationale = entry.get("rationale", "")
            status = entry.get("status", "active")
            outcome = entry.get("outcome")
            alternatives = entry.get("alternatives", [])
            success_criteria = entry.get("success_criteria", "")

            status_icon = {
                "active": "○",
                "validated": "✓",
                "invalidated": "✗",
                "superseded": "→",
            }.get(status, "?")

            lines.append(
                f"{i}. [{eid}] {status_icon} {status.upper()}  {created}  (relevance={score:.2f})"
            )
            lines.append(f"   Decision: {decision_text}")
            lines.append(f"   Rationale: {rationale[:150]}")
            if alternatives:
                lines.append(f"   Alternatives: {', '.join(alternatives[:4])}")
            if success_criteria:
                lines.append(f"   Success criteria: {success_criteria[:120]}")
            if outcome:
                lines.append(f"   Outcome: {outcome[:150]}")
            lines.append("")

            # Detect potential conflicts with previous decisions
            for prev_eid, _, prev_entry in decisions[: i - 1]:
                has_neg = _has_negation(decision_text) != _has_negation(
                    prev_entry.get("decision", "")
                )
                if has_neg and score > 0.3:
                    conflict_flags.append((prev_eid, eid))

        if conflict_flags:
            lines.append("POTENTIAL CONFLICTS DETECTED:")
            for id1, id2 in conflict_flags[:3]:
                e1 = journal_snapshot.get(id1, {})
                e2 = journal_snapshot.get(id2, {})
                lines.append(f"  [{id1}] '{e1.get('decision', '')[:60]}...'")
                lines.append(f"  [{id2}] '{e2.get('decision', '')[:60]}...'")
                lines.append("  (Review for contradiction)")
                lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool 6: Surface relevant
    # ------------------------------------------------------------------

    def bb7_journal_surface_relevant(
        self,
        context_text: str,
        max_results: int = 5,
    ) -> str:
        """
        Proactively surface journal entries most relevant to the current context.
        Applies a 1.5× recency boost to entries from the last 7 days.

        Args:
            context_text: Current work context, task description, or code snippet.
            max_results: Max entries to surface (default 5).

        Returns:
            Ranked list of relevant thoughts and decisions.
        """
        if not context_text:
            return "Error: 'context_text' must be a non-empty string."

        max_results = max(1, min(int(max_results), 20))

        with self._lock:
            results = self._bm25.search(context_text, max_results=max_results * 3)
            journal_snapshot = dict(self._journal)

        if not results:
            return "No relevant journal entries found for the given context."

        week_ago = time.time() - 604800

        # Apply recency boost and re-rank
        boosted: List[Tuple[float, str, Dict[str, Any]]] = []
        for eid, score in results:
            entry = journal_snapshot.get(eid, {})
            recency_boost = 1.5 if entry.get("created", 0) >= week_ago else 1.0
            final = score * recency_boost
            boosted.append((final, eid, entry))

        boosted.sort(reverse=True)

        lines = [
            f"Relevant journal entries for current context "
            f"(top {min(max_results, len(boosted))}):\n"
        ]
        for i, (final, eid, entry) in enumerate(boosted[:max_results], 1):
            etype = entry.get("type", "unknown")
            created = datetime.fromtimestamp(entry.get("created", 0)).strftime(
                "%Y-%m-%d"
            )
            snippet = self._entry_snippet(entry)
            recency_note = " [RECENT]" if entry.get("created", 0) >= week_ago else ""

            if etype == "decision":
                status = entry.get("status", "active")
                lines.append(
                    f"{i:2d}. [{eid}] decision ({status}) — score={final:.3f}{recency_note}  {created}"
                )
                lines.append(f"      Decision: {entry.get('decision', '')[:120]}")
            else:
                conf = entry.get("confidence", 0.0)
                lines.append(
                    f"{i:2d}. [{eid}] {etype} (conf={conf:.0%}) — score={final:.3f}{recency_note}  {created}"
                )
                lines.append(f"      {snippet}")

            outcome = entry.get("outcome")
            if outcome:
                lines.append(f"      Outcome: {outcome[:100]}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool 7: Detect conflicts
    # ------------------------------------------------------------------

    def bb7_journal_detect_conflicts(
        self,
        topic: str = "",
    ) -> str:
        """
        Find decisions that may contradict each other on the same topic.

        Uses BM25 similarity + negation word heuristic to identify pairs
        of decisions where one affirms what another denies.

        Args:
            topic: Optional topic to focus conflict detection (empty = scan all decisions).

        Returns:
            Formatted report of detected conflicts.
        """
        with self._lock:
            journal_snapshot = dict(self._journal)

        decisions = {
            eid: e for eid, e in journal_snapshot.items() if e.get("type") == "decision"
        }

        if not decisions:
            return "No decisions in journal — nothing to check for conflicts."

        # If topic given, filter to relevant decisions first
        candidate_ids: List[str]
        if topic.strip():
            with self._lock:
                results = self._bm25.search(
                    topic, max_results=30, filter_ids=set(decisions.keys())
                )
            candidate_ids = [eid for eid, _ in results]
        else:
            candidate_ids = list(decisions.keys())

        if not candidate_ids:
            return f"No decisions related to '{topic}' found."

        conflicts: List[Dict[str, Any]] = []
        checked: Set[Tuple[str, str]] = set()

        for i, id1 in enumerate(candidate_ids):
            e1 = decisions.get(id1, {})
            text1 = e1.get("decision", "") + " " + e1.get("rationale", "")
            tokens1 = _tokenize(text1)
            neg1 = _has_negation(e1.get("decision", ""))

            for id2 in candidate_ids[i + 1 :]:
                pair: Tuple[str, str] = (id1, id2) if id1 <= id2 else (id2, id1)
                if pair in checked:
                    continue
                checked.add(pair)

                e2 = decisions.get(id2, {})
                neg2 = _has_negation(e2.get("decision", ""))

                # BM25 similarity (use one as query against the other)
                with self._lock:
                    score = self._bm25.score(id2, tokens1)
                if score < 0.3:
                    continue

                # Flag as conflict if one affirms and the other negates
                if neg1 != neg2:
                    conflicts.append(
                        {
                            "id1": id1,
                            "id2": id2,
                            "score": score,
                            "decision1": e1.get("decision", "")[:120],
                            "decision2": e2.get("decision", "")[:120],
                            "status1": e1.get("status", "active"),
                            "status2": e2.get("status", "active"),
                        }
                    )

        conflicts.sort(key=lambda x: x["score"], reverse=True)

        if not conflicts:
            scope = f"about '{topic}'" if topic.strip() else "across all decisions"
            return f"No contradicting decisions detected {scope}."

        scope = f"related to '{topic}'" if topic.strip() else "across all decisions"
        lines = [
            f"Conflict Report — {len(conflicts)} potential contradiction(s) {scope}:\n"
        ]
        for i, c in enumerate(conflicts[:10], 1):
            lines.append(
                f"{i}. Similarity={c['score']:.2f}"
                f"  [{c['id1']}] {c['status1'].upper()} vs [{c['id2']}] {c['status2'].upper()}"
            )
            lines.append(f"   A: {c['decision1']}")
            lines.append(f"   B: {c['decision2']}")
            lines.append(
                "   RESOLUTION: Review both decisions — one may need to be "
                "superseded or validated."
            )
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool 8: Generate retrospective
    # ------------------------------------------------------------------

    def bb7_journal_generate_retrospective(
        self,
        days: int = 30,
    ) -> str:
        """
        Synthesise journal entries from the last N days into a retrospective document.

        Sections:
          1. Decisions made (with validation status)
          2. Key insights captured
          3. Hypotheses (validated vs invalidated)
          4. Open questions
          5. Decision quality metrics

        Args:
            days: Look-back window in days (default 30).

        Returns:
            Formatted retrospective document.
        """
        days = max(1, min(int(days), 3650))
        cutoff = time.time() - (days * 86400)

        with self._lock:
            journal_snapshot = dict(self._journal)

        recent = {
            eid: e
            for eid, e in journal_snapshot.items()
            if e.get("created", 0) >= cutoff
        }

        if not recent:
            return f"No journal entries found in the last {days} days."

        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for e in recent.values():
            t = e.get("type", "thought")
            by_type.setdefault(t, []).append(e)

        # Sort each group by creation time
        for t in by_type:
            by_type[t].sort(key=lambda x: x.get("created", 0))

        decisions = by_type.get("decision", [])
        validated_d = [d for d in decisions if d.get("status") == "validated"]
        invalidated_d = [d for d in decisions if d.get("status") == "invalidated"]
        active_d = [d for d in decisions if d.get("status") == "active"]

        # Decision quality score
        decided_with_outcome = [d for d in decisions if d.get("outcome")]
        quality_score: Optional[float] = None
        if decided_with_outcome:
            quality_score = len(validated_d) / len(decided_with_outcome)

        outcome_rate = len([e for e in recent.values() if e.get("outcome")]) / len(
            recent
        )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        start_str = datetime.fromtimestamp(cutoff).strftime("%Y-%m-%d")
        lines = [
            "# Session Retrospective",
            "",
            f"Period: {start_str} — {now_str} ({days} days)",
            f"Total entries: {len(recent)} | Outcome tracking: {outcome_rate:.0%}",
            "",
        ]

        # --- Decisions ---
        if decisions:
            lines.append(f"## Decisions ({len(decisions)} total)")
            lines.append("")
            if validated_d:
                lines.append(f"### Validated ({len(validated_d)})")
                for d in validated_d[:5]:
                    dt = datetime.fromtimestamp(d["created"]).strftime("%m-%d")
                    lines.append(f"- [{d['id']}] {dt} ✓ {d['decision'][:100]}")
                    if d.get("outcome"):
                        lines.append(f"  Outcome: {d['outcome'][:120]}")
                lines.append("")

            if invalidated_d:
                lines.append(
                    f"### Invalidated — Lessons Learned ({len(invalidated_d)})"
                )
                for d in invalidated_d[:5]:
                    dt = datetime.fromtimestamp(d["created"]).strftime("%m-%d")
                    lines.append(f"- [{d['id']}] {dt} ✗ {d['decision'][:100]}")
                    if d.get("outcome"):
                        lines.append(f"  What happened: {d['outcome'][:120]}")
                    if d.get("alternatives"):
                        lines.append(
                            f"  Better alternatives: {', '.join(d['alternatives'][:3])}"
                        )
                lines.append("")

            if active_d:
                lines.append(f"### Still Active ({len(active_d)})")
                for d in active_d[:5]:
                    dt = datetime.fromtimestamp(d["created"]).strftime("%m-%d")
                    lines.append(f"- [{d['id']}] {dt} ○ {d['decision'][:100]}")
                lines.append("")

        # --- Insights ---
        insights = by_type.get("insight", [])
        if insights:
            lines.append(f"## Key Insights ({len(insights)})")
            lines.append("")
            for ins in insights[:8]:
                conf = ins.get("confidence", 0.0)
                dt = datetime.fromtimestamp(ins["created"]).strftime("%m-%d")
                lines.append(
                    f"- [{ins['id']}] {dt} (conf={conf:.0%}) {ins['content'][:150]}"
                )
            lines.append("")

        # --- Hypotheses ---
        hypotheses = by_type.get("hypothesis", [])
        if hypotheses:
            validated_h = [h for h in hypotheses if h.get("outcome_validated") is True]
            invalidated_h = [
                h for h in hypotheses if h.get("outcome_validated") is False
            ]
            open_h = [h for h in hypotheses if h.get("outcome_validated") is None]
            lines.append(f"## Hypotheses ({len(hypotheses)} total)")
            lines.append(
                f"Validated: {len(validated_h)} | "
                f"Invalidated: {len(invalidated_h)} | "
                f"Open: {len(open_h)}"
            )
            lines.append("")
            for h in hypotheses[:5]:
                status_sym = (
                    "✓"
                    if h.get("outcome_validated")
                    else ("✗" if h.get("outcome_validated") is False else "?")
                )
                lines.append(f"- [{h['id']}] {status_sym} {h['content'][:120]}")
            lines.append("")

        # --- Open questions ---
        questions = by_type.get("question", [])
        unanswered = [q for q in questions if not q.get("outcome")]
        if unanswered:
            lines.append(f"## Open Questions ({len(unanswered)})")
            lines.append("")
            for q in unanswered[:5]:
                dt = datetime.fromtimestamp(q["created"]).strftime("%m-%d")
                lines.append(f"- [{q['id']}] {dt} {q['content'][:120]}")
            lines.append("")

        # --- Metrics ---
        lines.append("## Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total entries | {len(recent)} |")
        lines.append(f"| Decisions | {len(decisions)} |")
        lines.append(f"| Insights | {len(insights)} |")
        lines.append(f"| Hypotheses | {len(hypotheses)} |")
        lines.append(f"| Open questions | {len(unanswered)} |")
        lines.append(f"| Outcome tracking rate | {outcome_rate:.0%} |")
        if quality_score is not None:
            lines.append(f"| Decision quality score | {quality_score:.0%} |")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool 9: Get reasoning chain
    # ------------------------------------------------------------------

    def bb7_journal_get_reasoning_chain(
        self,
        decision_id: str,
    ) -> str:
        """
        Reconstruct the reasoning chain that led to a specific decision.

        Follows the decision's linked_thoughts to collect supporting thought
        entries, then sorts them chronologically to show how reasoning evolved.

        Args:
            decision_id: ID of the decision entry to trace.

        Returns:
            Chronological reasoning chain narrative.
        """
        if not decision_id:
            return "Error: 'decision_id' must be a non-empty string."

        with self._lock:
            journal_snapshot = dict(self._journal)

        entry = journal_snapshot.get(str(decision_id).strip())
        if not entry:
            return f"Error: Entry '{decision_id}' not found."
        if entry.get("type") != "decision":
            return (
                f"Error: Entry '{decision_id}' is a {entry.get('type')}, not a decision. "
                f"Use bb7_journal_get_reasoning_chain with a decision ID."
            )

        linked_thought_ids = entry.get("linked_thoughts", [])

        # Also find thoughts that were created before the decision and have high BM25 similarity
        decision_text = entry.get("decision", "") + " " + entry.get("rationale", "")
        thought_ids_in_journal = {
            eid
            for eid, e in journal_snapshot.items()
            if e.get("type") in self.THOUGHT_TYPES
            and e.get("created", float("inf")) <= entry.get("created", 0)
        }

        inferred: List[str] = []
        if thought_ids_in_journal:
            with self._lock:
                bm25_results = self._bm25.search(
                    decision_text, max_results=10, filter_ids=thought_ids_in_journal
                )
            inferred = [
                eid
                for eid, s in bm25_results
                if s > 0.5 and eid not in linked_thought_ids
            ]

        all_thought_ids = list(dict.fromkeys(linked_thought_ids + inferred))

        thoughts = [
            journal_snapshot[tid] for tid in all_thought_ids if tid in journal_snapshot
        ]
        thoughts.sort(key=lambda x: x.get("created", 0))

        decision_date = datetime.fromtimestamp(entry.get("created", 0)).strftime(
            "%Y-%m-%d %H:%M"
        )
        lines = [
            f"Reasoning Chain for Decision [{decision_id}]",
            f"Decision made: {decision_date}",
            "",
            f"DECISION: {entry.get('decision', '')}",
            f"RATIONALE: {entry.get('rationale', '')}",
            "",
        ]

        if thoughts:
            lines.append(f"Supporting reasoning ({len(thoughts)} entries):")
            lines.append("")
            for i, t in enumerate(thoughts, 1):
                dt = datetime.fromtimestamp(t.get("created", 0)).strftime(
                    "%Y-%m-%d %H:%M"
                )
                etype = t.get("type", "thought")
                conf = t.get("confidence", 0.0)
                tag = "[inferred]" if t["id"] in inferred else "[linked]"
                lines.append(f"{i}. [{t['id']}] {etype} (conf={conf:.0%}) {tag}  {dt}")
                lines.append(f"   {t.get('content', '')[:200]}")
                if t.get("context"):
                    lines.append(f"   Context: {t['context'][:100]}")
                lines.append("")
        else:
            lines.append("No supporting reasoning entries found.")
            lines.append(
                "Tip: Record thoughts with bb7_journal_record_thought and link them with linked_entries."
            )

        if entry.get("outcome"):
            lines.append(f"OUTCOME: {entry['outcome']}")
            val = entry.get("outcome_validated")
            if val is True:
                lines.append("RESULT: ✓ Decision validated")
            elif val is False:
                lines.append("RESULT: ✗ Decision invalidated — see outcome above")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool 10: Stats
    # ------------------------------------------------------------------

    def bb7_journal_stats(self) -> str:
        """
        Journal statistics: entry counts, decision quality, outcome rate,
        most common tags, and recent activity summary.
        """
        with self._lock:
            journal_snapshot = dict(self._journal)

        if not journal_snapshot:
            return "Journal is empty — no entries recorded yet."

        n = len(journal_snapshot)
        week_ago = time.time() - 604800

        type_counts: Dict[str, int] = {}
        tags_counter: Counter = Counter()
        with_outcome = 0
        validated_decisions = 0
        invalidated_decisions = 0
        total_decisions = 0
        recent_7d = 0
        confidence_scores: List[float] = []

        for entry in journal_snapshot.values():
            etype = entry.get("type", "unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1
            tags_counter.update(entry.get("tags", []))
            if entry.get("outcome"):
                with_outcome += 1
            if etype == "decision":
                total_decisions += 1
                status = entry.get("status", "active")
                if status == "validated":
                    validated_decisions += 1
                elif status == "invalidated":
                    invalidated_decisions += 1
            if entry.get("created", 0) >= week_ago:
                recent_7d += 1
            if "confidence" in entry:
                confidence_scores.append(entry["confidence"])

        outcome_rate = with_outcome / n
        decided_with_outcomes = validated_decisions + invalidated_decisions
        quality_score: Optional[float] = (
            validated_decisions / decided_with_outcomes
            if decided_with_outcomes > 0
            else None
        )
        avg_conf = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )

        lines = [
            "Thought Journal Statistics",
            "=" * 45,
            f"Total entries          : {n}",
            f"Recent (7 days)     : {recent_7d}",
            f"BM25 indexed docs   : {self._bm25.total_docs}",
            "",
            "Entry Types:",
        ]
        for etype, count in sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {etype:<15s}: {count:4d} ({count / n * 100:.1f}%)")

        lines += [
            "",
            "Decision Metrics:",
            f"  Total decisions     : {total_decisions}",
            f"  Validated           : {validated_decisions}",
            f"  Invalidated         : {invalidated_decisions}",
            f"  Active (no outcome) : {total_decisions - decided_with_outcomes}",
        ]
        if quality_score is not None:
            lines.append(
                f"  Decision quality    : {quality_score:.0%} (validated/total-with-outcome)"
            )

        lines += [
            "",
            "Tracking Metrics:",
            f"  Outcome tracking rate: {outcome_rate:.0%} ({with_outcome}/{n} entries)",
            f"  Avg confidence       : {avg_conf:.0%}",
        ]

        if tags_counter:
            top_tags = tags_counter.most_common(8)
            lines.append("")
            lines.append("Top Tags:")
            for tag, count in top_tags:
                lines.append(f"  #{tag}: {count}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _entry_snippet(self, entry: Dict[str, Any], max_len: int = 120) -> str:
        """Return a short text snippet from the most informative field."""
        for field in ("content", "decision", "rationale"):
            text = entry.get(field, "")
            if text:
                return text[:max_len] + ("..." if len(text) > max_len else "")
        return ""

    # ------------------------------------------------------------------
    # Tool 11: Linked entries (reverse map from memory key)
    # ------------------------------------------------------------------

    def bb7_journal_linked_entries(
        self, memory_key: str, include_content: bool = True
    ) -> str:
        """
        Given a memory key, return all journal entries that linked to it.

        This is the reverse lookup: memory_key → [journal entries].
        Useful for understanding *why* a memory was created or what decisions
        reference it.

        Args:
            memory_key: The memory store key to look up.
            include_content: If True, include entry content previews.

        Returns:
            Formatted string listing linked journal entries.
        """
        memory_key = str(memory_key or "").strip()
        if not memory_key:
            return "Error: 'memory_key' is required."

        with self._lock:
            entry_ids = self._reverse_map.get(memory_key, [])

        if not entry_ids:
            return f"No journal entries linked to memory key '{memory_key}'."

        parts = [f"Journal entries linked to memory '{memory_key}': ({len(entry_ids)} found)\n"]
        for eid in entry_ids:
            with self._lock:
                entry = self._journal.get(eid)
            if not entry:
                parts.append(f"  [{eid}] (entry deleted)")
                continue

            entry_type = entry.get("type", "unknown")
            created = entry.get("created", 0)
            ts_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(created)) if created else "?"

            line = f"  [{eid}] {entry_type} | {ts_str}"

            if include_content:
                content = (
                    entry.get("content", "")
                    or entry.get("decision", "")
                    or ""
                )
                if content:
                    line += f" | {content[:100]}{'...' if len(content) > 100 else ''}"

            parts.append(line)

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # MCP tool registration
    # ------------------------------------------------------------------

    def get_tools(self) -> Dict[str, Any]:
        """Return all MCP tool definitions with bb7_ prefix."""
        return {
            "bb7_journal_record_thought": {
                "function": lambda content, type="thought", context="", confidence=0.7, tags=None, linked_memories=None, linked_files=None: (
                    self.bb7_journal_record_thought(
                        content,
                        type,
                        context,
                        float(confidence),
                        tags or [],
                        linked_memories or [],
                        linked_files or [],
                    )
                ),
                "description": (
                    "Record a thought, insight, hypothesis, observation, or question "
                    "with confidence level and optional links to memories and files. "
                    "Creates durable reasoning provenance for future sessions."
                ),
                "parameters": [
                    {
                        "name": "content",
                        "type": "string",
                        "required": True,
                        "description": "The thought, insight, or reasoning to capture.",
                    },
                    {
                        "name": "type",
                        "type": "string",
                        "required": False,
                        "description": "Entry type: thought|insight|hypothesis|observation|question (default: thought)",
                    },
                    {
                        "name": "context",
                        "type": "string",
                        "required": False,
                        "description": "Situational context that prompted this thought.",
                    },
                    {
                        "name": "confidence",
                        "type": "number",
                        "required": False,
                        "description": "Confidence level 0.0-1.0 (default 0.7).",
                    },
                    {
                        "name": "tags",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                        "description": "Classification tags.",
                    },
                    {
                        "name": "linked_memories",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                        "description": "Memory keys (from bb7_memory_store) to link.",
                    },
                    {
                        "name": "linked_files",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                        "description": "File paths relevant to this thought.",
                    },
                ],
            },
            "bb7_journal_capture_decision": {
                "function": lambda decision, rationale, alternatives=None, constraints=None, risk_assessment="", success_criteria="", linked_memories=None, linked_files=None: (
                    self.bb7_journal_capture_decision(
                        decision,
                        rationale,
                        alternatives,
                        constraints,
                        risk_assessment,
                        success_criteria,
                        linked_memories or [],
                        linked_files or [],
                    )
                ),
                "description": (
                    "Record a decision with full provenance: rationale, alternatives "
                    "considered, constraints, risk assessment, and success criteria. "
                    "This creates an auditable decision trail."
                ),
                "parameters": [
                    {
                        "name": "decision",
                        "type": "string",
                        "required": True,
                        "description": "What was decided.",
                    },
                    {
                        "name": "rationale",
                        "type": "string",
                        "required": True,
                        "description": "Why this decision was made.",
                    },
                    {
                        "name": "alternatives",
                        "type": "string",
                        "required": False,
                        "description": "Comma-separated or JSON array of alternatives considered.",
                    },
                    {
                        "name": "constraints",
                        "type": "string",
                        "required": False,
                        "description": "Comma-separated or JSON array of constraints.",
                    },
                    {
                        "name": "risk_assessment",
                        "type": "string",
                        "required": False,
                        "description": "What could go wrong with this decision.",
                    },
                    {
                        "name": "success_criteria",
                        "type": "string",
                        "required": False,
                        "description": "How to know if this decision was correct.",
                    },
                    {
                        "name": "linked_memories",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                        "description": "Relevant memory keys.",
                    },
                    {
                        "name": "linked_files",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                        "description": "Relevant file paths.",
                    },
                ],
            },
            "bb7_journal_add_outcome": {
                "function": lambda entry_id, outcome, validated=None: (
                    self.bb7_journal_add_outcome(
                        entry_id,
                        outcome,
                        None if validated is None else bool(validated),
                    )
                ),
                "description": (
                    "Retrospectively record what happened as a result of a thought "
                    "or decision. For decisions, validated=true marks as confirmed, "
                    "validated=false marks as invalidated."
                ),
                "parameters": [
                    {
                        "name": "entry_id",
                        "type": "string",
                        "required": True,
                        "description": "8-char entry ID from prior record/capture call.",
                    },
                    {
                        "name": "outcome",
                        "type": "string",
                        "required": True,
                        "description": "What actually happened.",
                    },
                    {
                        "name": "validated",
                        "type": "boolean",
                        "required": False,
                        "description": "true=confirmed correct, false=was wrong, omit=unknown.",
                    },
                ],
            },
            "bb7_journal_search": {
                "function": lambda query, max_results=5, entry_type=None: (
                    self.bb7_journal_search(query, int(max_results), entry_type)
                ),
                "description": "BM25-ranked full-text search across all journal entries.",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "required": True,
                        "description": "Search query.",
                    },
                    {
                        "name": "max_results",
                        "type": "number",
                        "required": False,
                        "description": "Max results (default 5).",
                    },
                    {
                        "name": "entry_type",
                        "type": "string",
                        "required": False,
                        "description": "Filter by type: thought|insight|hypothesis|observation|question|decision",
                    },
                ],
            },
            "bb7_journal_get_decision_trail": {
                "function": lambda topic, days=90: self.bb7_journal_get_decision_trail(
                    topic, int(days)
                ),
                "description": (
                    "Get the chronological decision history for a topic. "
                    "Shows decisions, their rationale, status, and outcomes — "
                    "and flags potential contradictions."
                ),
                "parameters": [
                    {
                        "name": "topic",
                        "type": "string",
                        "required": True,
                        "description": "Topic or keyword to trace decisions for.",
                    },
                    {
                        "name": "days",
                        "type": "number",
                        "required": False,
                        "description": "Look-back window in days (default 90).",
                    },
                ],
            },
            "bb7_journal_surface_relevant": {
                "function": lambda context_text, max_results=5: (
                    self.bb7_journal_surface_relevant(context_text, int(max_results))
                ),
                "description": (
                    "Proactively surface journal entries most relevant to the current "
                    "context. Applies a recency boost to recent entries. "
                    "Use at session start to recover relevant prior reasoning."
                ),
                "parameters": [
                    {
                        "name": "context_text",
                        "type": "string",
                        "required": True,
                        "description": "Current work context or task description.",
                    },
                    {
                        "name": "max_results",
                        "type": "number",
                        "required": False,
                        "description": "Max entries to surface (default 5).",
                    },
                ],
            },
            "bb7_journal_detect_conflicts": {
                "function": lambda topic="": self.bb7_journal_detect_conflicts(
                    str(topic)
                ),
                "description": (
                    "Find decisions that may contradict each other. "
                    "Uses BM25 similarity + negation word detection to identify "
                    "decisions where one affirms what another denies."
                ),
                "parameters": [
                    {
                        "name": "topic",
                        "type": "string",
                        "required": False,
                        "description": "Optional topic to focus detection (empty = scan all decisions).",
                    },
                ],
            },
            "bb7_journal_generate_retrospective": {
                "function": lambda days=30: self.bb7_journal_generate_retrospective(
                    int(days)
                ),
                "description": (
                    "Generate a structured retrospective from the last N days of journal entries. "
                    "Includes decisions made, insights, hypothesis validation, open questions, "
                    "and decision quality metrics."
                ),
                "parameters": [
                    {
                        "name": "days",
                        "type": "number",
                        "required": False,
                        "description": "Look-back window in days (default 30).",
                    },
                ],
            },
            "bb7_journal_get_reasoning_chain": {
                "function": lambda decision_id: self.bb7_journal_get_reasoning_chain(
                    str(decision_id)
                ),
                "description": (
                    "Reconstruct the reasoning chain that led to a specific decision. "
                    "Follows linked thoughts and infers additional supporting entries "
                    "using BM25 similarity."
                ),
                "parameters": [
                    {
                        "name": "decision_id",
                        "type": "string",
                        "required": True,
                        "description": "Decision entry ID (8-char hex).",
                    },
                ],
            },
            "bb7_journal_stats": {
                "function": self.bb7_journal_stats,
                "description": (
                    "Journal statistics: entry counts by type, decision quality score, "
                    "outcome tracking rate, confidence averages, and top tags."
                ),
                "parameters": [],
            },
            "bb7_journal_linked_entries": {
                "function": lambda memory_key, include_content=True: (
                    self.bb7_journal_linked_entries(
                        str(memory_key),
                        bool(include_content) if not isinstance(include_content, str)
                        else include_content.strip().lower() in {"true", "1", "yes"},
                    )
                ),
                "description": (
                    "Reverse lookup: given a memory key, return all journal entries "
                    "that linked to it. Useful for understanding why a memory was "
                    "created or what decisions reference it."
                ),
                "parameters": [
                    {
                        "name": "memory_key",
                        "type": "string",
                        "required": True,
                        "description": "The memory store key to look up.",
                    },
                    {
                        "name": "include_content",
                        "type": "boolean",
                        "required": False,
                        "description": "Include content previews (default true).",
                    },
                ],
            },
        }


# ---------------------------------------------------------------------------
# Standalone smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import tempfile

    logging.basicConfig(level=logging.INFO)

    with tempfile.TemporaryDirectory() as tmp:
        j = ThoughtJournalTool(data_dir=tmp)

        t1 = j.bb7_journal_record_thought(
            "BM25 provides better retrieval than Jaccard for sparse text",
            type="insight",
            confidence=0.9,
        )
        print(t1)

        t2 = j.bb7_journal_record_thought(
            "Ebbinghaus decay curve models human memory retention well",
            type="hypothesis",
            confidence=0.75,
            context="reading memory research",
        )
        print(t2)

        d1 = j.bb7_journal_capture_decision(
            "Use BM25 instead of Jaccard for memory search",
            "BM25 handles term frequency and document length normalisation",
            alternatives="Jaccard similarity, TF-IDF cosine, edit distance",
            constraints="No ML libraries, pure Python 3.8+",
            risk_assessment="BM25 may miss exact substring matches",
            success_criteria="Search precision improves by >20% on test queries",
        )
        print(d1)

        # Extract the decision ID
        decision_id = d1.split("[id: ")[1].split("]")[0]

        print(
            j.bb7_journal_add_outcome(
                decision_id,
                "BM25 retrieval proved superior in all test cases",
                validated=True,
            )
        )
        print(j.bb7_journal_search("BM25 memory retrieval"))
        print(j.bb7_journal_surface_relevant("working on improving search quality"))
        print(j.bb7_journal_generate_retrospective(days=1))
        print(j.bb7_journal_stats())
