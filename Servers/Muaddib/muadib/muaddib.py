#!/usr/bin/env python3
"""
Digital Twin Tool — Phase 1 -- Renamed Muad'dib

This Takes the Tool Server Orchestrator, not routing of data as data routes r handled in interface but it does handle tool call data routing just not high level. This will utilize my tool_output_head and structured_data_output_head as the input outputs. This should work almost like a LoRa in the sense of it has a forward/backwards pass, not that it is a lora. This is the mcp server made Neural Network.

ARCHITECTURE
============

Two concerns, one module:

1. DigitalTwinBackbone (pure Python, zero torch dependency):
   Ring-buffer of tool-call observations + Q-table over
   (recent_tool_context -> tool_name) mappings. This is the substrate that
   watches every bb7_ call flow through the server and learns tool-routing
   preferences from outcomes. Pure Python so the server boots regardless of
   the torch environment, and so Lisan/the twin load cleanly into the P.A.N.
   agent shell where torch may or may not be present.

2. ToolSubstrateTokenizer (torch, optional):
   Projects symbolic tool-sequences into a shared d_model manifold M so that
   downstream modality heads (structured_data_output_head, tool_output_head,
   visual, code, ...) can consume `hidden_states [1, seq_len, d_model]`
   without caring how the sequence was produced. This is the chart map
   from ToolSpace -> M in the tensor-field framing.

   Phase 1 stack (deliberately minimal):
     - Token embedding + category embedding + scalar param projection
     - RoPE (rotary position encoding, frequency-aligned, no learned positions)
     - Single-head attention  (attention as a TOOL, not the architecture)
     - SwiGLU FFN             (strict upgrade over vanilla FFN, ~zero cost)
     - Output projection to d_model

   Explicitly NOT in Phase 1:
     - Knowledge Graph Enhanced Attention  (no populated graph yet unless past 6 months show fruitful.)
     - Grouped Query Attention             (one head, GQA doesn't apply right now. It will need extending however as there is extra modalities.)
     - Sliding Key Memory Network          (sequences are short)
     - Policy / value reward heads         (come later when trajectories exist)

NAMING
======
All public surface methods start with bb7_ (server registers them).
All private helpers start with _ (Lisan's existing convention, kept here).

DATA DIRECTORY
==============
Follows SOVEREIGN_DATA_DIR -> MCP_DATA_DIR -> repo_root/data resolution
exactly like memory_tool.py and exoskeleton_tool.py. State persists to
`data/digital_twin/` so the twin survives server restarts.

Source: Sovereign MCP Server - Digital Twin Observation Engine
Version: 1.0.0-phase1
Status: Production Stable (pure Python backbone), Experimental (torch tokenizer)
"""

import copy
import hashlib
import json
import logging
import math
import os
import random
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Sovereign data directory — single source of truth for all persistent state.
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
# Torch req, setup current is optional. Pure-Python backbone works without it; tokenizer
# requires it. Server must boot cleanly in either case.
# ---------------------------------------------------------------------------
_TORCH_AVAILABLE: bool
try:
    import torch  # type: ignore[import]
    import torch.nn as nn  # type: ignore[import]
    import torch.nn.functional as F  # type: ignore[import]

    _TORCH_AVAILABLE = True
except Exception as _torch_err:
    _TORCH_AVAILABLE = False
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    logging.getLogger(__name__).info(
        "digital_twin_tool: torch unavailable (%s); backbone will run in "
        "pure-Python mode, tokenizer will be disabled.",
        _torch_err,
    )

_SAFETENSORS_AVAILABLE: bool = False
_safetensors_save_file: Optional[Callable[..., Any]] = None
_safetensors_load_file: Optional[Callable[..., Any]] = None
if _TORCH_AVAILABLE:
    try:
        from safetensors.torch import (  # type: ignore[import]
            load_file as _safetensors_load_file,
            save_file as _safetensors_save_file,
        )

        _SAFETENSORS_AVAILABLE = True
    except Exception as _safe_err:
        logging.getLogger(__name__).warning(
            "digital_twin_tool: safetensors unavailable (%s); "
            "self-play weight checkpoints are disabled and tokenizer saves "
            "will fall back to legacy .pt format.",
            _safe_err,
        )

# ---------------------------------------------------------------------------
# Advanced modality bridge gate. Active by default — this server is always
# running with accumulated training data. Set MUADIB_ADVANCED_MODE=0 only
# to emergency-disable (e.g. debugging a regression).
# ---------------------------------------------------------------------------
_MUADIB_ADVANCED_MODE: bool = os.getenv("MUADIB_ADVANCED_MODE", "1") != "0"

# ---------------------------------------------------------------------------
# Neural backbone — the Aeron neural memory stack. Gated separately from
# torch because the backbone modules have their own import chain. When
# available, NeuralSubstrateTokenizer replaces the Phase 1 stub.
# ---------------------------------------------------------------------------
_NEURAL_CONFIG_AVAILABLE: bool = False
_NEURAL_BACKBONE_AVAILABLE: bool = False
_SELF_PLAY_AVAILABLE: bool = False
if _TORCH_AVAILABLE:
    try:
        from .neural_config import NeuralNetConfig

        _NEURAL_CONFIG_AVAILABLE = True
    except Exception as _config_err:
        NeuralNetConfig = None  # type: ignore[assignment,misc]
        logging.getLogger(__name__).warning(
            "digital_twin_tool: neural_config import failed; "
            "neural backbone and self-play head unavailable: %s",
            _config_err,
        )

if _TORCH_AVAILABLE and _NEURAL_CONFIG_AVAILABLE:
    try:
        from .neural_config import (  # type: ignore[no-redef]
            MuadDibSelfPlayHead,
            SelfPlayConfig,
        )

        _SELF_PLAY_AVAILABLE = True
    except Exception as _self_play_err:
        MuadDibSelfPlayHead = None  # type: ignore[assignment,misc]
        SelfPlayConfig = None  # type: ignore[assignment,misc]
        logging.getLogger(__name__).warning(
            "digital_twin_tool: self-play head unavailable: %s",
            _self_play_err,
        )

if _TORCH_AVAILABLE and _NEURAL_CONFIG_AVAILABLE:
    try:
        from .aeron_neural_memory import (
            NeuralMemoryNetwork,
            KnowledgeGraphAttention,
            ContinualLearningModule,
            FeedForwardNetwork,
            MultiHeadAttention,
        )

        _NEURAL_BACKBONE_AVAILABLE = True
    except Exception as _backbone_err:
        logging.getLogger(__name__).info(
            "digital_twin_tool: neural backbone unavailable (%s); "
            "falling back to Phase 1 stub tokenizer.",
            _backbone_err,
        )


