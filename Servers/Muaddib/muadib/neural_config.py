#!/usr/bin/env python3
"""
Neural Configuration and Primitive Components for the Muad'Dib Neural Substrate.

Defines NeuralNetConfig (the dataclass consumed by all neural memory modules)
and foundational components that aeron_neural_memory.py depends on:
  - AeronRMSNorm       (Pre-norm layer normalization, LLaMA-style)
  - AeronRotaryEmbedding (RoPE with NTK-aware dynamic scaling)
  - apply_rotary_pos_emb (rotary application helper)
  - summarize_per_class_uncertainty (active learning utility)

This file must import cleanly without side effects.

Source: Sovereign MCP Server — Muad'Dib Neural Substrate
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, List

import torch
import torch.nn as nn
import torch.nn.functional as F


# ═══════════════════════════════════════════════════════════════════════════
#  NEURAL NET CONFIG
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class NeuralNetConfig:
    """
    Configuration for the Muad'Dib neural memory backbone.

    Consumed by: MultiHeadAttention, KnowledgeGraphAttention,
    FeedForwardNetwork, TransformerEncoder/DecoderLayer,
    NeuralMemoryNetwork, ContinualLearningModule,
    UncertaintyQuantification, ActiveLearningManager.

    Maps cleanly from SubstrateConfig via the from_substrate classmethod.
    """

    # ── Core dimensions ──────────────────────────────────────────────────
    d_model: int = 512
    nhead: int = 8
    num_kv_heads: int = 4          # GQA: KV heads shared across query heads
    dim_feedforward: int = 2048    # SwiGLU intermediate (before 2/3 reduction)
    vocab_size: int = 4096         # Max tool identifiers

    # ── Derived (computed from core, cached for perf) ────────────────────
    head_dim: int = field(init=False)
    num_kv_groups: int = field(init=False)

    # ── Regularization ───────────────────────────────────────────────────
    dropout: float = 0.1

    # ── Positional encoding ──────────────────────────────────────────────
    max_position_embeddings: int = 512
    rope_theta: float = 10000.0
    rope_scaling: float = 1.0      # NTK-aware scaling factor

    # ── Initialization ───────────────────────────────────────────────────
    initializer_range: float = 1.0  # Xavier gain

    # ── Normalization ────────────────────────────────────────────────────
    rms_norm_eps: float = 1e-6

    def __post_init__(self) -> None:
        """Compute derived fields and validate constraints."""
        self.head_dim = self.d_model // self.nhead
        if self.d_model % self.nhead != 0:
            raise ValueError(
                f"d_model ({self.d_model}) must be divisible by nhead ({self.nhead})"
            )
        if self.nhead % self.num_kv_heads != 0:
            raise ValueError(
                f"nhead ({self.nhead}) must be divisible by "
                f"num_kv_heads ({self.num_kv_heads})"
            )
        self.num_kv_groups = self.nhead // self.num_kv_heads

    @classmethod
    def from_substrate(cls, substrate_config) -> "NeuralNetConfig":
        """
        Bridge a SubstrateConfig (from muaddib.py) into a NeuralNetConfig.

        Preserves d_model and vocab_size from the substrate; applies
        neural-specific defaults for everything else.
        """
        d_model = getattr(substrate_config, "d_model", 512)
        vocab_size = getattr(substrate_config, "vocab_size", 4096)
        dropout = getattr(substrate_config, "dropout", 0.1)
        rope_theta = getattr(substrate_config, "rope_theta", 10000.0)
        max_seq = getattr(substrate_config, "max_seq_len", 512)

        # GQA configuration: 8 query heads, 4 KV heads (2:1 ratio)
        nhead = 8
        num_kv_heads = 4

        return cls(
            d_model=d_model,
            nhead=nhead,
            num_kv_heads=num_kv_heads,
            dim_feedforward=d_model * 4,
            vocab_size=vocab_size,
            dropout=dropout if dropout > 0 else 0.1,
            max_position_embeddings=max_seq,
            rope_theta=rope_theta,
        )


# ═══════════════════════════════════════════════════════════════════════════
#  AERON RMS NORM
# ═══════════════════════════════════════════════════════════════════════════


class AeronRMSNorm(nn.Module):
    """
    Root Mean Square Layer Normalization (LLaMA / Gemma style).

    Cheaper than LayerNorm — no mean subtraction, no bias term.
    Empirically matches or exceeds LayerNorm for transformer pre-norm.

    weight * (x / sqrt(mean(x^2) + eps))
    """

    def __init__(self, hidden_size: int, eps: float = 1e-6) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.variance_epsilon = eps

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        input_dtype = hidden_states.dtype
        hidden_states = hidden_states.to(torch.float32)
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.variance_epsilon)
        return self.weight * hidden_states.to(input_dtype)

    def extra_repr(self) -> str:
        return f"{self.weight.shape[0]}, eps={self.variance_epsilon}"


# ═══════════════════════════════════════════════════════════════════════════
#  AERON ROTARY EMBEDDING (RoPE)
# ═══════════════════════════════════════════════════════════════════════════


class AeronRotaryEmbedding(nn.Module):
    """
    Rotary Position Embedding with NTK-aware dynamic scaling.

    Standard RoPE implementation compatible with GQA heads.
    Caches cos/sin tables for the max sequence length seen so far,
    extending dynamically when longer sequences appear.

    Reference: Su et al. 2021 — "RoFormer: Enhanced Transformer with
    Rotary Position Embedding"
    """

    def __init__(
        self,
        dim: int,
        max_position_embeddings: int = 512,
        base: float = 10000.0,
        scaling_factor: float = 1.0,
    ) -> None:
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        self.scaling_factor = scaling_factor

        # Compute inverse frequencies
        inv_freq = 1.0 / (
            self.base ** (torch.arange(0, self.dim, 2).float() / self.dim)
        )
        self.register_buffer("inv_freq", inv_freq, persistent=False)

        # Build initial cos/sin cache
        self._set_cos_sin_cache(max_position_embeddings)

    def _set_cos_sin_cache(self, seq_len: int) -> None:
        """Build or extend the cos/sin position cache."""
        self.max_seq_len_cached = seq_len
        t = torch.arange(seq_len, device=self.inv_freq.device, dtype=torch.float32)

        # NTK-aware scaling
        if self.scaling_factor != 1.0:
            t = t / self.scaling_factor

        freqs = torch.outer(t, self.inv_freq)
        # [seq_len, dim/2] → [seq_len, dim] via cat
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos_cached", emb.cos(), persistent=False)
        self.register_buffer("sin_cached", emb.sin(), persistent=False)

    def forward(
        self, x: torch.Tensor, seq_len: Optional[int] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns (cos, sin) position tables of shape [seq_len, head_dim].

        Args:
            x: Input tensor (only used for device/dtype inference)
            seq_len: Sequence length to compute positions for
        """
        if seq_len is None:
            seq_len = x.shape[-2]

        if seq_len > self.max_seq_len_cached:
            self._set_cos_sin_cache(seq_len)

        return (
            self.cos_cached[:seq_len].to(dtype=x.dtype),
            self.sin_cached[:seq_len].to(dtype=x.dtype),
        )


