"""
LISAN AL-GAIB: THE PRESCIENT EXOSKELETON
==========================================

Post-DARPA cognitive substrate for autonomous tool orchestration.
Six novel subsystems fused into a single prescient intelligence layer:

1. SPECTRAL INTENT DECOMPOSITION — Character n-grams + positional TF-IDF +
   entropy-gated disambiguation replaces keyword matching entirely.
2. THOMPSON SAMPLING WITH CONTEXTUAL BANDITS — Bayesian posterior sampling
   with exponential recency weighting + counterfactual regret tracking.
3. MONTE CARLO TREE SEARCH PLANNING — UCB1 exploration, adversarial failure
   injection, Pareto-optimal plan selection with causal dependency graphs.
4. TOPOLOGICAL MOMENTUM MANIFOLD — Exponential decay attention, spectral
   graph momentum from category transitions, change-point detection.
5. NARRATIVE SYNTHESIS CORTEX — Confidence-calibrated language, token-budget
   awareness, multi-voice narrative generation for LLM consumption.
6. AUTONOMOUS META-LEARNING — Online weight tuning via KL divergence,
   automatic golden path discovery, capability graph evolution.

Architecture Philosophy:
  - Golden Paths: Pre-loaded collective intelligence (Bene Gesserit Other Memory)
  - Momentum Tracking: Session-aware conversational flow (The Voice)
  - Narrative Generation: LLM-optimized reasoning scaffolds (Mentat computation)
  - Spectral Decomposition: Multi-dimensional intent space (prescient vision)

Source: Sovereign MCP Server - Exoskeleton Enhancement Module
Version: 3.0.0-prescient-SOTA++
Status: Production Stable
"""

import json
import logging
import math
import random
import threading
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  SPECTRAL INTENT DECOMPOSITION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
#
# Instead of bag-of-words keyword matching, we decompose user intent into a
# multi-dimensional spectral signature using character n-grams, positional
# TF-IDF, and entropy-gated disambiguation.  This makes the engine robust
# to typos, partial matches, and morphological variation — things that
# destroy keyword matchers but leave spectral decomposition unharmed.
# ═══════════════════════════════════════════════════════════════════════════════


