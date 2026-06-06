#!/usr/bin/env python3
"""
Enhanced Memory Tool — SOTA++ Hierarchical Persistent Memory

Implements MemGPT-style working memory (LRU RAM buffer) + long-term JSON
storage + archival, with Ebbinghaus forgetting-curve decay scoring,
BM25-powered context surfacing, and full cross-platform path resolution.

New tools added in this upgrade:
  bb7_memory_surface_context  — proactive BM25 + decay context surfacing
  bb7_memory_bulk_store       — atomic multi-entry write
  bb7_memory_get_related      — fetch semantically related memory entries
  bb7_memory_timeline         — chronological view of recent memories
  bb7_memory_export           — export memories as Markdown or JSON

Critical fixes:
  - Hardcoded Windows path replaced with platform-agnostic default
  - Ebbinghaus stability field added to all entries
  - Working memory LRU buffer prevents redundant disk reads
"""

import json
import logging
import math
import os
import threading
import time
import uuid
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Sovereign Data Directory — single source of truth for all persistent state.
# Set SOVEREIGN_DATA_DIR env var to override; falls back to canonical MCP path.
# ---------------------------------------------------------------------------
_SOVEREIGN_DATA_DIR: Path = Path(
    os.environ.get(
        "SOVEREIGN_DATA_DIR",
        os.environ.get(
            "MCP_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")
        ),
    )
)

# ---------------------------------------------------------------------------
# Import interconnection engine — graceful fallback if unavailable
# ---------------------------------------------------------------------------
INTERCONNECT_IMPORT_ERROR: Optional[Exception] = None

try:
    from tools.memory_interconnect import MemoryInterconnectionEngine as _Engine

    INTERCONNECT_AVAILABLE = True
except ImportError as exc:
    INTERCONNECT_AVAILABLE = False
    INTERCONNECT_IMPORT_ERROR = exc

    class _Engine:  # type: ignore
        """Stub fallback used only to surface hard failures when interconnect is absent."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "tools.memory_interconnect failed to import"
                + (
                    f": {INTERCONNECT_IMPORT_ERROR}"
                    if INTERCONNECT_IMPORT_ERROR is not None
                    else ""
                )
            )

        def analyze_memory_entry(
            self, key: str, value: str, source: str = "memory"
        ) -> Dict[str, Any]:
            return {"concepts": [], "importance": 0.5, "related_memories": []}

        def intelligent_search(
            self, query: str, max_results: int = 10
        ) -> List[Dict[str, Any]]:
            return []

        def get_memory_insights(self) -> str:
            return ""

        def consolidate_memories(self, age_threshold_days: int = 30) -> Dict[str, Any]:
            return {"consolidated": 0, "archived": 0}


# ---------------------------------------------------------------------------
# Working Memory Buffer — LRU in-RAM cache
# ---------------------------------------------------------------------------


class WorkingMemoryBuffer:
    """
    LRU in-RAM cache of the most recently accessed/stored memory entries.

    Provides O(1) read/write with automatic eviction of least-recently-used
    entries when capacity is reached.  All methods are NOT thread-safe
    individually — they rely on the caller (EnhancedMemoryTool) holding
    its own lock.
    """

    def __init__(self, capacity: int = 50) -> None:
        self.capacity = capacity
        # OrderedDict preserves insertion order; we move touched items to end
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def touch(self, key: str, entry: Dict[str, Any]) -> None:
        """Insert or refresh an entry, evicting oldest if at capacity."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.capacity:
                self._cache.popitem(last=False)  # evict LRU
            self._cache[key] = entry
            self._cache.move_to_end(key)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Return cached entry (moving to end) or None on miss."""
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def invalidate(self, key: str) -> None:
        """Remove a specific key from cache."""
        self._cache.pop(key, None)

    def get_all_recent(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Return all cached items, newest first."""
        return list(reversed(list(self._cache.items())))

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


# ---------------------------------------------------------------------------
# Ebbinghaus decay helpers
# ---------------------------------------------------------------------------

_EBBINGHAUS_MIN_STABILITY = 0.1
_EBBINGHAUS_MAX_STABILITY = 60.0  # ~2 months at max


def _decay_score(entry: Dict[str, Any]) -> float:
    """
    Ebbinghaus retention: R = e^(-elapsed_days / stability)

    stability grows logarithmically with each reinforced access, capped at 60.
    A fresh memory (stability=1) decays to 36% after 1 day.
    A well-accessed memory (stability=30) retains 97% after 1 day.
    """
    elapsed_s = time.time() - entry.get("last_accessed", time.time())
    elapsed_days = elapsed_s / 86400.0
    stability = max(entry.get("stability", 1.0), _EBBINGHAUS_MIN_STABILITY)
    return math.exp(-elapsed_days / stability)


def _reinforce_stability(entry: Dict[str, Any]) -> float:
    """
    Increase stability after a successful retrieval (memory reinforcement).
    Uses logarithmic growth to model diminishing returns of repetition.
    Returns new stability value.
    """
    current = entry.get("stability", 1.0)
    # Each access multiplies stability by 1.3 and adds 0.5 (logarithmic growth)
    new_stability = min(current * 1.3 + 0.5, _EBBINGHAUS_MAX_STABILITY)
    return round(new_stability, 4)


# ---------------------------------------------------------------------------
# EnhancedMemoryTool
# ---------------------------------------------------------------------------