# ═══════════════════════════════════════════════════════════════════════════
#  ROTARY APPLICATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotates half the hidden dims of the input for RoPE."""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Apply rotary position embeddings to query and key tensors.

    Args:
        q: Query tensor [batch, heads, seq_len, head_dim]
        k: Key tensor   [batch, heads, seq_len, head_dim]
        cos: Cosine position table [seq_len, head_dim]
        sin: Sine position table   [seq_len, head_dim]

    Returns:
        Tuple of (q_rotated, k_rotated) with same shapes as input.
    """
    # Reshape cos/sin to broadcast: [1, 1, seq_len, head_dim]
    cos = cos.unsqueeze(0).unsqueeze(0)
    sin = sin.unsqueeze(0).unsqueeze(0)

    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


# ═══════════════════════════════════════════════════════════════════════════
#  ACTIVE LEARNING UTILITY
# ═══════════════════════════════════════════════════════════════════════════


def summarize_per_class_uncertainty(
    per_class_tensor: torch.Tensor, top_k: int = 5
) -> Dict[str, torch.Tensor]:
    """
    Reduce per-class epistemic uncertainty to sample-level scores and
    token summaries.

    Used by ActiveLearningManager._summarize_per_class_uncertainty.

    Args:
        per_class_tensor: Uncertainty per class, shape varies by source.
            Typical: [batch, seq_len, vocab_size] or [batch, vocab_size].
        top_k: Number of top uncertain classes to retain per sample.

    Returns:
        Dict with:
          - 'sample_scores': [batch] — mean uncertainty per sample
          - 'top_scores': [batch, top_k] — top-k uncertainties per sample
          - 'top_indices': [batch, top_k] — class indices of top-k
    """
    # Collapse to [batch, classes] if 3D
    if per_class_tensor.dim() == 3:
        # Mean over sequence dimension
        per_class_tensor = per_class_tensor.mean(dim=1)

    # Ensure 2D
    if per_class_tensor.dim() == 1:
        per_class_tensor = per_class_tensor.unsqueeze(0)

    # Sample-level scores (mean over classes)
    sample_scores = per_class_tensor.mean(dim=-1)

    # Top-k per sample
    actual_k = min(top_k, per_class_tensor.shape[-1])
    top_scores, top_indices = torch.topk(per_class_tensor, k=actual_k, dim=-1)

    return {
        "sample_scores": sample_scores,
        "top_scores": top_scores,
        "top_indices": top_indices,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  MUAD'DIB SELF-PLAY POLICY/VALUE HEAD
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class SelfPlayConfig:
    """
    Configuration for Muad'Dib's bounded self-play policy/value head.

    This is intentionally separate from the main NeuralSubstrateTokenizer.
    Continuous self-play trains candidate policy/value weights, writes them as
    safetensors checkpoints, and only promotes a fully-written candidate. JSON
    files remain metadata/ledger only; tensor weights live in safetensors.
    """

    d_model: int = 512
    vocab_size: int = 4096
    max_seq_len: int = 16
    hidden_size: int = 512
    dropout: float = 0.05
    policy_weight: float = 1.0
    value_weight: float = 0.5
    entropy_weight: float = 0.01
    checkpoint_keep: int = 5
    seed: int = 1337

    def __post_init__(self) -> None:
        if self.d_model <= 0:
            raise ValueError("d_model must be positive")
        if self.vocab_size <= 1:
            raise ValueError("vocab_size must be greater than 1")
        if self.max_seq_len <= 0:
            raise ValueError("max_seq_len must be positive")
        if self.hidden_size <= 0:
            raise ValueError("hidden_size must be positive")
        if not (0.0 <= self.dropout < 1.0):
            raise ValueError("dropout must be in [0.0, 1.0)")

    @classmethod
    def from_substrate(cls, substrate_config) -> "SelfPlayConfig":
        """Bridge a SubstrateConfig-like object into self-play defaults."""
        return cls(
            d_model=int(getattr(substrate_config, "d_model", 512)),
            vocab_size=int(getattr(substrate_config, "vocab_size", 4096)),
            max_seq_len=min(16, int(getattr(substrate_config, "max_seq_len", 64))),
        )


class MuadDibSelfPlayHead(nn.Module):
    """
    Small policy/value network trained by Muad'Dib self-play.

    Input:
      tool_ids: [batch, seq_len]
      attention_mask: optional [batch, seq_len] boolean mask

    Output:
      policy_logits: [batch, vocab_size]
      value: [batch]
      pooled: [batch, d_model]

    The head is deliberately compact and isolated. It can be trained
    continuously without mutating the live tokenizer in-place.
    """

    def __init__(self, config: SelfPlayConfig) -> None:
        super().__init__()
        self.config = config
        self.tool_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.position_embedding = nn.Embedding(config.max_seq_len, config.d_model)
        self.input_norm = AeronRMSNorm(config.d_model)
        self.encoder = nn.Sequential(
            nn.Linear(config.d_model, config.hidden_size),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_size, config.d_model),
        )
        self.output_norm = AeronRMSNorm(config.d_model)
        self.policy_head = nn.Linear(config.d_model, config.vocab_size)
        self.value_head = nn.Sequential(
            nn.Linear(config.d_model, config.hidden_size),
            nn.SiLU(),
            nn.Linear(config.hidden_size, 1),
            nn.Tanh(),
        )
        self._init_weights()

    def _init_weights(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(
        self,
        tool_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        if tool_ids.dim() != 2:
            raise ValueError("tool_ids must have shape [batch, seq_len]")

        batch_size, seq_len = tool_ids.shape
        if seq_len > self.config.max_seq_len:
            raise ValueError(
                f"sequence length {seq_len} exceeds max_seq_len={self.config.max_seq_len}"
            )

        positions = torch.arange(seq_len, device=tool_ids.device).unsqueeze(0)
        positions = positions.expand(batch_size, seq_len)
        x = self.tool_embedding(tool_ids) + self.position_embedding(positions)
        x = self.input_norm(x)
        x = x + self.encoder(x)
        x = self.output_norm(x)

        if attention_mask is None:
            pooled = x.mean(dim=1)
        else:
            mask = attention_mask.to(dtype=x.dtype).unsqueeze(-1)
            denom = mask.sum(dim=1).clamp_min(1.0)
            pooled = (x * mask).sum(dim=1) / denom

        return {
            "policy_logits": self.policy_head(pooled),
            "value": self.value_head(pooled).squeeze(-1),
            "pooled": pooled,
        }