# ═══════════════════════════════════════════════════════════════════════════
#  §1  SUBSTRATE CONFIG
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class SubstrateConfig:
    """
    Configuration for the shared substrate manifold M.

    d_model sets the dimensionality of M. Modality heads consume tensors of
    shape [batch, seq_len, d_model]. Default 512 matches common modality
    head defaults; when Eclogue is wired in, use SubstrateConfig.from_eclogue
    to inherit its hidden_size.
    """

    d_model: int = 512
    vocab_size: int = 4096  # max distinct tool_names the tokenizer can embed
    n_categories: int = 32  # distinct tool categories (memory, file, shell, ...)
    max_seq_len: int = 64  # max tool-sequence length the tokenizer handles
    n_attention_heads: int = 1  # attention as a TOOL — single head, on purpose
    ffn_hidden_mult: float = 8.0 / 3.0  # SwiGLU standard: 2/3 * 4 * d_model
    dropout: float = 0.0  # off by default; set to 0.1 for eventual continously runtime training 
    rope_theta: float = 10000.0  # RoPE base frequency

    @classmethod
    def from_eclogue(cls, eclogue_config: Any) -> "SubstrateConfig":
        """Build a SubstrateConfig inheriting d_model from an EclogueConfig."""
        hidden = getattr(eclogue_config, "hidden_size", None) or getattr(
            eclogue_config, "d_model", 512
        )
        return cls(d_model=int(hidden))

    @property
    def ffn_hidden_size(self) -> int:
        """SwiGLU intermediate dim, rounded to multiple of 64 for efficiency."""
        raw = int(self.d_model * self.ffn_hidden_mult)
        return ((raw + 63) // 64) * 64


# ═══════════════════════════════════════════════════════════════════════════
#  §2  DIGITAL TWIN BACKBONE  (pure Python, no torch)
# ═══════════════════════════════════════════════════════════════════════════


class _StateHasher:
    """
    Deterministic state hashing for the Q-table.

    State = sha256(recent_tool_names[-window:] + current_category)[:8].
    The 8-char hex collision space is 2^32 which is plenty for a single
    server's lifetime of observations.
    """

    def __init__(self, window: int = 5) -> None:
        self._window = window

    def hash_state(
        self,
        recent_tools: List[str],
        current_category: str = "misc",
    ) -> str:
        """Compute an 8-char hex state key from recent context."""
        tail = recent_tools[-self._window :] if recent_tools else []
        payload = json.dumps(
            {"tools": tail, "cat": current_category},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


class _ObservationBuffer:
    """
    Ring buffer of (state, action, reward, next_state, timestamp) tuples.

    Fixed-size deque; oldest observations drop off the tail automatically.
    Thread-safe via a single lock because the server fires observations
    from daemon threads after every tool call.
    """

    def __init__(self, maxlen: int = 10_000) -> None:
        self._buf: Deque[Dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def record(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append one observation. Fire-and-forget from the server."""
        entry = {
            "state": state,
            "action": action,
            "reward": float(reward),
            "next_state": next_state,
            "ts": time.time(),
            "meta": dict(metadata or {}),
        }
        with self._lock:
            self._buf.append(entry)

    def recent(self, n: int = 100) -> List[Dict[str, Any]]:
        """Return the last n observations (newest last)."""
        with self._lock:
            if n >= len(self._buf):
                return list(self._buf)
            return list(self._buf)[-n:]

    def size(self) -> int:
        with self._lock:
            return len(self._buf)

    def dump(self) -> List[Dict[str, Any]]:
        """Return all observations as a list (for persistence)."""
        with self._lock:
            return list(self._buf)

    def load(self, entries: List[Dict[str, Any]]) -> None:
        """Restore observations from a dumped list."""
        with self._lock:
            self._buf.clear()
            for e in entries:
                self._buf.append(e)


class _QTable:
    """
    Tabular Q-learning over (state -> action -> Q-value).

    Update rule (standard TD(0)):
        Q(s,a) += lr * (reward + gamma * max_a' Q(s',a') - Q(s,a))

    State keys come from _StateHasher, action keys are tool_names.
    Thread-safe via a single lock because update and read happen concurrently.
    """

    def __init__(self, learning_rate: float = 0.1, discount: float = 0.9) -> None:
        self._q: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._lr = float(learning_rate)
        self._gamma = float(discount)
        self._lock = threading.Lock()

    def update(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
    ) -> float:
        """TD(0) update. Returns the new Q(s,a)."""
        with self._lock:
            current_q = self._q[state].get(action, 0.0)
            next_qs = self._q.get(next_state, {})
            max_next = max(next_qs.values()) if next_qs else 0.0
            td_target = reward + self._gamma * max_next
            new_q = current_q + self._lr * (td_target - current_q)
            self._q[state][action] = new_q
            return new_q

    def get(self, state: str, action: str) -> float:
        with self._lock:
            return self._q.get(state, {}).get(action, 0.0)

    def scores_for(self, state: str, candidates: List[str]) -> Dict[str, float]:
        """Return raw Q-values for each candidate tool in this state."""
        with self._lock:
            row = self._q.get(state, {})
            return {tool: row.get(tool, 0.0) for tool in candidates}

    def q_bonus(
        self,
        state: str,
        candidates: List[str],
        max_bonus: float = 0.25,
    ) -> Dict[str, float]:
        """
        Return a [0.0, max_bonus] bonus per candidate, scaled so the highest
        Q in this state gets max_bonus, the lowest gets 0.0.

        Shape matches the existing momentum_bonus in _score_tools so when
        wiring into exoskeleton later it drops in as a single additive term.
        """
        raw = self.scores_for(state, candidates)
        if not raw:
            return {}
        values = list(raw.values())
        lo, hi = min(values), max(values)
        span = hi - lo
        if span < 1e-9:
            return {tool: 0.0 for tool in candidates}
        return {
            tool: max_bonus * ((q - lo) / span) for tool, q in raw.items()
        }

    def size(self) -> int:
        with self._lock:
            return sum(len(row) for row in self._q.values())

    def n_states(self) -> int:
        with self._lock:
            return len(self._q)

    def top_entries(self, n: int = 10) -> List[Dict[str, Any]]:
        """Return the top-n highest-Q state/action pairs (for inspection)."""
        with self._lock:
            flat: List[Tuple[str, str, float]] = []
            for state, row in self._q.items():
                for action, q in row.items():
                    flat.append((state, action, q))
            flat.sort(key=lambda t: t[2], reverse=True)
            return [
                {"state": s, "action": a, "q": round(q, 4)} for s, a, q in flat[:n]
            ]

    def dump(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            return {s: dict(row) for s, row in self._q.items()}

    def load(self, data: Dict[str, Dict[str, float]]) -> None:
        with self._lock:
            self._q.clear()
            for s, row in data.items():
                self._q[s] = dict(row)


class DigitalTwinBackbone:
    """
    The pure-Python observation engine.

    Responsibilities:
      1. Map each tool-call outcome to a (state, action, reward) triple.
      2. TD-update the Q-table from that triple.
      3. Persist state to disk so it survives server restarts.
      4. Expose q_bonus() for downstream scoring (exoskeleton will use it
         when you wire it in; until then it's observable but not active).

    This class is deliberately torch-free so the MCP server boots cleanly
    in any environment and so the twin loads into the P.A.N. agent shell
    without pulling the CUDA stack.
    """

    # Reward shaping — tuned to match the +0.25 momentum-bonus scale
    REWARD_SUCCESS: float = 1.0
    REWARD_ERROR: float = -0.5
    REWARD_DEEP_CHAIN_BONUS: float = 0.3  # when chain length >= 3
    REWARD_LOW_LATENCY_BONUS: float = 0.1  # when latency_ms < 500

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        buffer_size: int = 10_000,
        window: int = 5,
        learning_rate: float = 0.1,
        discount: float = 0.9,
        autosave_every_n: int = 50,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir or _SOVEREIGN_DATA_DIR).expanduser().resolve()
        self.twin_dir = self.data_dir / "digital_twin"
        self.twin_dir.mkdir(parents=True, exist_ok=True)
        self.qtable_file = self.twin_dir / "qtable.json"
        self.obs_file = self.twin_dir / "observations.json"

        self._hasher = _StateHasher(window=window)
        self._buffer = _ObservationBuffer(maxlen=buffer_size)
        self._qtable = _QTable(learning_rate=learning_rate, discount=discount)

        self._autosave_every = max(1, int(autosave_every_n))
        self._since_save = 0
        self._save_lock = threading.Lock()

        # Last known recent-tool context per session, so observe() can
        # build (state, next_state) without the caller juggling it.
        self._session_tail: Dict[str, List[str]] = defaultdict(list)
        self._tail_max = max(window, 8)

        self._load_from_disk()

    # -- core observation path ----------------------------------------------

    def observe(
        self,
        session_id: str,
        tool_name: str,
        category: str,
        success: bool,
        latency_ms: float,
        chain_length: int = 1,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record one tool-call observation and TD-update the Q-table.

        Called by the server (from a daemon thread) after each bb7_ execution.
        Never raises — failures are logged and swallowed to protect the
        tool-execution path.
        """
        try:
            tail = self._session_tail[session_id]
            state = self._hasher.hash_state(tail, category)
            new_tail = (tail + [tool_name])[-self._tail_max :]
            next_state = self._hasher.hash_state(new_tail, category)
            self._session_tail[session_id] = new_tail

            reward = self._compute_reward(
                success=success,
                latency_ms=latency_ms,
                chain_length=chain_length,
            )

            new_q = self._qtable.update(
                state=state,
                action=tool_name,
                reward=reward,
                next_state=next_state,
            )
            self._buffer.record(
                state=state,
                action=tool_name,
                reward=reward,
                next_state=next_state,
                metadata={
                    "session_id": session_id,
                    "category": category,
                    "success": bool(success),
                    "latency_ms": float(latency_ms),
                    "chain_length": int(chain_length),
                    "error": error,
                },
            )

            self._maybe_autosave()
            return {
                "ok": True,
                "state": state,
                "next_state": next_state,
                "reward": reward,
                "q_value": new_q,
            }
        except Exception as exc:
            self.logger.error("digital_twin observe failed: %s", exc, exc_info=True)
            return {"ok": False, "error": str(exc)}

    def _compute_reward(
        self,
        success: bool,
        latency_ms: float,
        chain_length: int,
    ) -> float:
        """Reward shaping matching the +0.25 momentum-bonus scale."""
        reward = self.REWARD_SUCCESS if success else self.REWARD_ERROR
        if success:
            if chain_length >= 3:
                reward += self.REWARD_DEEP_CHAIN_BONUS
            if latency_ms > 0 and latency_ms < 500.0:
                reward += self.REWARD_LOW_LATENCY_BONUS
        return reward

    # -- query surface ------------------------------------------------------

    def q_bonus(
        self,
        session_id: str,
        category: str,
        candidates: List[str],
        max_bonus: float = 0.25,
    ) -> Dict[str, float]:
        """
        Return normalized Q-bonuses in [0.0, max_bonus] for the given
        candidates at the current session+category state.

        Designed to drop into _score_tools as a single additive term.
        """
        tail = self._session_tail.get(session_id, [])
        state = self._hasher.hash_state(tail, category)
        return self._qtable.q_bonus(state, candidates, max_bonus=max_bonus)

    def status(self) -> Dict[str, Any]:
        return {
            "observations": self._buffer.size(),
            "states_learned": self._qtable.n_states(),
            "q_entries": self._qtable.size(),
            "sessions_tracked": len(self._session_tail),
            "top_q": self._qtable.top_entries(n=10),
            "torch_available": _TORCH_AVAILABLE,
        }

    # -- persistence --------------------------------------------------------

    def _maybe_autosave(self) -> None:
        self._since_save += 1
        if self._since_save >= self._autosave_every:
            self._since_save = 0
            try:
                self.save()
            except Exception as exc:
                self.logger.error("digital_twin autosave failed: %s", exc)

    def save(self) -> None:
        """Persist Q-table and observations atomically."""
        with self._save_lock:
            tmp_q = self.qtable_file.with_suffix(".json.tmp")
            tmp_o = self.obs_file.with_suffix(".json.tmp")
            try:
                with open(tmp_q, "w", encoding="utf-8") as f:
                    json.dump(self._qtable.dump(), f)
                os.replace(tmp_q, self.qtable_file)
                with open(tmp_o, "w", encoding="utf-8") as f:
                    json.dump(self._buffer.dump(), f)
                os.replace(tmp_o, self.obs_file)
            finally:
                for t in (tmp_q, tmp_o):
                    if t.exists():
                        try:
                            t.unlink()
                        except Exception:
                            pass

    def _load_from_disk(self) -> None:
        """Restore Q-table and observations from disk if present."""
        if self.qtable_file.exists():
            try:
                with open(self.qtable_file, "r", encoding="utf-8") as f:
                    self._qtable.load(json.load(f))
            except Exception as exc:
                self.logger.warning("digital_twin qtable load failed: %s", exc)
        if self.obs_file.exists():
            try:
                with open(self.obs_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
                self._buffer.load(entries)
                # Rebuild the session tails from recent observations
                for e in entries[-500:]:
                    sid = e.get("meta", {}).get("session_id")
                    if sid:
                        tail = self._session_tail[sid]
                        tail.append(e["action"])
                        if len(tail) > self._tail_max:
                            del tail[: -self._tail_max]
            except Exception as exc:
                self.logger.warning(
                    "digital_twin observations load failed: %s", exc
                )


# ═══════════════════════════════════════════════════════════════════════════
#  §3  TOOL SUBSTRATE TOKENIZER  (torch, the chart map into M)
# ═══════════════════════════════════════════════════════════════════════════
#
# Only defined when torch is available. The server never imports these
# classes directly — it goes through the DigitalTwinTool wrapper, which
# returns a clear "torch not available" error rather than crashing.
#
# The tokenizer is NOT trained in Phase 1. It's initialized randomly so
# the shapes are correct and the pipeline flows end-to-end. Training comes
# in Phase 2 once enough trajectories accumulate.
# ═══════════════════════════════════════════════════════════════════════════


if _TORCH_AVAILABLE:

    class _RoPE(nn.Module):
        """
        Rotary Position Encoding.

        Applies position information via rotation in 2D subspaces. No learned
        parameters, frequency-aligned, aligns with your frequency-substrate
        philosophy. Standard LLaMA/GPT-NeoX implementation.
        """

        def __init__(self, head_dim: int, max_seq_len: int, theta: float = 10000.0):
            super().__init__()
            assert head_dim % 2 == 0, "head_dim must be even for RoPE"
            inv_freq = 1.0 / (
                theta ** (torch.arange(0, head_dim, 2).float() / head_dim)
            )
            t = torch.arange(max_seq_len).float()
            freqs = torch.outer(t, inv_freq)  # [max_seq, head_dim/2]
            cos = freqs.cos()
            sin = freqs.sin()
            # Cache as non-parameter buffers
            self.register_buffer("cos", cos, persistent=False)
            self.register_buffer("sin", sin, persistent=False)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: [batch, seq, head_dim]
            seq_len = x.shape[-2]
            cos = self.cos[:seq_len].unsqueeze(0)  # [1, seq, head_dim/2]
            sin = self.sin[:seq_len].unsqueeze(0)
            x1, x2 = x.chunk(2, dim=-1)
            rotated = torch.cat(
                [x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1
            )
            return rotated

    class _SwiGLU(nn.Module):
        """
        SwiGLU FFN.

        SiLU(W_gate @ x) * (W_up @ x) -> W_down.
        Three matrices instead of two; intermediate dim = 2/3 * 4 * d_model
        keeps total parameter count roughly equal to a standard 4x FFN.

        Strict upgrade over vanilla FFN. Used by LLaMA, Mistral, Gemma,
        DeepSeek, Qwen. ~zero cost, measurable gain.
        """

        def __init__(self, d_model: int, hidden: int, dropout: float = 0.0):
            super().__init__()
            self.w_gate = nn.Linear(d_model, hidden, bias=False)
            self.w_up = nn.Linear(d_model, hidden, bias=False)
            self.w_down = nn.Linear(hidden, d_model, bias=False)
            self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.dropout(self.w_down(F.silu(self.w_gate(x)) * self.w_up(x)))

    class _SubstrateAttention(nn.Module):
        """
        Single-head attention with RoPE.

        Attention as a TOOL, not the architecture — one head, one pass, one
        purpose: weight the tool-token sequence by contextual relevance.
        RoPE is applied to Q and K only (not V) as in standard LLM practice.
        """

        def __init__(self, config: SubstrateConfig):
            super().__init__()
            assert config.n_attention_heads == 1, (
                "Phase 1 is single-head by design — attention is a tool, "
                "not the architecture. Raise this only with explicit intent."
            )
            self.d_model = config.d_model
            self.q_proj = nn.Linear(config.d_model, config.d_model, bias=False)
            self.k_proj = nn.Linear(config.d_model, config.d_model, bias=False)
            self.v_proj = nn.Linear(config.d_model, config.d_model, bias=False)
            self.o_proj = nn.Linear(config.d_model, config.d_model, bias=False)
            self.rope = _RoPE(
                head_dim=config.d_model,
                max_seq_len=config.max_seq_len,
                theta=config.rope_theta,
            )
            self.scale = 1.0 / math.sqrt(config.d_model)

        def forward(
            self,
            x: torch.Tensor,
            attn_mask: Optional[torch.Tensor] = None,
        ) -> torch.Tensor:
            # x: [batch, seq, d_model]
            q = self.rope(self.q_proj(x))
            k = self.rope(self.k_proj(x))
            v = self.v_proj(x)
            # [batch, seq, seq]
            scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
            if attn_mask is not None:
                scores = scores.masked_fill(~attn_mask, float("-inf"))
            weights = F.softmax(scores, dim=-1)
            out = torch.matmul(weights, v)
            return self.o_proj(out)

    class ToolSubstrateTokenizer(nn.Module):
        """
        Projects symbolic tool-sequences into the shared d_model manifold M.

        Input (forward): list of tool-token dicts:
            [{"tool_id": int, "category_id": int, "param_hash": float}, ...]

        Output: hidden_states [1, seq_len, d_model] — directly consumable by
        any modality head that follows the EclogueConfig(hidden_size)
        contract (structured_data_output_head, tool_output_head, etc.).

        Phase 1: embed -> RoPE-attention -> SwiGLU -> output projection.
        """

        def __init__(self, config: SubstrateConfig):
            super().__init__()
            self.config = config

            # Primary token embedding (tool identity)
            self.tool_embed = nn.Embedding(config.vocab_size, config.d_model)
            # Modality-agnostic category embedding (memory, file, shell, ...)
            self.cat_embed = nn.Embedding(config.n_categories, config.d_model)
            # Scalar param hash projected into a small subspace
            self.param_proj = nn.Linear(1, config.d_model, bias=False)

            # Fusion — additive with a learned mixing gate keeps parameter
            # count low vs a concat+linear at 3*d_model -> d_model.
            self.fusion_norm = nn.LayerNorm(config.d_model)

            self.attention = _SubstrateAttention(config)
            self.attn_norm = nn.LayerNorm(config.d_model)

            self.ffn = _SwiGLU(
                d_model=config.d_model,
                hidden=config.ffn_hidden_size,
                dropout=config.dropout,
            )
            self.ffn_norm = nn.LayerNorm(config.d_model)

            self.output_proj = nn.Linear(config.d_model, config.d_model, bias=False)

            # Sensible init — small scale keeps the random Phase 1 projection
            # bounded so downstream modality heads don't see absurd activations.
            self._init_weights()

        def _init_weights(self) -> None:
            for m in self.modules():
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight, mean=0.0, std=0.02)
                    if m.bias is not None:
                        nn.init.zeros_(m.bias)
                elif isinstance(m, nn.Embedding):
                    nn.init.normal_(m.weight, mean=0.0, std=0.02)

        def forward(
            self,
            tool_ids: torch.Tensor,  # [batch, seq] long
            category_ids: torch.Tensor,  # [batch, seq] long
            param_scalars: torch.Tensor,  # [batch, seq, 1] float
            attn_mask: Optional[torch.Tensor] = None,  # [batch, seq, seq] bool
        ) -> torch.Tensor:
            """
            Returns hidden_states [batch, seq, d_model] ready for any
            modality head consuming the EclogueConfig(hidden_size) contract.
            """
            tool_vec = self.tool_embed(tool_ids)
            cat_vec = self.cat_embed(category_ids)
            param_vec = self.param_proj(param_scalars)

            x = self.fusion_norm(tool_vec + cat_vec + param_vec)

            # Attention sublayer (pre-norm residual)
            x = x + self.attention(self.attn_norm(x), attn_mask=attn_mask)
            # FFN sublayer (pre-norm residual)
            x = x + self.ffn(self.ffn_norm(x))

            return self.output_proj(x)

    # ═══════════════════════════════════════════════════════════════════════
    #  §3b  NEURAL SUBSTRATE TOKENIZER  (full backbone, replaces Phase 1)
    # ═══════════════════════════════════════════════════════════════════════
    #
    # Wires the Aeron neural memory backbone into the tool-sequence encoding
    # pipeline. Core ordering (per user directive):
    #   1. NeuralMemoryNetwork — persistent memory, the core
    #   2. KnowledgeGraphAttention — KG-enhanced attention, extension
    #   3. ContinualLearningModule — EWC anti-forgetting, extension
    #
    # Falls back to ToolSubstrateTokenizer if neural backbone not available.
    # ═══════════════════════════════════════════════════════════════════════

    if _NEURAL_BACKBONE_AVAILABLE:

        class NeuralSubstrateTokenizer(nn.Module):
            """
            Production neural tokenizer replacing the Phase 1 single-head stub.

            Pipeline:
              embed(tool + category + param) → fuse
              → NeuralMemoryNetwork (persistent R/W memory, core)
              → KnowledgeGraphAttention (entity-relation attention, extension)
              → ContinualLearningModule (task conditioning, extension)
              → output_proj → [batch, seq, d_model]

            Preserves the same forward() signature as ToolSubstrateTokenizer
            so DigitalTwinTool.bb7_dt_encode() works unchanged.
            """

            def __init__(self, config: 'SubstrateConfig') -> None:
                super().__init__()
                self.config = config

                # Bridge SubstrateConfig → NeuralNetConfig for the backbone
                self.neural_config = NeuralNetConfig.from_substrate(config)

                # ── Embedding layers (same as Phase 1) ──────────────────
                self.tool_embed = nn.Embedding(config.vocab_size, config.d_model)
                self.cat_embed = nn.Embedding(config.n_categories, config.d_model)
                self.param_proj = nn.Linear(1, config.d_model, bias=False)
                self.fusion_norm = nn.LayerNorm(config.d_model)

                # ── Core: NeuralMemoryNetwork ────────────────────────────
                # Persistent external memory with read/write heads,
                # importance-based slot allocation, and consolidation.
                self.memory_network = NeuralMemoryNetwork(
                    config=self.neural_config,
                    memory_size=1000,
                    memory_dim=config.d_model,
                    num_memory_heads=8,
                    consolidation_threshold=0.8,
                )
                self.memory_norm = nn.LayerNorm(config.d_model)

                # ── Extension: KnowledgeGraphAttention ───────────────────
                # GQA + RoPE attention with KG entity/relation injection.
                self.kg_attention = KnowledgeGraphAttention(
                    config=self.neural_config,
                    kg_dim=128,
                    num_relations=50,
                    max_entities=config.vocab_size,
                    cache_size=10000,
                )
                self.kg_norm = nn.LayerNorm(config.d_model)

                # ── Extension: ContinualLearningModule ───────────────────
                # EWC anti-forgetting with task embeddings.
                self.continual_learning = ContinualLearningModule(
                    config=self.neural_config,
                    ewc_lambda=1000.0,
                    max_tasks=100,
                )

                # ── SwiGLU FFN ──────────────────────────────────────────
                self.ffn = FeedForwardNetwork(self.neural_config)
                self.ffn_norm = nn.LayerNorm(config.d_model)

                # ── Output projection ───────────────────────────────────
                self.output_proj = nn.Linear(config.d_model, config.d_model, bias=False)

                # ── Knowledge graph state (populated externally) ────────
                self._knowledge_graph: Optional[Dict] = None
                self._current_task_id: Optional[int] = None

                self._init_weights()

            def _init_weights(self) -> None:
                """Sensible init — bounded activations for untrained state."""
                for m in [self.tool_embed, self.cat_embed]:
                    nn.init.normal_(m.weight, mean=0.0, std=0.02)
                nn.init.normal_(self.param_proj.weight, mean=0.0, std=0.02)
                nn.init.normal_(self.output_proj.weight, mean=0.0, std=0.02)

            def set_knowledge_graph(self, kg: Dict) -> None:
                """Set the knowledge graph for KG-enhanced attention."""
                self._knowledge_graph = kg

            def set_task_id(self, task_id: int) -> None:
                """Set the current task for continual learning conditioning."""
                self._current_task_id = task_id

            def forward(
                self,
                tool_ids: torch.Tensor,      # [batch, seq] long
                category_ids: torch.Tensor,  # [batch, seq] long
                param_scalars: torch.Tensor,  # [batch, seq, 1] float
                attn_mask: Optional[torch.Tensor] = None,
                input_entities: Optional[torch.Tensor] = None,
            ) -> torch.Tensor:
                """
                Full neural pipeline: embed → memory → KG attention → CLM → FFN → output.

                Returns hidden_states [batch, seq, d_model].
                """
                # ── Step 1: Embedding fusion ─────────────────────────────
                tool_vec = self.tool_embed(tool_ids)
                cat_vec = self.cat_embed(category_ids)
                param_vec = self.param_proj(param_scalars)
                x = self.fusion_norm(tool_vec + cat_vec + param_vec)

                # ── Step 2: NeuralMemoryNetwork (core) ───────────────────
                # Read from and write to persistent memory.
                residual = x
                x_normed = self.memory_norm(x)
                x_mem, mem_info = self.memory_network(x_normed, mode='read_write')
                x = residual + x_mem

                # ── Step 3: KnowledgeGraphAttention (extension) ──────────
                # GQA + RoPE attention with optional KG injection.
                residual = x
                x_normed = self.kg_norm(x)
                x_attn, attn_weights = self.kg_attention(
                    query=x_normed,
                    key=x_normed,
                    value=x_normed,
                    input_entities=input_entities if input_entities is not None else tool_ids,
                    knowledge_graph=self._knowledge_graph,
                    attn_mask=attn_mask,
                )
                x = residual + x_attn

                # ── Step 4: ContinualLearningModule (extension) ──────────
                # Task-specific conditioning via learned task embeddings.
                x = self.continual_learning(
                    x,
                    task_id=self._current_task_id,
                    use_task_embedding=self._current_task_id is not None,
                )

                # ── Step 5: SwiGLU FFN ──────────────────────────────────
                residual = x
                x = residual + self.ffn(self.ffn_norm(x))

                # ── Step 6: Output projection ───────────────────────────
                return self.output_proj(x)

            def get_neural_stats(self) -> Dict[str, Any]:
                """Aggregate statistics from all neural subsystems."""
                stats: Dict[str, Any] = {'backbone': 'NeuralSubstrateTokenizer'}
                try:
                    stats['memory'] = self.memory_network.get_memory_statistics()
                except Exception:
                    stats['memory'] = 'unavailable'
                try:
                    stats['kg'] = self.kg_attention.get_kg_statistics()
                except Exception:
                    stats['kg'] = 'unavailable'
                try:
                    stats['continual_learning'] = self.continual_learning.get_task_statistics()
                except Exception:
                    stats['continual_learning'] = 'unavailable'
                return stats


# ═══════════════════════════════════════════════════════════════════════════
#  §4  DIGITAL TWIN TOOL  (bb7_ surface, server-registered)
# ═══════════════════════════════════════════════════════════════════════════


class DigitalTwinTool:
    """
    Public bb7_ surface for the digital twin.

    Exposes:
      bb7_dt_observe    — record a tool-call outcome (TD-update the Q-table)
      bb7_dt_q_scores   — query Q-bonuses for a candidate tool set
      bb7_dt_encode     — project a tool sequence into hidden_states
      bb7_dt_status     — inspection / health
      bb7_dt_save       — manual persist (autosave runs every 50 observations)

    All output is raw JSON-compatible dicts. No cleanup — the server handles
    MCP content-block formatting at the transport boundary.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        substrate_config: Optional[SubstrateConfig] = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.backbone = DigitalTwinBackbone(data_dir=data_dir)
        self.config = substrate_config or SubstrateConfig()

        # Vocabulary mapping — tool_name -> int, built lazily as tools appear.
        # Persisted alongside the Q-table so retrained tokenizers reload the
        # same ids.
        self._vocab_lock = threading.Lock()
        self._tool_vocab: Dict[str, int] = {}
        self._category_vocab: Dict[str, int] = {}
        self._vocab_file = self.backbone.twin_dir / "vocab.json"
        self._load_vocab()

        # Tokenizer is instantiated lazily on first encode() call so the
        # server boots fast and torch isn't touched if never used.
        self._tokenizer: Optional[Any] = None
        self._tokenizer_lock = threading.Lock()
        self._checkpoint_lock = threading.RLock()

        # Self-play policy/value head. This is intentionally separate from
        # the live tokenizer: continuous self-play trains a candidate copy,
        # writes it as safetensors, and only then swaps the promoted head.
        self.self_play_dir = self.backbone.twin_dir / "self_play"
        self.self_play_dir.mkdir(parents=True, exist_ok=True)
        self._self_play_head: Optional[Any] = None
        self._self_play_lock = threading.RLock()
        self._self_play_meta_file = self.self_play_dir / "checkpoint_meta.json"
        self._self_play_config: Optional[Any] = (
            SelfPlayConfig.from_substrate(self.config)
            if _SELF_PLAY_AVAILABLE and SelfPlayConfig is not None
            else None
        )

        # Advanced modality bridge — instantiated when MUADIB_ADVANCED_MODE=1.
        # Fail-open: if init raises, server still boots and bridge stays None.
        self._advanced_bridge: Optional[Any] = None
        if _MUADIB_ADVANCED_MODE:
            try:
                from muadib.advanced_bridge import (
                    AdvancedBridgeConfig,
                    AdvancedModalityBridge,
                )
                self._advanced_bridge = AdvancedModalityBridge(
                    config=AdvancedBridgeConfig(),
                    backbone_ref=self.backbone,
                    twin_ref=self,
                )
                self.logger.info(
                    "Muad'Dib advanced bridge initialized (MUADIB_ADVANCED_MODE=1)"
                )
            except Exception as _bridge_err:
                self.logger.warning(
                    "Muad'Dib advanced bridge init failed (non-fatal): %s", _bridge_err
                )
                self._advanced_bridge = None

    # -- vocab --------------------------------------------------------------

    def _tool_id(self, name: str) -> int:
        with self._vocab_lock:
            if name in self._tool_vocab:
                return self._tool_vocab[name]
            new_id = len(self._tool_vocab) % self.config.vocab_size
            self._tool_vocab[name] = new_id
            self._save_vocab()
            return new_id

    def _category_id(self, category: str) -> int:
        with self._vocab_lock:
            if category in self._category_vocab:
                return self._category_vocab[category]
            new_id = len(self._category_vocab) % self.config.n_categories
            self._category_vocab[category] = new_id
            self._save_vocab()
            return new_id

    def _save_vocab(self) -> None:
        payload = {
            "tools": self._tool_vocab,
            "categories": self._category_vocab,
        }
        tmp = self._vocab_file.with_suffix(".json.tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp, self._vocab_file)
        except Exception as exc:
            self.logger.warning("vocab save failed: %s", exc)

    def _load_vocab(self) -> None:
        if not self._vocab_file.exists():
            return
        try:
            with open(self._vocab_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._tool_vocab = dict(data.get("tools", {}))
            self._category_vocab = dict(data.get("categories", {}))
        except Exception as exc:
            self.logger.warning("vocab load failed: %s", exc)

    # -- tokenizer lazy instantiation ---------------------------------------

    def _get_tokenizer(self) -> Optional[Any]:
        """Lazily instantiate the tokenizer.

        Prefers NeuralSubstrateTokenizer (full backbone) when available,
        falls back to ToolSubstrateTokenizer (Phase 1 stub) otherwise.
        """
        if not _TORCH_AVAILABLE:
            return None
        with self._tokenizer_lock:
            if self._tokenizer is None:
                if _NEURAL_BACKBONE_AVAILABLE:
                    try:
                        self._tokenizer = NeuralSubstrateTokenizer(self.config)
                        self._load_neural_checkpoint()
                        self._tokenizer.eval()
                        self.logger.info(
                            "digital_twin: NeuralSubstrateTokenizer initialized "
                            "(backbone active)"
                        )
                    except Exception as exc:
                        self.logger.warning(
                            "digital_twin: NeuralSubstrateTokenizer failed (%s), "
                            "falling back to Phase 1 stub.",
                            exc,
                        )
                        self._tokenizer = ToolSubstrateTokenizer(self.config)
                        self._tokenizer.eval()
                else:
                    self._tokenizer = ToolSubstrateTokenizer(self.config)
                    self._tokenizer.eval()
            return self._tokenizer

    # -- bb7_ public surface ------------------------------------------------

    def bb7_dt_observe(
        self,
        tool_name: str,
        category: str = "misc",
        success: bool = True,
        latency_ms: float = 0.0,
        chain_length: int = 1,
        session_id: str = "default",
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record one tool-call observation. Called by the server (via daemon
        thread in ambient-memory-exchange) after each bb7_ execution.

        Returns TD-update details for inspection. Never blocks execution.
        """
        # Touch the vocab so the tokenizer will have an id ready when needed
        self._tool_id(tool_name)
        self._category_id(category)
        return self.backbone.observe(
            session_id=session_id,
            tool_name=tool_name,
            category=category,
            success=bool(success),
            latency_ms=float(latency_ms),
            chain_length=int(chain_length),
            error=error,
        )

    def bb7_dt_q_scores(
        self,
        candidates: List[str],
        category: str = "misc",
        session_id: str = "default",
        max_bonus: float = 0.25,
    ) -> Dict[str, Any]:
        """
        Return normalized Q-bonuses for the candidate tool set at the
        current session state. Drop-in for the exoskeleton _score_tools
        formula when wiring is done.
        """
        bonuses = self.backbone.q_bonus(
            session_id=session_id,
            category=category,
            candidates=list(candidates),
            max_bonus=float(max_bonus),
        )
        return {
            "ok": True,
            "session_id": session_id,
            "category": category,
            "bonuses": bonuses,
            "max_bonus": max_bonus,
        }

    def bb7_dt_encode(
        self,
        tool_sequence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Project a symbolic tool sequence into the shared d_model manifold.

        Input: list of dicts with keys:
            tool_name (str, required)
            category  (str, optional, default "misc")
            param_hash (float, optional, default 0.0)

        Output: {"shape": [1, seq, d_model], "hidden_states": nested list}
        when torch is available, else {"ok": False, "error": "..."}.

        Phase 1: tokenizer is randomly initialized. Shapes are correct,
        projections are not yet semantically meaningful. Downstream modality
        heads can be plugged in today against the shape contract; training
        the tokenizer comes when trajectories accumulate.
        """
        if not _TORCH_AVAILABLE:
            return {
                "ok": False,
                "error": "torch unavailable — tokenizer disabled",
                "fallback": "backbone q-table is still active",
            }
        if not tool_sequence:
            return {"ok": False, "error": "empty tool_sequence"}
        if len(tool_sequence) > self.config.max_seq_len:
            return {
                "ok": False,
                "error": f"sequence exceeds max_seq_len={self.config.max_seq_len}",
            }

        tok = self._get_tokenizer()
        if tok is None:
            return {"ok": False, "error": "tokenizer init failed"}

        try:
            tool_ids = [self._tool_id(t["tool_name"]) for t in tool_sequence]
            cat_ids = [
                self._category_id(t.get("category", "misc"))
                for t in tool_sequence
            ]
            params = [float(t.get("param_hash", 0.0)) for t in tool_sequence]

            tool_tensor = torch.tensor([tool_ids], dtype=torch.long)
            cat_tensor = torch.tensor([cat_ids], dtype=torch.long)
            param_tensor = torch.tensor([params], dtype=torch.float).unsqueeze(-1)

            with torch.no_grad():
                hidden_states = tok(tool_tensor, cat_tensor, param_tensor)

            return {
                "ok": True,
                "shape": list(hidden_states.shape),
                "d_model": self.config.d_model,
                "sequence_length": len(tool_sequence),
                "hidden_states": hidden_states.tolist(),
            }
        except Exception as exc:
            self.logger.error("bb7_dt_encode failed: %s", exc, exc_info=True)
            return {"ok": False, "error": str(exc)}

    def bb7_dt_status(self) -> Dict[str, Any]:
        """Health / inspection snapshot of the twin."""
        status = self.backbone.status()
        bridge_health: Dict[str, Any] = (
            self._advanced_bridge.health if self._advanced_bridge is not None else {}
        )
        status.update(
            {
                "vocab_size_used": len(self._tool_vocab),
                "vocab_size_max": self.config.vocab_size,
                "categories_used": len(self._category_vocab),
                "d_model": self.config.d_model,
                "max_seq_len": self.config.max_seq_len,
                "tokenizer_initialized": self._tokenizer is not None,
                "safetensors_available": _SAFETENSORS_AVAILABLE,
                "self_play_available": _SELF_PLAY_AVAILABLE,
                "self_play_head_initialized": self._self_play_head is not None,
                "self_play_checkpoint_meta": self._read_json_file(
                    self._self_play_meta_file
                ),
                "advanced_bridge_available": bridge_health.get("available", False),
                "advanced_bridge_active": bridge_health.get("active", False),
                "advanced_bridge_last_error": bridge_health.get("last_error"),
                "advanced_bridge_provenance_dist": bridge_health.get(
                    "provenance_dist", {}
                ),
            }
        )
        return status

    def bb7_dt_advanced_features(
        self,
        candidates: List[str],
        category: str = "misc",
        session_id: str = "default",
        recent_tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Query advanced modality features for candidate tools via the bridge.

        Returns per-tool provenance-tagged scores when MUADIB_ADVANCED_MODE=1.
        Always safe to call: returns {"ok": False, "reason": "bridge_disabled"}
        when mode is off. Never raises.
        """
        if self._advanced_bridge is None:
            return {
                "ok": False,
                "reason": "bridge_disabled",
                "mode": "MUADIB_ADVANCED_MODE=0",
                "features": {},
                "bridge_health": {
                    "advanced_bridge_available": False,
                    "advanced_bridge_active": False,
                    "advanced_bridge_last_error": None,
                },
            }
        try:
            raw = self._advanced_bridge.extract(
                candidates=list(candidates),
                category=str(category),
                session_id=str(session_id),
                recent_tools=list(recent_tools or []),
            )
            return {
                "ok": True,
                "mode": "MUADIB_ADVANCED_MODE=1",
                "features": {name: feat.to_dict() for name, feat in raw.items()},
                "bridge_health": self._advanced_bridge.health,
            }
        except Exception as exc:
            return {
                "ok": False,
                "reason": str(exc),
                "features": {},
                "bridge_health": self._advanced_bridge.health
                if self._advanced_bridge is not None
                else {},
            }

    def bb7_dt_save(self) -> Dict[str, Any]:
        """Manual persistence. Autosave fires every 50 observations anyway."""
        try:
            self.backbone.save()
            self._save_vocab()
            self._save_neural_checkpoint()
            return {"ok": True, "saved_at": time.time()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def bb7_dt_encode_catalog(
        self,
        tool_names: List[str],
        tool_categories: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Encode a flat list of tool names into per-tool d_model embedding vectors.

        This is the correct API for batch catalog encoding — callers pass
        List[str] and receive a dict of {tool_name: [float, ...] (d_model)}.
        It wraps bb7_dt_encode(), which expects List[Dict], and handles chunking
        transparently when the catalog exceeds max_seq_len (e.g. 110 tools > 64
        max_seq_len).  Each chunk is encoded independently and the per-tool
        vectors are assembled into a single flat embeddings dict.

        Args:
            tool_names:      Tool names to encode, order within each chunk
                             determines position in hidden_states.
            tool_categories: Optional category map {tool_name: category_str}.
                             Defaults to "misc" for any tool not in the map.

        Returns:
            {
                "ok": True,
                "embeddings": {tool_name: [float, ...] (d_model vector)},
                "d_model": int,
                "encoded_count": int,
                "chunks": int,          # number of forward passes used
            }
            On torch unavailable or encode failure:
            {"ok": False, "error": str}
        """
        if not tool_names:
            return {"ok": False, "error": "tool_names is empty"}

        if not _TORCH_AVAILABLE:
            return {
                "ok": False,
                "error": "torch unavailable — catalog encoding disabled",
                "fallback": "backbone q-table is still active",
            }

        categories = tool_categories or {}
        chunk_size: int = max(1, self.config.max_seq_len)
        all_embeddings: Dict[str, List[float]] = {}
        d_model: int = self.config.d_model
        chunks_used: int = 0
        last_error: Optional[str] = None

        # Chunk the catalog so every encode call stays within max_seq_len.
        for chunk_start in range(0, len(tool_names), chunk_size):
            chunk = tool_names[chunk_start : chunk_start + chunk_size]

            tool_sequence = [
                {
                    "tool_name": name,
                    "category": categories.get(name, "misc"),
                    "param_hash": 0.0,
                }
                for name in chunk
            ]

            encode_result = self.bb7_dt_encode(tool_sequence)
            if not isinstance(encode_result, dict) or not encode_result.get("ok"):
                last_error = encode_result.get("error", "unknown") if isinstance(encode_result, dict) else "non-dict result"
                self.logger.warning(
                    "bb7_dt_encode_catalog chunk [%d:%d] failed: %s",
                    chunk_start, chunk_start + len(chunk), last_error,
                )
                continue  # best-effort: skip failed chunks rather than aborting

            hidden_states = encode_result.get("hidden_states")
            d_model = encode_result.get("d_model", self.config.d_model)
            chunks_used += 1

            if not hidden_states:
                continue

            try:
                batch_0 = hidden_states[0]  # [seq_len, d_model] for this chunk
                for pos, name in enumerate(chunk):
                    if pos < len(batch_0):
                        all_embeddings[name] = batch_0[pos]
            except Exception as exc:
                self.logger.error(
                    "bb7_dt_encode_catalog extraction failed on chunk [%d:%d]: %s",
                    chunk_start, chunk_start + len(chunk), exc,
                    exc_info=True,
                )
                last_error = str(exc)

        if not all_embeddings:
            return {
                "ok": False,
                "error": last_error or "all chunks failed to encode",
            }

        return {
            "ok": True,
            "embeddings": all_embeddings,
            "d_model": d_model,
            "encoded_count": len(all_embeddings),
            "chunks": chunks_used,
        }

    # -- checkpoint utilities -----------------------------------------------

    def _read_json_file(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            self.logger.warning("failed reading checkpoint metadata %s: %s", path, exc)
            return {}

    def _sha256_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _state_dict_for_safetensors(self, module: Any) -> Dict[str, Any]:
        if not isinstance(module, nn.Module):
            raise TypeError("module must be a torch.nn.Module")
        state: Dict[str, Any] = {}
        for key, value in module.state_dict().items():
            if hasattr(value, "detach"):
                state[key] = value.detach().cpu().contiguous()
        return state

    def _metadata_for_safetensors(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        # safetensors metadata is string-only by design.
        return {str(key): str(value) for key, value in metadata.items()}

    # -- neural checkpoint persistence --------------------------------------

    @property
    def _checkpoint_dir(self) -> Path:
        return self.backbone.twin_dir

    @property
    def _checkpoint_meta_file(self) -> Path:
        return self._checkpoint_dir / "checkpoint_meta.json"

    def _get_checkpoint_version(self) -> int:
        """Read current checkpoint version from meta file."""
        if self._checkpoint_meta_file.exists():
            try:
                with open(self._checkpoint_meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                return int(meta.get("version", 0))
            except Exception:
                pass
        return 0

    def _save_neural_checkpoint(self) -> None:
        """
        Persist neural model weights as a versioned checkpoint.

        Contract:
          checkpoint_v{N}.safetensors — tensor state_dict (preferred/current)
          checkpoint_v{N}.pt          — legacy fallback only if safetensors missing
          checkpoint_meta.json        — active pointer + metadata ledger

        Keeps last 3 checkpoint versions, prunes older. Uses atomic write
        (.tmp → rename) for crash safety. JSON is metadata, not weights.
        """
        if not _TORCH_AVAILABLE or self._tokenizer is None:
            return
        if not isinstance(self._tokenizer, nn.Module):
            return

        with self._checkpoint_lock:
            version = self._get_checkpoint_version() + 1
            use_safetensors = _SAFETENSORS_AVAILABLE and _safetensors_save_file is not None
            suffix = ".safetensors" if use_safetensors else ".pt"
            ckpt_path = self._checkpoint_dir / f"checkpoint_v{version}{suffix}"
            tmp_path = ckpt_path.with_name(f"{ckpt_path.name}.{os.getpid()}.tmp")
            meta_tmp = self._checkpoint_meta_file.with_name(
                f"{self._checkpoint_meta_file.name}.{os.getpid()}.tmp"
            )

            try:
                metadata = {
                    "kind": "tokenizer",
                    "version": version,
                    "timestamp": time.time(),
                    "observation_count": self.backbone._buffer.size(),
                    "q_entries": self.backbone._qtable.size(),
                    "backbone_type": type(self._tokenizer).__name__,
                    "format": "safetensors" if use_safetensors else "torch_pt_legacy",
                }

                if use_safetensors:
                    state = self._state_dict_for_safetensors(self._tokenizer)
                    _safetensors_save_file(  # type: ignore[misc]
                        state,
                        str(tmp_path),
                        metadata=self._metadata_for_safetensors(metadata),
                    )
                else:
                    self.logger.warning(
                        "safetensors unavailable; writing legacy .pt tokenizer checkpoint"
                    )
                    torch.save(self._tokenizer.state_dict(), tmp_path)
                os.replace(tmp_path, ckpt_path)

                metadata.update(
                    {
                        "active_checkpoint": ckpt_path.name,
                        "active_checkpoint_path": str(ckpt_path),
                        "sha256": self._sha256_file(ckpt_path),
                        "bytes": ckpt_path.stat().st_size,
                    }
                )
                with open(meta_tmp, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                os.replace(meta_tmp, self._checkpoint_meta_file)

                # Prune old checkpoints (keep last 3 versions)
                self._prune_checkpoints(keep=3)

                self.logger.info(
                    "digital_twin: saved %s checkpoint v%d (%s)",
                    metadata["format"],
                    version,
                    type(self._tokenizer).__name__,
                )
            except Exception as exc:
                self.logger.error(
                    "digital_twin checkpoint save failed: %s", exc, exc_info=True
                )
                # Clean up tmp files
                for tmp in (tmp_path, meta_tmp):
                    if tmp.exists():
                        try:
                            tmp.unlink()
                        except Exception:
                            pass

    def _load_neural_checkpoint(self) -> None:
        """
        Load the latest valid neural checkpoint into the tokenizer.

        Prefers safetensors checkpoints. Legacy .pt files remain load-only
        migration fallbacks so existing deployments can promote into the
        safetensors path on the next save.
        """
        if not _TORCH_AVAILABLE or self._tokenizer is None:
            return
        if not isinstance(self._tokenizer, nn.Module):
            return

        candidates: List[Path] = []
        meta = self._read_json_file(self._checkpoint_meta_file)
        active = meta.get("active_checkpoint")
        if isinstance(active, str) and active:
            active_path = self._checkpoint_dir / active
            if active_path.exists():
                candidates.append(active_path)

        import re

        discovered: List[Tuple[int, int, Path]] = []
        for ckpt_path in self._checkpoint_dir.glob("checkpoint_v*.*"):
            match = re.match(
                r"checkpoint_v(\d+)\.(safetensors|pt)$", ckpt_path.name
            )
            if not match:
                continue
            version = int(match.group(1))
            # Prefer safetensors for equal versions.
            format_rank = 1 if match.group(2) == "safetensors" else 0
            discovered.append((version, format_rank, ckpt_path))
        discovered.sort(reverse=True)
        for _version, _rank, ckpt_path in discovered:
            if ckpt_path not in candidates:
                candidates.append(ckpt_path)

        if not candidates:
            self.logger.info("digital_twin: no checkpoint found, starting fresh")
            return

        for ckpt_path in candidates[:6]:
            try:
                if ckpt_path.suffix == ".safetensors":
                    if not _SAFETENSORS_AVAILABLE or _safetensors_load_file is None:
                        raise RuntimeError("safetensors loader unavailable")
                    state_dict = _safetensors_load_file(  # type: ignore[misc]
                        str(ckpt_path),
                        device="cpu",
                    )
                else:
                    state_dict = torch.load(
                        ckpt_path, map_location="cpu", weights_only=True
                    )
                self._tokenizer.load_state_dict(state_dict, strict=False)
                self.logger.info(
                    "digital_twin: loaded checkpoint %s", ckpt_path.name
                )
                return
            except Exception as exc:
                self.logger.warning(
                    "digital_twin: checkpoint %s corrupt/unloadable (%s), trying previous",
                    ckpt_path.name,
                    exc,
                )

        self.logger.warning(
            "digital_twin: no valid checkpoint found, starting from "
            "random initialization"
        )

    def _prune_checkpoints(self, keep: int = 3) -> None:
        """Keep only the N most recent checkpoint versions."""
        import re

        grouped: Dict[int, List[Path]] = defaultdict(list)
        for ckpt_path in self._checkpoint_dir.glob("checkpoint_v*.*"):
            match = re.match(
                r"checkpoint_v(\d+)\.(safetensors|pt)$", ckpt_path.name
            )
            if match:
                grouped[int(match.group(1))].append(ckpt_path)

        versions = sorted(grouped)
        if len(versions) <= keep:
            return
        keep_versions = set(versions[-keep:])
        for version, paths in grouped.items():
            if version in keep_versions:
                continue
            for old_ckpt in paths:
                try:
                    old_ckpt.unlink()
                except Exception as exc:
                    self.logger.warning(
                        "digital_twin: failed to prune %s: %s", old_ckpt, exc
                    )

    # -- self-play head persistence/training --------------------------------

    @staticmethod
    def _parse_env_bool(value: Optional[str], default: bool = False) -> bool:
        if value is None:
            return bool(default)
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "lock", "locked", "freeze", "frozen"}:
            return True
        if normalized in {"0", "false", "no", "off", "unlock", "unlocked", "thaw"}:
            return False
        return bool(default)

    def _self_play_lock_snapshot(self) -> Dict[str, Any]:
        """
        Return the current active-head promotion lock.

        This is a semantic lock over promotion, not an OS/file lock and not a
        safetensors serialization primitive. Continuous self-play may still
        train and archive candidate weights while this is true; it just cannot
        advance the active/champion pointer or swap the live in-memory head.
        """
        env_value = os.getenv("MUADIB_SELF_PLAY_LOCK_ACTIVE")
        meta = self._read_json_file(self._self_play_meta_file)
        if env_value is not None:
            return {
                "active_locked": self._parse_env_bool(env_value, False),
                "lock_source": "env:MUADIB_SELF_PLAY_LOCK_ACTIVE",
                "locked_checkpoint": meta.get("locked_checkpoint")
                or meta.get("active_checkpoint"),
                "lock_reason": meta.get("lock_reason"),
            }
        return {
            "active_locked": bool(meta.get("active_locked", False)),
            "lock_source": "checkpoint_meta",
            "locked_checkpoint": meta.get("locked_checkpoint")
            or meta.get("active_checkpoint"),
            "lock_reason": meta.get("lock_reason"),
        }

    def _self_play_active_locked(self) -> bool:
        return bool(self._self_play_lock_snapshot().get("active_locked", False))

    def _get_self_play_head(self) -> Optional[Any]:
        """Lazily instantiate and load the isolated self-play policy/value head."""
        if not _TORCH_AVAILABLE:
            return None
        if not _SELF_PLAY_AVAILABLE or MuadDibSelfPlayHead is None:
            return None
        if self._self_play_config is None:
            return None
        with self._self_play_lock:
            if self._self_play_head is None:
                head = MuadDibSelfPlayHead(self._self_play_config)
                self._self_play_head = head
                self._load_self_play_checkpoint()
                self._self_play_head.eval()
            return self._self_play_head

    def _next_self_play_version(self) -> int:
        meta = self._read_json_file(self._self_play_meta_file)
        try:
            return int(meta.get("version", 0)) + 1
        except Exception:
            return 1

    def _self_play_checkpoint_candidates(self) -> List[Path]:
        import re

        candidates: List[Path] = []
        meta = self._read_json_file(self._self_play_meta_file)
        active = meta.get("active_checkpoint")
        if isinstance(active, str) and active:
            active_path = self.self_play_dir / active
            if active_path.exists():
                candidates.append(active_path)

        discovered: List[Tuple[int, Path]] = []
        for ckpt_path in self.self_play_dir.glob("self_play_head_v*.safetensors"):
            match = re.match(r"self_play_head_v(\d+)\.safetensors$", ckpt_path.name)
            if match:
                discovered.append((int(match.group(1)), ckpt_path))
        discovered.sort(reverse=True)
        for _version, ckpt_path in discovered:
            if ckpt_path not in candidates:
                candidates.append(ckpt_path)
        return candidates

    def _load_self_play_checkpoint(self) -> None:
        if (
            not _TORCH_AVAILABLE
            or self._self_play_head is None
            or not isinstance(self._self_play_head, nn.Module)
        ):
            return
        for ckpt_path in self._self_play_checkpoint_candidates()[:5]:
            try:
                if not _SAFETENSORS_AVAILABLE or _safetensors_load_file is None:
                    raise RuntimeError("safetensors loader unavailable")
                state_dict = _safetensors_load_file(str(ckpt_path), device="cpu")  # type: ignore[misc]
                self._self_play_head.load_state_dict(state_dict, strict=False)
                self.logger.info(
                    "digital_twin: loaded self-play checkpoint %s", ckpt_path.name
                )
                return
            except Exception as exc:
                self.logger.warning(
                    "digital_twin: self-play checkpoint %s unloadable (%s)",
                    ckpt_path.name,
                    exc,
                )

    def _save_self_play_checkpoint(
        self,
        head: Any,
        metrics: Dict[str, Any],
        promoted: bool,
        promotion_requested: Optional[bool] = None,
        active_locked: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if not _TORCH_AVAILABLE or not isinstance(head, nn.Module):
            raise RuntimeError("self-play head is not a torch module")
        if not _SAFETENSORS_AVAILABLE or _safetensors_save_file is None:
            raise RuntimeError("safetensors is required for self-play weights")

        version = self._next_self_play_version()
        ckpt_path = self.self_play_dir / f"self_play_head_v{version}.safetensors"
        tmp_path = ckpt_path.with_name(f"{ckpt_path.name}.{os.getpid()}.tmp")
        meta_tmp = self._self_play_meta_file.with_name(
            f"{self._self_play_meta_file.name}.{os.getpid()}.tmp"
        )

        metadata = {
            "kind": "muadib_self_play_head",
            "version": version,
            "timestamp": time.time(),
            "format": "safetensors",
            "promoted": bool(promoted),
            "promotion_requested": bool(
                promoted if promotion_requested is None else promotion_requested
            ),
            "active_locked": bool(active_locked)
            if active_locked is not None
            else self._self_play_active_locked(),
            "episodes": int(metrics.get("episodes", 0)),
            "avg_reward": float(metrics.get("avg_reward", 0.0)),
            "avg_loss": float(metrics.get("avg_loss", 0.0)),
        }

        try:
            state = self._state_dict_for_safetensors(head)
            _safetensors_save_file(  # type: ignore[misc]
                state,
                str(tmp_path),
                metadata=self._metadata_for_safetensors(metadata),
            )
            os.replace(tmp_path, ckpt_path)
            metadata.update(
                {
                    "checkpoint": ckpt_path.name,
                    "checkpoint_path": str(ckpt_path),
                    "sha256": self._sha256_file(ckpt_path),
                    "bytes": ckpt_path.stat().st_size,
                }
            )

            previous_meta = self._read_json_file(self._self_play_meta_file)
            lock_snapshot = self._self_play_lock_snapshot()
            if promoted:
                locked_now = False
            elif lock_snapshot.get("lock_source") == "env:MUADIB_SELF_PLAY_LOCK_ACTIVE":
                locked_now = bool(lock_snapshot.get("active_locked", False))
            else:
                locked_now = bool(
                    metadata["active_locked"]
                    or previous_meta.get("active_locked", False)
                    or lock_snapshot.get("active_locked", False)
                )
            ledger = {
                **previous_meta,
                "version": version,
                "latest_candidate": ckpt_path.name,
                "latest_candidate_path": str(ckpt_path),
                "latest_candidate_sha256": metadata["sha256"],
                "latest_metrics": metrics,
                "updated_at": time.time(),
                "format": "safetensors",
                "active_locked": locked_now,
                "lock_source": lock_snapshot.get("lock_source"),
                "promotion_requested": metadata["promotion_requested"],
                "promotion_effective": bool(promoted),
            }
            if locked_now:
                ledger["locked_checkpoint"] = (
                    previous_meta.get("locked_checkpoint")
                    or previous_meta.get("active_checkpoint")
                    or lock_snapshot.get("locked_checkpoint")
                )
            if promoted:
                ledger.update(
                    {
                        "active_checkpoint": ckpt_path.name,
                        "active_checkpoint_path": str(ckpt_path),
                        "active_checkpoint_sha256": metadata["sha256"],
                        "active_version": version,
                        "promoted_at": time.time(),
                        "locked_checkpoint": None,
                    }
                )
            with open(meta_tmp, "w", encoding="utf-8") as handle:
                json.dump(ledger, handle, indent=2, ensure_ascii=False)
            os.replace(meta_tmp, self._self_play_meta_file)
            self._prune_self_play_checkpoints(
                keep=int(getattr(self._self_play_config, "checkpoint_keep", 5) or 5)
            )
            return metadata
        finally:
            for tmp in (tmp_path, meta_tmp):
                try:
                    if tmp.exists():
                        tmp.unlink()
                except OSError:
                    pass

    def _prune_self_play_checkpoints(self, keep: int = 5) -> None:
        import re

        meta = self._read_json_file(self._self_play_meta_file)
        protected_names = {
            name
            for name in (
                meta.get("active_checkpoint"),
                meta.get("locked_checkpoint"),
            )
            if isinstance(name, str) and name
        }
        checkpoints: List[Tuple[int, Path]] = []
        for ckpt_path in self.self_play_dir.glob("self_play_head_v*.safetensors"):
            match = re.match(r"self_play_head_v(\d+)\.safetensors$", ckpt_path.name)
            if match:
                checkpoints.append((int(match.group(1)), ckpt_path))
        checkpoints.sort()
        if len(checkpoints) <= keep:
            return
        keep_versions = {version for version, _path in checkpoints[-keep:]}
        for version, ckpt_path in checkpoints:
            if version in keep_versions or ckpt_path.name in protected_names:
                continue
            try:
                ckpt_path.unlink()
            except Exception as exc:
                self.logger.warning(
                    "digital_twin: failed to prune self-play checkpoint %s: %s",
                    ckpt_path,
                    exc,
                )

    def _normalize_tool_catalog(self, tool_catalog: Optional[Any]) -> List[Dict[str, str]]:
        tools: List[Dict[str, str]] = []
        if isinstance(tool_catalog, dict):
            for name, info in tool_catalog.items():
                if not isinstance(name, str) or not name:
                    continue
                category = "misc"
                if isinstance(info, dict):
                    category = str(info.get("category", "misc") or "misc")
                tools.append({"name": name, "category": category})
        elif isinstance(tool_catalog, list):
            for item in tool_catalog:
                if isinstance(item, str) and item:
                    tools.append({"name": item, "category": "misc"})
                elif isinstance(item, dict):
                    name = str(item.get("name") or item.get("tool_name") or "")
                    if name:
                        tools.append(
                            {
                                "name": name,
                                "category": str(item.get("category", "misc") or "misc"),
                            }
                        )

        if not tools:
            # Fallback to whatever the live twin has already observed.
            reverse_categories = {
                name: "misc" for name in self._tool_vocab.keys()
            }
            tools = [
                {"name": name, "category": reverse_categories.get(name, "misc")}
                for name in sorted(self._tool_vocab.keys())
            ]
        return tools

    def _self_play_reward(self, sequence: List[Dict[str, str]]) -> float:
        if not sequence:
            return 0.0
        tail: List[str] = []
        q_values: List[float] = []
        categories: List[str] = []
        for item in sequence:
            name = item["name"]
            category = item.get("category", "misc")
            state = self.backbone._hasher.hash_state(tail, category)
            q_values.append(self.backbone._qtable.get(state, name))
            categories.append(category)
            tail.append(name)
        q_mean = sum(q_values) / max(1, len(q_values))
        diversity = len(set(categories)) / max(1, len(categories))
        known_ratio = sum(1 for q in q_values if abs(q) > 1e-9) / max(1, len(q_values))
        reward = (0.65 * math.tanh(q_mean)) + (0.20 * (2.0 * diversity - 1.0)) + (
            0.15 * (2.0 * known_ratio - 1.0)
        )
        return max(-1.0, min(1.0, reward))

    def bb7_dt_self_play(
        self,
        tool_catalog: Optional[Any] = None,
        episodes: int = 32,
        max_steps: int = 4,
        learning_rate: Optional[float] = None,
        promote: bool = False,
        update_qtable: bool = False,
        session_id: str = "muadib_self_play",
    ) -> Dict[str, Any]:
        """
        Run bounded Muad'Dib self-play and persist real tensor weights.

        The live self-play head is never mutated in-place. Training happens on
        a candidate copy, the candidate is written as `.safetensors`, and only
        a complete checkpoint explicitly requested for promotion is swapped into
        the active head. JSON is metadata/ledger only.
        """
        if not _TORCH_AVAILABLE:
            return {"ok": False, "error": "torch unavailable"}
        if not _SELF_PLAY_AVAILABLE:
            return {"ok": False, "error": "self-play head unavailable"}
        if not _SAFETENSORS_AVAILABLE:
            return {"ok": False, "error": "safetensors is required for weights"}

        tools = self._normalize_tool_catalog(tool_catalog)
        if not tools:
            return {"ok": False, "error": "no tools available for self-play"}

        config = self._self_play_config
        if config is None:
            return {"ok": False, "error": "self-play config unavailable"}
        episodes = max(1, min(512, int(episodes)))
        max_steps = max(2, min(int(config.max_seq_len), int(max_steps)))
        lr = float(learning_rate if learning_rate is not None else 3e-4)
        requested_promote = bool(promote)
        lock_snapshot = self._self_play_lock_snapshot()
        active_locked = bool(lock_snapshot.get("active_locked", False))
        effective_promote = requested_promote and not active_locked

        with self._self_play_lock:
            base_head = self._get_self_play_head()
            if base_head is None or not isinstance(base_head, nn.Module):
                return {"ok": False, "error": "self-play head init failed"}
            candidate = copy.deepcopy(base_head)

        candidate.train()
        optimizer = torch.optim.AdamW(candidate.parameters(), lr=lr)
        rng = random.Random(int(config.seed) + int(time.time() * 1000) % 1_000_000)
        losses: List[float] = []
        rewards: List[float] = []
        example_sequences: List[List[str]] = []

        for episode_idx in range(episodes):
            sequence = [rng.choice(tools) for _ in range(max_steps)]
            reward = self._self_play_reward(sequence)
            rewards.append(reward)
            if len(example_sequences) < 3:
                example_sequences.append([item["name"] for item in sequence])

            tool_ids = [self._tool_id(item["name"]) for item in sequence]
            target_tool_id = torch.tensor([tool_ids[-1]], dtype=torch.long)
            input_ids = torch.tensor([tool_ids], dtype=torch.long)
            attention_mask = torch.ones_like(input_ids, dtype=torch.bool)
            reward_target = torch.tensor([reward], dtype=torch.float32)

            output = candidate(input_ids, attention_mask=attention_mask)
            policy_logits = output["policy_logits"]
            value = output["value"]
            policy_loss = F.cross_entropy(policy_logits, target_tool_id)
            value_loss = F.mse_loss(value, reward_target)
            probs = F.softmax(policy_logits, dim=-1).clamp_min(1e-9)
            entropy = -(probs * probs.log()).sum(dim=-1).mean()
            loss = (
                float(config.policy_weight) * policy_loss
                + float(config.value_weight) * value_loss
                - float(config.entropy_weight) * entropy
            )

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(candidate.parameters(), max_norm=1.0)
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))

            if update_qtable:
                for step_idx, item in enumerate(sequence, start=1):
                    self.backbone.observe(
                        session_id=session_id,
                        tool_name=item["name"],
                        category=item.get("category", "misc"),
                        success=reward >= 0.0,
                        latency_ms=0.0,
                        chain_length=step_idx,
                        error=None if reward >= 0.0 else "synthetic_self_play_negative_reward",
                    )

        candidate.eval()
        metrics = {
            "episodes": episodes,
            "max_steps": max_steps,
            "learning_rate": lr,
            "avg_reward": sum(rewards) / max(1, len(rewards)),
            "min_reward": min(rewards) if rewards else 0.0,
            "max_reward": max(rewards) if rewards else 0.0,
            "avg_loss": sum(losses) / max(1, len(losses)),
            "min_loss": min(losses) if losses else 0.0,
            "max_loss": max(losses) if losses else 0.0,
            "tool_count": len(tools),
            "update_qtable": bool(update_qtable),
            "training_mode": (
                "candidate_copy_atomic_safetensors_promote"
                if effective_promote
                else "candidate_copy_atomic_safetensors_archive_locked_active"
            ),
            "promotion_requested": requested_promote,
            "active_locked": active_locked,
            "lock_source": lock_snapshot.get("lock_source"),
        }
        checkpoint = self._save_self_play_checkpoint(
            candidate,
            metrics=metrics,
            promoted=effective_promote,
            promotion_requested=requested_promote,
            active_locked=active_locked,
        )

        if effective_promote:
            with self._self_play_lock:
                self._self_play_head = candidate

        return {
            "ok": True,
            "surface": "bb7_dt_self_play",
            "weights_format": "safetensors",
            "promotion_requested": requested_promote,
            "promoted": effective_promote,
            "active_locked": active_locked,
            "lock_source": lock_snapshot.get("lock_source"),
            "locked_checkpoint": lock_snapshot.get("locked_checkpoint"),
            "checkpoint": checkpoint,
            "metrics": metrics,
            "example_sequences": example_sequences,
            "qtable_updated": bool(update_qtable),
            "note": (
                "Self-play trained a candidate policy/value head and saved real "
                "tensor weights as safetensors. JSON metadata is only a ledger."
            ),
        }

    def bb7_dt_self_play_lock(
        self,
        locked: bool = True,
        reason: str = "",
        operator: str = "bb7",
    ) -> Dict[str, Any]:
        """
        Persistently lock/unlock active self-play promotion.

        Locking does not stop continuous candidate training. It prevents
        candidate promotion so the active/champion self-play head remains
        reproducible until unlocked or overridden by
        MUADIB_SELF_PLAY_LOCK_ACTIVE.
        """
        self.self_play_dir.mkdir(parents=True, exist_ok=True)
        meta_tmp = self._self_play_meta_file.with_name(
            f"{self._self_play_meta_file.name}.{os.getpid()}.lock.tmp"
        )
        with self._self_play_lock:
            meta = self._read_json_file(self._self_play_meta_file)
            now = time.time()
            locked_bool = bool(locked)
            meta.update(
                {
                    "active_locked": locked_bool,
                    "lock_reason": str(reason or ""),
                    "lock_operator": str(operator or "bb7"),
                    "lock_updated_at": now,
                }
            )
            if locked_bool:
                meta.update(
                    {
                        "locked_at": now,
                        "locked_checkpoint": meta.get("active_checkpoint"),
                    }
                )
            else:
                meta.update(
                    {
                        "unlocked_at": now,
                        "locked_checkpoint": None,
                    }
                )
            try:
                with open(meta_tmp, "w", encoding="utf-8") as handle:
                    json.dump(meta, handle, indent=2, ensure_ascii=False)
                os.replace(meta_tmp, self._self_play_meta_file)
            finally:
                try:
                    if meta_tmp.exists():
                        meta_tmp.unlink()
                except OSError:
                    pass

        snapshot = self._self_play_lock_snapshot()
        env_override = snapshot.get("lock_source") == "env:MUADIB_SELF_PLAY_LOCK_ACTIVE"
        return {
            "ok": True,
            "surface": "bb7_dt_self_play_lock",
            "requested_locked": bool(locked),
            "effective_locked": bool(snapshot.get("active_locked", False)),
            "lock_source": snapshot.get("lock_source"),
            "env_override": env_override,
            "locked_checkpoint": snapshot.get("locked_checkpoint"),
            "note": (
                "This is a promotion/champion lock. Safetensors files remain "
                "real tensor checkpoints; continuous self-play may still archive "
                "candidates while the active head is locked."
            ),
        }

    def bb7_dt_checkpoint_status(self) -> Dict[str, Any]:
        """Return tensor checkpoint status without loading or mutating weights."""
        tokenizer_meta = self._read_json_file(self._checkpoint_meta_file)
        self_play_meta = self._read_json_file(self._self_play_meta_file)
        lock_snapshot = self._self_play_lock_snapshot()
        tokenizer_safetensors = sorted(
            p.name for p in self._checkpoint_dir.glob("checkpoint_v*.safetensors")
        )
        tokenizer_legacy_pt = sorted(
            p.name for p in self._checkpoint_dir.glob("checkpoint_v*.pt")
        )
        self_play_safetensors = sorted(
            p.name for p in self.self_play_dir.glob("self_play_head_v*.safetensors")
        )
        return {
            "ok": True,
            "torch_available": _TORCH_AVAILABLE,
            "safetensors_available": _SAFETENSORS_AVAILABLE,
            "tokenizer": {
                "meta": tokenizer_meta,
                "safetensors_checkpoints": tokenizer_safetensors,
                "legacy_pt_checkpoints": tokenizer_legacy_pt,
                "active_format": tokenizer_meta.get("format"),
            },
            "self_play": {
                "available": _SELF_PLAY_AVAILABLE,
                "head_initialized": self._self_play_head is not None,
                "meta": self_play_meta,
                "safetensors_checkpoints": self_play_safetensors,
                "active_checkpoint": self_play_meta.get("active_checkpoint"),
                "active_locked": lock_snapshot.get("active_locked", False),
                "lock_source": lock_snapshot.get("lock_source"),
                "locked_checkpoint": lock_snapshot.get("locked_checkpoint"),
            },
        }

    # -- server registration surface ----------------------------------------

    def get_tools(self) -> Dict[str, Callable[..., Dict[str, Any]]]:
        """
        Return the bb7_ tool map the server registers from this file.

        Matches the pattern used by memory_tool.py, exoskeleton_tool.py, etc.
        """
        return {
            "bb7_dt_observe": self.bb7_dt_observe,
            "bb7_dt_q_scores": self.bb7_dt_q_scores,
            "bb7_dt_encode": self.bb7_dt_encode,
            "bb7_dt_encode_catalog": self.bb7_dt_encode_catalog,
            "bb7_dt_advanced_features": self.bb7_dt_advanced_features,
            "bb7_dt_self_play": self.bb7_dt_self_play,
            "bb7_dt_self_play_lock": self.bb7_dt_self_play_lock,
            "bb7_dt_checkpoint_status": self.bb7_dt_checkpoint_status,
            "bb7_dt_status": self.bb7_dt_status,
            "bb7_dt_save": self.bb7_dt_save,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  §5  MODULE-LEVEL SMOKE TEST
# ═══════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("digital_twin_tool")

    print("=" * 72)
    print("  DIGITAL TWIN TOOL — PHASE 1 SMOKE TEST")
    print("=" * 72)

    # Run in a tmp dir so the smoke test doesn't pollute real state
    import tempfile

    tmp_root = Path(tempfile.mkdtemp(prefix="digital_twin_smoke_"))
    print(f"\n[smoke] tmp data dir: {tmp_root}")

    tool = DigitalTwinTool(data_dir=tmp_root)

    # --- §1: observe a chain of tool calls -------------------------------
    print("\n[§1] Observing tool calls...")
    calls = [
        ("bb7_exo_bootstrap", "exoskeleton", True, 120.0, 1),
        ("bb7_lisan_intend", "exoskeleton", True, 85.0, 2),
        ("bb7_exo_route", "exoskeleton", True, 200.0, 3),
        ("bb7_memory_store", "memory", True, 45.0, 4),
        ("bb7_exo_reflect", "exoskeleton", True, 60.0, 5),
        ("bb7_run_command", "shell", False, 800.0, 1),  # intentional failure
    ]
    for name, cat, success, latency, chain_len in calls:
        r = tool.bb7_dt_observe(
            tool_name=name,
            category=cat,
            success=success,
            latency_ms=latency,
            chain_length=chain_len,
            session_id="smoke_test",
        )
        print(
            f"     {name:<24} success={success} "
            f"reward={r.get('reward'):+.2f} q={r.get('q_value'):+.4f}"
        )

    # --- §2: Q-bonus query -----------------------------------------------
    print("\n[§2] Q-bonus query for candidates:")
    candidates = [
        "bb7_memory_store",
        "bb7_exo_reflect",
        "bb7_run_command",
        "bb7_never_seen",
    ]
    resp = tool.bb7_dt_q_scores(
        candidates=candidates,
        category="exoskeleton",
        session_id="smoke_test",
    )
    for name, bonus in resp["bonuses"].items():
        print(f"     {name:<24} bonus = {bonus:+.4f}")

    # --- §3: Encode (torch path) -----------------------------------------
    print("\n[§3] Encode symbolic sequence -> hidden_states:")
    if _TORCH_AVAILABLE:
        seq = [
            {"tool_name": "bb7_exo_bootstrap", "category": "exoskeleton"},
            {"tool_name": "bb7_lisan_intend", "category": "exoskeleton"},
            {"tool_name": "bb7_memory_store", "category": "memory"},
        ]
        enc = tool.bb7_dt_encode(tool_sequence=seq)
        if enc["ok"]:
            print(f"     shape            = {enc['shape']}")
            print(f"     d_model          = {enc['d_model']}")
            print(f"     sequence_length  = {enc['sequence_length']}")
            print(
                f"     sample activation (batch=0, pos=0, dim=0..3) = "
                f"{enc['hidden_states'][0][0][:4]}"
            )
        else:
            print(f"     ENCODE FAILED: {enc.get('error')}")
    else:
        print("     torch unavailable — tokenizer disabled, backbone active")

    # --- §4: status snapshot ---------------------------------------------
    print("\n[§4] Status:")
    status = tool.bb7_dt_status()
    for k, v in status.items():
        if k == "top_q":
            print(f"     top_q:")
            for entry in v:
                print(
                    f"        state={entry['state']} "
                    f"action={entry['action']:<22} q={entry['q']:+.4f}"
                )
        else:
            print(f"     {k:<24} {v}")

    # --- §5: persistence round-trip --------------------------------------
    print("\n[§5] Persistence round-trip:")
    save_result = tool.bb7_dt_save()
    print(f"     save: {save_result}")
    tool2 = DigitalTwinTool(data_dir=tmp_root)
    s2 = tool2.bb7_dt_status()
    assert s2["observations"] == status["observations"], "observation count mismatch"
    assert s2["q_entries"] == status["q_entries"], "q-entry count mismatch"
    print(
        f"     reload: observations={s2['observations']} "
        f"q_entries={s2['q_entries']} ✓"
    )

    # cleanup
    import shutil

    shutil.rmtree(tmp_root, ignore_errors=True)

    print("\n" + "=" * 72)
    print("  PHASE 1 SMOKE TEST PASSED")
    print("=" * 72)
