"""
Muad'Dib Advanced Modality Bridge

Produces per-tool, provenance-tagged routing features from real learned signals.
Three independent extractors, each circuit-broken independently, all fail-open.

Provenance weights enforce signal quality automatically:
  trained_q        1.00  — Q-table TD-learned values (real outcomes)
  trained_cooccur  0.85  — observation-buffer co-occurrence (real sequences)
  untrained_embed  0.20  — embedding table (consistent but not semantically trained)
  stub             0.00  — never used

Max effective contribution at alpha_base=0.15:
  trained_q:        0.15 * score * 1.00  (up to 0.15)
  trained_cooccur:  0.15 * score * 0.85  (up to 0.127)
  untrained_embed:  0.15 * 0.30 * 0.20  = 0.009  (near-zero by construction)

Circuit breaker: lazy half-open (no background threads).
Cache: LRU + TTL, thread-safe.
"""

import logging
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Force-fail env flag for test isolation (does not silence extractor logs)
# ---------------------------------------------------------------------------
MUADIB_ADVANCED_FORCE_FAIL: bool = (
    os.getenv("MUADIB_ADVANCED_FORCE_FAIL", "0") == "1"
)


# ═══════════════════════════════════════════════════════════════════════════
#  §1  PROVENANCE
# ═══════════════════════════════════════════════════════════════════════════


class ProvenanceTag(str, Enum):
    TRAINED_Q = "trained_q"
    TRAINED_COOCCUR = "trained_cooccur"
    UNTRAINED_EMBED = "untrained_embed"
    STUB = "stub"


_PROVENANCE_WEIGHTS: Dict[str, float] = {
    ProvenanceTag.TRAINED_Q: 1.00,
    ProvenanceTag.TRAINED_COOCCUR: 0.85,
    ProvenanceTag.UNTRAINED_EMBED: 0.20,
    ProvenanceTag.STUB: 0.00,
}


# ═══════════════════════════════════════════════════════════════════════════
#  §2  CONFIG & FEATURE SET
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class AdvancedBridgeConfig:
    alpha_base: float = 0.15
    min_confidence: float = 0.30
    feature_cache_ttl_s: float = 8.0
    feature_cache_max: int = 128
    max_consecutive_failures: int = 5
    circuit_reset_interval_s: float = 300.0


@dataclass
class AdvancedFeatureSet:
    tool_name: str
    raw_score: float
    confidence: float
    provenance: ProvenanceTag
    effective_score: float  # raw_score * confidence * provenance_weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "raw_score": round(self.raw_score, 4),
            "confidence": round(self.confidence, 4),
            "provenance": self.provenance.value,
            "provenance_weight": _PROVENANCE_WEIGHTS[self.provenance],
            "effective_score": round(self.effective_score, 4),
        }


def _make_feat(
    tool_name: str,
    raw_score: float,
    confidence: float,
    provenance: ProvenanceTag,
) -> AdvancedFeatureSet:
    weight = _PROVENANCE_WEIGHTS[provenance]
    effective = max(0.0, min(1.0, raw_score)) * max(0.0, min(1.0, confidence)) * weight
    return AdvancedFeatureSet(
        tool_name=tool_name,
        raw_score=max(0.0, min(1.0, raw_score)),
        confidence=max(0.0, min(1.0, confidence)),
        provenance=provenance,
        effective_score=round(effective, 6),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  §3  LRU + TTL CACHE
# ═══════════════════════════════════════════════════════════════════════════


class _LRUTTLCache:
    """Thread-safe LRU+TTL cache."""

    def __init__(self, max_size: int = 128, ttl_s: float = 8.0) -> None:
        self._store: OrderedDict[Any, Tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl_s = ttl_s
        self._lock = threading.Lock()

    def get(self, key: Any) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            value, ts = self._store[key]
            if time.time() - ts > self._ttl_s:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return value

    def put(self, key: Any, value: Any) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, time.time())
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)