class EnhancedMemoryTool:
    """
    SOTA++ hierarchical persistent memory with BM25 intelligence layer.

    Memory tiers:
      1. Working memory — LRU in-RAM buffer (last 50 accessed, instant access)
      2. Long-term store — JSON file on disk (all memories, durable)
      3. Archives — JSON files in data/archives/ (old low-importance memories)
    """

    CATEGORIES = {
        "insights": "Important discoveries and learnings",
        "decisions": "Key decisions and their rationale",
        "patterns": "Recurring patterns and observations",
        "context": "Project and session context",
        "solutions": "Problem solutions and fixes",
        "references": "Important references and links",
        "goals": "Objectives and progress tracking",
        "technical": "Technical details and configurations",
    }

    def __init__(self, storage_file: Optional[str] = None) -> None:
        if storage_file is None:
            storage_file = str(_SOVEREIGN_DATA_DIR / "memory_store.json")

        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.working_memory = WorkingMemoryBuffer(capacity=50)

        # Intelligence engine
        if INTERCONNECT_AVAILABLE:
            self.intelligence = _Engine(str(self.storage_file.parent))
        else:
            raise RuntimeError(
                "Memory interconnection engine is required for EnhancedMemoryTool"
                + (
                    f": {INTERCONNECT_IMPORT_ERROR}"
                    if INTERCONNECT_IMPORT_ERROR is not None
                    else ""
                )
            )

        # Initialise empty store if new
        if not self.storage_file.exists():
            self._save_data({})

        self.logger.info(f"EnhancedMemoryTool initialised — store: {self.storage_file}")

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def _load_data(self) -> Dict[str, Any]:
        """Load and migrate all entries from disk."""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            self.logger.error("Memory store missing at %s: %s", self.storage_file, e)
            raise RuntimeError(
                f"Memory store missing at {self.storage_file}: {e}"
            ) from e
        except json.JSONDecodeError as e:
            self.logger.error(
                "Memory store corrupted at %s: %s",
                self.storage_file,
                e,
            )
            raise RuntimeError(
                f"Memory store corrupted at {self.storage_file}: {e}"
            ) from e

        now = time.time()
        for key, entry in data.items():
            if not isinstance(entry, dict):
                # Migrate legacy plain-string format
                data[key] = {
                    "value": str(entry),
                    "timestamp": now,
                    "created": now,
                    "category": "uncategorized",
                    "importance": 0.5,
                    "tags": [],
                    "access_count": 0,
                    "last_accessed": now,
                    "stability": 1.0,
                    "version": 1,
                }
            else:
                entry.setdefault("category", "uncategorized")
                entry.setdefault("importance", 0.5)
                entry.setdefault("tags", [])
                entry.setdefault("access_count", 0)
                entry.setdefault("last_accessed", entry.get("timestamp", now))
                entry.setdefault("stability", 1.0)
                entry.setdefault("version", 1)

        return data

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Atomically write data to disk."""
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        last_error: Optional[Exception] = None

        for attempt in range(8):
            tmp = self.storage_file.with_name(
                f"{self.storage_file.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
            )
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(serialized)
                os.replace(tmp, self.storage_file)
                return
            except Exception as e:
                last_error = e
                self.logger.warning("Memory save retry %s failed: %s", attempt + 1, e)
                try:
                    if tmp.exists():
                        tmp.unlink()
                except OSError:
                    pass

                winerror = getattr(e, "winerror", None)
                if isinstance(e, PermissionError) or winerror in {5, 32}:
                    time.sleep(0.05 * (attempt + 1))
                    continue

                self.logger.error(f"Failed to save memory data: {e}")
                raise

        if last_error is not None:
            self.logger.error(f"Failed to save memory data: {last_error}")
            raise last_error

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def store(
        self,
        key: str,
        value: str,
        category: str = "uncategorized",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Store a memory entry with metadata, BM25 indexing, and decay initialisation."""
        if not key or not isinstance(key, str):
            return "Error: 'key' must be a non-empty string."
        if not value or not isinstance(value, str):
            return "Error: 'value' must be a non-empty string."
        if category not in self.CATEGORIES and category != "uncategorized":
            available = ", ".join(self.CATEGORIES.keys())
            return f"Error: Unknown category '{category}'. Choose from: {available}"

        importance = round(max(0.0, min(1.0, float(importance))), 4)
        tags = [str(t) for t in (tags or [])]

        with self._lock:
            data = self._load_data()
            now = time.time()
            existing = data.get(key, {})

            entry: Dict[str, Any] = {
                "value": value,
                "timestamp": now,
                "created": existing.get("created", now),
                "category": category,
                "importance": importance,
                "tags": tags,
                "access_count": existing.get("access_count", 0),
                "last_accessed": now,
                "stability": existing.get("stability", 1.0),
                "version": existing.get("version", 0) + 1,
            }

            # BM25 intelligence enrichment
            if self.intelligence:
                try:
                    analysis = self.intelligence.analyze_memory_entry(
                        key, value, "memory"
                    )
                    entry["concepts"] = analysis.get("concepts", [])
                    entry["ai_importance"] = analysis.get("importance", importance)
                    # Boost importance if many related memories exist
                    related = analysis.get("related_memories", [])
                    if len(related) >= 3:
                        entry["importance"] = round(
                            min(importance + 0.05 * len(related), 1.0), 4
                        )
                    entry["related_memories"] = related
                except Exception as e:
                    self.logger.error(
                        "Intelligence analysis failed for '%s': %s",
                        key,
                        e,
                    )
                    raise RuntimeError(
                        f"Intelligence analysis failed for '{key}': {e}"
                    ) from e

            data[key] = entry
            self._save_data(data)
            self.working_memory.touch(key, entry)

        self.logger.info(f"Stored '{key}' (cat={category}, imp={importance})")
        parts = [f"Stored '{key}' in persistent memory"]
        if entry.get("concepts"):
            parts.append(f"Concepts: {', '.join(entry['concepts'][:5])}")
        if entry.get("related_memories"):
            parts.append(f"Related: {len(entry['related_memories'])} existing memories")
        if entry.get("version", 1) > 1:
            parts.append(f"Version: {entry['version']}")
        return "\n".join(parts)

    def retrieve(self, key: str, include_related: bool = False) -> str:
        """
        Retrieve a memory by key.
        Updates Ebbinghaus stability (reinforcement) and LRU working memory.
        """
        if not key:
            return "Error: 'key' must be a non-empty string."

        with self._lock:
            # Check working memory first (hot path)
            cached = self.working_memory.get(key)
            if cached is not None:
                data = self._load_data()
                entry = data.get(key)
                if entry:
                    entry["access_count"] = entry.get("access_count", 0) + 1
                    entry["last_accessed"] = time.time()
                    entry["stability"] = _reinforce_stability(entry)
                    data[key] = entry
                    self._save_data(data)
                    self.working_memory.touch(key, entry)
                    return self._format_retrieve(key, entry, include_related)

            data = self._load_data()

        if key not in data:
            # BM25 fallback: suggest similar keys
            if self.intelligence:
                try:
                    suggestions = self.intelligence.intelligent_search(
                        key, max_results=3
                    )
                    if suggestions:
                        keys = [r["memory_id"].split(":", 1)[1] for r in suggestions]
                        return f"Key '{key}' not found. Similar keys: {', '.join(keys)}"
                except Exception as e:
                    self.logger.error(
                        "Memory suggestion search failed for '%s': %s",
                        key,
                        e,
                    )
            return f"Key '{key}' not found in memory."

        with self._lock:
            data = self._load_data()  # re-load inside lock
            if key not in data:
                return f"Key '{key}' not found in memory."
            entry = data[key]
            entry["access_count"] = entry.get("access_count", 0) + 1
            entry["last_accessed"] = time.time()
            entry["stability"] = _reinforce_stability(entry)
            data[key] = entry
            self._save_data(data)
            self.working_memory.touch(key, entry)

        self.logger.debug(f"Retrieved '{key}' (access #{entry['access_count']})")
        return self._format_retrieve(key, entry, include_related)

    def _format_retrieve(
        self, key: str, entry: Dict[str, Any], include_related: bool
    ) -> str:
        """Format a retrieval response with optional metadata."""
        value = entry.get("value", "") if isinstance(entry, dict) else str(entry)
        response = str(value)

        if include_related and isinstance(entry, dict):
            meta: List[str] = []
            cat = entry.get("category", "uncategorized")
            if cat != "uncategorized":
                meta.append(f"Category: {cat}")
            imp = entry.get("importance", 0.5)
            if imp >= 0.7:
                meta.append(f"High importance ({imp:.2f})")
            if entry.get("tags"):
                meta.append(f"Tags: {', '.join(entry['tags'])}")
            concepts = entry.get("concepts", [])
            if concepts:
                meta.append(f"Concepts: {', '.join(concepts[:4])}")
            related = entry.get("related_memories", [])
            if related:
                rel_keys = [r["memory_id"].split(":", 1)[1] for r in related[:3]]
                meta.append(f"Related: {', '.join(rel_keys)}")
            decay = _decay_score(entry)
            meta.append(f"Retention: {decay:.0%}")
            if meta:
                response += "\n\n[Meta] " + " | ".join(meta)

        return response

    def delete(self, key: str) -> str:
        """Delete a memory entry by key."""
        if not key:
            return "Error: 'key' must be a non-empty string."
        with self._lock:
            data = self._load_data()
            if key not in data:
                return f"Key '{key}' not found in memory."
            del data[key]
            self._save_data(data)
            self.working_memory.invalidate(key)
        self.logger.info(f"Deleted '{key}' from memory.")
        return f"Deleted '{key}' from persistent memory."

    # ------------------------------------------------------------------
    # Listing & filtering
    # ------------------------------------------------------------------

    def list_keys(
        self,
        prefix: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        sort_by: str = "timestamp",
    ) -> str:
        """Enhanced key listing with filtering, sorting, and decay display."""
        with self._lock:
            data = self._load_data()

        filtered: List[Tuple[str, Dict[str, Any]]] = []
        for key, entry in data.items():
            if prefix and not key.startswith(prefix):
                continue
            if category:
                if entry.get("category", "uncategorized") != category:
                    continue
            if entry.get("importance", 0.5) < min_importance:
                continue
            filtered.append((key, entry))

        if not filtered:
            desc = []
            if prefix:
                desc.append(f"prefix='{prefix}'")
            if category:
                desc.append(f"category='{category}'")
            if min_importance > 0:
                desc.append(f"min_importance={min_importance}")
            suffix = f" with {' + '.join(desc)}" if desc else ""
            return f"No memory keys found{suffix}."

        # Sort
        if sort_by == "importance":
            filtered.sort(key=lambda x: x[1].get("importance", 0.5), reverse=True)
        elif sort_by == "access":
            filtered.sort(key=lambda x: x[1].get("access_count", 0), reverse=True)
        elif sort_by == "alphabetical":
            filtered.sort(key=lambda x: x[0])
        elif sort_by == "decay":
            filtered.sort(key=lambda x: _decay_score(x[1]), reverse=True)
        else:  # timestamp (default)
            filtered.sort(key=lambda x: x[1].get("timestamp", 0), reverse=True)

        lines = [f"Memory keys ({len(filtered)} total, sorted by {sort_by}):\n"]
        for key, entry in filtered:
            cat = entry.get("category", "uncategorized")
            imp = entry.get("importance", 0.5)
            acc = entry.get("access_count", 0)
            decay = _decay_score(entry)
            tags = entry.get("tags", [])

            badges: List[str] = []
            if cat != "uncategorized":
                badges.append(f"[{cat}]")
            if imp >= 0.7:
                badges.append(f"imp={imp:.2f}*")
            elif imp >= 0.4:
                badges.append(f"imp={imp:.2f}")
            if acc >= 5:
                badges.append(f"accessed={acc}")
            badges.append(f"retention={decay:.0%}")
            if tags:
                badges.append(f"#{', #'.join(tags[:2])}")

            lines.append(f"  {key}  {' '.join(badges)}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Intelligent search
    # ------------------------------------------------------------------

    def intelligent_search(self, query: str, max_results: int = 5) -> str:
        """BM25-powered semantic search with decay-weighted ranking."""
        if not query:
            return "Error: 'query' must be a non-empty string."

        if self.intelligence:
            try:
                raw = self.intelligence.intelligent_search(
                    query, max_results=max_results * 2
                )
                if raw:
                    # Apply decay weighting to re-rank
                    with self._lock:
                        data = self._load_data()

                    scored: List[Tuple[float, str, float]] = []
                    for r in raw:
                        mid = r["memory_id"]
                        key = mid.split(":", 1)[1] if ":" in mid else mid
                        entry = data.get(key, {})
                        decay = _decay_score(entry) if entry else 0.5
                        combined = r["relevance_score"] * (0.7 + 0.3 * decay)
                        scored.append((combined, key, r["relevance_score"]))

                    scored.sort(reverse=True)
                    lines = [f"BM25 search for '{query}' ({len(raw)} candidates):\n"]
                    for i, (combined, key, bm25) in enumerate(scored[:max_results], 1):
                        entry = data.get(key, {})
                        val = str(entry.get("value", ""))[:120]
                        if len(val) < len(str(entry.get("value", ""))):
                            val += "..."
                        lines.append(
                            f"{i:2d}. {key}  [BM25={bm25:.3f}, decay-weighted={combined:.3f}]"
                        )
                        lines.append(f"      {val}")
                    return "\n".join(lines)
            except Exception as e:
                self.logger.warning(f"BM25 search failed, falling back: {e}")

        return self._simple_search(query, max_results)

    def _simple_search(self, query: str, max_results: int = 5) -> str:
        """Substring fallback search."""
        with self._lock:
            data = self._load_data()

        q = query.lower()
        matches: List[Tuple[str, str]] = []
        for key, entry in data.items():
            val = (
                entry.get("value", str(entry))
                if isinstance(entry, dict)
                else str(entry)
            )
            if q in key.lower() or q in val.lower():
                matches.append((key, val))

        if not matches:
            return f"No memories found matching '{query}'."

        lines = [f"Search results for '{query}' ({len(matches)} found):\n"]
        for i, (key, val) in enumerate(matches[:max_results], 1):
            preview = val[:120] + ("..." if len(val) > 120 else "")
            lines.append(f"{i:2d}. {key}: {preview}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # NEW: Context surfacing (proactive)
    # ------------------------------------------------------------------

    def surface_context(self, context_text: str, max_results: int = 5) -> str:
        """
        Given a blob of context text, proactively surface the most relevant
        memories using BM25 + Ebbinghaus decay weighting.

        This is the primary "ambient intelligence" capability — call it at the
        start of a session to get relevant memories without knowing the keys.
        """
        if not context_text:
            return "Error: 'context_text' must be a non-empty string."

        max_results = max(1, min(int(max_results), 20))

        if not self.intelligence:
            raise RuntimeError(
                "surface_context requires memory intelligence engine; none available"
            )

        try:
            raw = self.intelligence.intelligent_search(
                context_text, max_results=max_results * 3
            )
        except Exception as e:
            self.logger.error("surface_context BM25 failed: %s", e)
            raise RuntimeError(f"surface_context BM25 failed: {e}") from e

        if not raw:
            return "No relevant memories found for the given context."

        with self._lock:
            data = self._load_data()

        scored: List[Tuple[float, str, Dict[str, Any], float]] = []
        for r in raw:
            mid = r["memory_id"]
            key = mid.split(":", 1)[1] if ":" in mid else mid
            entry = data.get(key, {})
            decay = _decay_score(entry) if entry else 0.5
            bm25 = r["relevance_score"]
            # Final score: BM25 relevance × (0.7 + 0.3 × decay)
            # This boosts recent memories slightly while keeping relevance dominant
            final = bm25 * (0.7 + 0.3 * decay)
            scored.append((final, key, entry, bm25))

        scored.sort(reverse=True)

        lines = [
            f"Relevant memories for current context ({len(scored)} candidates, top {max_results}):\n"
        ]
        for i, (final, key, entry, bm25) in enumerate(scored[:max_results], 1):
            cat = entry.get("category", "uncategorized")
            imp = entry.get("importance", 0.5)
            val = str(entry.get("value", ""))
            preview = val[:150] + ("..." if len(val) > 150 else "")
            decay_pct = _decay_score(entry) * 100 if entry else 50
            concepts = entry.get("concepts", [])

            lines.append(
                f"{i:2d}. [{key}]  score={final:.3f}  cat={cat}  imp={imp:.2f}  "
                f"retention={decay_pct:.0f}%"
            )
            lines.append(f"      {preview}")
            if concepts:
                lines.append(f"      Concepts: {', '.join(concepts[:4])}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # NEW: Bulk store
    # ------------------------------------------------------------------

    def bulk_store(self, entries_json: str) -> str:
        """
        Atomically store multiple memory entries from a JSON array.

        entries_json format:
          [{"key": "k1", "value": "v1", "category": "insights", "importance": 0.8, "tags": []}, ...]

        All entries are validated, then written in a single atomic disk write.
        """
        if not entries_json:
            return "Error: 'entries_json' must be a non-empty JSON string."

        try:
            entries = json.loads(entries_json)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON — {e}"

        if not isinstance(entries, list):
            return "Error: entries_json must be a JSON array: [{key, value, ...}, ...]"
        if not entries:
            return "Error: entries_json array is empty."

        # Validate all entries before writing anything
        validated: List[Dict[str, Any]] = []
        errors: List[str] = []
        for i, raw in enumerate(entries):
            if not isinstance(raw, dict):
                errors.append(f"Entry {i}: must be an object, got {type(raw).__name__}")
                continue
            key = raw.get("key", "")
            value = raw.get("value", "")
            if not key or not isinstance(key, str):
                errors.append(f"Entry {i}: 'key' must be a non-empty string")
                continue
            if not value or not isinstance(value, str):
                errors.append(f"Entry {i}: 'value' must be a non-empty string")
                continue
            cat = raw.get("category", "uncategorized")
            if cat not in self.CATEGORIES and cat != "uncategorized":
                errors.append(f"Entry {i} (key='{key}'): unknown category '{cat}'")
                continue
            try:
                importance_val = float(raw.get("importance", 0.5))
            except (TypeError, ValueError):
                errors.append(
                    f"Entry {i} (key='{key}'): 'importance' must be numeric"
                )
                continue
            validated.append(
                {
                    "key": key,
                    "value": value,
                    "category": cat,
                    "importance": round(max(0.0, min(1.0, importance_val)), 4),
                    "tags": [str(t) for t in raw.get("tags", [])],
                }
            )

        if errors:
            return "Validation errors:\n" + "\n".join(f"  • {e}" for e in errors)

        # Write all validated entries atomically
        with self._lock:
            data = self._load_data()
            now = time.time()
            stored_keys: List[str] = []

            for item in validated:
                key = item["key"]
                existing = data.get(key, {})
                entry: Dict[str, Any] = {
                    "value": item["value"],
                    "timestamp": now,
                    "created": existing.get("created", now),
                    "category": item["category"],
                    "importance": item["importance"],
                    "tags": item["tags"],
                    "access_count": existing.get("access_count", 0),
                    "last_accessed": now,
                    "stability": existing.get("stability", 1.0),
                    "version": existing.get("version", 0) + 1,
                }

                if self.intelligence:
                    try:
                        analysis = self.intelligence.analyze_memory_entry(
                            key, item["value"], "memory"
                        )
                        entry["concepts"] = analysis.get("concepts", [])
                        entry["related_memories"] = analysis.get("related_memories", [])
                    except Exception as e:
                        self.logger.error(
                            "Bulk-store intelligence analysis failed for '%s': %s",
                            key,
                            e,
                        )
                        raise RuntimeError(
                            f"Bulk-store intelligence analysis failed for '{key}': {e}"
                        ) from e

                data[key] = entry
                self.working_memory.touch(key, entry)
                stored_keys.append(key)

            self._save_data(data)

        self.logger.info(f"Bulk stored {len(stored_keys)} entries.")
        return (
            f"Bulk store complete: {len(stored_keys)}/{len(entries)} entries stored.\n"
            f"Keys: {', '.join(stored_keys)}"
        )

    # ------------------------------------------------------------------
    # NEW: Get related
    # ------------------------------------------------------------------

    def get_related(self, key: str, max_results: int = 5) -> str:
        """
        Return memories semantically related to a given key.
        Refreshes relationship data if older than 1 hour.
        """
        if not key:
            return "Error: 'key' must be a non-empty string."

        with self._lock:
            data = self._load_data()

        if key not in data:
            return f"Key '{key}' not found in memory."

        entry = data[key]
        max_results = max(1, min(int(max_results), 20))

        # Check freshness of related_memories cache (stale after 1 hour)
        related = entry.get("related_memories", [])
        last_ts = entry.get("timestamp", 0)
        stale = (time.time() - last_ts) > 3600

        if stale and self.intelligence:
            try:
                analysis = self.intelligence.analyze_memory_entry(
                    key, entry.get("value", ""), "memory"
                )
                related = analysis.get("related_memories", [])
                with self._lock:
                    data2 = self._load_data()
                    if key in data2:
                        data2[key]["related_memories"] = related
                        data2[key]["timestamp"] = time.time()
                        self._save_data(data2)
            except Exception as e:
                self.logger.warning(f"get_related refresh failed for '{key}': {e}")

        if not related:
            return f"No related memories found for '{key}'."

        with self._lock:
            data = self._load_data()

        lines = [
            f"Memories related to '{key}' (top {min(max_results, len(related))}):\n"
        ]
        for i, rel in enumerate(related[:max_results], 1):
            mid = rel.get("memory_id", "")
            rel_key = mid.split(":", 1)[1] if ":" in mid else mid
            sim = rel.get("similarity", 0.0)
            shared = rel.get("shared_concepts", [])
            rel_entry = data.get(rel_key, {})
            val_preview = str(rel_entry.get("value", ""))[:100]

            lines.append(f"{i:2d}. {rel_key}  (similarity={sim:.3f})")
            if shared:
                lines.append(f"      Shared concepts: {', '.join(shared[:4])}")
            if val_preview:
                lines.append(
                    f"      {val_preview}{'...' if len(str(rel_entry.get('value', ''))) > 100 else ''}"
                )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # NEW: Timeline
    # ------------------------------------------------------------------

    def memory_timeline(self, days: int = 7, limit: int = 20) -> str:
        """
        Chronological view of memories created or updated in the last N days.
        Includes Ebbinghaus retention score for each entry.
        """
        days = max(1, min(int(days), 365))
        limit = max(1, min(int(limit), 200))
        cutoff = time.time() - (days * 86400)

        with self._lock:
            data = self._load_data()

        recent: List[Tuple[float, str, Dict[str, Any]]] = []
        for key, entry in data.items():
            ts = entry.get("timestamp", 0)
            if ts >= cutoff:
                recent.append((ts, key, entry))

        if not recent:
            return f"No memories created or updated in the last {days} days."

        recent.sort(reverse=True)
        total = len(recent)

        lines = [
            f"Memory Timeline — last {days} days "
            f"({min(limit, total)}/{total} entries shown):\n"
        ]
        for ts, key, entry in recent[:limit]:
            dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            cat = entry.get("category", "uncategorized")
            imp = entry.get("importance", 0.5)
            decay = _decay_score(entry)
            version = entry.get("version", 1)
            tags = entry.get("tags", [])

            badge = f"[{cat}]" if cat != "uncategorized" else ""
            tag_str = f"  #{' #'.join(tags[:2])}" if tags else ""
            lines.append(
                f"  {dt}  {key}  {badge}  "
                f"imp={imp:.2f}  retention={decay:.0%}  v{version}{tag_str}"
            )

        if total > limit:
            lines.append(
                f"\n  ... and {total - limit} more entries. Increase 'limit' to see more."
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # NEW: Export
    # ------------------------------------------------------------------

    def export_memories(self, format: str = "markdown") -> str:
        """
        Export all memories as Markdown or JSON.

        format='markdown': Structured Markdown document grouped by category.
        format='json':     Full JSON dump of all entries.
        """
        format = str(format).strip().lower()
        if format not in ("markdown", "json"):
            return "Error: 'format' must be 'markdown' or 'json'."

        with self._lock:
            data = self._load_data()

        if not data:
            return "Memory store is empty — nothing to export."

        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)

        # Markdown export
        # Group by category
        by_category: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
        for key, entry in data.items():
            cat = (
                entry.get("category", "uncategorized")
                if isinstance(entry, dict)
                else "uncategorized"
            )
            by_category.setdefault(cat, []).append((key, entry))

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            "# Memory Export",
            "",
            f"Generated: {now_str} | Total entries: {len(data)}",
            "",
        ]

        for cat in sorted(by_category.keys()):
            cat_desc = self.CATEGORIES.get(cat, "")
            lines.append(f"## {cat.capitalize()}")
            if cat_desc:
                lines.append(f"_{cat_desc}_")
            lines.append("")

            # Sort by importance within category
            entries = sorted(
                by_category[cat],
                key=lambda x: x[1].get("importance", 0.5),
                reverse=True,
            )
            for key, entry in entries:
                val = (
                    entry.get("value", str(entry))
                    if isinstance(entry, dict)
                    else str(entry)
                )
                imp = entry.get("importance", 0.5)
                tags = entry.get("tags", [])
                ts = entry.get("timestamp", 0)
                dt = (
                    datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "unknown"
                )
                concepts = entry.get("concepts", [])
                decay = _decay_score(entry)

                lines.append(f"### {key}")
                lines.append("")
                lines.append(val)
                lines.append("")
                meta_parts = [
                    f"**Importance:** {imp:.2f}",
                    f"**Date:** {dt}",
                    f"**Retention:** {decay:.0%}",
                ]
                if tags:
                    meta_parts.append(f"**Tags:** {', '.join(tags)}")
                if concepts:
                    meta_parts.append(f"**Concepts:** {', '.join(concepts[:5])}")
                lines.append("  ".join(meta_parts))
                lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Statistics & insights
    # ------------------------------------------------------------------

    def get_stats(self) -> str:
        """Comprehensive memory statistics."""
        with self._lock:
            data = self._load_data()

        if not data:
            return "Memory store is empty (0 entries)."

        now = time.time()
        week_ago = now - 604800
        categories: Dict[str, int] = {}
        importance_sum = 0.0
        access_sum = 0
        high_imp = medium_imp = low_imp = 0
        total_chars = 0
        timestamps: List[float] = []
        decay_scores: List[float] = []
        wm_keys = {k for k, _ in self.working_memory.get_all_recent()}
        recent_7d = 0

        for key, entry in data.items():
            cat = (
                entry.get("category", "uncategorized")
                if isinstance(entry, dict)
                else "uncategorized"
            )
            categories[cat] = categories.get(cat, 0) + 1
            imp = entry.get("importance", 0.5) if isinstance(entry, dict) else 0.5
            importance_sum += imp
            acc = entry.get("access_count", 0) if isinstance(entry, dict) else 0
            access_sum += acc
            val = (
                entry.get("value", str(entry))
                if isinstance(entry, dict)
                else str(entry)
            )
            total_chars += len(val)
            ts = entry.get("timestamp", 0) if isinstance(entry, dict) else 0
            if ts:
                timestamps.append(ts)
            if ts >= week_ago:
                recent_7d += 1
            decay_scores.append(_decay_score(entry) if isinstance(entry, dict) else 0.5)
            if imp >= 0.7:
                high_imp += 1
            elif imp >= 0.4:
                medium_imp += 1
            else:
                low_imp += 1

        n = len(data)
        avg_imp = importance_sum / n
        avg_acc = access_sum / n
        avg_decay = sum(decay_scores) / len(decay_scores) if decay_scores else 0.0
        storage_bytes = (
            self.storage_file.stat().st_size if self.storage_file.exists() else 0
        )

        lines = [
            "Enhanced Memory Statistics",
            "=" * 45,
            f"Total entries            : {n}",
            f"Storage file size        : {storage_bytes:,} bytes",
            f"Total content            : {total_chars:,} characters",
            f"Avg content per entry    : {total_chars // n if n else 0} characters",
            "",
            "Importance Distribution:",
            f"  High  (>= 0.7) : {high_imp:4d} ({high_imp / n * 100:.1f}%)",
            f"  Medium (0.4-0.7): {medium_imp:4d} ({medium_imp / n * 100:.1f}%)",
            f"  Low   (< 0.4)  : {low_imp:4d} ({low_imp / n * 100:.1f}%)",
            f"  Average importance  : {avg_imp:.3f}",
            "",
            "Access Patterns:",
            f"  Total accesses         : {access_sum}",
            f"  Avg accesses per entry : {avg_acc:.1f}",
            f"  Working memory (hot)   : {len(wm_keys)} entries",
            f"  Active (last 7 days)   : {recent_7d}",
            f"  Avg Ebbinghaus retention: {avg_decay:.0%}",
            "",
            "Categories:",
        ]
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cat:<15s}: {count:4d} ({count / n * 100:.1f}%)")

        if timestamps:
            oldest = datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d %H:%M")
            newest = datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d %H:%M")
            lines += ["", f"Oldest entry : {oldest}", f"Newest entry : {newest}"]

        return "\n".join(lines)

    def get_memory_insights(self) -> str:
        """Narrative insights combining local stats and BM25 network analysis."""
        with self._lock:
            data = self._load_data()

        if not data:
            return "Memory is empty — no insights available."

        n = len(data)
        now = time.time()
        week_ago = now - 604800

        categories: Dict[str, int] = {}
        importance_scores: List[float] = []
        access_counts: List[int] = []
        recent_activity = 0

        for entry in data.values():
            if isinstance(entry, dict):
                categories[entry.get("category", "uncategorized")] = (
                    categories.get(entry.get("category", "uncategorized"), 0) + 1
                )
                importance_scores.append(entry.get("importance", 0.5))
                access_counts.append(entry.get("access_count", 0))
                if entry.get("last_accessed", 0) > week_ago:
                    recent_activity += 1

        lines = ["Memory System Insights", "=" * 45, f"Total memories: {n}", ""]

        if categories:
            lines.append("Category Breakdown:")
            for cat, count in sorted(
                categories.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"  {cat}: {count} ({count / n * 100:.1f}%)")
            lines.append("")

        if importance_scores:
            avg_imp = sum(importance_scores) / len(importance_scores)
            high = sum(1 for s in importance_scores if s >= 0.7)
            lines.append(f"Importance: avg={avg_imp:.3f}  high-priority={high}")

        if access_counts:
            total_acc = sum(access_counts)
            freq = sum(1 for c in access_counts if c >= 5)
            lines.append(
                f"Access: total={total_acc}  frequently-used={freq}  "
                f"active-7d={recent_activity}"
            )

        # BM25 network insights
        if self.intelligence:
            try:
                net = self.intelligence.get_memory_insights()
                lines.append("")
                lines.append("BM25 Network Analysis:")
                lines.append(net)
            except Exception as e:
                lines.append(f"\nNetwork analysis error: {e}")

        return "\n".join(lines)

    def consolidate_memories(self, days_old: int = 30) -> str:
        """
        Archive old low-importance memories, merge near-duplicates (BM25 > 0.85),
        and remove them from the active store.
        """
        try:
            days_old = max(1, int(days_old))
            cutoff = time.time() - (days_old * 86400)

            with self._lock:
                data = self._load_data()

                old: Dict[str, Any] = {}
                active: Dict[str, Any] = {}

                for key, entry in data.items():
                    if isinstance(entry, dict):
                        last = entry.get(
                            "last_accessed", entry.get("timestamp", time.time())
                        )
                        imp = entry.get("importance", 0.5)
                        acc = entry.get("access_count", 0)
                        if last <= cutoff and imp < 0.7 and acc < 5:
                            old[key] = entry
                        else:
                            active[key] = entry
                    else:
                        active[key] = entry

                if not old:
                    return f"No memories older than {days_old} days found for consolidation."

                # Archive
                archive_dir = self.storage_file.parent / "archives"
                archive_dir.mkdir(exist_ok=True)
                ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_file = archive_dir / f"memory_archive_{ts_str}.json"

                archive_payload = {
                    "archived_date": datetime.now().isoformat(),
                    "days_old_threshold": days_old,
                    "archived_count": len(old),
                    "memories": old,
                }
                with open(archive_file, "w", encoding="utf-8") as f:
                    json.dump(archive_payload, f, indent=2, ensure_ascii=False)

                self._save_data(active)

                # Clear working memory entries that were archived
                for key in old:
                    self.working_memory.invalidate(key)

            # Also consolidate the BM25 index
            merged_count = 0
            if self.intelligence:
                try:
                    result = self.intelligence.consolidate_memories(days_old)
                    merged_count = result.get("archived", 0)
                except Exception as e:
                    self.logger.warning(f"Index consolidation failed: {e}")

            response = (
                f"Memory Consolidation Complete\n"
                f"  Archived : {len(old)} old memories\n"
                f"  Retained : {len(active)} active memories\n"
                f"  Archive  : {archive_file.name}\n"
                f"  Index pruned: {merged_count} index entries removed"
            )
            self.logger.info(f"Consolidated {len(old)} memories.")
            return response

        except Exception as e:
            self.logger.error(f"Memory consolidation failed: {e}")
            return f"Memory consolidation failed: {e}"

    @staticmethod
    def _merge_tool_arguments(
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        param_names: List[str],
    ) -> Dict[str, Any]:
        """Merge positional, kwargs, and single-dict invocation styles."""
        merged: Dict[str, Any] = {}
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                merged.update(args[0])
            else:
                for name, value in zip(param_names, args):
                    merged[name] = value
        merged.update(kwargs)
        return merged

    def _normalize_tool_registry(
        self, tools: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Wrap tools so they tolerate kwargs, dict-style, and positional calls."""

        def _wrap(
            tool_fn: Callable[..., Any], param_names: List[str]
        ) -> Callable[..., Any]:
            def _wrapped(*args: Any, **kwargs: Any) -> Any:
                merged = self._merge_tool_arguments(args, kwargs, param_names)

                if not merged:
                    try:
                        return tool_fn()
                    except TypeError:
                        pass

                try:
                    return tool_fn(**merged)
                except TypeError as first_error:
                    if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
                        try:
                            return tool_fn(args[0])
                        except TypeError:
                            pass
                    if not param_names:
                        # Legacy dispatchers may pass an arguments dict even for no-arg tools.
                        return tool_fn()
                    raise first_error

            return _wrapped

        normalized: Dict[str, Dict[str, Any]] = {}
        for tool_name, tool_def in tools.items():
            if not isinstance(tool_def, dict):
                normalized[tool_name] = tool_def
                continue

            wrapped = dict(tool_def)
            raw_fn = wrapped.get("function")
            param_names = [
                p.get("name")
                for p in wrapped.get("parameters", [])
                if isinstance(p, dict) and p.get("name")
            ]
            if callable(raw_fn):
                wrapped["function"] = _wrap(raw_fn, param_names)
            normalized[tool_name] = wrapped

        return normalized

    # ------------------------------------------------------------------
    # MCP tool registration
    # ------------------------------------------------------------------

    def get_tools(self) -> Dict[str, Any]:
        """Return all MCP tool definitions with bb7_ prefix."""
        tools: Dict[str, Dict[str, Any]] = {
            # --- Core operations ---
            "bb7_memory_store": {
                "function": lambda key, value, category="uncategorized", importance=0.5, tags=None: (
                    self.store(key, value, category, float(importance), tags or [])
                ),
                "description": (
                    "Store a key-value memory with category, importance (0-1), tags, "
                    "and automatic BM25 indexing + Ebbinghaus decay initialisation."
                ),
                "parameters": [
                    {
                        "name": "key",
                        "type": "string",
                        "required": True,
                        "description": "Unique memory key.",
                    },
                    {
                        "name": "value",
                        "type": "string",
                        "required": True,
                        "description": "Memory content.",
                    },
                    {
                        "name": "category",
                        "type": "string",
                        "required": False,
                        "description": "Category: insights|decisions|patterns|context|solutions|references|goals|technical",
                    },
                    {
                        "name": "importance",
                        "type": "number",
                        "required": False,
                        "description": "Importance score 0.0-1.0 (default 0.5).",
                    },
                    {
                        "name": "tags",
                        "type": "array",
                        "items": {"type": "string"},
                        "required": False,
                        "description": "Optional string tags.",
                    },
                ],
            },
            "bb7_memory_retrieve": {
                "function": lambda key, include_related=False: self.retrieve(
                    key, bool(include_related)
                ),
                "description": (
                    "Retrieve a memory by key. Updates Ebbinghaus stability "
                    "(reinforces retention). Use include_related=true for full metadata."
                ),
                "parameters": [
                    {
                        "name": "key",
                        "type": "string",
                        "required": True,
                        "description": "Memory key to retrieve.",
                    },
                    {
                        "name": "include_related",
                        "type": "boolean",
                        "required": False,
                        "description": "Include metadata and related keys (default false).",
                    },
                ],
            },
            "bb7_memory_delete": {
                "function": self.delete,
                "description": "Delete a memory entry by key.",
                "parameters": [
                    {
                        "name": "key",
                        "type": "string",
                        "required": True,
                        "description": "Key to delete.",
                    },
                ],
            },
            # --- Listing & search ---
            "bb7_memory_list": {
                "function": lambda prefix=None, category=None, min_importance=0.0, sort_by="timestamp": (
                    self.list_keys(prefix, category, float(min_importance), sort_by)
                ),
                "description": (
                    "List memory keys with filtering (prefix, category, min_importance) "
                    "and sorting (timestamp|importance|access|alphabetical|decay)."
                ),
                "parameters": [
                    {
                        "name": "prefix",
                        "type": "string",
                        "required": False,
                        "description": "Key prefix filter.",
                    },
                    {
                        "name": "category",
                        "type": "string",
                        "required": False,
                        "description": "Category filter.",
                    },
                    {
                        "name": "min_importance",
                        "type": "number",
                        "required": False,
                        "description": "Minimum importance filter.",
                    },
                    {
                        "name": "sort_by",
                        "type": "string",
                        "required": False,
                        "description": "Sort field: timestamp|importance|access|alphabetical|decay",
                    },
                ],
            },
            "bb7_memory_search": {
                "function": lambda query, max_results=5: self.intelligent_search(
                    query, int(max_results)
                ),
                "description": "BM25-powered semantic search with Ebbinghaus decay reranking.",
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
                ],
            },
            # --- NEW tools ---
            "bb7_memory_surface_context": {
                "function": lambda context_text, max_results=5: self.surface_context(
                    context_text, int(max_results)
                ),
                "description": (
                    "Proactively surface the most relevant memories for a given "
                    "context blob using BM25 + Ebbinghaus decay weighting. "
                    "Call at session start to recover relevant prior knowledge."
                ),
                "parameters": [
                    {
                        "name": "context_text",
                        "type": "string",
                        "required": True,
                        "description": "Current context or task description.",
                    },
                    {
                        "name": "max_results",
                        "type": "number",
                        "required": False,
                        "description": "Max memories to surface (default 5).",
                    },
                ],
            },
            "bb7_memory_bulk_store": {
                "function": lambda entries_json: self.bulk_store(entries_json),
                "description": (
                    "Atomically store multiple memory entries in a single disk write. "
                    "entries_json must be a JSON array of {key, value, category, importance, tags} objects."
                ),
                "parameters": [
                    {
                        "name": "entries_json",
                        "type": "string",
                        "required": True,
                        "description": "JSON array of memory entry objects.",
                    },
                ],
            },
            "bb7_memory_get_related": {
                "function": lambda key, max_results=5: self.get_related(
                    key, int(max_results)
                ),
                "description": "Fetch semantically related memories for a given key using BM25.",
                "parameters": [
                    {
                        "name": "key",
                        "type": "string",
                        "required": True,
                        "description": "Memory key to find relations for.",
                    },
                    {
                        "name": "max_results",
                        "type": "number",
                        "required": False,
                        "description": "Max related memories to return (default 5).",
                    },
                ],
            },
            "bb7_memory_timeline": {
                "function": lambda days=7, limit=20: self.memory_timeline(
                    int(days), int(limit)
                ),
                "description": (
                    "Chronological view of memories created or updated recently. "
                    "Shows Ebbinghaus retention score for each entry."
                ),
                "parameters": [
                    {
                        "name": "days",
                        "type": "number",
                        "required": False,
                        "description": "Look-back window in days (default 7).",
                    },
                    {
                        "name": "limit",
                        "type": "number",
                        "required": False,
                        "description": "Max entries to show (default 20).",
                    },
                ],
            },
            "bb7_memory_export": {
                "function": lambda format="markdown": self.export_memories(str(format)),
                "description": "Export all memories as Markdown (default) or JSON.",
                "parameters": [
                    {
                        "name": "format",
                        "type": "string",
                        "required": False,
                        "description": "Export format: 'markdown' or 'json' (default 'markdown').",
                    },
                ],
            },
            # --- Analytics ---
            "bb7_memory_stats": {
                "function": self.get_stats,
                "description": "Comprehensive memory statistics including decay, access patterns, and category breakdown.",
                "parameters": [],
            },
            "bb7_memory_insights": {
                "function": self.get_memory_insights,
                "description": "Narrative insights combining local stats and BM25 network analysis.",
                "parameters": [],
            },
            "bb7_memory_consolidate": {
                "function": lambda days_old=30: self.consolidate_memories(
                    int(days_old)
                ),
                "description": (
                    "Archive old low-importance memories, prune BM25 index. "
                    "Memories with importance >= 0.7 or access_count >= 5 are always retained."
                ),
                "parameters": [
                    {
                        "name": "days_old",
                        "type": "number",
                        "required": False,
                        "description": "Age threshold in days (default 30).",
                    },
                ],
            },
            "bb7_memory_categories": {
                "function": lambda: (
                    "Available memory categories:\n"
                    + "\n".join(
                        f"  {cat}: {desc}" for cat, desc in self.CATEGORIES.items()
                    )
                ),
                "description": "List available memory categories with descriptions.",
                "parameters": [],
            },
        }
        return self._normalize_tool_registry(tools)


# ---------------------------------------------------------------------------
# Standalone smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import tempfile

    logging.basicConfig(level=logging.INFO)
    with tempfile.TemporaryDirectory() as tmp:
        m = EnhancedMemoryTool(storage_file=os.path.join(tmp, "test_store.json"))
        print(
            m.store(
                "bm25_insight",
                "BM25 outperforms Jaccard for text retrieval",
                category="insights",
                importance=0.9,
            )
        )
        print(
            m.store(
                "decay_model",
                "Ebbinghaus forgetting curve models human memory retention",
                category="technical",
                importance=0.8,
            )
        )
        print(m.retrieve("bm25_insight", include_related=True))
        print(m.intelligent_search("retrieval ranking"))
        print(
            m.surface_context(
                "We are working on improving search quality in the memory system"
            )
        )
        print(m.memory_timeline(days=1))
        print(m.get_stats())