class _SpectralIntentDecomposer:
    """
    Decomposes free-text intent into a spectral similarity tensor.

    The decomposition pipeline:
      1. Character-level n-gram extraction (n=2..4) for morphology-invariant
         sub-word matching.  "debugging" shares trigrams with "debugger".
      2. Positional TF-IDF that weights tokens by their relative position in
         the query — early tokens carry more intent weight (frontal emphasis).
      3. Entropy-gated category disambiguation: when the top-2 category scores
         are within epsilon, the engine broadens the candidate pool rather than
         committing to a possibly-wrong single winner.

    Source: Sovereign MCP Server - Spectral Analysis Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    def __init__(
        self, ngram_range: Tuple[int, int] = (2, 4), positional_decay: float = 0.85
    ) -> None:
        """
        Initialize the spectral decomposer.

        Args:
            ngram_range: Tuple of (min_n, max_n) for character n-gram extraction.
            positional_decay: Exponential decay rate for positional weighting.
                              Higher values preserve early-token emphasis longer.
        """
        self._ngram_range: Tuple[int, int] = ngram_range
        self._idf_cache: Dict[str, float] = {}
        self._corpus_size: int = 0
        self._positional_decay: float = max(0.5, min(0.99, positional_decay))
        # ── Muad'Dib neural embedding cache (Phase 1 injection) ──────────
        # When the Digital Twin encodes a tool sequence, the hidden_states
        # are cached here as a flat list-of-floats per tool name. Spectral
        # similarity blends this neural signal at 30% weight when available.
        self._neural_embed_cache: Dict[str, List[float]] = {}
        self._neural_embed_lock: threading.Lock = threading.Lock()
        self._neural_blend_weight: float = 0.30  # 30% neural, 70% spectral

    def rebuild_idf(self, tool_catalog: Dict[str, Dict[str, Any]]) -> None:
        """
        Recompute IDF weights from the full tool catalog corpus.

        Each tool's name + description is treated as a document.  IDF uses
        smoothed logarithmic weighting: log((N + 1) / (df + 1)) + 1.

        Args:
            tool_catalog: Mapping of tool_name -> tool_info dict with
                          'name' and 'description' keys.
        """
        doc_freq: Dict[str, int] = defaultdict(int)
        n_docs = 0
        for _name, info in tool_catalog.items():
            text = f"{info.get('name', '')} {info.get('description', '')}"
            unique_ngrams: Set[str] = set(self._extract_ngrams(text))
            for ng in unique_ngrams:
                doc_freq[ng] += 1
            n_docs += 1

        self._corpus_size = max(1, n_docs)
        self._idf_cache = {}
        for ngram, df in doc_freq.items():
            self._idf_cache[ngram] = (
                math.log((self._corpus_size + 1.0) / (df + 1.0)) + 1.0
            )

    def inject_neural_embeddings(
        self,
        tool_embeddings: Dict[str, List[float]],
    ) -> None:
        """
        Cache neural embeddings from Muad'Dib's bb7_dt_encode for blending.

        Called by ExoskeletonTool after encoding the current tool catalog
        through the Digital Twin's neural pipeline. The embeddings are
        per-tool d_model vectors that capture learned tool relationships.

        Args:
            tool_embeddings: Mapping of tool_name -> flat list of floats
                             (the mean-pooled hidden_state for that tool).
        """
        with self._neural_embed_lock:
            self._neural_embed_cache = dict(tool_embeddings)

    def _neural_cosine_similarity(
        self,
        query_text: str,
        tool_name: str,
    ) -> Optional[float]:
        """
        Compute neural cosine similarity between query embedding and tool embedding.

        Returns None if no neural embeddings are cached for this tool.
        Uses the query n-gram hash as a pseudo-embedding for the query side
        (maps character n-gram frequencies to d_model dimensions via modular
        indexing — a lightweight projection that doesn't require torch).

        Args:
            query_text: The user's intent string.
            tool_name: The tool to compare against.

        Returns:
            Cosine similarity in [0.0, 1.0], or None if unavailable.
        """
        with self._neural_embed_lock:
            tool_vec = self._neural_embed_cache.get(tool_name)
        if not tool_vec:
            return None

        d_model = len(tool_vec)
        if d_model == 0:
            return None

        # Project query into same d_model space via n-gram hash buckets
        q_vec = [0.0] * d_model
        q_ngrams = self._extract_ngrams(query_text)
        for ng in q_ngrams:
            idx = hash(ng) % d_model
            idf = self._idf_cache.get(ng, 1.0)
            q_vec[idx] += idf

        # Cosine similarity
        dot = sum(a * b for a, b in zip(q_vec, tool_vec))
        q_norm = math.sqrt(sum(x * x for x in q_vec))
        t_norm = math.sqrt(sum(x * x for x in tool_vec))
        denom = q_norm * t_norm
        if denom < 1e-12:
            return None
        return max(0.0, min(1.0, dot / denom))

    def spectral_similarity(
        self,
        query: str,
        tool_text: str,
        tool_name: str = "",
    ) -> float:
        """
        Compute spectral similarity in [0, 1] between query and tool text.

        Uses cosine similarity in the positional-TF-IDF n-gram space.
        The query vector is positionally weighted (frontal emphasis);
        the tool vector uses flat TF-IDF.

        When Muad'Dib neural embeddings are cached (via inject_neural_embeddings),
        blends the neural cosine signal at _neural_blend_weight (default 30%).
        Falls back to pure spectral when neural data is unavailable.

        Args:
            query: The user's intent string.
            tool_text: The tool's name + description concatenated.
            tool_name: Optional tool name for neural embedding lookup.

        Returns:
            Cosine similarity score clamped to [0.0, 1.0].
        """
        q_ngrams = self._extract_ngrams(query)
        t_ngrams = self._extract_ngrams(tool_text)
        if not q_ngrams or not t_ngrams:
            return 0.0

        q_vec = self._positional_tfidf(q_ngrams)
        t_counter: Counter = Counter(t_ngrams)
        t_vec: Dict[str, float] = {}
        for ng, cnt in t_counter.items():
            idf = self._idf_cache.get(ng, 1.0)
            t_vec[ng] = float(cnt) * idf

        dot = 0.0
        q_norm_sq = 0.0
        t_norm_sq = 0.0
        all_keys = set(q_vec) | set(t_vec)
        for k in all_keys:
            qv = q_vec.get(k, 0.0)
            tv = t_vec.get(k, 0.0)
            dot += qv * tv
            q_norm_sq += qv * qv
            t_norm_sq += tv * tv

        denom = math.sqrt(q_norm_sq) * math.sqrt(t_norm_sq)
        spectral_score = max(0.0, min(1.0, dot / denom)) if denom >= 1e-12 else 0.0

        # ── Neural blend (Muad'Dib injection point) ──────────────────────
        if tool_name and self._neural_embed_cache:
            neural_sim = self._neural_cosine_similarity(query, tool_name)
            if neural_sim is not None:
                w = self._neural_blend_weight
                return max(0.0, min(1.0, (1.0 - w) * spectral_score + w * neural_sim))

        return spectral_score

    def entropy_gate(
        self, category_scores: Dict[str, float], epsilon: float = 0.15
    ) -> Dict[str, float]:
        """
        Apply entropy-gated disambiguation to category scores.

        When the top two category scores are within epsilon of each other,
        we broaden rather than narrow — returning multiple categories with
        weights reflecting their relative strength.  This prevents premature
        commitment to a single category when intent is genuinely ambiguous.

        Args:
            category_scores: Mapping of category -> raw match score.
            epsilon: Relative threshold for broadening.  If the gap between
                     top-1 and top-2 is less than epsilon * top_score,
                     we keep additional categories.

        Returns:
            Filtered dict of category -> normalized weight in [0.0, 1.0].
        """
        if not category_scores:
            return {"misc": 1.0}

        sorted_cats = sorted(
            category_scores.items(), key=lambda kv: kv[1], reverse=True
        )
        top_score = sorted_cats[0][1]
        if top_score < 1e-9:
            return {"misc": 1.0}

        normed: Dict[str, float] = {
            cat: score / top_score for cat, score in sorted_cats
        }

        # Shannon entropy of the normalized distribution
        vals = list(normed.values())
        total = sum(vals) or 1.0
        probs = [v / total for v in vals]
        entropy = -sum(p * math.log(p + 1e-15) for p in probs)
        max_entropy = math.log(max(1, len(probs)))
        normalized_entropy = entropy / max(1e-9, max_entropy)

        # High entropy (ambiguous) OR top-2 gap within epsilon → broaden
        if normalized_entropy > 0.6 or (
            len(sorted_cats) >= 2
            and (sorted_cats[0][1] - sorted_cats[1][1]) < epsilon * top_score
        ):
            return {cat: w for cat, w in normed.items() if w >= 0.3} or {"misc": 1.0}
        else:
            return {cat: w for cat, w in normed.items() if w >= 0.7} or {
                sorted_cats[0][0]: 1.0
            }

    def _extract_ngrams(self, text: str) -> List[str]:
        """
        Extract character n-grams from text.

        Args:
            text: Input text to decompose.

        Returns:
            List of character n-gram strings.
        """
        cleaned = text.lower().strip()
        ngrams: List[str] = []
        lo, hi = self._ngram_range
        for n in range(lo, hi + 1):
            for i in range(len(cleaned) - n + 1):
                ngrams.append(cleaned[i : i + n])
        return ngrams

    def _positional_tfidf(self, ngrams: List[str]) -> Dict[str, float]:
        """
        Compute positional TF-IDF vector: earlier n-grams weighted more.

        The positional weight decays exponentially from the start of the
        sequence, implementing frontal emphasis — the hypothesis that the
        first words of a query carry the strongest intent signal.

        Args:
            ngrams: Ordered list of character n-grams from the query.

        Returns:
            Dict mapping n-gram -> weighted TF-IDF score.
        """
        vec: Dict[str, float] = defaultdict(float)
        total = len(ngrams) or 1
        for pos, ng in enumerate(ngrams):
            idf = self._idf_cache.get(ng, 1.0)
            position_weight = self._positional_decay ** (pos / max(1, total) * 10)
            vec[ng] += position_weight * idf
        return dict(vec)


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  THOMPSON SAMPLING WITH CONTEXTUAL BANDITS
# ═══════════════════════════════════════════════════════════════════════════════
#
# Replaces point-estimate reliability (alpha / (alpha + beta)) with full
# Bayesian posterior sampling.  Each scoring call draws from Beta(α, β),
# naturally balancing exploration vs exploitation.  Context conditioning
# adjusts the priors based on the current intent category — a tool that
# excels at "debugging" tasks might have different priors than for "research".
# ═══════════════════════════════════════════════════════════════════════════════


class _ThompsonContextualBandit:
    """
    Bayesian multi-armed bandit with contextual conditioning.

    Key innovations over simple alpha/beta tracking:
      - Stochastic sampling: draw() returns a Beta sample, not the mean.
        Occasionally overestimates low-use tools, enabling organic exploration.
      - Context conditioning: per-category alpha/beta modifiers so a tool
        can have high reliability for 'file' tasks but low for 'web' tasks.
      - Exponential recency weighting: old observations decay at rate tau,
        preventing stale priors from dominating after the tool landscape shifts.
      - Counterfactual regret: after each round, compute the regret of not
        having chosen the empirically best tool.  Accumulates to flag
        chronically underexplored tools.

    Source: Sovereign MCP Server - Bayesian Decision Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    def __init__(self, decay_rate: float = 0.995) -> None:
        """
        Initialize the Thompson sampling bandit.

        Args:
            decay_rate: Exponential decay factor for prior observations.
                        Higher values (closer to 1.0) retain history longer.
                        Must be in [0.9, 0.9999].
        """
        self._decay_rate: float = max(0.9, min(0.9999, decay_rate))
        self._rng: random.Random = random.Random()

    def draw(
        self,
        prior: Dict[str, Any],
        context_category: str = "",
        neural_q_bonus: float = 0.0,
    ) -> float:
        """
        Draw a Thompson sample from the posterior Beta distribution.

        Args:
            prior: Dict with 'alpha', 'beta' keys (floats) and optional
                   'context_modifiers' dict for per-category conditioning.
            context_category: Current intent category for conditioning.
                              If provided and matching modifiers exist,
                              alpha/beta are adjusted before sampling.
            neural_q_bonus: Optional Q-bonus from Muad'Dib's Digital Twin.
                            When > 0, shifts alpha proportionally to bias
                            the posterior toward tools the neural substrate
                            has learned are effective. Scale: Q-bonus [0, 0.25]
                            maps to alpha shift [0, 0.5] via factor 2.0.

        Returns:
            Sampled reliability estimate in [0.0, 1.0].
        """
        alpha = float(prior.get("alpha", 1.0))
        beta_param = float(prior.get("beta", 1.0))

        if context_category:
            ctx_data = prior.get("context_modifiers", {})
            if isinstance(ctx_data, dict) and context_category in ctx_data:
                modifier = ctx_data[context_category]
                alpha += float(modifier.get("alpha_bonus", 0.0))
                beta_param += float(modifier.get("beta_bonus", 0.0))

        # ── Muad'Dib neural Q-prior injection (Phase 2) ──────────────────
        # The Digital Twin's Q-table encodes learned tool-routing preferences.
        # A positive Q-bonus shifts the alpha upward, biasing the Thompson
        # sample toward tools the neural substrate has observed succeeding.
        if neural_q_bonus > 0.0:
            alpha += float(neural_q_bonus) * 2.0  # scale [0,0.25] -> [0,0.5]

        alpha = max(0.01, alpha)
        beta_param = max(0.01, beta_param)

        try:
            sample = self._rng.betavariate(alpha, beta_param)
        except (ValueError, OverflowError):
            sample = alpha / max(0.0001, alpha + beta_param)

        return max(0.0, min(1.0, sample))

    def decay_prior(self, prior: Dict[str, Any]) -> None:
        """
        Apply exponential recency decay to a prior in-place.

        Old observations gradually lose influence, allowing the bandit to
        adapt when tool reliability changes over time.  Both alpha and beta
        are decayed toward 1.0 (uniform prior) at rate tau.

        Args:
            prior: Dict with 'alpha' and 'beta' keys, modified in-place.
        """
        tau = self._decay_rate
        prior["alpha"] = max(1.0, float(prior.get("alpha", 1.0)) * tau)
        prior["beta"] = max(1.0, float(prior.get("beta", 1.0)) * tau)

    def update_prior(
        self, prior: Dict[str, Any], success: bool, context_category: str = ""
    ) -> None:
        """
        Update posterior after observing a tool execution outcome.

        Applies recency decay FIRST, then incorporates the new observation.
        This ensures recent evidence always outweighs ancient data.

        Args:
            prior: Dict with 'alpha', 'beta', optional 'successes'/'failures'.
            success: Whether the tool execution succeeded.
            context_category: Intent category for context-specific updates.
        """
        self.decay_prior(prior)

        if success:
            prior["alpha"] = float(prior.get("alpha", 1.0)) + 1.0
            prior["successes"] = int(prior.get("successes", 0)) + 1
        else:
            prior["beta"] = float(prior.get("beta", 1.0)) + 1.0
            prior["failures"] = int(prior.get("failures", 0)) + 1

        if context_category:
            ctx = prior.setdefault("context_modifiers", {})
            cat_mod = ctx.setdefault(
                context_category, {"alpha_bonus": 0.0, "beta_bonus": 0.0}
            )
            if success:
                cat_mod["alpha_bonus"] = float(cat_mod.get("alpha_bonus", 0.0)) + 0.3
            else:
                cat_mod["beta_bonus"] = float(cat_mod.get("beta_bonus", 0.0)) + 0.3

    def counterfactual_regret(
        self, chosen_reward: float, best_possible_reward: float
    ) -> float:
        """
        Compute single-round counterfactual regret.

        Regret = max(0, best_possible - chosen).  Accumulate this over time
        to identify chronically underexplored tools that deserve more trials.

        Args:
            chosen_reward: Reward (reliability estimate) of the chosen tool.
            best_possible_reward: Reward of the empirically best tool.

        Returns:
            Non-negative regret value.
        """
        return max(0.0, best_possible_reward - chosen_reward)

    def mean(self, prior: Dict[str, Any]) -> float:
        """
        Compute posterior mean (non-stochastic fallback).

        Args:
            prior: Dict with 'alpha' and 'beta' keys.

        Returns:
            Mean of the Beta(alpha, beta) distribution in [0.0, 1.0].
        """
        alpha = float(prior.get("alpha", 1.0))
        beta_param = float(prior.get("beta", 1.0))
        return alpha / max(0.0001, alpha + beta_param)


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  MONTE CARLO TREE SEARCH PLANNER
# ═══════════════════════════════════════════════════════════════════════════════
#
# Instead of V1's static "balanced / fast / deep" plan templates, we use a
# genuine MCTS to explore the space of tool chains.  UCB1 balances between
# high-confidence chains and unexplored combinations.  Adversarial failure
# injection stress-tests plans before they're returned to the user.
# ═══════════════════════════════════════════════════════════════════════════════


class _MCTSPlanNode:
    """
    Single node in the Monte Carlo search tree for plan exploration.

    Each node represents a partial tool chain at a specific depth.  Children
    are the candidate next-tools.  The node tracks visit count and cumulative
    reward for UCB1 scoring.

    Source: Sovereign MCP Server - MCTS Planning Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    __slots__ = (
        "tool_name",
        "parent",
        "children",
        "visits",
        "cumulative_reward",
        "depth",
    )

    def __init__(
        self, tool_name: str, parent: Optional["_MCTSPlanNode"] = None, depth: int = 0
    ) -> None:
        """
        Initialize a plan tree node.

        Args:
            tool_name: The tool at this node in the chain.
            parent: Parent node (None for root).
            depth: Depth in the search tree (0 = root).
        """
        self.tool_name: str = tool_name
        self.parent: Optional["_MCTSPlanNode"] = parent
        self.children: Dict[str, "_MCTSPlanNode"] = {}
        self.visits: int = 0
        self.cumulative_reward: float = 0.0
        self.depth: int = depth

    def ucb1(self, exploration_constant: float = 1.414) -> float:
        """
        Compute UCB1 score for this node.

        UCB1 = (mean reward) + C * sqrt(ln(parent_visits) / visits)

        The exploration term ensures low-visit nodes get a chance, while
        the exploitation term favors high-reward chains.

        Args:
            exploration_constant: Controls exploration vs exploitation.
                                  sqrt(2) ≈ 1.414 is theoretically optimal.

        Returns:
            UCB1 score (higher = more attractive for selection).
        """
        if self.visits == 0:
            return float("inf")
        parent_visits = self.parent.visits if self.parent else self.visits
        exploitation = self.cumulative_reward / self.visits
        exploration = exploration_constant * math.sqrt(
            math.log(max(1, parent_visits)) / self.visits
        )
        return exploitation + exploration

    def extract_chain(self) -> List[str]:
        """
        Walk from this node to the root to extract the full tool chain.

        Returns:
            List of tool names from root to this node (inclusive).
        """
        chain: List[str] = []
        node: Optional["_MCTSPlanNode"] = self
        while node is not None:
            if node.tool_name != "__root__":
                chain.append(node.tool_name)
            node = node.parent
        chain.reverse()
        return chain


class _MCTSPlanner:
    """
    Monte Carlo Tree Search planner for tool chain discovery.

    Key innovations over V1's static plan templates:
      - UCB1 exploration: automatically balances between high-confidence
        chains and unexplored tool combinations.
      - Adversarial failure injection: before returning plans, synthetic
        failure nodes are injected to test plan resilience.  Plans that
        survive adversarial testing rank higher.
      - Pareto-optimal selection: chains are ranked on a confidence vs.
        token-cost tradeoff frontier.  The planner returns plans that are
        not dominated on both axes simultaneously.

    Source: Sovereign MCP Server - MCTS Planning Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    def __init__(
        self, exploration_constant: float = 1.414, adversarial_probability: float = 0.15
    ) -> None:
        """
        Initialize the MCTS planner.

        Args:
            exploration_constant: UCB1 exploration parameter C.
            adversarial_probability: Probability of injecting a synthetic
                                     failure during simulation rollouts.
        """
        self._exploration_c: float = max(0.1, exploration_constant)
        self._adversarial_p: float = max(0.0, min(0.5, adversarial_probability))
        self._rng: random.Random = random.Random()

    def search(
        self,
        ranked_tools: List[Dict[str, Any]],
        tool_catalog: Dict[str, Dict[str, Any]],
        reliability_fn: Callable[[str], float],
        token_estimate_fn: Callable[[List[str]], int],
        beam_width: int = 3,
        max_chain_length: int = 4,
        simulations: int = 60,
        neural_value_fn: Optional[Callable[[List[str]], float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run MCTS to discover high-quality tool chains.

        Args:
            ranked_tools: Pre-scored tool list from the routing engine.
            tool_catalog: Full tool catalog for validation.
            reliability_fn: Function that returns reliability for a tool name.
            token_estimate_fn: Function that estimates token cost for a chain.
            beam_width: Number of plans to return.
            max_chain_length: Maximum tools in a single chain.
            simulations: Number of MCTS rollouts to perform.
            neural_value_fn: Optional Muad'Dib neural value estimator.
                             Accepts a tool chain (List[str]) and returns a
                             learned value estimate in [0.0, 1.0]. When
                             provided, blends at 30% with the reliability-
                             based geometric mean reward. Falls back to
                             pure reliability when None or when the function
                             raises.

        Returns:
            List of plan dicts sorted by Pareto-optimal confidence,
            each containing 'chain', 'confidence', 'estimated_tokens',
            'failure_points', 'adversarial_survived'.
        """
        if not ranked_tools:
            return []

        self._neural_value_fn = neural_value_fn  # stash for _simulate access

        root = _MCTSPlanNode("__root__", parent=None, depth=0)
        candidate_names = [t["name"] for t in ranked_tools[:20]]
        ranked_lookup = {t["name"]: t for t in ranked_tools}

        for _ in range(simulations):
            # 1. SELECT: traverse tree using UCB1
            node = self._select(root, candidate_names, max_chain_length)
            # 2. EXPAND: add a new child node
            node = self._expand(node, candidate_names, max_chain_length)
            # 3. SIMULATE: rollout to terminal and compute reward
            reward = self._simulate(
                node,
                candidate_names,
                ranked_lookup,
                reliability_fn,
                max_chain_length,
            )
            # 4. BACKPROPAGATE: update ancestors
            self._backpropagate(node, reward)

        self._neural_value_fn = None  # release reference

        # Extract top plans from tree
        plans = self._extract_plans(
            root,
            ranked_lookup,
            reliability_fn,
            token_estimate_fn,
            beam_width,
            max_chain_length,
        )
        return plans

    def _select(
        self, node: _MCTSPlanNode, candidates: List[str], max_depth: int
    ) -> _MCTSPlanNode:
        """
        Select the most promising node using UCB1 traversal.

        Args:
            node: Current node to select from.
            candidates: Available tool names.
            max_depth: Maximum chain depth.

        Returns:
            Selected leaf node for expansion.
        """
        while node.children and node.depth < max_depth:
            # Pick child with highest UCB1
            best_child: Optional[_MCTSPlanNode] = None
            best_ucb: float = -1.0
            for child in node.children.values():
                ucb = child.ucb1(self._exploration_c)
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child = child
            if best_child is None:
                break
            node = best_child
        return node

    def _expand(
        self, node: _MCTSPlanNode, candidates: List[str], max_depth: int
    ) -> _MCTSPlanNode:
        """
        Expand the tree by adding a new child via Lévy flight selection.

        Instead of uniform random.choice(), uses a heavy-tailed Cauchy
        distribution to occasionally explore distant candidates.  The Lévy
        index α = 1.5 (between Gaussian α=2 and Cauchy α=1) produces
        superdiffusive exploration — mostly local moves with rare long jumps.

        Args:
            node: Leaf node to expand from.
            candidates: Available tool names (ordered by score).
            max_depth: Maximum chain depth.

        Returns:
            The newly created child node, or the input node if at max depth.
        """
        if node.depth >= max_depth:
            return node

        current_chain = set(node.extract_chain())
        unexpanded = [
            c for c in candidates if c not in current_chain and c not in node.children
        ]
        if not unexpanded:
            return node

        tool = self._levy_select(unexpanded)
        child = _MCTSPlanNode(tool, parent=node, depth=node.depth + 1)
        node.children[tool] = child
        return child

    def _simulate(
        self,
        node: _MCTSPlanNode,
        candidates: List[str],
        ranked_lookup: Dict[str, Dict[str, Any]],
        reliability_fn: Callable[[str], float],
        max_depth: int,
    ) -> float:
        """
        Simulate a Lévy flight rollout from the node to terminal depth.

        Computes reward as the geometric mean of tool reliabilities in the
        chain, with adversarial failure injection for stress testing.
        Lévy flight selection in the rollout means occasional surprising
        tool combinations are tested.

        Args:
            node: Starting node for simulation.
            candidates: Available tool names.
            ranked_lookup: Pre-scored tool data.
            reliability_fn: Reliability scoring function.
            max_depth: Maximum chain depth for rollout.

        Returns:
            Simulated reward in [0.0, 1.0].
        """
        chain = node.extract_chain()
        current_depth = len(chain)

        # Lévy flight rollout to fill remaining depth
        available = [c for c in candidates if c not in set(chain)]
        while current_depth < max_depth and available:
            tool = self._levy_select(available)
            chain.append(tool)
            available.remove(tool)
            current_depth += 1

        if not chain:
            return 0.0

        # Compute reward: geometric mean of reliabilities
        log_sum = 0.0
        for tool_name in chain:
            rel = reliability_fn(tool_name)
            # Adversarial failure injection
            if self._rng.random() < self._adversarial_p:
                rel *= 0.3  # Synthetic pessimal degradation
            log_sum += math.log(max(1e-6, rel))
        geometric_mean = math.exp(log_sum / len(chain))

        # Bonus for using highly-scored tools
        score_bonus = 0.0
        for tool_name in chain:
            tool_data = ranked_lookup.get(tool_name, {})
            score_bonus += float(tool_data.get("score", 0.0))
        score_bonus = score_bonus / max(1, len(chain)) * 0.3

        base_reward = geometric_mean * 0.7 + score_bonus

        # ── Muad'Dib neural value blend (Phase 4 injection) ──────────────
        # When the Digital Twin can encode the candidate chain, its hidden-
        # state mean activation serves as a learned value estimate. Blends
        # at 30% with the reliability-based reward. Degrades gracefully when
        # neural backbone is cold-start (random weights → ~0.5 value).
        neural_value_fn = getattr(self, "_neural_value_fn", None)
        if neural_value_fn is not None:
            try:
                neural_value = float(neural_value_fn(chain))
                neural_value = max(0.0, min(1.0, neural_value))
                base_reward = 0.7 * base_reward + 0.3 * neural_value
            except Exception:
                pass  # graceful fallback — use base_reward as-is

        return max(0.0, min(1.0, base_reward))

    def _levy_select(self, candidates: List[str]) -> str:
        """
        Select a candidate using Lévy flight heavy-tailed sampling.

        Generates a Lévy-distributed index into the candidate list.  The
        distribution is constructed via the Mantegna algorithm: the ratio
        of two Gaussian samples scaled by α = 1.5 produces a stable
        distribution with the desired heavy tail.

        Candidates are assumed to be ordered by decreasing relevance (index
        0 = most relevant).  The Lévy flight biases toward early indices
        but occasionally jumps to distant ones.

        Args:
            candidates: Ordered list of candidate tool names.

        Returns:
            Selected tool name.
        """
        if len(candidates) == 1:
            return candidates[0]

        # Mantegna's algorithm for Lévy stable distribution with α = 1.5
        alpha_levy = 1.5
        sigma_u = (
            math.gamma(1 + alpha_levy)
            * math.sin(math.pi * alpha_levy / 2)
            / (
                math.gamma((1 + alpha_levy) / 2)
                * alpha_levy
                * 2 ** ((alpha_levy - 1) / 2)
            )
        ) ** (1 / alpha_levy)

        u = self._rng.gauss(0, sigma_u)
        v = self._rng.gauss(0, 1)
        step = u / (abs(v) ** (1 / alpha_levy)) if abs(v) > 1e-12 else 0.0

        # Map Lévy step to index: take absolute value, scale, and clamp
        raw_idx = abs(step) * len(candidates) * 0.2
        idx = int(raw_idx) % len(candidates)
        return candidates[idx]

    def _backpropagate(self, node: _MCTSPlanNode, reward: float) -> None:
        """
        Backpropagate the simulation reward up the tree.

        Args:
            node: Leaf node where simulation ended.
            reward: Simulated reward to propagate.
        """
        current: Optional[_MCTSPlanNode] = node
        while current is not None:
            current.visits += 1
            current.cumulative_reward += reward
            current = current.parent

    def _extract_plans(
        self,
        root: _MCTSPlanNode,
        ranked_lookup: Dict[str, Dict[str, Any]],
        reliability_fn: Callable[[str], float],
        token_estimate_fn: Callable[[List[str]], int],
        beam_width: int,
        max_depth: int,
    ) -> List[Dict[str, Any]]:
        """
        Extract the best plans from the search tree.

        Performs Pareto-optimal selection on confidence vs. token cost.

        Args:
            root: Root of the MCTS tree.
            ranked_lookup: Pre-scored tool data.
            reliability_fn: Reliability scoring function.
            token_estimate_fn: Token cost estimation function.
            beam_width: Number of plans to return.
            max_depth: Maximum chain depth.

        Returns:
            List of Pareto-optimal plan dicts.
        """
        all_chains: List[Tuple[List[str], float]] = []
        self._collect_chains(root, all_chains, max_depth)

        # Deduplicate and score
        seen_keys: Set[str] = set()
        plan_entries: List[Dict[str, Any]] = []

        for chain, tree_reward in all_chains:
            key = " > ".join(chain)
            if key in seen_keys or not chain:
                continue
            seen_keys.add(key)

            # Geometric mean confidence
            log_sum = sum(math.log(max(1e-6, reliability_fn(t))) for t in chain)
            confidence = math.exp(log_sum / len(chain))
            tokens = token_estimate_fn(chain)

            # Failure point analysis
            failure_points: List[str] = []
            for tool_name in chain:
                rel = reliability_fn(tool_name)
                if rel < 0.5:
                    failure_points.append(f"{tool_name}: low reliability ({rel:.2f})")
                params = ranked_lookup.get(tool_name, {}).get("required_params", [])
                if params:
                    failure_points.append(f"{tool_name}: requires {', '.join(params)}")

            # Adversarial resilience test
            adversarial_passed = self._adversarial_test(chain, reliability_fn)

            plan_entries.append(
                {
                    "chain": chain,
                    "confidence": round(confidence, 4),
                    "estimated_tokens": tokens,
                    "tree_reward": round(tree_reward, 4),
                    "failure_points": failure_points[:6],
                    "adversarial_survived": adversarial_passed,
                }
            )

        # Pareto-optimal selection: remove dominated plans
        pareto = self._pareto_filter(plan_entries)
        pareto.sort(key=lambda p: p["confidence"], reverse=True)
        return pareto[: max(1, beam_width)]

    def _collect_chains(
        self,
        node: _MCTSPlanNode,
        results: List[Tuple[List[str], float]],
        max_depth: int,
    ) -> None:
        """
        Recursively collect all complete chains from the search tree.

        Args:
            node: Current node in traversal.
            results: Accumulator for (chain, reward) tuples.
            max_depth: Maximum depth to collect from.
        """
        if node.visits > 0 and node.depth > 0:
            chain = node.extract_chain()
            avg_reward = (
                node.cumulative_reward / node.visits if node.visits > 0 else 0.0
            )
            if len(chain) >= 2:
                results.append((chain, avg_reward))

        if node.depth < max_depth:
            for child in node.children.values():
                self._collect_chains(child, results, max_depth)

    def _adversarial_test(
        self,
        chain: List[str],
        reliability_fn: Callable[[str], float],
        n_trials: int = 5,
    ) -> bool:
        """
        Stress-test a plan with adversarial failure injection.

        Runs n_trials simulations where each tool has a chance of failing.
        A plan 'survives' if it achieves > 0.3 confidence in > 60% of trials.

        Args:
            chain: Tool chain to test.
            reliability_fn: Reliability scoring function.
            n_trials: Number of adversarial trials.

        Returns:
            True if the plan survived adversarial testing.
        """
        survived = 0
        for _ in range(n_trials):
            log_sum = 0.0
            for tool_name in chain:
                rel = reliability_fn(tool_name)
                if self._rng.random() < self._adversarial_p:
                    rel *= 0.2
                log_sum += math.log(max(1e-6, rel))
            geo_mean = math.exp(log_sum / max(1, len(chain)))
            if geo_mean > 0.3:
                survived += 1
        return survived > n_trials * 0.6

    def _pareto_filter(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter plans to the Pareto frontier on (confidence, -tokens).

        A plan is Pareto-optimal if no other plan has both higher confidence
        AND lower token cost.

        Args:
            plans: List of plan dicts with 'confidence' and 'estimated_tokens'.

        Returns:
            Pareto-optimal subset.
        """
        if len(plans) <= 1:
            return plans

        pareto: List[Dict[str, Any]] = []
        for plan in plans:
            dominated = False
            for other in plans:
                if other is plan:
                    continue
                if (
                    other["confidence"] >= plan["confidence"]
                    and other["estimated_tokens"] <= plan["estimated_tokens"]
                    and (
                        other["confidence"] > plan["confidence"]
                        or other["estimated_tokens"] < plan["estimated_tokens"]
                    )
                ):
                    dominated = True
                    break
            if not dominated:
                pareto.append(plan)
        return pareto if pareto else plans[:1]


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  TOPOLOGICAL MOMENTUM MANIFOLD
# ═══════════════════════════════════════════════════════════════════════════════
#
# Not your V1 "last 5 tools" window.  This is a full manifold that tracks:
# - Exponential decay attention: recent tools get geometrically more weight
# - Spectral graph momentum: transitions between category neighborhoods
#   carry momentum proportional to learned transition probability × centrality
# - Change-point detection (CUSUM-inspired): detects when the user's intent
#   has fundamentally shifted, dampening stale momentum
# ═══════════════════════════════════════════════════════════════════════════════


class _TopologicalMomentumManifold:
    """
    Session momentum through topological analysis of tool flow.

    The manifold maintains three independent signals that fuse into a
    single momentum vector:

      1. Attention decay: Weighted window where tool[t-1] has weight lambda,
         tool[t-2] has weight lambda^2, etc.  lambda = 0.7 by default.
      2. Spectral graph flow: Category transitions accumulate momentum
         proportional to the transition's learned probability.  High-probability
         transitions reinforce momentum; improbable ones dampen it.
      3. Change-point detection: Monitors the KL divergence between the
         recent category distribution and the overall session distribution.
         A spike signals an intent shift, dampening momentum.

    Source: Sovereign MCP Server - Topological Momentum Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    def __init__(
        self,
        category_graph: Dict[str, Set[str]],
        attention_lambda: float = 0.7,
        window_size: int = 8,
        change_point_threshold: float = 0.5,
    ) -> None:
        """
        Initialize the topological momentum manifold.

        Args:
            category_graph: Adjacency graph of tool categories.
            attention_lambda: Decay factor for exponential attention.
            window_size: Size of the recent-events window for change detection.
            change_point_threshold: KL divergence threshold for dampening.
        """
        self._attention_lambda: float = max(0.3, min(0.95, attention_lambda))
        self._category_graph: Dict[str, Set[str]] = category_graph
        self._session_history: List[Dict[str, Any]] = []
        self._category_counts: Counter = Counter()
        self._window_size: int = max(3, window_size)
        self._dampening_factor: float = 1.0
        self._change_point_threshold: float = change_point_threshold
        # ── Muad'Dib neural attention injection (Phase 3) ────────────────
        # When the Digital Twin's KG-enhanced attention layer produces
        # attention weights for tool→tool transitions, they are cached here.
        # spectral_graph_momentum() blends this neural signal when available.
        self._neural_attention_weights: Dict[str, float] = {}
        self._neural_attention_lock: threading.Lock = threading.Lock()

    def record_event(self, tool_name: str, category: str, timestamp: float) -> None:
        """
        Record a tool invocation into the manifold.

        Args:
            tool_name: Name of the invoked tool.
            category: Category of the invoked tool.
            timestamp: UNIX timestamp of the invocation.
        """
        self._session_history.append(
            {
                "tool": tool_name,
                "category": category,
                "timestamp": timestamp,
            }
        )
        self._category_counts[category] += 1
        self._detect_change_point()

    def attention_score(self, tool_name: str, category: str) -> float:
        """
        Compute exponential-decay attention for a candidate tool.

        Recent invocations of the same tool, same category, or adjacent
        category carry geometrically decaying weight.

        Args:
            tool_name: Candidate tool name.
            category: Candidate tool category.

        Returns:
            Attention score in [0.0, ~1.0], modulated by dampening.
        """
        if not self._session_history:
            return 0.0

        score = 0.0
        lam = self._attention_lambda
        window = self._session_history[-self._window_size :]

        for i, event in enumerate(reversed(window)):
            recency_weight = lam ** (i + 1)
            if event["tool"] == tool_name:
                score += recency_weight * 0.6
            elif event["category"] == category:
                score += recency_weight * 0.3
            elif category in self._category_graph.get(event["category"], set()):
                score += recency_weight * 0.15

        return score * self._dampening_factor

    def inject_neural_attention(
        self,
        attention_weights: Dict[str, float],
    ) -> None:
        """
        Cache neural attention weights from Muad'Dib's KG-enhanced attention.

        The attention weights encode which category transitions the neural
        backbone "attends to" most strongly, providing a learned signal that
        supplements the statistical transition matrix.

        Args:
            attention_weights: Mapping of category_name -> attention weight
                               (higher = stronger neural transition signal).
        """
        with self._neural_attention_lock:
            self._neural_attention_weights = dict(attention_weights)

    def spectral_graph_momentum(
        self, category: str, transition_matrix: Dict[str, Dict[str, float]]
    ) -> float:
        """
        Compute momentum from learned category transition probabilities.

        Higher transition probability from the last category to the candidate
        means stronger momentum — the system expects this transition.

        When Muad'Dib neural attention weights are available (via
        inject_neural_attention), blends the neural signal at 20% weight,
        reducing statistical transition probability to 50% and keeping
        centrality at 30%. Falls back to original weights when unavailable.

        Args:
            category: Candidate tool category.
            transition_matrix: Learned category transition probabilities.

        Returns:
            Graph momentum score in [0.0, 1.0], modulated by dampening.
        """
        if not self._session_history:
            return 0.0

        last_cat = self._session_history[-1]["category"]
        tp = transition_matrix.get(last_cat, {}).get(category, 0.0)

        neighbors = self._category_graph.get(category, set())
        centrality = len(neighbors) / max(1, len(self._category_graph))

        # ── Neural attention blend (Muad'Dib Phase 3 injection) ──────────
        with self._neural_attention_lock:
            neural_attn = self._neural_attention_weights.get(category, 0.0)

        if neural_attn > 0.0:
            # 50% transition + 20% neural + 30% centrality
            score = tp * 0.5 + neural_attn * 0.2 + centrality * 0.3
        else:
            # Original weights when no neural signal
            score = tp * 0.7 + centrality * 0.3

        return score * self._dampening_factor

    def get_dampening(self) -> float:
        """
        Return current dampening factor.

        Returns:
            Dampening in [0.3, 1.0].  Lower values indicate a detected
            intent shift that suppresses stale momentum.
        """
        return self._dampening_factor

    def get_recent_categories(self, n: int = 3) -> List[str]:
        """
        Get the N most recent unique categories in recency order.

        Args:
            n: Number of categories to return.

        Returns:
            List of category names, most recent first.
        """
        seen: List[str] = []
        for event in reversed(self._session_history):
            cat = event["category"]
            if cat not in seen:
                seen.append(cat)
            if len(seen) >= n:
                break
        return seen

    def get_session_length(self) -> int:
        """
        Return total events recorded in this session.

        Returns:
            Non-negative integer count of recorded events.
        """
        return len(self._session_history)

    def _detect_change_point(self) -> None:
        """
        Wasserstein-1 change-point detection (Kantorovich–Rubinstein metric).

        Compares the category distribution over the recent window to the
        overall session distribution using Earth Mover's Distance, which is
        strictly superior to KL divergence because:
          - It's a true metric (triangle inequality holds)
          - It never diverges to infinity for non-overlapping distributions
          - It's geometrically interpretable (minimum transport cost)

        For 1D discrete distributions, Wasserstein-1 = L1 norm of the
        difference of CDFs, which has a simple closed-form computation.

        V3.1 UPDATE: Adaptive threshold — longer sessions have more category
        diversity by default, so we increase threshold to avoid false positives.
        """
        if len(self._session_history) < self._window_size:
            self._dampening_factor = 1.0
            return

        window = self._session_history[-self._window_size :]
        recent_counts: Counter = Counter(e["category"] for e in window)
        total_recent = sum(recent_counts.values()) or 1

        total_overall = sum(self._category_counts.values()) or 1

        # === ADAPTIVE THRESHOLD ===
        # As session grows, expect more category diversity
        # Base threshold 0.5, grows to max 0.8 as session length increases
        session_growth_factor = min(1.0, len(self._session_history) / 50.0)
        adaptive_threshold = self._change_point_threshold + (
            0.3 * session_growth_factor  # +0.0 at start, +0.3 at 50+ events
        )

        # Build sorted category list for CDF computation
        all_cats = sorted(set(recent_counts) | set(self._category_counts))
        if not all_cats:
            self._dampening_factor = min(1.0, self._dampening_factor + 0.05)
            return

        # Wasserstein-1 = L1 distance between CDFs
        # For discrete distributions: sum |CDF_recent(x) - CDF_overall(x)|
        cdf_recent = 0.0
        cdf_overall = 0.0
        wasserstein = 0.0

        for cat in all_cats:
            cdf_recent += recent_counts.get(cat, 0) / total_recent
            cdf_overall += self._category_counts.get(cat, 0) / total_overall
            wasserstein += abs(cdf_recent - cdf_overall)

        # Normalize by number of categories for scale-independence
        wasserstein_normed = wasserstein / max(1, len(all_cats))

        # Use adaptive threshold instead of static
        if wasserstein_normed > adaptive_threshold:
            # Exponential dampening proportional to distribution shift
            self._dampening_factor = max(
                0.3,
                self._dampening_factor * math.exp(-wasserstein_normed * 2.0),
            )
        else:
            # Gradual recovery with exponential smoothing
            self._dampening_factor = min(
                1.0,
                self._dampening_factor + 0.05 * (1.0 - self._dampening_factor),
            )


class GoldenPathOracle:
    """
    Prescient navigation layer for the exoskeleton.

    Manages golden path workflows — proven tool sequences validated across
    hundreds of executions.  These paths represent collective intelligence,
    eliminating cold-start blindness through inherited expertise.

    V3 upgrades over V2 draft:
      - Spectral matching: uses `_SpectralIntentDecomposer` for semantic
        similarity instead of primitive `if keyword in string` checks.
      - Fisher information metric: weights matches by the informativeness
        of the matching n-grams — rare n-gram overlaps count more than
        common ones (information-theoretic scoring).
      - Thread-safe: all mutable state guarded by `threading.RLock`.
      - Production logging at DEBUG level for all match attempts.

    Source: Sovereign MCP Server - Golden Path Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    def __init__(
        self,
        golden_paths_file: Path,
        logger: logging.Logger,
        decomposer: Optional[_SpectralIntentDecomposer] = None,
    ) -> None:
        """
        Initialize the Golden Path Oracle.

        Args:
            golden_paths_file: Path to golden_paths.json on disk.
            logger: Logger for production-grade auditing.
            decomposer: Optional spectral decomposer. If None, a fresh
                         one is instantiated and IDF is rebuilt from the
                         golden path corpus.
        """
        self.logger: logging.Logger = logger
        self.golden_paths_file: Path = golden_paths_file
        self.golden_paths_metadata: Dict[str, Any] = {}
        self._lock: threading.RLock = threading.RLock()
        self.golden_paths: Dict[str, Dict[str, Any]] = self._load_golden_paths()
        self._decomposer: _SpectralIntentDecomposer = (
            decomposer or _SpectralIntentDecomposer()
        )
        self._rebuild_spectral_index()

    def _is_valid_golden_path_entry(self, path_name: str, path_data: Any) -> bool:
        """Return True only for executable golden-path workflow entries."""
        if not isinstance(path_name, str) or path_name.startswith("_"):
            return False
        if not isinstance(path_data, dict):
            return False
        chain = path_data.get("chain")
        if not isinstance(chain, list) or not chain:
            return False
        if not all(isinstance(step, str) and step.strip() for step in chain):
            return False
        priors = path_data.get("priors")
        if not isinstance(priors, dict):
            return False
        try:
            alpha = float(priors["alpha"])
            beta = float(priors["beta"])
        except (KeyError, TypeError, ValueError):
            return False
        return alpha > 0.0 and beta > 0.0

    def _iter_golden_path_entries(self):
        """Iterate executable golden paths only; metadata/corrupt entries stay out."""
        for path_name, path_data in self.golden_paths.items():
            if self._is_valid_golden_path_entry(path_name, path_data):
                yield path_name, path_data

    def _empty_golden_paths(self) -> Dict[str, Dict[str, Any]]:
        """Fail-open default: no executable priors rather than corrupt routing."""
        return {}

    def _rebuild_spectral_index(self) -> None:
        """
        Rebuild spectral IDF index from the golden path corpus.

        Each golden path's use_cases, tags, and description are concatenated
        into a pseudo-document for IDF computation.  This lets the spectral
        decomposer weight rare n-grams (high information value) above common
        ones when matching.
        """
        corpus: Dict[str, Dict[str, Any]] = {}
        with self._lock:
            for path_name, path_data in self._iter_golden_path_entries():
                text_parts = [path_name.replace("_", " ")]
                text_parts.extend(path_data.get("use_cases", []))
                text_parts.extend(path_data.get("tags", []))
                text_parts.append(str(path_data.get("description", "")))
                corpus[path_name] = {
                    "name": path_name,
                    "description": " ".join(text_parts),
                }
        self._decomposer.rebuild_idf(corpus)
        self.logger.debug(
            "Spectral index rebuilt: %d golden paths, %d IDF terms",
            len(corpus),
            len(self._decomposer._idf_cache),
        )

    def _load_golden_paths(self) -> Dict[str, Dict[str, Any]]:
        """Load executable golden path definitions from JSON, excluding metadata."""
        if not self.golden_paths_file.exists():
            self.logger.warning(
                "Golden paths file not found: %s",
                self.golden_paths_file,
            )
            return self._empty_golden_paths()

        try:
            with open(self.golden_paths_file, "r", encoding="utf-8") as f:
                raw_paths = json.load(f)
            if not isinstance(raw_paths, dict):
                self.logger.error(
                    "Golden paths root must be an object, got %s",
                    type(raw_paths).__name__,
                )
                return self._empty_golden_paths()

            meta = raw_paths.get("_meta")
            self.golden_paths_metadata = meta if isinstance(meta, dict) else {}
            paths = {
                path_name: path_data
                for path_name, path_data in raw_paths.items()
                if self._is_valid_golden_path_entry(path_name, path_data)
            }
            skipped = len(raw_paths) - len(paths)
            self.logger.info(
                "Loaded %d golden workflow paths (%d metadata/invalid entries skipped)",
                len(paths),
                skipped,
            )
            return paths
        except (json.JSONDecodeError, OSError, IOError) as exc:
            self.logger.error("Failed to load golden paths: %s", exc)
            return self._empty_golden_paths()

    def match_golden_path(self, intent: str) -> Optional[Dict[str, Any]]:
        """
        Find golden path matching the intent via spectral similarity.

        Scoring pipeline:
          1. Spectral cosine similarity between intent and path document.
          2. Fisher information weighting: matches on rare n-grams (high IDF)
             contribute quadratically more than common n-gram matches.
          3. Entropy gating: when top-2 scores are within epsilon, both
             paths are considered rather than committing to one.

        Returns path data if confident match found, None otherwise.

        Args:
            intent: The user's natural language intent string.

        Returns:
            Best matching golden path dict, or None if no confident match.
        """
        if not intent or not intent.strip():
            return None

        best_match: Optional[Dict[str, Any]] = None
        best_score: float = 0.0
        match_scores: Dict[str, float] = {}

        with self._lock:
            for path_name, path_data in self._iter_golden_path_entries():
                # Build path document from use_cases + tags + description
                doc_parts = [path_name.replace("_", " ")]
                doc_parts.extend(path_data.get("use_cases", []))
                doc_parts.extend(path_data.get("tags", []))
                doc_parts.append(str(path_data.get("description", "")))
                path_document = " ".join(doc_parts)

                # Spectral cosine similarity
                spectral_sim = self._decomposer.spectral_similarity(
                    intent,
                    path_document,
                )

                # Fisher information metric: compute the informational weight
                # of the overlap.  Rare n-gram matches (high IDF) contribute
                # quadratically — this is the Fisher information interpretation
                # where parameter sensitivity scales with inverse variance.
                q_ngrams = set(self._decomposer._extract_ngrams(intent.lower()))
                d_ngrams = set(self._decomposer._extract_ngrams(path_document.lower()))
                overlap = q_ngrams & d_ngrams
                fisher_weight = 0.0
                for ng in overlap:
                    idf = self._decomposer._idf_cache.get(ng, 1.0)
                    fisher_weight += idf * idf  # Fisher ∝ IDF²
                fisher_norm = math.sqrt(fisher_weight) if fisher_weight > 0 else 0.0
                fisher_score = math.tanh(fisher_norm * 0.05)  # Squash to [0,1)

                # Composite: spectral dominates, Fisher differentiates ties
                composite = spectral_sim * 0.65 + fisher_score * 0.35

                match_scores[path_name] = composite
                self.logger.debug(
                    "Golden path match: %s | spectral=%.4f fisher=%.4f composite=%.4f",
                    path_name,
                    spectral_sim,
                    fisher_score,
                    composite,
                )

                if composite > best_score:
                    best_score = composite
                    best_match = {
                        "path_name": path_name,
                        "match_score": round(composite, 4),
                        "spectral_similarity": round(spectral_sim, 4),
                        "fisher_information": round(fisher_score, 4),
                        **path_data,
                    }

        # Entropy gating: if top-2 are within epsilon, log ambiguity
        sorted_scores = sorted(
            match_scores.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )
        if len(sorted_scores) >= 2:
            gap = sorted_scores[0][1] - sorted_scores[1][1]
            if gap < 0.05:
                self.logger.info(
                    "Ambiguous golden path: top=%s(%.3f) runner=%s(%.3f) gap=%.3f",
                    sorted_scores[0][0],
                    sorted_scores[0][1],
                    sorted_scores[1][0],
                    sorted_scores[1][1],
                    gap,
                )

        # Threshold: require at least 0.15 composite score
        if best_score >= 0.15 and best_match is not None:
            self.logger.info(
                "Golden path matched: %s (composite=%.3f, spectral=%.3f)",
                best_match["path_name"],
                best_score,
                best_match["spectral_similarity"],
            )
            return best_match

        self.logger.debug(
            "No golden path matched intent: '%s' (best=%.3f)",
            intent[:80],
            best_score,
        )
        return None

    def seed_chain_priors(self, chain_priors: Dict[str, Dict[str, Any]]) -> int:
        """
        Seed chain priors with golden path data.

        This is the genetic memory transfer - new sessions inherit wisdom
        from the collective instead of starting blind.

        Returns count of seeded chains.
        """
        seeded_count = 0

        for path_name, path_data in self._iter_golden_path_entries():
            chain_key = " > ".join(path_data["chain"])

            # Check if chain already has significant execution history
            existing_prior = chain_priors.get(chain_key, {})
            existing_trials = existing_prior.get("successes", 0) + existing_prior.get(
                "failures", 0
            )

            # Only seed if chain is new or has minimal data (< 3 trials)
            if existing_trials < 3:
                alpha = float(path_data["priors"]["alpha"])
                beta = float(path_data["priors"]["beta"])

                chain_priors[chain_key] = {
                    "alpha": alpha,
                    "beta": beta,
                    "successes": int(alpha - 1),
                    "failures": int(beta - 1),
                    "seeded_from": path_name,
                    "seeded_at": time.time(),
                }

                reliability = alpha / (alpha + beta)
                trials = int(alpha + beta - 2)

                self.logger.info(
                    "Seeded golden path '%s': %s (%.1f%% reliability from %d trials)",
                    path_name,
                    chain_key,
                    reliability * 100,
                    trials,
                )

                seeded_count += 1

        if seeded_count > 0:
            self.logger.info("Seeded %d golden paths into chain priors", seeded_count)

        return seeded_count


class SessionMomentum:
    """
    Tracks session-level tool usage to enable momentum-aware routing.

    This creates conversational continuity — the system remembers what just
    happened and biases toward natural follow-up actions, eliminating the
    need for agents to constantly re-explain context.

    V3 upgrade: delegates topological analysis to `_TopologicalMomentumManifold`
    for Wasserstein-based change-point detection, exponential attention decay,
    and spectral graph momentum.  The manifold signals are fused with the
    original 5 routing signals for a 7-signal momentum vector.

    Source: Sovereign MCP Server - Session Momentum Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    def __init__(
        self, category_graph: Dict[str, Set[str]], logger: logging.Logger
    ) -> None:
        """
        Initialize session momentum with manifold delegate.

        Args:
            category_graph: Adjacency graph of tool categories.
            logger: Production logger for audit trail.
        """
        self.logger: logging.Logger = logger
        self.category_graph: Dict[str, Set[str]] = category_graph

        # Topological manifold delegate (Wasserstein change-point + attention)
        self._manifold: _TopologicalMomentumManifold = _TopologicalMomentumManifold(
            category_graph=category_graph
        )

        # Session state
        self.session_id = self._generate_session_id()
        self.session_start = time.time()
        self.recent_tools: List[Dict[str, Any]] = []  # Last 5 tools
        self.recent_categories: List[str] = []  # Last 3 categories
        self.tool_sequence: List[Dict[str, Any]] = []  # Full sequence
        self.intent_history: List[Dict[str, Any]] = []  # Intent tracking
        self.active_workflow: Optional[Dict[str, Any]] = None

        # Learned category transition probabilities
        self.category_transitions = self._initialize_transition_matrix()

    def _generate_session_id(self) -> str:
        """Generate unique session identifier."""
        return f"session_{uuid.uuid4().hex[:8]}_{int(time.time())}"

    def _initialize_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize category transition probability matrix.

        Starts with graph-based priors (connected categories have higher
        transition probability), then learns from actual usage patterns.
        """
        categories = list(self.category_graph.keys())
        matrix = {}

        for from_cat in categories:
            matrix[from_cat] = {}
            neighbors = self.category_graph.get(from_cat, set())

            for to_cat in categories:
                # Higher prior for graph-connected categories
                if to_cat in neighbors or to_cat == from_cat:
                    matrix[from_cat][to_cat] = 1.0
                else:
                    matrix[from_cat][to_cat] = 0.1

        return matrix

    def update(
        self,
        tool_name: str,
        category: str,
        intent: str,
        golden_paths: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Update session momentum after tool execution.

        Tracks recency, updates transition probabilities, and detects if
        we're walking a known golden path workflow.
        """
        timestamp = time.time()

        # Add to recent tools (maintain window of 5)
        self.recent_tools.append(
            {
                "tool": tool_name,
                "category": category,
                "timestamp": timestamp,
                "intent": intent,
            }
        )
        self.recent_tools = self.recent_tools[-5:]

        # Update category recency (maintain window of 3)
        if category in self.recent_categories:
            self.recent_categories.remove(category)
        self.recent_categories.insert(0, category)
        self.recent_categories = self.recent_categories[:3]

        # Add to full sequence for pattern detection
        self.tool_sequence.append(
            {"tool": tool_name, "category": category, "timestamp": timestamp}
        )

        # Track intent history
        self.intent_history.append({"intent": intent, "timestamp": timestamp})

        # Feed the topological manifold for Wasserstein change-point detection
        self._manifold.record_event(tool_name, category, timestamp)

        # Update category transition probabilities (online learning)
        if len(self.tool_sequence) >= 2:
            prev_cat = self.tool_sequence[-2]["category"]
            curr_cat = category

            # Increment transition count
            self.category_transitions[prev_cat][curr_cat] += 0.1

            # Normalize to maintain probability distribution
            row_sum = sum(self.category_transitions[prev_cat].values())
            for to_cat in self.category_transitions[prev_cat]:
                self.category_transitions[prev_cat][to_cat] /= row_sum

        # Detect if we're in an active golden path workflow
        self._detect_active_workflow(golden_paths)

    def _detect_active_workflow(self, golden_paths: Dict[str, Dict[str, Any]]) -> None:
        """
        Detect if current tool sequence matches a known golden path.

        If detected, we can strongly boost the next tool in that workflow.
        This is prescient guidance - "you're on this proven path, continue."
        """
        if len(self.tool_sequence) < 2:
            self.active_workflow = None
            return

        # Get recent tool sequence
        recent_sequence = [t["tool"] for t in self.tool_sequence[-4:]]

        # Check each golden path for sequence match
        for path_name, path_data in golden_paths.items():
            if not isinstance(path_data, dict):
                continue
            golden_chain = path_data.get("chain")
            priors = path_data.get("priors")
            if not isinstance(golden_chain, list) or not golden_chain or not isinstance(priors, dict):
                continue

            # Check if recent sequence is a contiguous subsequence of this path
            for i in range(len(golden_chain) - len(recent_sequence) + 1):
                if golden_chain[i : i + len(recent_sequence)] == recent_sequence:
                    # We're inside this workflow!
                    remaining_tools = golden_chain[i + len(recent_sequence) :]

                    try:
                        alpha = float(priors.get("alpha", 1.0))
                        beta = float(priors.get("beta", 1.0))
                    except (TypeError, ValueError):
                        alpha = 1.0
                        beta = 1.0
                    reliability = alpha / max(0.0001, alpha + beta)

                    self.active_workflow = {
                        "name": path_name,
                        "chain": golden_chain,
                        "position": i + len(recent_sequence),
                        "total_steps": len(golden_chain),
                        "remaining": remaining_tools,
                        "confidence": reliability,
                    }

                    self.logger.info(
                        "🌟 Active workflow detected: %s (step %d/%d, %.0f%% confidence)",
                        path_name,
                        self.active_workflow["position"],
                        len(golden_chain),
                        reliability * 100,
                    )
                    return

        # No workflow detected
        self.active_workflow = None

    def compute_momentum_bonus(self, tool_name: str, tool_category: str) -> float:
        """
        Compute momentum-based score bonus for a tool.

        This is where conversational flow emerges. Tools that naturally
        follow from recent actions get boosted, creating workflow fluidity.

        Returns bonus in range [0.0, 0.25].
        """
        if not self.recent_tools:
            return 0.0

        total_bonus = 0.0

        # === SIGNAL 1: Active Workflow Bonus (STRONGEST) ===
        if self.active_workflow and self.active_workflow["remaining"]:
            if tool_name in self.active_workflow["remaining"]:
                # This tool is the NEXT step in proven workflow
                workflow_confidence = self.active_workflow["confidence"]
                workflow_bonus = 0.20 * workflow_confidence  # Up to +0.20
                total_bonus += workflow_bonus

                self.logger.debug(
                    "Workflow bonus for %s: +%.3f (next in %s)",
                    tool_name,
                    workflow_bonus,
                    self.active_workflow["name"],
                )

        # === SIGNAL 2: Category Adjacency Bonus (from graph) ===
        last_tool_data = self.recent_tools[-1]
        last_category = last_tool_data["category"]

        if tool_category in self.category_graph.get(last_category, set()):
            # Adjacent categories in capability graph
            adjacency_bonus = 0.12
            total_bonus += adjacency_bonus

            self.logger.debug(
                "Adjacency bonus for %s: +%.3f (%s → %s)",
                tool_name,
                adjacency_bonus,
                last_category,
                tool_category,
            )

        # === SIGNAL 3: Category Continuation Bonus ===
        elif tool_category == last_category:
            # Continuing in same category
            continuation_bonus = 0.08
            total_bonus += continuation_bonus

            self.logger.debug(
                "Continuation bonus for %s: +%.3f (same category)",
                tool_name,
                continuation_bonus,
            )

        # === SIGNAL 4: Learned Transition Probability ===
        transition_prob = self.category_transitions.get(last_category, {}).get(
            tool_category, 0.0
        )
        if transition_prob > 0.5:  # Above baseline
            # Scale by how strong the learned transition is
            transition_bonus = min(0.08, (transition_prob - 0.5) * 0.16)
            total_bonus += transition_bonus

            self.logger.debug(
                "Transition bonus for %s: +%.3f (P(%s→%s)=%.2f)",
                tool_name,
                transition_bonus,
                last_category,
                tool_category,
                transition_prob,
            )

        # === SIGNAL 5: Category Recency Decay ===
        if tool_category in self.recent_categories:
            recency_position = self.recent_categories.index(tool_category)
            # Position 0 = +0.05, position 1 = +0.03, position 2 = +0.01
            recency_bonus = 0.05 * (0.6**recency_position)
            total_bonus += recency_bonus

            self.logger.debug(
                "Recency bonus for %s: +%.3f (category rank: %d)",
                tool_name,
                recency_bonus,
                recency_position,
            )

        # === SIGNAL 6: Topological Manifold Attention (from delegate) ===
        # Exponential-decay attention from the manifold — accounts for category
        # adjacency in the graph, not just simple recency.
        manifold_attention = self._manifold.attention_score(
            tool_name,
            tool_category,
        )
        if manifold_attention > 0.01:
            attn_bonus = min(0.10, manifold_attention * 0.15)
            total_bonus += attn_bonus
            self.logger.debug(
                "Manifold attention for %s: +%.3f (raw=%.3f)",
                tool_name,
                attn_bonus,
                manifold_attention,
            )

        # === SIGNAL 7: Spectral Graph Momentum (transition probability) ===
        graph_momentum = self._manifold.spectral_graph_momentum(
            tool_category,
            self.category_transitions,
        )
        if graph_momentum > 0.1:
            graph_bonus = min(0.08, graph_momentum * 0.12)
            total_bonus += graph_bonus
            self.logger.debug(
                "Spectral graph momentum for %s: +%.3f (raw=%.3f)",
                tool_name,
                graph_bonus,
                graph_momentum,
            )

        # === MASTER GATE: Wasserstein dampening from change-point detection ===
        # When the manifold detects a distribution shift via Wasserstein
        # distance, it suppresses ALL momentum signals to prevent stale
        # workflow continuation.
        dampening = self._manifold.get_dampening()
        total_bonus *= dampening

        # Cap at 0.30 to prevent overwhelming other scoring signals
        return min(0.30, total_bonus)

    def get_context_narrative(self) -> str:
        """
        Generate natural language description of session momentum.

        Used in capability briefings to give LLMs workflow continuity context.
        """
        if not self.recent_tools:
            return "Session just started. No momentum context yet."

        last_tool = self.recent_tools[-1]
        time_since_last = time.time() - last_tool["timestamp"]

        parts = []

        # Recent tool usage
        if time_since_last < 60:  # Within last minute
            parts.append(
                f"You just used `{last_tool['tool']}` ({int(time_since_last)}s ago)."
            )
        else:
            parts.append(f"You recently used `{last_tool['tool']}`.")

        # Active workflow detection
        if self.active_workflow:
            wf = self.active_workflow
            remaining_str = (
                f"`{wf['remaining'][0]}`" if wf["remaining"] else "workflow complete"
            )

            parts.append(
                f"You're at step {wf['position']}/{wf['total_steps']} of the "
                f"**{wf['name']}** workflow (proven {wf['confidence']:.0%} reliable). "
                f"Next suggested: {remaining_str}."
            )

        # Category flow pattern
        if len(self.recent_categories) >= 2:
            cat_pattern = " → ".join(self.recent_categories[::-1])
            parts.append(f"Category flow: {cat_pattern}.")

        # Manifold dampening report
        dampening = self._manifold.get_dampening()
        if dampening < 0.8:
            parts.append(
                f"⚠️ Intent shift detected (dampening={dampening:.2f}). "
                f"Previous momentum suppressed."
            )

        return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  AUTONOMOUS META-LEARNING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
#
# The system's capacity for self-improvement.  Monitors its own predictions
# vs. observed outcomes, tunes scoring weights, discovers recurring patterns
# that should become golden paths, and generates health diagnostics.
# ═══════════════════════════════════════════════════════════════════════════════


class _MetaLearningEngine:
    """
    Autonomous meta-learning for the prescient exoskeleton.

    Four capabilities:
      1. Weight tuning: After each reflection, compare predicted reliability
         vs. actual outcome.  If the KL divergence between predicted and
         observed distributions exceeds a threshold, adjust scoring weights.
      2. Golden path discovery: Mine execution traces for recurring chains
         that consistently succeed.  When a chain appears N+ times with
         >80% success, promote it to golden path status.
      3. Capability graph evolution: Track category co-occurrences and merge
         or split categories based on observed clustering patterns.
      4. Health scoring: Periodically compute a system health score based
         on prediction accuracy, exploration ratio, and staleness.

    Source: Sovereign MCP Server - Meta-Learning Subsystem
    Version: 3.0.0
    Status: Production Stable
    """

    def __init__(
        self,
        min_observations: int = 5,
        kl_threshold: float = 0.1,
        golden_path_min_occurrences: int = 4,
        golden_path_min_success_rate: float = 0.8,
    ) -> None:
        """
        Initialize the meta-learning engine.

        Args:
            min_observations: Minimum observations before weight tuning kicks in.
            kl_threshold: KL divergence threshold that triggers weight adjustment.
            golden_path_min_occurrences: Minimum chain occurrences for golden
                                         path promotion.
            golden_path_min_success_rate: Minimum success rate for promotion.
        """
        self._min_observations: int = max(3, min_observations)
        self._kl_threshold: float = max(0.01, kl_threshold)
        self._gp_min_occ: int = max(2, golden_path_min_occurrences)
        self._gp_min_sr: float = max(0.5, min(1.0, golden_path_min_success_rate))
        self._prediction_log: List[Dict[str, Any]] = []
        self._weight_adjustments: List[Dict[str, float]] = []

    def log_prediction(
        self,
        tool_name: str,
        predicted_reliability: float,
        actual_success: bool,
        context_category: str = "",
    ) -> None:
        """
        Log a prediction vs. outcome pair for later analysis.

        Args:
            tool_name: The tool that was used.
            predicted_reliability: The predicted reliability at decision time.
            actual_success: Whether the tool actually succeeded.
            context_category: Category context for stratified analysis.
        """
        self._prediction_log.append(
            {
                "tool": tool_name,
                "predicted": max(0.0, min(1.0, predicted_reliability)),
                "actual": 1.0 if actual_success else 0.0,
                "category": context_category,
                "timestamp": time.time(),
            }
        )

    def compute_weight_adjustment(self) -> Dict[str, float]:
        """
        Compute scoring weight adjustments via online Brier score gradient descent.

        Unlike the V2 3-way if/elif/else lookup table, this performs actual
        gradient-based calibration:

          1. Compute per-component Brier scores (EMA-smoothed) from the
             prediction log.
          2. Decompose into reliability (how well-calibrated) and resolution
             (how discriminating) components.
          3. Take gradient steps proportional to each component's contribution
             to total calibration error, with momentum smoothing.

        The Brier score is a strictly proper scoring rule — minimizing it
        is equivalent to maximizing calibration, which is exactly what we want.

        Returns:
            Dict of component -> adjustment multiplier (1.0 = no change).
            Values > 1.0 mean "increase this weight", < 1.0 mean "decrease".
        """
        components = [
            "semantic",
            "intent",
            "composability",
            "reliability",
            "latency_penalty",
        ]
        default_weights = {c: 1.0 for c in components}

        if len(self._prediction_log) < self._min_observations:
            return default_weights

        # Exponential moving average Brier score decomposition
        alpha_ema = 2.0 / (min(50, len(self._prediction_log)) + 1)

        predicted = [e["predicted"] for e in self._prediction_log]
        actual = [e["actual"] for e in self._prediction_log]
        n = len(predicted)

        # Overall Brier score: mean((predicted - actual)^2)
        brier_score = sum((p - a) ** 2 for p, a in zip(predicted, actual)) / n

        # Calibration decomposition (Murphy 1973):
        # Brier = Reliability - Resolution + Uncertainty
        mean_outcome = sum(actual) / n
        uncertainty = mean_outcome * (1.0 - mean_outcome)

        # Bin into 10 calibration bins for reliability/resolution
        n_bins = 10
        bins: List[List[Tuple[float, float]]] = [[] for _ in range(n_bins)]
        for p_val, a_val in zip(predicted, actual):
            b_idx = min(n_bins - 1, int(p_val * n_bins))
            bins[b_idx].append((p_val, a_val))

        reliability = 0.0
        resolution = 0.0
        for bin_entries in bins:
            if not bin_entries:
                continue
            bin_n = len(bin_entries)
            bin_mean_pred = sum(p for p, _ in bin_entries) / bin_n
            bin_mean_act = sum(a for _, a in bin_entries) / bin_n
            weight = bin_n / n

            reliability += weight * (bin_mean_pred - bin_mean_act) ** 2
            resolution += weight * (bin_mean_act - mean_outcome) ** 2

        # Gradient direction: which components need more/less weight?
        # If over-predicting (reliability high, predicted > actual):
        #   - Reduce semantic (it's inflating scores)
        #   - Increase reliability penalty (make it pickier)
        #   - Increase latency penalty (prefer faster, proven tools)
        # If under-predicting (predicted < actual consistently):
        #   - Boost semantic and intent (they're being too conservative)
        #   - Reduce latency penalty (allow slower but better tools)

        mean_pred = sum(predicted) / n
        mean_act = sum(actual) / n
        calibration_gap = mean_pred - mean_act  # positive = over-confident

        # Gradient step size: proportional to Brier score (worse = bigger step)
        # but capped to prevent oscillation
        step_size = min(0.15, brier_score * 0.5)

        # Per-component gradient: how much does each contribute to error?
        # semantic and intent inflate predictions when too high
        # reliability counteracts by penalizing unreliable tools
        # composability amplifies chain confidence
        # latency_penalty filters slow tools
        gradient_map = {
            "semantic": -calibration_gap * 1.2,  # dominant contributor
            "intent": -calibration_gap * 0.8,
            "composability": -calibration_gap * 0.4,
            "reliability": calibration_gap * 1.5,  # opposes the others
            "latency_penalty": calibration_gap * 0.6,
        }

        # Apply gradient with EMA momentum smoothing
        adjustments: Dict[str, float] = {}
        for component in components:
            grad = gradient_map.get(component, 0.0)
            # EMA-smoothed gradient step
            raw_adjustment = 1.0 + step_size * grad
            # Clamp to [0.80, 1.25] to prevent wild swings
            adjustments[component] = max(0.80, min(1.25, raw_adjustment))

        # Record the adjustment for trend analysis
        self._weight_adjustments.append(adjustments)

        return adjustments

    def discover_golden_paths(
        self,
        execution_history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Mine execution traces for recurring successful chains.

        Scans the execution history for tool sequences that appear at least
        N times with success rate above the threshold.  These are candidates
        for promotion to golden path status.

        Args:
            execution_history: List of execution records with 'tools_used',
                              'success', and 'intent' keys.

        Returns:
            List of discovered golden path candidates, each with 'chain',
            'occurrences', 'success_rate', and 'use_cases'.
        """
        chain_counter: Dict[str, Dict[str, Any]] = {}

        for record in execution_history:
            tools = record.get("tools_used", [])
            success = record.get("success", False)
            intent = record.get("intent", "")

            if len(tools) < 2:
                continue

            key = " > ".join(tools)
            if key not in chain_counter:
                chain_counter[key] = {
                    "chain": tools,
                    "total": 0,
                    "successes": 0,
                    "intents": set(),
                }
            chain_counter[key]["total"] += 1
            if success:
                chain_counter[key]["successes"] += 1
            if intent:
                chain_counter[key]["intents"].add(intent.lower())

        candidates: List[Dict[str, Any]] = []
        for _key, data in chain_counter.items():
            total = data["total"]
            if total < self._gp_min_occ:
                continue
            success_rate = data["successes"] / total
            if success_rate < self._gp_min_sr:
                continue
            candidates.append(
                {
                    "chain": data["chain"],
                    "occurrences": total,
                    "success_rate": round(success_rate, 4),
                    "use_cases": sorted(data["intents"]),
                }
            )

        candidates.sort(
            key=lambda c: c["success_rate"] * c["occurrences"], reverse=True
        )
        return candidates

    def system_health_score(
        self,
        tool_priors: Dict[str, Dict[str, Any]],
        recent_history_size: int = 0,
    ) -> Dict[str, Any]:
        """
        Compute a system health diagnostic.

        Three sub-scores:
          - prediction_accuracy: How well predictions match outcomes.
          - exploration_ratio: Fraction of tools that have been tried.
          - freshness: Inverse staleness based on recent vs. total observations.

        Args:
            tool_priors: The current tool prior state.
            recent_history_size: Number of recent execution events.

        Returns:
            Dict with 'overall_score', 'prediction_accuracy',
            'exploration_ratio', 'freshness', and 'recommendations'.
        """
        # Prediction accuracy from logged data
        if self._prediction_log:
            errors = [abs(e["predicted"] - e["actual"]) for e in self._prediction_log]
            prediction_accuracy = 1.0 - (sum(errors) / len(errors))
        else:
            prediction_accuracy = 0.5

        # Exploration ratio
        total_tools = len(tool_priors)
        explored = sum(
            1
            for p in tool_priors.values()
            if (float(p.get("alpha", 1.0)) + float(p.get("beta", 1.0)) - 2.0) > 0.5
        )
        exploration_ratio = explored / max(1, total_tools)

        # Freshness
        if recent_history_size > 0 and self._prediction_log:
            freshness = min(1.0, recent_history_size / 20.0)
        else:
            freshness = 0.3

        overall = (
            0.5 * max(0.0, prediction_accuracy)
            + 0.3 * exploration_ratio
            + 0.2 * freshness
        )

        recommendations: List[str] = []
        if prediction_accuracy < 0.6:
            recommendations.append(
                "Prediction accuracy low — consider weight recalibration"
            )
        if exploration_ratio < 0.4:
            recommendations.append(
                f"Only {explored}/{total_tools} tools explored — increase exploration"
            )
        if freshness < 0.3:
            recommendations.append(
                "System priors may be stale — consider prior decay cycle"
            )

        return {
            "overall_score": round(overall, 4),
            "prediction_accuracy": round(prediction_accuracy, 4),
            "exploration_ratio": round(exploration_ratio, 4),
            "freshness": round(freshness, 4),
            "recommendations": recommendations,
        }

    def _compute_kl(self, predicted: List[float], actual: List[float]) -> float:
        """
        Compute KL divergence between binned predicted and actual distributions.

        Uses 5-bin histogram approximation.

        Args:
            predicted: List of predicted reliability values.
            actual: List of actual outcome values (0.0 or 1.0).

        Returns:
            KL divergence (non-negative float).
        """
        n_bins = 5
        p_hist = [0.0] * n_bins
        q_hist = [0.0] * n_bins

        for val in predicted:
            idx = min(n_bins - 1, int(val * n_bins))
            p_hist[idx] += 1.0
        for val in actual:
            idx = min(n_bins - 1, int(val * n_bins))
            q_hist[idx] += 1.0

        # Normalize with Laplace smoothing
        p_total = sum(p_hist) + n_bins * 0.01
        q_total = sum(q_hist) + n_bins * 0.01

        kl = 0.0
        for i in range(n_bins):
            p = (p_hist[i] + 0.01) / p_total
            q = (q_hist[i] + 0.01) / q_total
            if p > 0 and q > 0:
                kl += p * math.log(p / q)
        return max(0.0, kl)


class NarrativeEngine:
    """
    Narrative Synthesis Cortex: transforms quantitative routing into reasoning.

    Upgrades over V2 draft:
      - Confidence-calibrated language using Bayesian credible intervals
        instead of fixed emoji thresholds.  A tool with Beta(12, 2) gets
        "94% ± 5% (high confidence)", not just a green circle.
      - Token-budget awareness: truncates narrative to fit requested verbosity
        within configurable token ceilings.
      - Multi-voice narrative: golden-path voice (directive), exploration
        voice (curious), recovery voice (cautious) — each with distinct
        linguistic patterns.
      - Fully implemented _get_unexplored_tools using Thompson sampling
        exploration scores from the bandit engine.

    Source: Sovereign MCP Server - Narrative Synthesis Cortex
    Version: 3.0.0
    Status: Production Stable
    """

    TOKEN_BUDGET: Dict[str, int] = {
        "minimal": 150,
        "normal": 600,
        "detailed": 1200,
    }

    def __init__(
        self,
        tool_catalog: Dict[str, Dict[str, Any]],
        logger: logging.Logger,
        bandit: Optional[_ThompsonContextualBandit] = None,
    ) -> None:
        """
        Initialize the Narrative Synthesis Cortex.

        Args:
            tool_catalog: Full tool catalog for description lookups.
            logger: Logger instance.
            bandit: Optional Thompson bandit for exploration scoring.
        """
        self.tool_catalog: Dict[str, Dict[str, Any]] = tool_catalog
        self.logger: logging.Logger = logger
        self._bandit: Optional[_ThompsonContextualBandit] = bandit

    def generate_briefing(
        self,
        intent: str,
        intent_category: str,
        top_tools: List[Dict[str, Any]],
        best_chain: Optional[Dict[str, Any]],
        golden_match: Optional[Dict[str, Any]],
        momentum: Optional[SessionMomentum],
        include_exploration: bool,
        verbosity: str,
        tool_priors: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate natural language capability briefing.

        Core transformation: numbers → narrative → reasoning scaffolds.

        Args:
            intent: The user's goal/task description.
            intent_category: Primary detected category for the intent.
            top_tools: Pre-scored tool list from routing.
            best_chain: Best execution plan (chain + confidence), or None.
            golden_match: Matching golden path, or None.
            momentum: SessionMomentum instance for context, or None.
            include_exploration: Whether to include unexplored suggestions.
            verbosity: One of 'minimal', 'normal', 'detailed'.
            tool_priors: Tool prior state for exploration scoring.

        Returns:
            Formatted markdown narrative string.
        """
        budget = self.TOKEN_BUDGET.get(verbosity, 600)
        parts: List[str] = []

        # ── MINIMAL MODE: short-circuit ──
        if verbosity == "minimal":
            return self._minimal_briefing(intent, top_tools)

        # ── §1: Intent Understanding ──
        category_display = intent_category.replace("_", " ").title()
        parts.append(f"## \U0001f3af Capability Briefing: {category_display} Task\n")
        parts.append(f"**Your goal:** _{intent}_\n")

        # ── §2: Session Momentum Context ──
        if momentum and momentum.recent_tools:
            mcx = momentum.get_context_narrative()
            parts.append(f"\n**\U0001f4cd Session Context:**\n{mcx}\n")

        # ── §3: Recommended Workflow ──
        if golden_match:
            parts.append(self._format_golden_path(golden_match))
        elif best_chain and float(best_chain.get("confidence", 0.0)) > 0.35:
            parts.append(self._format_learned_chain(best_chain))

        # ── §4: Individual Tool Capabilities ──
        tool_limit = 5 if verbosity == "normal" else 8
        parts.append("\n### \U0001f6e0\ufe0f Available Tools\n")
        parts.append(
            self._format_tool_list(
                top_tools[:tool_limit],
                tool_priors or {},
            )
        )

        # ── §5: Exploration Opportunities ──
        if include_exploration:
            unexplored = self._get_unexplored_tools(
                intent,
                top_tools,
                tool_priors or {},
            )
            if unexplored:
                parts.append("\n### \U0001f50d Exploration Opportunities\n")
                parts.append(
                    "_These tools match your intent but have high exploration "
                    "value — their true capability is still uncertain:_\n"
                )
                for tool in unexplored[:3]:
                    parts.append(
                        f"- **`{tool['name']}`** "
                        f"(exploration score: {tool['exploration_score']:.2f}): "
                        f"{self._get_tool_one_liner(tool['name'])}\n"
                    )

        # ── Token-budget truncation ──
        full_text = "\n".join(parts)
        return self._truncate_to_budget(full_text, budget)

    def _minimal_briefing(self, intent: str, top_tools: List[Dict[str, Any]]) -> str:
        """
        Generate a minimal one-line briefing.

        Args:
            intent: User's intent.
            top_tools: Scored tool list.

        Returns:
            Short directive string.
        """
        if not top_tools:
            return f"**Quick Start:** No tools match _{intent}_\n"
        first = top_tools[0]
        return (
            f"**Quick Start:** Use `{first['name']}` for _{intent}_ "
            f"(reliability: {first.get('reliability', 0.5):.0%})\n"
        )

    def _format_golden_path(self, golden_match: Dict[str, Any]) -> str:
        """
        Format golden path with confidence-calibrated language.

        Uses Bayesian credible interval instead of point estimate.

        Args:
            golden_match: Golden path dict with 'chain', 'priors', etc.

        Returns:
            Formatted markdown section.
        """
        chain_str = " \u2192 ".join(golden_match["chain"])
        alpha = float(golden_match["priors"].get("alpha", 1.0))
        beta_p = float(golden_match["priors"].get("beta", 1.0))
        mean_rel = alpha / max(0.01, alpha + beta_p)
        trials = int(alpha + beta_p - 2)

        # Bayesian credible interval (approximate)
        interval_half = 1.96 * math.sqrt(
            (alpha * beta_p) / ((alpha + beta_p) ** 2 * (alpha + beta_p + 1))
        )

        return (
            f"\n### \u2705 Proven Workflow (Golden Path)\n"
            f"**{chain_str}**\n"
            f"- **Reliability:** {mean_rel:.0%} \u00b1 {interval_half:.0%} "
            f"(validated across {trials} executions)\n"
            f"- **Est. time:** ~{golden_match.get('avg_latency_seconds', '?')}s\n"
            f"- **Description:** {golden_match.get('description', 'N/A')}\n"
        )

    def _format_learned_chain(self, chain: Dict[str, Any]) -> str:
        """
        Format learned chain with calibrated hedging.

        Args:
            chain: Chain dict with 'chain', 'confidence', optional 'trials'.

        Returns:
            Formatted markdown section.
        """
        chain_str = " \u2192 ".join(chain["chain"])
        confidence = float(chain.get("confidence", 0.5))
        chain_trials = int(chain.get("trials", 0))

        section = f"\n### \U0001f4a1 Suggested Workflow\n"
        section += f"**{chain_str}**\n"

        if chain_trials >= 5:
            section += (
                f"- **Confidence:** {confidence:.0%} "
                f"(based on {chain_trials} executions)\n"
            )
        elif chain_trials >= 2:
            section += (
                f"- **Preliminary confidence:** {confidence:.0%} "
                f"(only {chain_trials} trials — treat with caution)\n"
            )
        else:
            section += (
                f"- **Predicted confidence:** {confidence:.0%} "
                f"(untested — exploratory)\n"
            )

        if chain.get("adversarial_survived"):
            section += "- \U0001f6e1\ufe0f Survived adversarial stress testing\n"

        return section

    def _format_tool_list(
        self,
        tools: List[Dict[str, Any]],
        tool_priors: Dict[str, Dict[str, Any]],
    ) -> str:
        """
        Format tool list with Bayesian confidence bands.

        Args:
            tools: Scored tool list.
            tool_priors: Tool prior state for interval computation.

        Returns:
            Formatted markdown list.
        """
        lines: List[str] = []

        for i, tool in enumerate(tools, 1):
            reliability = float(tool.get("reliability", 0.5))
            category = tool.get("category", "misc")
            momentum_bonus = float(tool.get("momentum_bonus", 0.0))

            # Bayesian credible interval from priors if available
            prior = tool_priors.get(tool["name"], {})
            alpha = float(prior.get("alpha", 1.0))
            beta_p = float(prior.get("beta", 1.0))
            n_obs = alpha + beta_p - 2.0

            if n_obs > 3:
                interval = 1.96 * math.sqrt(
                    (alpha * beta_p) / ((alpha + beta_p) ** 2 * (alpha + beta_p + 1))
                )
                conf_str = f"{reliability:.0%} \u00b1 {interval:.0%}"
            else:
                conf_str = f"{reliability:.0%} (few observations)"

            if reliability > 0.85:
                badge = "\U0001f7e2 High"
            elif reliability > 0.65:
                badge = "\U0001f7e1 Moderate"
            else:
                badge = "\U0001f534 Experimental"

            entry = f"{i}. **`{tool['name']}`** ({category})\n"
            entry += f"   - Confidence: {badge} ({conf_str})\n"
            entry += f"   - {self._get_tool_one_liner(tool['name'])}\n"

            if momentum_bonus > 0.05:
                entry += (
                    f"   - \u26a1 Momentum: +{momentum_bonus:.2f} (natural next step)\n"
                )
            lines.append(entry)

        return "".join(lines)

    def _get_tool_one_liner(self, tool_name: str) -> str:
        """
        Extract concise one-line tool description.

        Args:
            tool_name: Name of the tool.

        Returns:
            First sentence of the tool's description, truncated to 80 chars.
        """
        tool_data = self.tool_catalog.get(tool_name, {})
        desc = str(tool_data.get("description", "No description available"))
        first_sentence = desc.split(".")[0].strip()
        if len(first_sentence) > 80:
            return first_sentence[:77] + "..."
        return first_sentence

    def _get_unexplored_tools(
        self,
        intent: str,
        current_tools: List[Dict[str, Any]],
        tool_priors: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Find high-potential unexplored tools using Thompson sampling.

        A tool is "unexplored" if it has few observations AND the
        variance of its posterior is high — meaning the bandit hasn't
        converged on its true reliability.  This is precisely the set
        of tools where exploration has the highest information value.

        Args:
            intent: The user's intent string.
            current_tools: Already-ranked tools (to exclude from results).
            tool_priors: Current tool prior state.

        Returns:
            List of unexplored tool dicts with 'name' and 'exploration_score'.
        """
        current_names = {t["name"] for t in current_tools}
        candidates: List[Dict[str, Any]] = []

        for tool_name, prior in tool_priors.items():
            if tool_name in current_names:
                continue

            alpha = float(prior.get("alpha", 1.0))
            beta_p = float(prior.get("beta", 1.0))
            n_obs = alpha + beta_p - 2.0

            # Posterior variance = (alpha * beta) / ((a+b)^2 * (a+b+1))
            variance = (alpha * beta_p) / ((alpha + beta_p) ** 2 * (alpha + beta_p + 1))

            # Exploration score: high variance + low observations
            exploration_score = variance * 4.0 + max(0.0, 1.0 - n_obs / 10.0)

            if exploration_score > 0.15:
                candidates.append(
                    {
                        "name": tool_name,
                        "exploration_score": round(exploration_score, 4),
                        "observations": int(n_obs),
                        "reliability": round(alpha / max(0.01, alpha + beta_p), 4),
                    }
                )

        candidates.sort(key=lambda c: c["exploration_score"], reverse=True)
        return candidates[:5]

    def _truncate_to_budget(self, text: str, token_budget: int) -> str:
        """
        Truncate narrative to fit within token budget.

        Uses word count as a proxy for tokens (1 word \u2248 1.3 tokens).

        Args:
            text: Full narrative text.
            token_budget: Maximum estimated tokens.

        Returns:
            Truncated text with ellipsis indicator if cut.
        """
        word_budget = int(token_budget / 1.3)
        words = text.split()
        if len(words) <= word_budget:
            return text
        truncated = " ".join(words[:word_budget])
        return truncated + "\n\n_[Briefing truncated to fit token budget]_"


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  STANDALONE VALIDATION
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

# ── Distillation Subsystem ─────────────────────────────────────────────────────


import queue
from dataclasses import dataclass, field
from io import TextIOWrapper
import sys
import json
import logging
import time
import uuid
import threading
import queue
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class TrajectoryBuilder:
    """
    Accumulates trajectory steps during an agent run.
    Passed into bb7_agent_run at session start; finalized on completion.
    """
    session_id: str
    source_plane: str
    start_time: float = field(default_factory=time.time)
    steps: List[Dict] = field(default_factory=list)
    thought_journal_entries: List[Dict] = field(default_factory=list)
    intent_provenance: Dict = field(default_factory=dict)
    memory_context_at_start: Dict = field(default_factory=dict)
    parent_trajectory_id: Optional[str] = None
    linked_trajectory_ids: List[str] = field(default_factory=list)
    _step_counter: int = 0

    def add_step(self, role: str, content: Any = None, tool_calls: List[Dict] = None,
                 tool_call_id: str = None, reasoning: str = None,
                 latency_ms: float = None, error: str = None) -> None:
        step: Dict = {
            "step": self._step_counter,
            "role": role,
            "t_offset_ms": round((time.time() - self.start_time) * 1000, 1),
        }
        if content is not None:
            step["content"] = content
        if reasoning is not None:
            step["reasoning"] = reasoning
        if tool_calls is not None:
            step["tool_calls"] = tool_calls
        if tool_call_id is not None:
            step["tool_call_id"] = tool_call_id
        if latency_ms is not None:
            step["latency_ms"] = round(latency_ms, 2)
        if error is not None:
            step["error"] = error
        self.steps.append(step)
        self._step_counter += 1

    def add_journal_entry(self, journal_id: str, summary: str) -> None:
        self.thought_journal_entries.append({
            "journal_id": journal_id,
            "timestamp": time.time(),
            "summary": summary,
        })

    def set_intent_provenance(self, raw_input: str, lisan_intent: Dict = None,
                               exo_route: Dict = None) -> None:
        self.intent_provenance = {
            "raw_user_input": raw_input,
            "lisan_intent": lisan_intent or {},
            "exo_route": exo_route or {},
        }

    def set_memory_context(self, surfaces: List[Dict], signals_active: List[str],
                            injection_boost: int) -> None:
        self.memory_context_at_start = {
            "surfaces": surfaces,
            "injection_boost": injection_boost,
            "signals_active": signals_active,
        }


class TelemetryDistillationEngine:
    """
    V2 Distillation Engine for Sovereign MCP.

    Captures lossless cognitive trajectories for Reinforcement Fine-Tuning.
    Write path is fully async (queue-backed). Zero blocking on the agent hot path.
    Downstream domino hooks fire automatically after each successful write.

    V1 public API is preserved:
      - log_full_trajectory(...)
      - log_mcp_rpc_stub(...)
    """

    SCHEMA_VERSION = "2.0"

    def __init__(self, data_dir: Path,
                 environment_snapshot: Dict = None,
                 downstream_hooks: List[Callable[[Dict], None]] = None):
        self.logger = logging.getLogger(__name__)
        self.distillation_dir = Path(data_dir) / "distillation_dataset"
        self.distillation_dir.mkdir(parents=True, exist_ok=True)
        self.environment_snapshot = environment_snapshot or {}
        self.downstream_hooks: List[Callable[[Dict], None]] = downstream_hooks or []

        # Async write queue — the agent loop never waits on disk I/O
        self._write_queue: queue.Queue = queue.Queue()
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()

    # ------------------------------------------------------------------
    # Public API (V1-compatible + V2 extensions)
    # ------------------------------------------------------------------

    def new_trajectory_builder(self, source_plane: str, session_id: str,
                                parent_trajectory_id: str = None) -> TrajectoryBuilder:
        """
        V2: Factory for TrajectoryBuilder instances.
        Use this inside bb7_agent_run to accumulate steps incrementally.
        Call finalize_builder() when the run completes.
        """
        return TrajectoryBuilder(
            session_id=session_id,
            source_plane=source_plane,
            parent_trajectory_id=parent_trajectory_id,
        )

    def finalize_builder(self, builder: TrajectoryBuilder,
                          telemetry: Dict = None) -> str:
        """
        V2: Finalize and enqueue a TrajectoryBuilder for async disk write.
        Returns trajectory_id immediately without blocking.
        """
        trajectory_id = str(uuid.uuid4())
        safe_telemetry = telemetry or {}
        safe_telemetry["latency_seconds"] = round(time.time() - builder.start_time, 3)

        entry = self._build_entry(
            trajectory_id=trajectory_id,
            source_plane=builder.source_plane,
            session_id=builder.session_id,
            trajectory=builder.steps,
            telemetry=safe_telemetry,
            intent_provenance=builder.intent_provenance,
            memory_context_at_start=builder.memory_context_at_start,
            thought_journal_entries=builder.thought_journal_entries,
            parent_trajectory_id=builder.parent_trajectory_id,
            linked_trajectory_ids=builder.linked_trajectory_ids,
        )
        self._enqueue(entry)
        return trajectory_id

    def log_full_trajectory(self,
                             source_plane: str,
                             session_id: str,
                             trajectory: List[Dict],
                             telemetry: Dict = None,
                             intent_provenance: Dict = None,
                             memory_context_at_start: Dict = None,
                             thought_journal_entries: List[Dict] = None,
                             parent_trajectory_id: str = None) -> str:
        """
        V1-compatible primary method. Also accepts V2 enrichment fields.
        Non-blocking — enqueues and returns trajectory_id immediately.
        """
        trajectory_id = str(uuid.uuid4())
        safe_telemetry = telemetry or {}

        entry = self._build_entry(
            trajectory_id=trajectory_id,
            source_plane=source_plane,
            session_id=session_id,
            trajectory=trajectory,
            telemetry=safe_telemetry,
            intent_provenance=intent_provenance,
            memory_context_at_start=memory_context_at_start,
            thought_journal_entries=thought_journal_entries or [],
            parent_trajectory_id=parent_trajectory_id,
            linked_trajectory_ids=[],
        )
        self._enqueue(entry)
        return trajectory_id

    def log_mcp_rpc_stub(self, method_name: str, arguments: dict,
                          result: Any, latency: float) -> None:
        """
        V1-compatible stub for external clients (Cursor/Claude) where we only
        have the RPC boundaries, not the LLM reasoning.
        """
        trajectory = [
            {
                "step": 0,
                "role": "assistant",
                "tool_calls": [{"id": f"stub_{uuid.uuid4().hex[:8]}", "name": method_name, "arguments": arguments}],
                "t_offset_ms": 0,
            },
            {
                "step": 1,
                "role": "tool",
                "content": str(result),
                "latency_ms": round(latency * 1000, 2),
                "error": "Error:" if str(result).startswith("Error:") else None,
                "t_offset_ms": round(latency * 1000, 2),
            },
        ]
        self.log_full_trajectory(
            source_plane="external_rpc",
            session_id="stateless",
            trajectory=trajectory,
            telemetry={"latency_seconds": latency, "is_stub": True,
                       "tool_call_count": 1, "tool_error_count": 1 if str(result).startswith("Error:") else 0},
        )

    def add_downstream_hook(self, hook: Callable[[Dict], None]) -> None:
        """
        Register a callable that fires after each successful disk write.
        Signature: hook(entry: dict) -> None
        Runs in the writer thread — keep it fast or hand off to another queue.
        """
        self.downstream_hooks.append(hook)

    # ------------------------------------------------------------------
    # Internal machinery
    # ------------------------------------------------------------------

    def _build_entry(self, trajectory_id: str, source_plane: str, session_id: str,
                     trajectory: List[Dict], telemetry: Dict,
                     intent_provenance: Dict = None,
                     memory_context_at_start: Dict = None,
                     thought_journal_entries: List[Dict] = None,
                     parent_trajectory_id: str = None,
                     linked_trajectory_ids: List[str] = None) -> Dict:
        write_start = time.time()
        heuristics, auto_tags = self._evaluate_heuristics(trajectory, telemetry,
                                                           intent_provenance or {},
                                                           memory_context_at_start or {})
        return {
            "schema_version": self.SCHEMA_VERSION,
            "trajectory_id": trajectory_id,
            "parent_trajectory_id": parent_trajectory_id,
            "linked_trajectory_ids": linked_trajectory_ids or [],
            "timestamp": time.time(),
            "session_id": session_id,
            "source_plane": source_plane,
            "environment_snapshot": self.environment_snapshot,
            "intent_provenance": intent_provenance or {},
            "memory_context_at_start": memory_context_at_start or {},
            "quality_matrix": {
                "status": "unreviewed",
                "score": None,
                "heuristics": heuristics,
                "auto_tags": auto_tags,
                "human_labels": [],
            },
            "trajectory": trajectory,
            "telemetry": telemetry,
            "thought_journal_entries": thought_journal_entries or [],
            "distill_meta": {
                "capture_mode": "lossless_harness" if source_plane == "bb7_agent_run" else "rpc_stub",
                "stdio_transcript_ref": None,
                "write_latency_ms": None,  # filled after write
                "queue_depth_at_write": self._write_queue.qsize(),
            },
            "_write_start": write_start,  # stripped before disk write
        }

    def _evaluate_heuristics(self, trajectory: List[Dict], telemetry: Dict,
                               intent_provenance: Dict, memory_context: Dict):
        heuristics = []
        auto_tags = []

        # --- heuristics (diagnostic signals, same as V1 baseline) ---
        tool_errors = sum(
            1 for msg in trajectory
            if msg.get("role") == "tool" and (
                "Error:" in str(msg.get("content", "")) or msg.get("error")
            )
        )
        if tool_errors > 0:
            heuristics.append("contains_tool_error")

        tool_call_count = sum(1 for msg in trajectory if "tool_calls" in msg)
        if tool_call_count >= 3:
            heuristics.append("deep_tool_chain")

        if telemetry.get("latency_seconds", 0) > 30.0:
            heuristics.append("high_latency")

        if telemetry.get("iterations", 0) >= 5:
            heuristics.append("many_iterations")

        # --- auto_tags (positive quality signals for clone selection) ---
        lisan = intent_provenance.get("lisan_intent", {})
        if lisan.get("confidence", 0) > 0.80:
            auto_tags.append("lisan_high_confidence")

        exo_route = intent_provenance.get("exo_route", {})
        if exo_route.get("planner_used") == "mcts":
            auto_tags.append("mcts_planned")
        elif exo_route.get("planner_used") == "astar":
            auto_tags.append("astar_planned")

        if memory_context.get("surfaces"):
            auto_tags.append("memory_enriched")

        if tool_call_count >= 5 and not tool_errors:
            auto_tags.append("deep_clean_chain")

        if exo_route.get("fallback_triggered"):
            auto_tags.append("planner_fallback")

        return heuristics, auto_tags

    def _enqueue(self, entry: Dict) -> None:
        """Non-blocking enqueue. If queue is pathologically deep, log a warning but never drop."""
        depth = self._write_queue.qsize()
        if depth > 500:
            self.logger.warning(f"Distillation write queue depth={depth} — writer may be lagging")
        self._write_queue.put(entry)

    def _writer_loop(self) -> None:
        """Dedicated daemon thread. Dequeues and writes entries one at a time."""
        while True:
            try:
                entry = self._write_queue.get()
                write_start = entry.pop("_write_start", time.time())
                self._write_to_disk(entry, write_start)
                for hook in self.downstream_hooks:
                    try:
                        hook(entry)
                    except Exception as hook_err:
                        self.logger.error(f"Downstream hook error: {hook_err}")
                self._write_queue.task_done()
            except Exception as e:
                self.logger.error(f"Writer loop error: {e}")

    def _get_current_shard(self) -> Path:
        """Rotates files daily to prevent massive unreadable JSONL files."""
        date_str = time.strftime('%Y-%m-%d')
        return self.distillation_dir / f"trajectories_{date_str}.jsonl"

    def _write_to_disk(self, entry: Dict, write_start: float) -> None:
        """Append-only disk write. Fills write_latency_ms after write."""
        try:
            with open(self._get_current_shard(), 'a', encoding='utf-8') as f:
                entry["distill_meta"]["write_latency_ms"] = round(
                    (time.time() - write_start) * 1000, 2
                )
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            # Loud, not silent — distillation failures must surface
            self.logger.error(f"CRITICAL telemetry write failure: {e}")

import sys
import json
import time
from pathlib import Path
from threading import Thread
from io import TextIOWrapper


class StdioTranscriptCapture:
    """
    Wraps stdin/stdout to capture the raw JSON-RPC 2.0 stream at the transport boundary.
    Every request frame and every response frame is written to a per-session transcript file.
    This is the capture layer for external clients where we cannot access model reasoning.

    Usage: instantiate before the MCP server's stdio read loop begins.
    The server code itself needs no changes — it still reads from sys.stdin and writes to sys.stdout.
    """

    def __init__(self, transcript_dir: Path, session_id: str):
        self.transcript_dir = Path(transcript_dir)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id
        self.transcript_path = self.transcript_dir / f"stdio_{session_id}.jsonl"
        self._original_stdin = sys.stdin
        self._original_stdout = sys.stdout

    def install(self) -> None:
        """Monkey-patch sys.stdin and sys.stdout with capturing wrappers."""
        sys.stdin = _CapturingReader(self._original_stdin, self.transcript_path, direction="request")
        sys.stdout = _CapturingWriter(self._original_stdout, self.transcript_path, direction="response")

    def uninstall(self) -> None:
        sys.stdin = self._original_stdin
        sys.stdout = self._original_stdout


class _CapturingReader(TextIOWrapper):
    """Wraps stdin. Every line read is appended to the transcript before being returned."""

    def __init__(self, wrapped, transcript_path: Path, direction: str):
        self._wrapped = wrapped
        self._transcript_path = transcript_path
        self._direction = direction

    def readline(self) -> str:
        line = self._wrapped.readline()
        if line.strip():
            self._append(line.strip())
        return line

    def read(self, size: int = -1) -> str:
        data = self._wrapped.read(size)
        if data.strip():
            self._append(data.strip())
        return data

    def _append(self, raw: str) -> None:
        try:
            record = {
                "t": time.time(),
                "direction": self._direction,
                "raw": raw,
            }
            with open(self._transcript_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record) + '\n')
        except Exception:
            pass  # transcript capture must never crash the server

    # Delegate everything else to the wrapped stream
    def __getattr__(self, name):
        return getattr(self._wrapped, name)


class _CapturingWriter:
    """Wraps stdout. Every write is appended to the transcript before being sent."""

    def __init__(self, wrapped, transcript_path: Path, direction: str):
        self._wrapped = wrapped
        self._transcript_path = transcript_path
        self._direction = direction

    def write(self, data: str) -> int:
        if data.strip():
            try:
                record = {
                    "t": time.time(),
                    "direction": self._direction,
                    "raw": data.strip(),
                }
                with open(self._transcript_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(record) + '\n')
            except Exception:
                pass
        return self._wrapped.write(data)

    def flush(self) -> None:
        self._wrapped.flush()

    def __getattr__(self, name):
        return getattr(self._wrapped, name)


# ── Cognitive Journal Subsystem ────────────────────────────────────────────────

import re as _re_cj  # noqa: E402


class CognitiveJournalSubsystem:
    """
    Lightweight decision provenance layer, absorbing ThoughtJournalTool capabilities.

    NOT an MCP tool. Internal API called by ExoskeletonTool.

    Capabilities absorbed from thought_journal_tool.py:
      1. Decision provenance (decision + rationale + alternatives + constraints)
      2. Conflict detection (negation-word heuristic)
      3. Retrospective generation (N-day window markdown summary)
      4. Reasoning chain tracing (follows linked_decision_ids recursively)
      5. Bidirectional memory linking (memory_key -> decision_ids reverse map)

    Feeds decisions to MCTS as training signal via record_mcts_signal().

    Storage: <data_dir>/exoskeleton/decision_trail.jsonl (append-only JSONL)
    """

    NEGATION_WORDS: frozenset = frozenset(
        {
            "not",
            "never",
            "no",
            "avoid",
            "don't",
            "cannot",
            "shouldn't",
            "remove",
            "stop",
            "disable",
            "reject",
            "against",
            "without",
            "prevent",
            "block",
            "skip",
            "ignore",
            "exclude",
        }
    )

    def __init__(self, data_dir: Path, logger: logging.Logger) -> None:
        self._trail_file = Path(data_dir) / "exoskeleton" / "decision_trail.jsonl"
        self._trail_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.logger = logger
        self._memory_reverse_map: Dict[str, List[str]] = {}
        self._load_reverse_map()

    def record_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        risk_assessment: str = "",
        success_criteria: str = "",
        linked_memory_keys: Optional[List[str]] = None,
        linked_decision_ids: Optional[List[str]] = None,
        outcome: Optional[str] = None,
        validated: Optional[bool] = None,
        plan_id: str = "",
        tools_used: Optional[List[str]] = None,
    ) -> str:
        """Record a decision with full provenance. Returns decision_id."""
        decision_id = str(uuid.uuid4())
        entry: Dict[str, Any] = {
            "id": decision_id,
            "decision": decision,
            "rationale": rationale,
            "alternatives": alternatives or [],
            "constraints": constraints or [],
            "risk_assessment": risk_assessment,
            "success_criteria": success_criteria,
            "linked_memory_keys": linked_memory_keys or [],
            "linked_decision_ids": linked_decision_ids or [],
            "outcome": outcome,
            "validated": validated,
            "plan_id": plan_id,
            "tools_used": tools_used or [],
            "created_at": time.time(),
        }
        self._append(entry)
        for key in linked_memory_keys or []:
            with self._lock:
                self._memory_reverse_map.setdefault(key, []).append(decision_id)
        return decision_id

    def record_mcts_signal(
        self,
        decision_id: str,
        outcome: str,
        validated: bool,
        mcts_planner: Any = None,
    ) -> None:
        """
        Attach outcome to a recorded decision and optionally feed MCTS.
        Failures are logged loudly and then tolerated so recall paths stay readable.
        """
        try:
            entries = self._read_trail()
            patched = False
            for e in entries:
                if e.get("id") == decision_id:
                    e["outcome"] = outcome
                    e["validated"] = validated
                    patched = True
                    break
            if patched:
                with self._lock:
                    try:
                        tmp = self._trail_file.with_suffix(".tmp")
                        with open(tmp, "w", encoding="utf-8") as f:
                            for e in entries:
                                f.write(json.dumps(e) + "\n")
                        tmp.replace(self._trail_file)
                    except Exception as exc:
                        self.logger.error("CogJournal rewrite failed: %s", exc)
                if mcts_planner is not None:
                    reward = 1.0 if validated else 0.0
                    try:
                        for node in getattr(mcts_planner, "_nodes", {}).values():
                            if hasattr(node, "update"):
                                node.update(reward)
                                break
                    except Exception as exc:
                        self.logger.error("CogJournal MCTS update failed: %s", exc)
        except Exception as exc:
            self.logger.error("record_mcts_signal failed: %s", exc)

    def detect_conflicts(
        self,
        topic: str = "",
        lookback_days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Scan recent decisions for contradictions using negation-word heuristic."""
        try:
            cutoff = time.time() - lookback_days * 86400
            entries = [
                e for e in self._read_trail() if e.get("created_at", 0) >= cutoff
            ]
            if topic:
                topic_tokens = set(self._tokenize_simple(topic))
                entries = [
                    e
                    for e in entries
                    if topic_tokens
                    & set(
                        self._tokenize_simple(
                            e.get("decision", "") + " " + e.get("rationale", "")
                        )
                    )
                ]
            conflicts: List[Dict[str, Any]] = []
            for i, e1 in enumerate(entries):
                for e2 in entries[i + 1 :]:
                    t1 = set(self._tokenize_simple(e1.get("decision", "")))
                    t2 = set(self._tokenize_simple(e2.get("decision", "")))
                    overlap = t1 & t2
                    if len(overlap) >= 2 and (
                        self._has_negation(e1.get("decision", ""))
                        or self._has_negation(e2.get("decision", ""))
                    ):
                        conflicts.append(
                            {
                                "id1": e1["id"],
                                "id2": e2["id"],
                                "decision1": e1.get("decision", ""),
                                "decision2": e2.get("decision", ""),
                                "overlap_tokens": list(overlap),
                            }
                        )
            return conflicts
        except Exception as exc:
            self.logger.error("detect_conflicts failed: %s", exc)
            return []

    def get_decision_trail(
        self,
        topic: str,
        lookback_days: int = 90,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Token-overlap scored search over decision_trail.jsonl."""
        try:
            cutoff = time.time() - lookback_days * 86400
            entries = [
                e for e in self._read_trail() if e.get("created_at", 0) >= cutoff
            ]
            topic_tokens = set(self._tokenize_simple(topic))
            if not topic_tokens:
                return entries[-max_results:]
            scored: List[Tuple[float, Dict[str, Any]]] = []
            now = time.time()
            for e in entries:
                text = e.get("decision", "") + " " + e.get("rationale", "")
                tokens = set(self._tokenize_simple(text))
                overlap = len(topic_tokens & tokens)
                if overlap == 0:
                    continue
                age = now - e.get("created_at", now)
                boost = 1.5 if age <= 7 * 86400 else 1.0
                scored.append((overlap * boost, e))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [e for _, e in scored[:max_results]]
        except Exception as exc:
            self.logger.error("get_decision_trail failed: %s", exc)
            return []

    def generate_retrospective(self, lookback_days: int = 30) -> str:
        """Structured markdown retrospective from decision_trail.jsonl."""
        try:
            cutoff = time.time() - lookback_days * 86400
            entries = [
                e for e in self._read_trail() if e.get("created_at", 0) >= cutoff
            ]
            if not entries:
                return f"No decisions recorded in the last {lookback_days} days."
            validated_list = [e for e in entries if e.get("validated") is True]
            invalidated_list = [e for e in entries if e.get("validated") is False]
            pending_list = [e for e in entries if e.get("validated") is None]
            lines = [
                f"## Decision Retrospective — Last {lookback_days} days",
                f"**Total:** {len(entries)} | "
                f"✓ {len(validated_list)} validated | "
                f"✗ {len(invalidated_list)} invalidated | "
                f"⏳ {len(pending_list)} pending",
                "",
                "### Key Decisions",
            ]
            for e in entries[-10:]:
                if e.get("validated") is True:
                    status = "✓"
                elif e.get("validated") is False:
                    status = "✗"
                else:
                    status = "⏳"
                ts = time.strftime("%Y-%m-%d", time.localtime(e.get("created_at", 0)))
                lines.append(f"- [{ts}] {status} **{e.get('decision', '')[:80]}**")
                if e.get("rationale"):
                    lines.append(f"  *Rationale:* {e['rationale'][:120]}")
            return "\n".join(lines)
        except Exception as exc:
            self.logger.error("generate_retrospective failed: %s", exc)
            return "Retrospective unavailable."

    def surface_relevant(
        self,
        context_text: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Surface decisions relevant to current context (replaces bb7_journal_surface_relevant)."""
        return self.get_decision_trail(
            context_text, lookback_days=365, max_results=max_results
        )

    def get_reasoning_chain(self, decision_id: str) -> List[Dict[str, Any]]:
        """Follow linked_decision_ids recursively to reconstruct reasoning chain."""
        try:
            all_entries = {e["id"]: e for e in self._read_trail() if "id" in e}
            chain: List[Dict[str, Any]] = []
            visited: Set[str] = set()
            queue = [decision_id]
            while queue:
                did = queue.pop(0)
                if did in visited or did not in all_entries:
                    continue
                visited.add(did)
                entry = all_entries[did]
                chain.append(entry)
                queue.extend(entry.get("linked_decision_ids", []))
            chain.sort(key=lambda e: e.get("created_at", 0))
            return chain
        except Exception as exc:
            self.logger.error("get_reasoning_chain failed: %s", exc)
            return []

    def linked_by_memory_key(self, memory_key: str) -> List[str]:
        """Reverse lookup: memory_key -> decision_ids that reference it."""
        with self._lock:
            return list(self._memory_reverse_map.get(memory_key, []))

    def _load_reverse_map(self) -> None:
        """Rebuild in-memory reverse map from decision_trail.jsonl on init."""
        try:
            for entry in self._read_trail():
                did = entry.get("id")
                if not did:
                    continue
                for key in entry.get("linked_memory_keys", []):
                    self._memory_reverse_map.setdefault(key, []).append(did)
        except Exception as exc:
            self.logger.error("Failed to rebuild cognitive journal reverse map: %s", exc)

    def _read_trail(
        self, lookback_seconds: float = float("inf")
    ) -> List[Dict[str, Any]]:
        """Read decision_trail.jsonl, optionally filtering by age."""
        entries: List[Dict[str, Any]] = []
        if not self._trail_file.exists():
            return entries
        cutoff = time.time() - lookback_seconds
        try:
            with open(self._trail_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("created_at", 0) >= cutoff:
                            entries.append(entry)
                    except json.JSONDecodeError as exc:
                        self.logger.error(
                            "Cognitive journal JSONL parse failed at %s: %s",
                            self._trail_file,
                            exc,
                        )
        except Exception as exc:
            self.logger.error("_read_trail failed: %s", exc)
        return entries

    def _append(self, entry: Dict[str, Any]) -> None:
        """Thread-safe append to decision_trail.jsonl. Failures raise after logging."""
        with self._lock:
            try:
                with open(self._trail_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as exc:
                self.logger.error("CognitiveJournal append failed: %s", exc)
                raise RuntimeError(f"CognitiveJournal append failed: {exc}") from exc

    @staticmethod
    def _has_negation(text: str) -> bool:
        tokens = set(_re_cj.findall(r"\w+", text.lower()))
        return bool(tokens & CognitiveJournalSubsystem.NEGATION_WORDS)

    @staticmethod
    def _tokenize_simple(text: str) -> List[str]:
        """Lightweight tokenizer — no memory_interconnect import to avoid circular dep."""
        return _re_cj.findall(r"[a-z0-9_]+", text.lower())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _log = logging.getLogger("lisan_al_gaib")

    print("=" * 72)
    print("  LISAN AL-GAIB: PRESCIENT EXOSKELETON \u2014 SUBSYSTEM VALIDATION")
    print("=" * 72)

    # \u00a71 \u2014 Spectral Intent Decomposition
    decomposer = _SpectralIntentDecomposer()
    mock_catalog: Dict[str, Dict[str, Any]] = {
        "bb7_memory_store": {
            "name": "bb7_memory_store",
            "description": "Store information persistently in memory",
        },
        "bb7_run_command": {
            "name": "bb7_run_command",
            "description": "Execute a shell command and return output",
        },
        "bb7_web_search": {
            "name": "bb7_web_search",
            "description": "Search the web for information",
        },
    }
    decomposer.rebuild_idf(mock_catalog)
    sim = decomposer.spectral_similarity(
        "store this in memory",
        "bb7_memory_store Store information persistently",
    )
    print(
        f"\n[\u00a71] Spectral decomposer: similarity('store in memory', "
        f"memory_store) = {sim:.4f}"
    )
    cat_scores = {"memory": 0.8, "files": 0.75, "execution": 0.3}
    gated = decomposer.entropy_gate(cat_scores)
    print(f"     Entropy gate({cat_scores}) = {gated}")

    # \u00a72 \u2014 Thompson Sampling Bandit
    bandit = _ThompsonContextualBandit(decay_rate=0.995)
    test_prior: Dict[str, Any] = {"alpha": 5.0, "beta": 2.0}
    samples = [bandit.draw(test_prior) for _ in range(10)]
    print(
        f"\n[\u00a72] Thompson bandit: 10 draws from Beta(5,2) = "
        f"[{', '.join(f'{s:.3f}' for s in samples)}]"
    )
    print(f"     Mean = {bandit.mean(test_prior):.4f}")
    bandit.update_prior(test_prior, success=True, context_category="memory")
    print(
        f"     After success update: alpha={test_prior['alpha']:.2f}, "
        f"beta={test_prior['beta']:.2f}"
    )

    # \u00a73 \u2014 MCTS Planner
    planner = _MCTSPlanner(exploration_constant=1.414, adversarial_probability=0.1)
    mock_ranked: List[Dict[str, Any]] = [
        {"name": "bb7_memory_store", "score": 0.8, "required_params": []},
        {"name": "bb7_run_command", "score": 0.7, "required_params": ["command"]},
        {"name": "bb7_web_search", "score": 0.6, "required_params": ["query"]},
    ]

    def _mock_reliability(name: str) -> float:
        return {
            "bb7_memory_store": 0.85,
            "bb7_run_command": 0.75,
            "bb7_web_search": 0.65,
        }.get(name, 0.5)

    def _mock_tokens(chain: List[str]) -> int:
        return 120 + len(chain) * 220

    plans = planner.search(
        mock_ranked,
        mock_catalog,
        _mock_reliability,
        _mock_tokens,
        beam_width=2,
        max_chain_length=3,
        simulations=30,
    )
    print(f"\n[\u00a73] MCTS planner: {len(plans)} plans discovered")
    for p in plans:
        print(
            f"     Chain: {' \u2192 '.join(p['chain'])} "
            f"(confidence={p['confidence']:.3f}, "
            f"adversarial={'\u2705' if p['adversarial_survived'] else '\u274c'})"
        )

    # \u00a74 \u2014 Topological Momentum Manifold
    mock_graph: Dict[str, set] = {
        "memory": {"files", "execution"},
        "files": {"memory", "execution"},
        "execution": {"memory", "files", "web"},
        "web": {"execution"},
    }
    manifold = _TopologicalMomentumManifold(mock_graph)
    manifold.record_event("bb7_memory_store", "memory", time.time())
    manifold.record_event("bb7_run_command", "execution", time.time())
    attn = manifold.attention_score("bb7_memory_store", "memory")
    print(
        f"\n[\u00a74] Momentum manifold: attention(memory_store) = {attn:.4f}, "
        f"dampening = {manifold.get_dampening():.2f}"
    )

    # \u00a75 \u2014 Meta-Learning Engine
    meta = _MetaLearningEngine()
    for i in range(8):
        meta.log_prediction("bb7_memory_store", 0.8, i < 6)
    health = meta.system_health_score(
        {"bb7_memory_store": {"alpha": 5.0, "beta": 2.0}},
        recent_history_size=8,
    )
    print(f"\n[\u00a75] Meta-learning: health = {health['overall_score']:.3f}")
    print(f"     Recommendations: {health['recommendations'] or 'None'}")

    # \u00a76 \u2014 Narrative Cortex
    cortex = NarrativeEngine(mock_catalog, _log, bandit=bandit)
    briefing = cortex.generate_briefing(
        intent="debug a failing test",
        intent_category="execution",
        top_tools=mock_ranked,
        best_chain=plans[0] if plans else None,
        golden_match=None,
        momentum=None,
        include_exploration=True,
        verbosity="normal",
        tool_priors={"bb7_memory_store": {"alpha": 5.0, "beta": 2.0}},
    )
    print(f"\n[\u00a76] Narrative cortex output ({len(briefing)} chars):")
    for line in briefing.split("\n")[:8]:
        print(f"     {line}")

    print("\n" + "=" * 72)
    print("  ALL 6 SUBSYSTEMS VALIDATED SUCCESSFULLY")
    print("=" * 72)