# ═══════════════════════════════════════════════════════════════════════════
#  §4  CIRCUIT BREAKER (lazy half-open)
# ═══════════════════════════════════════════════════════════════════════════


class _ExtractorCircuit:
    """
    Per-extractor lazy half-open circuit breaker.

    No background threads. On each should_run() call:
      - If closed: allow through.
      - If open + reset interval not elapsed: block.
      - If open + reset interval elapsed: allow one half-open probe.
        record_success() closes it; record_failure() re-opens it.
    """

    def __init__(self, max_failures: int, reset_interval_s: float) -> None:
        self._max_failures = max_failures
        self._reset_interval_s = reset_interval_s
        self._consecutive_failures = 0
        self._circuit_open = False
        self._circuit_open_at: float = 0.0
        self._lock = threading.Lock()

    def should_run(self) -> bool:
        with self._lock:
            if not self._circuit_open:
                return True
            if time.time() - self._circuit_open_at >= self._reset_interval_s:
                # Half-open: allow one probe
                self._circuit_open = False
                self._consecutive_failures = 0
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._circuit_open = False

    def record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                self._circuit_open = True
                self._circuit_open_at = time.time()

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._circuit_open

    @property
    def failures(self) -> int:
        with self._lock:
            return self._consecutive_failures


# ═══════════════════════════════════════════════════════════════════════════
#  §5  ADVANCED MODALITY BRIDGE
# ═══════════════════════════════════════════════════════════════════════════


class AdvancedModalityBridge:
    """
    Fail-open bridge from the Muad'Dib substrate to routing feature vectors.

    Constructor takes duck-typed references:
      backbone_ref — DigitalTwinBackbone instance (._buffer, ._qtable attrs)
      twin_ref     — DigitalTwinTool instance (bb7_dt_q_scores, bb7_dt_encode_catalog)

    Three signal extractors operate independently:
      1. _q_variance_signal     (trained_q)       — Q-table confidence-weighted bonuses
      2. _cooccurrence_signal   (trained_cooccur) — observation-buffer sequence counts
      3. _embed_cosine_signal   (untrained_embed) — embedding-table L2 norms

    All extractors are try/except + circuit-broken. A failure in one does NOT
    disable the others. extract() always returns a dict (empty on total failure).
    """

    def __init__(
        self,
        config: AdvancedBridgeConfig,
        backbone_ref: Any,
        twin_ref: Any,
    ) -> None:
        self.config = config
        self._backbone = backbone_ref
        self._twin = twin_ref
        self._available = True
        self._active = False
        self._last_error: Optional[str] = None
        self._last_activated: float = 0.0
        self._provenance_dist: Dict[str, int] = {p.value: 0 for p in ProvenanceTag}

        self._q_circuit = _ExtractorCircuit(
            config.max_consecutive_failures, config.circuit_reset_interval_s
        )
        self._cooccur_circuit = _ExtractorCircuit(
            config.max_consecutive_failures, config.circuit_reset_interval_s
        )
        self._embed_circuit = _ExtractorCircuit(
            config.max_consecutive_failures, config.circuit_reset_interval_s
        )
        self._cache = _LRUTTLCache(
            max_size=config.feature_cache_max, ttl_s=config.feature_cache_ttl_s
        )

    # ── public extract ──────────────────────────────────────────────────────

    def extract(
        self,
        candidates: List[str],
        category: str,
        session_id: str,
        recent_tools: List[str],
    ) -> Dict[str, AdvancedFeatureSet]:
        """
        Return per-tool AdvancedFeatureSet for each candidate.
        Always returns a dict — empty if all extractors fail.
        """
        if MUADIB_ADVANCED_FORCE_FAIL:
            raise RuntimeError(
                "MUADIB_ADVANCED_FORCE_FAIL is set — bridge intentionally disabled for testing"
            )

        if not candidates:
            return {}

        # Cache key: frozenset of candidates + category + 8-char session prefix
        cache_key = (frozenset(candidates), category, (session_id or "")[:8])
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        results: Dict[str, AdvancedFeatureSet] = {}

        # Signal 1 — Q-variance (trained_q, highest provenance weight)
        q_feats = self._q_variance_signal(candidates, category, session_id)
        results.update(q_feats)

        # Signal 2 — co-occurrence (trained_cooccur)
        cooccur_feats = self._cooccurrence_signal(candidates, recent_tools)
        for tool, feat in cooccur_feats.items():
            # Only overwrite if co-occurrence effective_score is higher
            if tool not in results or feat.effective_score > results[tool].effective_score:
                results[tool] = feat

        # Signal 3 — embed cosine (untrained_embed, fills gaps only)
        embed_feats = self._embed_cosine_signal(candidates, category)
        for tool, feat in embed_feats.items():
            if tool not in results:
                results[tool] = feat

        if results:
            self._active = True
            self._last_activated = time.time()
            for feat in results.values():
                key = feat.provenance.value
                self._provenance_dist[key] = self._provenance_dist.get(key, 0) + 1

        self._cache.put(cache_key, results)
        return results

    # ── extractor 1: Q-variance ─────────────────────────────────────────────

    def _q_variance_signal(
        self,
        candidates: List[str],
        category: str,
        session_id: str,
    ) -> Dict[str, AdvancedFeatureSet]:
        """
        Q-table confidence-weighted bonuses.

        Confidence = 1 - (std / (range + eps)), blended with observation count
        saturation. Tools unseen in the Q-table are excluded (not zeroed).
        """
        if not self._q_circuit.should_run():
            return {}
        try:
            q_result = self._twin.bb7_dt_q_scores(candidates, category, session_id)
            bonuses: Dict[str, float] = q_result.get("bonuses", {})

            # Walk Q-table internals for variance estimation
            qtable = self._backbone._qtable
            q_per_tool: Dict[str, List[float]] = {}
            with qtable._lock:
                for _state, row in qtable._q.items():
                    for tool in candidates:
                        if tool in row:
                            q_per_tool.setdefault(tool, []).append(row[tool])

            features: Dict[str, AdvancedFeatureSet] = {}
            for tool in candidates:
                values = q_per_tool.get(tool)
                if not values:
                    continue  # never seen in Q-table — skip (not zeroed)

                n = len(values)
                mean = sum(values) / n
                variance = sum((v - mean) ** 2 for v in values) / n
                std = variance ** 0.5
                span = max(values) - min(values)
                # High variance relative to span → lower confidence
                variance_conf = max(0.0, min(1.0, 1.0 - (std / (span + 1e-6))))
                # Saturate at 50 observations
                obs_conf = min(1.0, n / 50.0)
                confidence = variance_conf * 0.6 + obs_conf * 0.4

                if confidence < self.config.min_confidence:
                    continue

                raw = max(0.0, min(1.0, float(bonuses.get(tool, 0.0))))
                features[tool] = _make_feat(tool, raw, confidence, ProvenanceTag.TRAINED_Q)

            self._q_circuit.record_success()
            return features

        except Exception as exc:
            self._q_circuit.record_failure()
            self._last_error = f"q_variance: {exc}"
            if self._q_circuit.failures == 1:
                logger.warning("advanced_bridge q_variance failed: %s", exc)
            return {}

    # ── extractor 2: co-occurrence ──────────────────────────────────────────

    def _cooccurrence_signal(
        self,
        candidates: List[str],
        recent_tools: List[str],
    ) -> Dict[str, AdvancedFeatureSet]:
        """
        Observation-buffer co-occurrence.

        Counts how often each candidate appears as the action immediately after
        any of recent_tools in the historical observation deque.
        Confidence scales linearly with total observations, saturates at 500.
        """
        if not self._cooccur_circuit.should_run():
            return {}
        if not recent_tools:
            return {}
        try:
            buf = self._backbone._buffer
            total_obs = buf.size()
            confidence = min(1.0, total_obs / 500.0)

            if confidence < self.config.min_confidence:
                self._cooccur_circuit.record_success()
                return {}

            obs = buf.recent(500)
            recent_set = set(recent_tools)
            candidate_set = set(candidates)

            counts: Dict[str, int] = {c: 0 for c in candidates}
            for i in range(len(obs) - 1):
                if obs[i].get("action") in recent_set:
                    nxt = obs[i + 1].get("action")
                    if nxt in candidate_set:
                        counts[nxt] = counts.get(nxt, 0) + 1

            max_hits = max(counts.values()) if counts else 0
            if max_hits == 0:
                self._cooccur_circuit.record_success()
                return {}

            features: Dict[str, AdvancedFeatureSet] = {}
            for tool, count in counts.items():
                if count == 0:
                    continue
                raw = count / max_hits
                features[tool] = _make_feat(
                    tool, raw, confidence, ProvenanceTag.TRAINED_COOCCUR
                )

            self._cooccur_circuit.record_success()
            return features

        except Exception as exc:
            self._cooccur_circuit.record_failure()
            self._last_error = f"cooccur: {exc}"
            if self._cooccur_circuit.failures == 1:
                logger.warning("advanced_bridge cooccur failed: %s", exc)
            return {}

    # ── extractor 3: embed cosine (untrained) ──────────────────────────────

    def _embed_cosine_signal(
        self,
        candidates: List[str],
        category: str,
    ) -> Dict[str, AdvancedFeatureSet]:
        """
        Embedding-table L2-norm signal.

        Confidence is fixed at 0.30 (hardcoded — untrained embed is consistent
        but not semantically calibrated). Max contribution at alpha_base=0.15:
          0.15 * 0.30 * 0.20 = 0.009 (near-zero, by construction).
        """
        if not self._embed_circuit.should_run():
            return {}

        _EMBED_CONFIDENCE = 0.30  # intentionally fixed — do not raise

        try:
            category_map = {name: category for name in candidates}
            encode_result = self._twin.bb7_dt_encode_catalog(candidates, category_map)
            if not isinstance(encode_result, dict) or not encode_result.get("ok"):
                self._embed_circuit.record_success()
                return {}

            embeddings: Dict[str, List[float]] = encode_result.get("embeddings", {})
            if not embeddings:
                self._embed_circuit.record_success()
                return {}

            norms: Dict[str, float] = {}
            for tool, vec in embeddings.items():
                if vec:
                    norms[tool] = sum(v * v for v in vec) ** 0.5

            if not norms:
                self._embed_circuit.record_success()
                return {}

            max_norm = max(norms.values())
            if max_norm < 1e-9:
                self._embed_circuit.record_success()
                return {}

            features: Dict[str, AdvancedFeatureSet] = {}
            for tool in candidates:
                norm = norms.get(tool)
                if norm is None:
                    continue
                raw = norm / (max_norm + 1e-9)
                features[tool] = _make_feat(
                    tool, raw, _EMBED_CONFIDENCE, ProvenanceTag.UNTRAINED_EMBED
                )

            self._embed_circuit.record_success()
            return features

        except Exception as exc:
            self._embed_circuit.record_failure()
            self._last_error = f"embed_cosine: {exc}"
            if self._embed_circuit.failures == 1:
                logger.warning("advanced_bridge embed_cosine failed: %s", exc)
            return {}

    # ── health ──────────────────────────────────────────────────────────────

    @property
    def health(self) -> Dict[str, Any]:
        return {
            "available": self._available,
            "active": self._active,
            "last_error": self._last_error,
            "last_activated": self._last_activated,
            "q_circuit_open": self._q_circuit.is_open,
            "cooccur_circuit_open": self._cooccur_circuit.is_open,
            "embed_circuit_open": self._embed_circuit.is_open,
            "q_failures": self._q_circuit.failures,
            "cooccur_failures": self._cooccur_circuit.failures,
            "embed_failures": self._embed_circuit.failures,
            "provenance_dist": dict(self._provenance_dist),
        }
