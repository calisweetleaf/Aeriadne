#!/usr/bin/env python3
"""
Aeron Neural Memory — Production Backbone for the Muad'Dib Neural Substrate.

Contains the complete neural architecture stack:
  - MultiHeadAttention (GQA + RoPE)
  - KnowledgeGraphAttention (KG-enhanced attention extending MHA)
  - FeedForwardNetwork (SwiGLU)
  - TransformerEncoderLayer / TransformerDecoderLayer (Pre-Norm)
  - NeuralMemoryNetwork (Persistent external memory with R/W heads)
  - ContinualLearningModule (EWC anti-forgetting)
  - UncertaintyQuantification (MC Dropout, Deep Ensembles, Evidential DL)
  - ActiveLearningManager (Multi-strategy sample selection)

Source: Sovereign MCP Server — Muad'Dib Neural Substrate
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

from .neural_config import (
    NeuralNetConfig,
    AeronRMSNorm,
    AeronRotaryEmbedding,
    apply_rotary_pos_emb,
    summarize_per_class_uncertainty,
)


class MultiHeadAttention(nn.Module):
    """
    Grouped Query Attention (GQA) with Rotary Position Embeddings (RoPE).
    
    GQA shares K/V projections across groups of query heads. When
    num_kv_heads == nhead, this is standard MHA. When num_kv_heads == 1,
    this is Multi-Query Attention (MQA).
    
    Uses PyTorch's F.scaled_dot_product_attention for automatic FlashAttention-2 / 
    memory-efficient backend selection.
    """
    def __init__(self, config: NeuralNetConfig, is_decoder: bool = False,
                 is_cross_attention: bool = False):
        super().__init__()
        self.config = config
        self.nhead = config.nhead
        self.num_kv_heads = config.num_kv_heads
        self.d_model = config.d_model
        self.head_dim = config.head_dim
        self.num_kv_groups = config.num_kv_groups
        self.dropout_rate = config.dropout
        self.is_decoder = is_decoder
        self.is_cross_attention = is_cross_attention
        
        self.q_proj = nn.Linear(config.d_model, config.nhead * self.head_dim, bias=False)
        self.k_proj = nn.Linear(config.d_model, config.num_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(config.d_model, config.num_kv_heads * self.head_dim, bias=False)
        self.out_proj = nn.Linear(config.nhead * self.head_dim, config.d_model, bias=False)
        
        self.scale = 1.0 / math.sqrt(self.head_dim)
        
        self.attn_dropout = nn.Dropout(config.dropout)
        self.proj_dropout = nn.Dropout(config.dropout)
        
        if not self.is_cross_attention:
            self.rotary_emb = AeronRotaryEmbedding(
                dim=self.head_dim,
                max_position_embeddings=config.max_position_embeddings,
                base=config.rope_theta,
                scaling_factor=config.rope_scaling
            )
        
        self._init_weights()
    
    def _init_weights(self):
        """Initialize attention projection weights."""
        nn.init.xavier_uniform_(self.q_proj.weight, gain=self.config.initializer_range)
        nn.init.xavier_uniform_(self.k_proj.weight, gain=self.config.initializer_range)
        nn.init.xavier_uniform_(self.v_proj.weight, gain=self.config.initializer_range)
        nn.init.xavier_uniform_(self.out_proj.weight, gain=self.config.initializer_range)
    
    def _repeat_kv(self, hidden_states: torch.Tensor, n_rep: int) -> torch.Tensor:
        """Expand KV heads to match Q heads for GQA."""
        if n_rep == 1:
            return hidden_states
        batch, num_kv_heads, seq_len, head_dim = hidden_states.shape
        hidden_states = hidden_states[:, :, None, :, :].expand(
            batch, num_kv_heads, n_rep, seq_len, head_dim
        )
        return hidden_states.reshape(batch, num_kv_heads * n_rep, seq_len, head_dim)
    
    def forward(self, 
                query: torch.Tensor, 
                key: torch.Tensor, 
                value: torch.Tensor,
                attn_mask: Optional[torch.Tensor] = None,
                key_padding_mask: Optional[torch.Tensor] = None,
                position_bias: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        GQA + RoPE forward pass.
        
        Args:
            query: (batch_size, tgt_len, d_model)
            key: (batch_size, src_len, d_model)
            value: (batch_size, src_len, d_model)
            attn_mask: Attention mask (optional)
            key_padding_mask: Padding mask for keys (optional)
            position_bias: Legacy (ignored, RoPE handles positioning)
        
        Returns:
            attn_output: (batch_size, tgt_len, d_model)
            attn_weights: (batch_size, nhead, tgt_len, src_len)
        """
        batch_size, tgt_len, _ = query.size()
        src_len = key.size(1)
        
        Q = self.q_proj(query).view(batch_size, tgt_len, self.nhead, self.head_dim).transpose(1, 2)
        K = self.k_proj(key).view(batch_size, src_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        V = self.v_proj(value).view(batch_size, src_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        
        # Apply RoPE (self-attention only)
        if not self.is_cross_attention:
            cos, sin = self.rotary_emb(Q, seq_len=max(tgt_len, src_len))
            Q, K = apply_rotary_pos_emb(Q, K, cos[:tgt_len], sin[:tgt_len])
        
        # GQA: expand KV heads
        K = self._repeat_kv(K, self.num_kv_groups)
        V = self._repeat_kv(V, self.num_kv_groups)
        
        # Use PyTorch SDPA (auto-selects FlashAttention-2 / memory-efficient backend)
        try:
            sdpa_attn_mask = None
            is_causal = self.is_decoder and not self.is_cross_attention and tgt_len == src_len
            
            if key_padding_mask is not None:
                sdpa_attn_mask = key_padding_mask.unsqueeze(1).unsqueeze(2)
                sdpa_attn_mask = sdpa_attn_mask.expand(-1, -1, tgt_len, -1)
                sdpa_attn_mask = sdpa_attn_mask.to(dtype=Q.dtype)
                sdpa_attn_mask = sdpa_attn_mask.masked_fill(sdpa_attn_mask == 1, float('-inf'))
                is_causal = False
            
            if attn_mask is not None:
                if attn_mask.dim() == 2:
                    attn_mask = attn_mask.unsqueeze(0).unsqueeze(0)
                elif attn_mask.dim() == 3:
                    attn_mask = attn_mask.unsqueeze(1)
                attn_mask = attn_mask.to(device=Q.device)
                float_mask = torch.zeros_like(attn_mask, dtype=Q.dtype)
                if attn_mask.dtype == torch.bool:
                    float_mask = float_mask.masked_fill(~attn_mask, float('-inf'))
                else:
                    float_mask = float_mask.masked_fill(attn_mask == 0, float('-inf'))
                if sdpa_attn_mask is not None:
                    sdpa_attn_mask = sdpa_attn_mask + float_mask
                else:
                    sdpa_attn_mask = float_mask
                is_causal = False
            
            attn_output = F.scaled_dot_product_attention(
                Q, K, V,
                attn_mask=sdpa_attn_mask,
                dropout_p=self.dropout_rate if self.training else 0.0,
                is_causal=is_causal,
                scale=self.scale
            )
            with torch.no_grad():
                _diag_scores = torch.matmul(Q * self.scale, K.transpose(-2, -1))
                if sdpa_attn_mask is not None:
                    _diag_scores = _diag_scores + sdpa_attn_mask
                elif is_causal:
                    # Reproduce causal mask for diagnostic accuracy
                    _causal = torch.triu(
                        torch.full(
                            (_diag_scores.shape[-2], _diag_scores.shape[-1]),
                            float('-inf'), device=Q.device, dtype=Q.dtype
                        ),
                        diagonal=1
                    )
                    _diag_scores = _diag_scores + _causal
                attn_weights = F.softmax(_diag_scores, dim=-1)
        except Exception:
            # Fallback: manual attention
            attn_scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
            if attn_mask is not None:
                if attn_mask.dim() == 2:
                    attn_mask = attn_mask.unsqueeze(0).unsqueeze(0)
                elif attn_mask.dim() == 3:
                    attn_mask = attn_mask.unsqueeze(1)
                attn_mask = attn_mask.to(device=attn_scores.device)
                if attn_mask.dtype == torch.bool:
                    attn_scores = attn_scores.masked_fill(~attn_mask, float('-inf'))
                else:
                    attn_scores = attn_scores.masked_fill(attn_mask == 0, float('-inf'))
            if key_padding_mask is not None:
                kpm = key_padding_mask.unsqueeze(1).unsqueeze(2)
                attn_scores = attn_scores.masked_fill(kpm == 1, float('-inf'))
            attn_weights = F.softmax(attn_scores, dim=-1)
            attn_weights = self.attn_dropout(attn_weights)
            attn_output = torch.matmul(attn_weights, V)
        
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, tgt_len, self.d_model)
        attn_output = self.out_proj(attn_output)
        attn_output = self.proj_dropout(attn_output)
        
        return attn_output, attn_weights


class KnowledgeGraphAttention(MultiHeadAttention):
    """
    Knowledge Graph Enhanced Attention — injects structured knowledge
    from a knowledge graph into the attention mechanism.
    Inherits GQA + RoPE from base MultiHeadAttention.
    """
    def __init__(self, config: NeuralNetConfig, kg_dim: int = 128, num_relations: int = 50, 
                 max_entities: int = 100000, cache_size: int = 10000):
        super().__init__(config)
        self.kg_dim = kg_dim
        self.num_relations = num_relations
        self.max_entities = max_entities
        self.cache_size = cache_size
        
        self.relation_embeddings = nn.Embedding(num_relations, kg_dim)
        self.entity_embeddings = nn.Embedding(max_entities, kg_dim)
        
        self.kg_injector = nn.Sequential(
            nn.Linear(config.d_model + kg_dim, config.d_model * 2),
            AeronRMSNorm(config.d_model * 2),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model * 2, config.d_model),
            nn.Dropout(config.dropout)
        )
        
        self.kg_attention_bias = nn.Sequential(
            nn.Linear(kg_dim * 2, kg_dim),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(kg_dim, 1)
        )
        
        self.entity_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.kg_stats = {
            'total_queries': 0,
            'successful_lookups': 0,
            'cache_efficiency': 0.0
        }
        self._init_kg_weights()
    
    def _init_kg_weights(self):
        """Initialize knowledge graph specific weights."""
        nn.init.normal_(self.relation_embeddings.weight, std=0.02)
        nn.init.normal_(self.entity_embeddings.weight, std=0.02)
        for module in [self.kg_injector, self.kg_attention_bias]:
            for layer in module:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    if layer.bias is not None:
                        nn.init.zeros_(layer.bias)
    
    def _get_cached_entity_features(self, entity_id: int, knowledge_graph: Dict) -> Optional[torch.Tensor]:
        """Get cached entity features or compute and cache them."""
        cache_key = f"entity_{entity_id}"
        if cache_key in self.entity_cache:
            self.cache_hits += 1
            return self.entity_cache[cache_key]
        self.cache_misses += 1
        if entity_id not in knowledge_graph:
            return None
        relations = knowledge_graph[entity_id].get('relations', [])
        if not relations:
            return None
        if isinstance(relations, list):
            relations = torch.tensor(relations, dtype=torch.long, device=self.entity_embeddings.weight.device)
        rel_embeds = self.relation_embeddings(relations)
        entity_features = rel_embeds.mean(dim=0)
        if len(self.entity_cache) >= self.cache_size:
            oldest_key = next(iter(self.entity_cache))
            del self.entity_cache[oldest_key]
        self.entity_cache[cache_key] = entity_features.detach()
        return entity_features
    
    def get_entity_relations(self, entities: torch.Tensor, knowledge_graph: Dict) -> torch.Tensor:
        """Batch entity relation retrieval with caching."""
        self.kg_stats['total_queries'] += 1
        if knowledge_graph is None:
            return torch.zeros(entities.shape + (self.kg_dim,), device=entities.device)
        batch_size, seq_len = entities.shape
        kg_features = torch.zeros(batch_size, seq_len, self.kg_dim, device=entities.device)
        successful_lookups = 0
        for b in range(batch_size):
            entity_batch = entities[b]
            unique_entities = torch.unique(entity_batch)
            entity_feature_map = {}
            for entity_id in unique_entities:
                if entity_id.item() == 0:
                    continue
                features = self._get_cached_entity_features(entity_id.item(), knowledge_graph)
                if features is not None:
                    entity_feature_map[entity_id.item()] = features
                    successful_lookups += 1
            for i in range(seq_len):
                entity_id = entity_batch[i].item()
                if entity_id in entity_feature_map:
                    kg_features[b, i] = entity_feature_map[entity_id]
        self.kg_stats['successful_lookups'] += successful_lookups
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            self.kg_stats['cache_efficiency'] = self.cache_hits / total_cache_requests
        return kg_features
    
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor, 
                input_entities: Optional[torch.Tensor] = None, 
                knowledge_graph: Optional[Dict] = None,
                attn_mask: Optional[torch.Tensor] = None,
                key_padding_mask: Optional[torch.Tensor] = None,
                position_bias: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass with KG integration layered on top of GQA + RoPE."""
        attn_output, attn_weights = super().forward(
            query, key, value, attn_mask, key_padding_mask, position_bias
        )
        if input_entities is not None and knowledge_graph is not None:
            try:
                kg_features = self.get_entity_relations(input_entities, knowledge_graph)
                if kg_features.sum() == 0:
                    return attn_output, attn_weights
                combined_features = torch.cat([query, kg_features], dim=-1)
                kg_injection = self.kg_injector(combined_features)
                attn_output = attn_output + kg_injection
            except Exception as e:
                print(f"Warning: KG attention failed, falling back: {e}")
        return attn_output, attn_weights
    
    def get_kg_statistics(self) -> Dict[str, float]:
        """Get knowledge graph usage statistics."""
        return self.kg_stats.copy()
    
    def clear_cache(self):
        """Clear the entity cache."""
        self.entity_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0


class FeedForwardNetwork(nn.Module):
    """
    SwiGLU Feed-Forward Network — SOTA FFN architecture.
    
    SwiGLU: SiLU(W_gate @ x) * (W_up @ x) -> W_down.
    Consistently outperforms GELU/ReLU FFN.
    Used by LLaMA, Mistral, Gemma, DeepSeek, Qwen.
    
    Intermediate dim = 2/3 * dim_feedforward (3 matrices instead of 2
    keeps total params roughly equal to standard FFN).
    """
    def __init__(self, config: NeuralNetConfig):
        super().__init__()
        self.config = config
        intermediate_size = int(2 * config.dim_feedforward / 3)
        intermediate_size = ((intermediate_size + 255) // 256) * 256
        self.intermediate_size = intermediate_size
        
        self.gate_proj = nn.Linear(config.d_model, intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.d_model, intermediate_size, bias=False)
        self.down_proj = nn.Linear(intermediate_size, config.d_model, bias=False)
        self.act_fn = nn.SiLU()
        self.dropout = nn.Dropout(config.dropout)
        self._init_weights()
    
    def _init_weights(self):
        """Initialize SwiGLU weights."""
        nn.init.xavier_uniform_(self.gate_proj.weight, gain=self.config.initializer_range)
        nn.init.xavier_uniform_(self.up_proj.weight, gain=self.config.initializer_range)
        nn.init.xavier_uniform_(self.down_proj.weight, gain=self.config.initializer_range)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """SwiGLU: SiLU(gate(x)) * up(x) -> down -> dropout."""
        return self.dropout(self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x)))


class TransformerEncoderLayer(nn.Module):
    """
    Pre-Norm Encoder Layer with GQA + SwiGLU + RMSNorm.
    
    Pre-norm: norm BEFORE attention/FFN for better gradient flow in deep networks.
    Flow: x -> RMSNorm -> Self-Attn -> residual -> RMSNorm -> SwiGLU -> residual
    """
    def __init__(self, config: NeuralNetConfig):
        super().__init__()
        self.config = config
        self.self_attn = MultiHeadAttention(config)
        self.feed_forward = FeedForwardNetwork(config)
        self.input_layernorm = AeronRMSNorm(config.d_model, eps=config.rms_norm_eps)
        self.post_attention_layernorm = AeronRMSNorm(config.d_model, eps=config.rms_norm_eps)
    
    def forward(self, 
                src: torch.Tensor, 
                src_mask: Optional[torch.Tensor] = None,
                src_key_padding_mask: Optional[torch.Tensor] = None,
                position_bias: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Pre-norm encoder forward pass."""
        residual = src
        src = self.input_layernorm(src)
        attn_output, attn_weights = self.self_attn(
            src, src, src, 
            attn_mask=src_mask,
            key_padding_mask=src_key_padding_mask
        )
        src = residual + attn_output
        
        residual = src
        src = self.post_attention_layernorm(src)
        ffn_output = self.feed_forward(src)
        src = residual + ffn_output
        
        return src, attn_weights


class TransformerDecoderLayer(nn.Module):
    """
    Pre-Norm Decoder Layer with GQA + SwiGLU + RMSNorm.
    
    Three sub-layers: masked self-attn, cross-attn, SwiGLU FFN.
    Flow: x -> RMSNorm -> Self-Attn -> res -> RMSNorm -> Cross-Attn -> res -> RMSNorm -> SwiGLU -> res
    """
    def __init__(self, config: NeuralNetConfig):
        super().__init__()
        self.config = config
        self.self_attn = MultiHeadAttention(config, is_decoder=True)
        self.cross_attn = MultiHeadAttention(config, is_decoder=True, is_cross_attention=True)
        self.feed_forward = FeedForwardNetwork(config)
        self.input_layernorm = AeronRMSNorm(config.d_model, eps=config.rms_norm_eps)
        self.post_attention_layernorm = AeronRMSNorm(config.d_model, eps=config.rms_norm_eps)
        self.post_cross_attention_layernorm = AeronRMSNorm(config.d_model, eps=config.rms_norm_eps)
    
    def forward(self, 
                tgt: torch.Tensor, 
                memory: torch.Tensor,
                tgt_mask: Optional[torch.Tensor] = None,
                tgt_key_padding_mask: Optional[torch.Tensor] = None,
                memory_key_padding_mask: Optional[torch.Tensor] = None,
                position_bias: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Pre-norm decoder forward pass."""
        residual = tgt
        tgt = self.input_layernorm(tgt)
        self_attn_output, self_attn_weights = self.self_attn(
            tgt, tgt, tgt,
            attn_mask=tgt_mask,
            key_padding_mask=tgt_key_padding_mask
        )
        tgt = residual + self_attn_output
        
        residual = tgt
        tgt = self.post_attention_layernorm(tgt)
        cross_attn_output, cross_attn_weights = self.cross_attn(
            tgt, memory, memory,
            attn_mask=None,
            key_padding_mask=memory_key_padding_mask
        )
        tgt = residual + cross_attn_output
        
        residual = tgt
        tgt = self.post_cross_attention_layernorm(tgt)
        ffn_output = self.feed_forward(tgt)
        tgt = residual + ffn_output
        
        return tgt, self_attn_weights, cross_attn_weights

class NeuralMemoryNetwork(nn.Module):
    """
    Production-grade External Memory System for persistent information storage
    across long time horizons with advanced memory management, retrieval strategies,
    and memory consolidation mechanisms.
    """
    def __init__(self, config: NeuralNetConfig, memory_size: int = 1000, memory_dim: int = 512,
                 num_memory_heads: int = 8, consolidation_threshold: float = 0.8):
        super().__init__()
        self.config = config
        self.memory_size = memory_size
        self.memory_dim = memory_dim
        self.num_memory_heads = num_memory_heads
        self.consolidation_threshold = consolidation_threshold
        
        # Memory slots with enhanced initialization
        self.memory_keys = nn.Parameter(torch.randn(memory_size, memory_dim) * 0.02)
        self.memory_values = nn.Parameter(torch.randn(memory_size, memory_dim) * 0.02)
        
        # Memory usage and importance tracking
        self.register_buffer('memory_usage', torch.zeros(memory_size))
        self.register_buffer('memory_importance', torch.zeros(memory_size))
        self.register_buffer('memory_timestamps', torch.zeros(memory_size))
        self.register_buffer('access_counts', torch.zeros(memory_size))
        
        # Enhanced read/write mechanisms
        self.read_head = nn.MultiheadAttention(
            embed_dim=memory_dim,
            num_heads=num_memory_heads,
            dropout=config.dropout,
            batch_first=True
        )
        
        self.write_head = nn.Sequential(
            nn.Linear(config.d_model, memory_dim * 2),
            nn.LayerNorm(memory_dim * 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(memory_dim * 2, memory_dim)
        )
        
        # Memory gating with sophisticated control
        self.memory_gate = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, 4)  # read/write/update/consolidate
        )
        
        # Memory projection layers
        self.key_projection = nn.Linear(config.d_model, memory_dim)
        self.value_projection = nn.Linear(config.d_model, memory_dim)
        self.output_projection = nn.Linear(config.d_model + memory_dim, config.d_model)
        
        # Memory consolidation network
        self.consolidation_network = nn.Sequential(
            nn.Linear(memory_dim * 2, memory_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(memory_dim, 1),
            nn.Sigmoid()
        )
        
        # Statistics tracking
        self.memory_stats = {
            'total_reads': 0,
            'total_writes': 0,
            'consolidations': 0,
            'average_memory_usage': 0.0
        }
        
        self._init_memory_weights()
    
    def _init_memory_weights(self):
        """Initialize memory-specific weights."""
        for module in [self.write_head, self.memory_gate, self.consolidation_network]:
            for layer in module:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    if layer.bias is not None:
                        nn.init.zeros_(layer.bias)
    
    def _update_memory_statistics(self):
        """Update memory usage statistics."""
        used_slots = (self.memory_usage > 0).sum().item()
        self.memory_stats['average_memory_usage'] = used_slots / self.memory_size
    
    def _find_memory_slots(self, batch_size: int, importance_scores: torch.Tensor) -> torch.Tensor:
        """
        Advanced memory slot allocation considering usage, importance, and temporal factors.
        """
        # Compute composite scores for slot selection
        recency_weight = 0.3
        importance_weight = 0.4
        usage_weight = 0.3
        
        # Normalize factors
        normalized_usage = self.memory_usage / (self.memory_usage.max() + 1e-8)
        normalized_importance = self.memory_importance / (self.memory_importance.max() + 1e-8)
        
        # Time decay factor (older memories are more likely to be replaced)
        current_time = torch.max(self.memory_timestamps) + 1
        time_decay = torch.exp(-(current_time - self.memory_timestamps) * 0.01)
        
        # Composite score (lower is better for replacement)
        composite_scores = (
            usage_weight * normalized_usage +
            importance_weight * normalized_importance +
            recency_weight * time_decay
        )
        
        # Find slots with lowest composite scores
        available_slots = torch.argsort(composite_scores)[:batch_size]
        
        return available_slots
    
    def read_memory(self, query: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Enhanced memory reading with multi-head attention and relevance scoring.
        """
        self.memory_stats['total_reads'] += 1
        batch_size, seq_len, d_model = query.shape
        
        # Project query to memory dimension
        query_proj = self.key_projection(query.reshape(-1, d_model))
        query_proj = query_proj.reshape(batch_size, seq_len, self.memory_dim)
        
        # Multi-head attention over memory
        memory_keys_expanded = self.memory_keys.unsqueeze(0).expand(batch_size, -1, -1)
        memory_values_expanded = self.memory_values.unsqueeze(0).expand(batch_size, -1, -1)
        
        # Attention-based memory retrieval
        retrieved_memories, attention_weights = self.read_head(
            query_proj,
            memory_keys_expanded,
            memory_values_expanded
        )
        
        retrieved_memories = retrieved_memories.contiguous()
        attention_weights = attention_weights.contiguous()
        
        # Update access counts
        access_updates = attention_weights.sum(dim=(0, 1))
        self.access_counts += access_updates.detach()
        
        # Compute relevance scores
        relevance_scores = attention_weights.max(dim=-1)[0]  # Max attention as relevance
        
        return retrieved_memories, attention_weights, relevance_scores
    
    def write_memory(self, content: torch.Tensor, importance: torch.Tensor, 
                    gate_probs: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Enhanced memory writing with importance-based allocation and consolidation.
        """
        self.memory_stats['total_writes'] += 1
        batch_size, seq_len, d_model = content.shape
        
        # Aggregate content per batch (mean pooling)
        aggregated_content = content.mean(dim=1)  # (batch_size, d_model)
        
        # Project to memory dimensions
        new_keys = self.write_head(aggregated_content)  # (batch_size, memory_dim)
        new_values = self.value_projection(aggregated_content)  # (batch_size, d_model)
        
        # Find optimal memory slots
        available_slots = self._find_memory_slots(batch_size, importance)
        
        # Update memory slots
        write_mask = gate_probs[:, 1] > 0.5  # Write gate activation
        actual_writes = 0
        
        for i, slot_idx in enumerate(available_slots):
            if i < batch_size and write_mask[i]:
                slot_idx = slot_idx.item()
                
                # Store new memory
                self.memory_keys.data[slot_idx] = new_keys[i].detach()
                self.memory_values.data[slot_idx] = new_values[i].detach()
                
                # Update metadata
                self.memory_usage[slot_idx] = 1.0
                self.memory_importance[slot_idx] = importance[i].item()
                self.memory_timestamps[slot_idx] = torch.max(self.memory_timestamps) + 1
                
                actual_writes += 1
        
        return {
            'slots_written': actual_writes,
            'available_slots': available_slots,
            'write_mask': write_mask
        }
    
    def consolidate_memories(self) -> Dict[str, int]:
        """
        Memory consolidation to merge similar memories and optimize storage.
        """
        if self.memory_usage.sum() < self.memory_size * 0.8:
            return {'consolidated_pairs': 0}
        
        self.memory_stats['consolidations'] += 1
        consolidated_pairs = 0
        
        # Find active memory slots
        active_mask = self.memory_usage > 0
        active_indices = torch.where(active_mask)[0]
        
        if len(active_indices) < 2:
            return {'consolidated_pairs': 0}
        
        # Compute pairwise similarities
        active_keys = self.memory_keys[active_indices]
        similarities = torch.mm(active_keys, active_keys.t())
        similarities.fill_diagonal_(0)
        
        # Find highly similar pairs
        similarity_threshold = self.consolidation_threshold
        similar_pairs = torch.where(similarities > similarity_threshold)
        
        for i, j in zip(similar_pairs[0], similar_pairs[1]):
            if i >= j:  # Avoid duplicates
                continue
            
            idx_i, idx_j = active_indices[i], active_indices[j]
            
            # Decide which memory to keep (higher importance wins)
            if self.memory_importance[idx_i] >= self.memory_importance[idx_j]:
                keep_idx, remove_idx = idx_i, idx_j
            else:
                keep_idx, remove_idx = idx_j, idx_i
            
            # Consolidate: weighted average based on importance
            total_importance = self.memory_importance[keep_idx] + self.memory_importance[remove_idx]
            if total_importance > 0:
                w1 = self.memory_importance[keep_idx] / total_importance
                w2 = self.memory_importance[remove_idx] / total_importance
                
                # Update the kept memory
                self.memory_keys.data[keep_idx] = w1 * self.memory_keys[keep_idx] + w2 * self.memory_keys[remove_idx]
                self.memory_values.data[keep_idx] = w1 * self.memory_values[keep_idx] + w2 * self.memory_values[remove_idx]
                self.memory_importance[keep_idx] = total_importance
                
                # Clear the removed memory
                self.memory_usage[remove_idx] = 0
                self.memory_importance[remove_idx] = 0
                self.memory_timestamps[remove_idx] = 0
                self.access_counts[remove_idx] = 0
                
                consolidated_pairs += 1
        
        return {'consolidated_pairs': consolidated_pairs}
    
    def forward(self, x: torch.Tensor, mode: str = 'read_write') -> Tuple[torch.Tensor, Dict]:
        """
        Enhanced forward pass with adaptive memory operations.
        """
        batch_size, seq_len, d_model = x.shape
        
        # Compute memory gates
        gate_logits = self.memory_gate(x.mean(dim=1))  # (batch_size, 4)
        gate_probs = F.softmax(gate_logits, dim=-1)
        
        output_dict = {'gate_probs': gate_probs}
        
        if mode in ['read', 'read_write']:
            # Read from memory
            memory_recall, attention_weights, relevance_scores = self.read_memory(x)
            
            # Combine input with memory
            combined_input = torch.cat([x, memory_recall], dim=-1)
            x = self.output_projection(combined_input)
            
            output_dict.update({
                'memory_recall': memory_recall,
                'attention_weights': attention_weights,
                'relevance_scores': relevance_scores
            })
        
        if mode in ['write', 'read_write']:
            # Determine importance scores
            importance_scores = gate_probs[:, 2]  # Update gate as importance
            
            # Write to memory if needed
            write_info = self.write_memory(x, importance_scores, gate_probs)
            output_dict.update(write_info)
        
        # Memory consolidation (periodic)
        if mode == 'read_write' and gate_probs[:, 3].mean() > 0.7:  # Consolidation gate
            consolidation_info = self.consolidate_memories()
            output_dict.update(consolidation_info)
        
        # Update statistics
        self._update_memory_statistics()
        
        return x, output_dict
    
    def get_memory_statistics(self) -> Dict:
        """Get comprehensive memory usage statistics."""
        stats = self.memory_stats.copy()
        stats.update({
            'active_slots': (self.memory_usage > 0).sum().item(),
            'total_slots': self.memory_size,
            'memory_utilization': stats['average_memory_usage'],
            'most_accessed_slot': self.access_counts.argmax().item(),
            'least_accessed_slot': self.access_counts.argmin().item()
        })
        return stats
    
    def clear_memory(self, slot_indices: Optional[List[int]] = None):
        """Clear specific memory slots or all memory."""
        if slot_indices is None:
            # Clear all memory
            self.memory_usage.zero_()
            self.memory_importance.zero_()
            self.memory_timestamps.zero_()
            self.access_counts.zero_()
        else:
            # Clear specific slots
            for idx in slot_indices:
                if 0 <= idx < self.memory_size:
                    self.memory_usage[idx] = 0
                    self.memory_importance[idx] = 0
                    self.memory_timestamps[idx] = 0
                    self.access_counts[idx] = 0

class ContinualLearningModule(nn.Module):
    """
    Production-grade Continual Learning Module implementing Elastic Weight Consolidation (EWC)
    and advanced techniques to prevent catastrophic forgetting with task-specific adaptations,
    gradient-based importance estimation, and adaptive regularization.
    """
    def __init__(self, config: NeuralNetConfig, ewc_lambda: float = 1000.0, 
                 max_tasks: int = 100, importance_estimation_samples: int = 1000):
        super().__init__()
        self.config = config
        self.ewc_lambda = ewc_lambda
        self.max_tasks = max_tasks
        self.importance_estimation_samples = importance_estimation_samples
        
        # Task management
        self.current_task_id = 0
        self.task_registry = {}
        self.task_performance = {}
        
        # Fisher information matrices for each task
        self.fisher_matrices = nn.ModuleDict()
        self.task_importance_weights = nn.ParameterDict()
        self.optimal_parameters = nn.ParameterDict()
        
        # Task embeddings with learnable task representations
        self.task_embeddings = nn.Embedding(max_tasks, config.d_model)
        self.task_classifier = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, max_tasks)
        )
        
        # Adaptive regularization
        self.adaptive_lambda = nn.Parameter(torch.tensor(ewc_lambda))
        self.regularization_scheduler = {
            'decay_rate': 0.99,
            'min_lambda': 100.0,
            'performance_threshold': 0.95
        }
        
        # Replay buffer for experience replay
        self.replay_buffer = {
            'data': [],
            'labels': [],
            'task_ids': [],
            'max_size': 1000
        }
        
        # Continual learning statistics
        self.cl_stats = {
            'total_tasks': 0,
            'average_fisher_magnitude': 0.0,
            'forgetting_measure': 0.0,
            'transfer_efficiency': 0.0
        }
        
        self._init_cl_weights()
    
    def _init_cl_weights(self):
        """Initialize continual learning specific weights."""
        nn.init.normal_(self.task_embeddings.weight, std=0.02)
        for layer in self.task_classifier:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                if layer.bias is not None:
                    nn.init.zeros_(layer.bias)
    
    def compute_fisher_information(self, model: nn.Module, dataloader: DataLoader, 
                                 task_id: int, num_samples: Optional[int] = None) -> Dict[str, torch.Tensor]:
        """
        Enhanced Fisher information computation with improved sampling and numerical stability.
        """
        if num_samples is None:
            num_samples = self.importance_estimation_samples
        
        model.eval()
        fisher_dict = {}
        
        # Initialize Fisher matrices
        for name, param in model.named_parameters():
            if param.requires_grad:
                fisher_dict[name] = torch.zeros_like(param.data)
        
        sample_count = 0
        total_log_likelihood = 0.0
        
        with torch.enable_grad():
            for batch_idx, batch in enumerate(dataloader):
                if sample_count >= num_samples:
                    break
                
                # Prepare batch data
                if isinstance(batch, dict):
                    inputs = {k: v.to(model.device) if hasattr(v, 'to') else v 
                             for k, v in batch.items() if k != 'labels'}
                    targets = batch.get('labels', batch.get('input_ids'))
                else:
                    inputs, targets = batch
                    inputs = inputs.to(model.device)
                    targets = targets.to(model.device)
                
                # Forward pass
                model.zero_grad()
                if isinstance(inputs, dict):
                    outputs = model(**inputs)
                else:
                    outputs = model(inputs)
                
                # Get logits
                if isinstance(outputs, dict):
                    logits = outputs.get('logits', outputs.get('prediction', outputs))
                else:
                    logits = outputs
                
                # Sample from the model's predictive distribution
                if logits.dim() > 2:
                    logits = logits.view(-1, logits.size(-1))
                if targets.dim() > 1:
                    targets = targets.view(-1)
                
                # Compute log probabilities
                log_probs = F.log_softmax(logits, dim=-1)
                
                # Sample targets from the model's distribution for Fisher computation
                probs = F.softmax(logits, dim=-1)
                sampled_targets = torch.multinomial(probs, 1).squeeze()
                
                # Compute log likelihood
                log_likelihood = F.nll_loss(log_probs, sampled_targets, reduction='sum')
                total_log_likelihood += log_likelihood.item()
                
                # Backward pass to compute gradients
                log_likelihood.backward(retain_graph=False)
                
                # Accumulate squared gradients (Fisher approximation)
                for name, param in model.named_parameters():
                    if param.requires_grad and param.grad is not None:
                        fisher_dict[name] += param.grad.data ** 2
                
                sample_count += targets.size(0)
        
        # Normalize Fisher information by number of samples
        for name in fisher_dict:
            fisher_dict[name] /= sample_count
            
            # Numerical stability: add small epsilon to prevent division by zero
            fisher_dict[name] += 1e-8
        
        # Update statistics
        avg_fisher = torch.stack([f.mean() for f in fisher_dict.values()]).mean().item()
        self.cl_stats['average_fisher_magnitude'] = avg_fisher
        
        return fisher_dict
    
    def register_task(self, task_name: str, task_id: int, model: nn.Module, 
                     dataloader: DataLoader, importance_weight: float = 1.0) -> Dict[str, float]:
        """
        Enhanced task registration with comprehensive Fisher computation and parameter storage.
        """
        self.current_task_id = task_id
        self.cl_stats['total_tasks'] += 1
        
        # Store task information
        self.task_registry[task_id] = {
            'name': task_name,
            'importance': importance_weight,
            'registration_time': self.cl_stats['total_tasks']
        }
        
        # Compute Fisher information for this task
        print(f"Computing Fisher information for task: {task_name}")
        fisher_info = self.compute_fisher_information(model, dataloader, task_id)
        
        # Store Fisher matrices
        fisher_module = nn.ParameterDict()
        for name, fisher_matrix in fisher_info.items():
            # Ensure proper parameter registration
            fisher_module[name.replace('.', '_')] = nn.Parameter(fisher_matrix.clone().detach())
        
        self.fisher_matrices[str(task_id)] = fisher_module
        self.task_importance_weights[str(task_id)] = nn.Parameter(torch.tensor(importance_weight))
        
        # Store optimal parameters for this task
        optimal_params = nn.ParameterDict()
        for name, param in model.named_parameters():
            if param.requires_grad:
                optimal_params[name.replace('.', '_')] = nn.Parameter(param.clone().detach())
        
        self.optimal_parameters[str(task_id)] = optimal_params
        
        # Update replay buffer
        self._update_replay_buffer(dataloader, task_id)
        
        return {
            'task_id': task_id,
            'fisher_magnitude': self.cl_stats['average_fisher_magnitude'],
            'parameters_stored': len(optimal_params)
        }
    
    def _update_replay_buffer(self, dataloader: DataLoader, task_id: int):
        """Update replay buffer with representative samples from the new task."""
        samples_per_task = min(self.replay_buffer['max_size'] // max(1, self.cl_stats['total_tasks']), 100)
        
        # Sample data points
        sampled_data = []
        sampled_labels = []
        
        for batch_idx, batch in enumerate(dataloader):
            if len(sampled_data) >= samples_per_task:
                break
            
            if isinstance(batch, dict):
                data = batch.get('input_ids', batch.get('inputs'))
                labels = batch.get('labels', batch.get('targets', data))
            else:
                data, labels = batch
            
            # Random sampling from batch
            batch_size = data.size(0)
            indices = torch.randperm(batch_size)[:min(batch_size, samples_per_task - len(sampled_data))]
            
            sampled_data.extend([data[i] for i in indices])
            sampled_labels.extend([labels[i] for i in indices])
        
        # Add to replay buffer
        self.replay_buffer['data'].extend(sampled_data)
        self.replay_buffer['labels'].extend(sampled_labels)
        self.replay_buffer['task_ids'].extend([task_id] * len(sampled_data))
        
        # Maintain buffer size
        if len(self.replay_buffer['data']) > self.replay_buffer['max_size']:
            excess = len(self.replay_buffer['data']) - self.replay_buffer['max_size']
            self.replay_buffer['data'] = self.replay_buffer['data'][excess:]
            self.replay_buffer['labels'] = self.replay_buffer['labels'][excess:]
            self.replay_buffer['task_ids'] = self.replay_buffer['task_ids'][excess:]
    
    def compute_ewc_loss(self, model: nn.Module, current_loss: torch.Tensor, 
                        task_id: Optional[int] = None) -> torch.Tensor:
        """
        Enhanced EWC loss computation with adaptive regularization and selective consolidation.
        """
        if not self.fisher_matrices or len(self.fisher_matrices) == 0:
            return current_loss
        
        ewc_loss = 0.0
        total_penalty_terms = 0
        
        # Iterate through all previous tasks
        for stored_task_id, fisher_module in self.fisher_matrices.items():
            if task_id is not None and stored_task_id == str(task_id):
                continue  # Skip current task
            
            task_importance = self.task_importance_weights[stored_task_id]
            optimal_params = self.optimal_parameters[stored_task_id]
            
            task_penalty = 0.0
            param_count = 0
            
            # Compute penalty for each parameter
            for name, current_param in model.named_parameters():
                if not current_param.requires_grad:
                    continue
                
                param_key = name.replace('.', '_')
                
                if param_key in fisher_module and param_key in optimal_params:
                    fisher_matrix = fisher_module[param_key]
                    optimal_param = optimal_params[param_key]
                    
                    # Compute quadratic penalty
                    param_diff = current_param - optimal_param
                    penalty = torch.sum(fisher_matrix * (param_diff ** 2))
                    task_penalty += penalty
                    param_count += 1
            
            # Weight by task importance
            if param_count > 0:
                ewc_loss += task_importance * task_penalty
                total_penalty_terms += param_count
        
        # Adaptive regularization strength
        if total_penalty_terms > 0:
            ewc_loss = (self.adaptive_lambda / 2.0) * ewc_loss
            
            # Update adaptive lambda based on performance
            self._update_adaptive_lambda()
        
        total_loss = current_loss + ewc_loss
        return total_loss
    
    def _update_adaptive_lambda(self):
        """Update adaptive regularization strength based on learning progress."""
        # Simple decay schedule - can be made more sophisticated
        current_lambda = self.adaptive_lambda.data
        min_lambda = self.regularization_scheduler['min_lambda']
        decay_rate = self.regularization_scheduler['decay_rate']
        
        new_lambda = max(min_lambda, current_lambda * decay_rate)
        self.adaptive_lambda.data = torch.tensor(new_lambda)
    
    def detect_task_boundary(self, model_outputs: torch.Tensor, 
                           confidence_threshold: float = 0.8) -> bool:
        """
        Detect potential task boundaries using confidence-based heuristics.
        """
        if model_outputs.dim() > 2:
            model_outputs = model_outputs.view(-1, model_outputs.size(-1))
        
        # Compute prediction confidence
        probs = F.softmax(model_outputs, dim=-1)
        max_probs = probs.max(dim=-1)[0]
        avg_confidence = max_probs.mean().item()
        
        # Task boundary detected if confidence drops significantly
        return avg_confidence < confidence_threshold
    
    def forward(self, x: torch.Tensor, task_id: Optional[int] = None, 
               use_task_embedding: bool = True) -> torch.Tensor:
        """
        Enhanced forward pass with task-specific conditioning and adaptation.
        """
        if use_task_embedding and task_id is not None:
            # Add task-specific conditioning
            task_embed = self.task_embeddings(
                torch.tensor([task_id], device=x.device)
            )  # [1, d_model]
            
            if x.dim() == 3:
                # [1, d_model] -> [1, 1, d_model] -> [batch, seq, d_model]
                task_embed = task_embed.unsqueeze(1).expand(
                    x.size(0), x.size(1), -1
                )
                x = x + task_embed
            elif x.dim() == 2:
                # [1, d_model] -> [batch, d_model]
                task_embed = task_embed.expand(x.size(0), -1)
                x = x + task_embed
        
        return x
    
    def get_task_statistics(self) -> Dict[str, float]:
        """Get comprehensive continual learning statistics."""
        stats = self.cl_stats.copy()
        
        # Add runtime statistics
        stats.update({
            'registered_tasks': len(self.task_registry),
            'current_task_id': self.current_task_id,
            'replay_buffer_size': len(self.replay_buffer['data']),
            'adaptive_lambda': self.adaptive_lambda.item(),
            'fisher_memory_mb': sum(
                sum(p.numel() for p in module.parameters()) * 4 / (1024**2)
                for module in self.fisher_matrices.values()
            )
        })
        
        return stats
    
    def consolidate_knowledge(self, similarity_threshold: float = 0.9) -> Dict[str, int]:
        """
        Consolidate similar Fisher matrices to reduce memory usage.
        """
        if len(self.fisher_matrices) < 2:
            return {'consolidated_tasks': 0}
        
        consolidated = 0
        task_ids = list(self.fisher_matrices.keys())
        
        # Compare Fisher matrices for similarity
        for i in range(len(task_ids)):
            for j in range(i + 1, len(task_ids)):
                task_id_1, task_id_2 = task_ids[i], task_ids[j]
                
                if task_id_1 not in self.fisher_matrices or task_id_2 not in self.fisher_matrices:
                    continue
                
                # Compute similarity between Fisher matrices
                similarity = self._compute_fisher_similarity(
                    self.fisher_matrices[task_id_1],
                    self.fisher_matrices[task_id_2]
                )
                
                if similarity > similarity_threshold:
                    # Merge the Fisher matrices
                    self._merge_fisher_matrices(task_id_1, task_id_2)
                    consolidated += 1
        
        return {'consolidated_tasks': consolidated}
    
    def _compute_fisher_similarity(self, fisher1: nn.ParameterDict, 
                                  fisher2: nn.ParameterDict) -> float:
        """Compute cosine similarity between Fisher matrices."""
        similarities = []
        
        for param_name in fisher1.keys():
            if param_name in fisher2:
                f1 = fisher1[param_name].flatten()
                f2 = fisher2[param_name].flatten()
                
                # Cosine similarity
                sim = F.cosine_similarity(f1.unsqueeze(0), f2.unsqueeze(0), dim=1).item()
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _merge_fisher_matrices(self, task_id_1: str, task_id_2: str):
        """Merge two Fisher matrices using importance-weighted averaging."""
        importance_1 = self.task_importance_weights[task_id_1]
        importance_2 = self.task_importance_weights[task_id_2]
        total_importance = importance_1 + importance_2
        
        w1 = importance_1 / total_importance
        w2 = importance_2 / total_importance
        
        # Merge Fisher matrices
        fisher_1 = self.fisher_matrices[task_id_1]
        fisher_2 = self.fisher_matrices[task_id_2]
        
        for param_name in fisher_1.keys():
            if param_name in fisher_2:
                fisher_1[param_name].data = w1 * fisher_1[param_name] + w2 * fisher_2[param_name]
        
        # Update importance and remove second task
        self.task_importance_weights[task_id_1] = nn.Parameter(total_importance)
        del self.fisher_matrices[task_id_2]
        del self.task_importance_weights[task_id_2]
        del self.optimal_parameters[task_id_2]

class UncertaintyQuantification(nn.Module):
    """
    Production-grade Uncertainty Quantification module implementing multiple uncertainty
    estimation methods including Monte Carlo Dropout, Deep Ensembles, and Evidential
    Deep Learning with calibration and reliability assessment.
    """
    def __init__(self, config: NeuralNetConfig, num_mc_samples: int = 10, 
                 num_ensemble_members: int = 5, calibration_bins: int = 15):
        super().__init__()
        self.config = config
        self.num_mc_samples = num_mc_samples
        self.num_ensemble_members = num_ensemble_members
        self.calibration_bins = calibration_bins
        
        # Monte Carlo dropout layers with configurable rates
        self.mc_dropout_rates = [0.1, 0.15, 0.2]
        self.mc_dropout_layers = nn.ModuleList([
            nn.Dropout(p=rate, inplace=False) for rate in self.mc_dropout_rates
        ])
        
        # Enhanced uncertainty prediction heads
        self.aleatoric_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.LayerNorm(config.d_model // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, 2)  # Mean and log variance
        )
        
        self.epistemic_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2),
            nn.LayerNorm(config.d_model // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, config.d_model // 4),
            nn.ReLU(),
            nn.Linear(config.d_model // 4, 1)
        )
        
        # Evidential deep learning components
        self.evidence_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.LayerNorm(config.d_model),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.vocab_size * 4)  # alpha, beta, gamma, delta
        )
        
        # Ensemble prediction heads
        self.ensemble_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(config.d_model, config.d_model // 2),
                nn.ReLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.d_model // 2, config.vocab_size)
            ) for _ in range(num_ensemble_members)
        ])
        
        # Calibration components
        self.register_buffer('calibration_confidences', torch.zeros(calibration_bins))
        self.register_buffer('calibration_accuracies', torch.zeros(calibration_bins))
        self.register_buffer('calibration_counts', torch.zeros(calibration_bins))
        
        # Temperature scaling for calibration
        self.temperature = nn.Parameter(torch.ones(1))
        
        # Uncertainty statistics
        self.uncertainty_stats = {
            'calibration_error': 0.0,
            'average_confidence': 0.0,
            'reliability_score': 0.0,
            'coverage_probability': 0.0
        }
        
        self._init_uncertainty_weights()
    
    def _init_uncertainty_weights(self):
        """Initialize uncertainty-specific weights."""
        for module in [self.aleatoric_head, self.epistemic_head, self.evidence_head] + list(self.ensemble_heads):
            for layer in module:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    if layer.bias is not None:
                        nn.init.zeros_(layer.bias)
    
    def monte_carlo_forward(self, model: nn.Module, inputs: Dict, 
                           dropout_mode: str = 'adaptive') -> Dict[str, torch.Tensor]:
        """
        Enhanced Monte Carlo forward pass with adaptive dropout and improved sampling.
        """
        original_training_state = model.training
        model.train()  # Enable dropout for uncertainty estimation
        
        predictions = []
        feature_variations = []
        
        # Determine dropout configuration
        if dropout_mode == 'adaptive':
            # Use different dropout rates for different samples
            dropout_schedule = self.mc_dropout_rates * (self.num_mc_samples // len(self.mc_dropout_rates) + 1)
            dropout_schedule = dropout_schedule[:self.num_mc_samples]
        else:
            dropout_schedule = [self.mc_dropout_rates[0]] * self.num_mc_samples
        
        with torch.no_grad():
            for i in range(self.num_mc_samples):
                # Apply variable dropout if in adaptive mode
                if dropout_mode == 'adaptive':
                    self._set_model_dropout_rate(model, dropout_schedule[i])
                
                # Forward pass
                if isinstance(inputs, dict):
                    output = model(**inputs)
                else:
                    output = model(inputs)
                
                if isinstance(output, dict):
                    logits = output.get('logits', output.get('prediction'))
                    features = output.get('encoder_output', output.get('features'))
                else:
                    logits = output
                    features = None
                
                predictions.append(logits)
                if features is not None:
                    feature_variations.append(features)
        
        # Restore original training state
        model.train(original_training_state)
        
        predictions = torch.stack(predictions)  # (samples, batch, seq, vocab)
        
        # Compute predictive statistics
        pred_mean = predictions.mean(dim=0)
        pred_var = predictions.var(dim=0, unbiased=True)
        
        # Epistemic uncertainty (model uncertainty)
        epistemic_uncertainty = pred_var.mean(dim=-1)  # Average over vocab
        
        # Mutual information-based uncertainty
        avg_entropy = torch.stack([
            -torch.sum(F.softmax(pred, dim=-1) * F.log_softmax(pred, dim=-1), dim=-1)
            for pred in predictions
        ]).mean(dim=0)
        
        entropy_of_avg = -torch.sum(
            F.softmax(pred_mean, dim=-1) * F.log_softmax(pred_mean, dim=-1), dim=-1
        )
        
        mutual_information = avg_entropy - entropy_of_avg
        
        # Confidence estimation
        max_probs = F.softmax(pred_mean, dim=-1).max(dim=-1)[0]
        confidence = max_probs.mean(dim=-1) if max_probs.dim() > 1 else max_probs
        
        return {
            'logits': pred_mean,
            'predictive_variance': pred_var,
            'epistemic_uncertainty': epistemic_uncertainty,
            'mutual_information': mutual_information,
            'confidence': confidence,
            'prediction_samples': predictions
        }
    
    def _set_model_dropout_rate(self, model: nn.Module, dropout_rate: float):
        """Dynamically set dropout rate for all dropout layers in the model."""
        for module in model.modules():
            if isinstance(module, (nn.Dropout, nn.Dropout2d, nn.Dropout3d)):
                module.p = dropout_rate
    
    def deep_ensemble_forward(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Deep ensemble prediction with diversity regularization.
        """
        ensemble_predictions = []
        
        for head in self.ensemble_heads:
            pred = head(features)
            ensemble_predictions.append(pred)
        
        ensemble_predictions = torch.stack(ensemble_predictions)  # (ensemble_size, batch, seq, vocab)
        
        # Ensemble statistics
        ensemble_mean = ensemble_predictions.mean(dim=0)
        ensemble_var = ensemble_predictions.var(dim=0, unbiased=True)
        
        # Disagreement-based uncertainty
        disagreement = ensemble_var.mean(dim=-1)
        
        # Ensemble confidence
        ensemble_confidence = F.softmax(ensemble_mean, dim=-1).max(dim=-1)[0]
        
        return {
            'ensemble_logits': ensemble_mean,
            'ensemble_variance': ensemble_var,
            'disagreement_uncertainty': disagreement,
            'ensemble_confidence': ensemble_confidence,
            'individual_predictions': ensemble_predictions
        }
    
    def evidential_uncertainty(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Enhanced evidential deep learning for principled uncertainty quantification.
        """
        batch_size, seq_len, d_model = features.shape
        
        # Predict Dirichlet parameters
        evidence_params = self.evidence_head(features.reshape(-1, d_model))
        evidence_params = evidence_params.reshape(batch_size, seq_len, self.config.vocab_size, 4)
        
        # Extract Dirichlet parameters (ensure positivity)
        alpha = F.softplus(evidence_params[..., 0]) + 1  # Concentration parameters
        beta = F.softplus(evidence_params[..., 1]) + 1   # Beta parameters  
        gamma = F.softplus(evidence_params[..., 2]) + 1  # Gamma parameters
        delta = F.softplus(evidence_params[..., 3]) + 1  # Delta parameters
        
        # Compute sufficient statistics
        S = alpha + beta + gamma + delta  # Total evidence
        
        # Expected probabilities under Dirichlet
        expected_probs = alpha / S
        
        # Aleatoric uncertainty (inherent data uncertainty)
        aleatoric_uncertainty = (alpha * (S - alpha)) / (S ** 2 * (S + 1))
        aleatoric_uncertainty = aleatoric_uncertainty.sum(dim=-1)
        
        # Epistemic uncertainty (model uncertainty)
        epistemic_per_class = self.config.vocab_size / S
        epistemic_uncertainty = epistemic_per_class.mean(dim=-1)
        
        # Total uncertainty
        total_uncertainty = aleatoric_uncertainty + epistemic_uncertainty
        
        # Prediction confidence based on evidence
        confidence = alpha.max(dim=-1)[0] / S.max(dim=-1)[0]
        
        # Compute logits from expected probabilities
        logits = torch.log(expected_probs + 1e-8)
        
        return {
            'evidential_logits': logits,
            'dirichlet_alpha': alpha,
            'total_evidence': S,
            'aleatoric_uncertainty': aleatoric_uncertainty,
            'epistemic_uncertainty': epistemic_uncertainty,
            'epistemic_uncertainty_per_class': epistemic_per_class,
            'total_uncertainty': total_uncertainty,
            'evidential_confidence': confidence
        }
    
    def compute_calibration_error(self, confidences: torch.Tensor, 
                                accuracies: torch.Tensor) -> float:
        """
        Compute Expected Calibration Error (ECE) for model calibration assessment.
        """
        bin_boundaries = torch.linspace(0, 1, self.calibration_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0.0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Find predictions in this bin
            in_bin = (confidences > bin_lower.item()) & (confidences <= bin_upper.item())
            prop_in_bin = in_bin.float().mean()
            
            if prop_in_bin.item() > 0:
                accuracy_in_bin = accuracies[in_bin].float().mean()
                avg_confidence_in_bin = confidences[in_bin].mean()
                
                ece += torch.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return ece.item()
    
    def temperature_scaling_calibration(self, logits: torch.Tensor, 
                                      targets: torch.Tensor) -> torch.Tensor:
        """
        Apply temperature scaling for improved calibration.
        """
        # Apply temperature scaling
        scaled_logits = logits / self.temperature
        
        # Compute NLL loss for temperature optimization
        if targets is not None:
            nll_loss = F.cross_entropy(scaled_logits.view(-1, scaled_logits.size(-1)), 
                                     targets.view(-1))
            return scaled_logits, nll_loss
        
        return scaled_logits
    
    def forward(self, model: nn.Module, inputs: Dict, features: Optional[torch.Tensor] = None,
               method: str = 'monte_carlo', targets: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """
        Comprehensive uncertainty estimation using specified method(s).
        """
        results = {}
        
        # Get model features if not provided
        if features is None:
            with torch.no_grad():
                if isinstance(inputs, dict):
                    outputs = model(**inputs)
                else:
                    outputs = model(inputs)
                
                if isinstance(outputs, dict):
                    features = outputs.get('encoder_output', outputs.get('decoder_output'))
                    if features is None:
                        # Fallback to creating features from logits
                        logits = outputs.get('logits')
                        if logits is not None:
                            features = torch.randn(logits.shape[:-1] + (self.config.d_model,), 
                                                 device=logits.device)
                else:
                    features = torch.randn(outputs.shape[:-1] + (self.config.d_model,), 
                                         device=outputs.device)
        
        # Monte Carlo Dropout
        if method in ['monte_carlo', 'all']:
            mc_results = self.monte_carlo_forward(model, inputs)
            results.update({f'mc_{k}': v for k, v in mc_results.items()})
        
        # Deep Ensemble
        if method in ['ensemble', 'all']:
            ensemble_results = self.deep_ensemble_forward(features)
            results.update({f'ensemble_{k}': v for k, v in ensemble_results.items()})
        
        # Evidential Deep Learning
        if method in ['evidential', 'all']:
            evidential_results = self.evidential_uncertainty(features)
            results.update({f'evidential_{k}': v for k, v in evidential_results.items()})
        
        # Aleatoric and epistemic uncertainty estimation
        if features is not None:
            aleatoric_params = self.aleatoric_head(features)
            epistemic_score = self.epistemic_head(features)
            
            results.update({
                'aleatoric_mean': aleatoric_params[..., 0],
                'aleatoric_logvar': aleatoric_params[..., 1],
                'epistemic_score': epistemic_score.squeeze(-1)
            })
        
        # Temperature scaling calibration
        if 'logits' in results:
            calibrated_logits = self.temperature_scaling_calibration(
                results['logits'], targets
            )
            if isinstance(calibrated_logits, tuple):
                results['calibrated_logits'], results['temperature_loss'] = calibrated_logits
            else:
                results['calibrated_logits'] = calibrated_logits
        
        # Update uncertainty statistics
        self._update_uncertainty_statistics(results)
        
        return results
    
    def _update_uncertainty_statistics(self, results: Dict[str, torch.Tensor]):
        """Update running uncertainty statistics."""
        # Extract confidence measures
        confidences = []
        if 'confidence' in results:
            confidences.append(results['confidence'])
        if 'mc_confidence' in results:
            confidences.append(results['mc_confidence'])
        if 'ensemble_confidence' in results:
            confidences.append(results['ensemble_confidence'])
        
        if confidences:
            avg_confidence = torch.stack(confidences).mean().item()
            self.uncertainty_stats['average_confidence'] = avg_confidence
    
    def get_uncertainty_statistics(self) -> Dict[str, float]:
        """Get comprehensive uncertainty quantification statistics."""
        stats = self.uncertainty_stats.copy()
        
        # Add model-specific statistics
        stats.update({
            'num_mc_samples': self.num_mc_samples,
            'num_ensemble_members': self.num_ensemble_members,
            'temperature_value': self.temperature.item(),
            'calibration_bins': self.calibration_bins
        })
        
        return stats
    
    def update_calibration(self, confidences: torch.Tensor, 
                          accuracies: torch.Tensor):
        """Update calibration statistics with new data."""
        bin_boundaries = torch.linspace(0, 1, self.calibration_bins + 1)
        
        for i in range(self.calibration_bins):
            bin_mask = (confidences >= bin_boundaries[i]) & (confidences < bin_boundaries[i + 1])
            
            if bin_mask.sum() > 0:
                bin_confidence = confidences[bin_mask].mean()
                bin_accuracy = accuracies[bin_mask].float().mean()
                bin_count = bin_mask.sum().float()
                
                # Update running averages
                current_count = self.calibration_counts[i]
                total_count = current_count + bin_count
                
                if total_count > 0:
                    self.calibration_confidences[i] = (
                        (self.calibration_confidences[i] * current_count + 
                         bin_confidence * bin_count) / total_count
                    )
                    self.calibration_accuracies[i] = (
                        (self.calibration_accuracies[i] * current_count + 
                         bin_accuracy * bin_count) / total_count
                    )
                    self.calibration_counts[i] = total_count

class ActiveLearningManager:
    """
    Production-grade Active Learning Manager that selects the most informative samples
    for annotation to improve model performance efficiently with advanced query strategies,
    diversity measures, and budget optimization.
    """
    def __init__(self, model: 'TransformerNeuralNetBackbone', 
                 uncertainty_module: UncertaintyQuantification,
                 initial_budget: int = 1000, batch_size: int = 10):
        self.model = model
        self.uncertainty = uncertainty_module
        self.annotation_budget = initial_budget
        self.batch_size = batch_size
        
        # Query strategy configurations
        self.query_strategies = {
            'uncertainty_sampling': {'weight': 0.4, 'enabled': True},
            'diversity_sampling': {'weight': 0.3, 'enabled': True},
            'expected_gradient_length': {'weight': 0.2, 'enabled': True},
            'badge_sampling': {'weight': 0.1, 'enabled': True}
        }
        
        # Sample pools
        self.labeled_pool = set()
        self.unlabeled_pool = set()
        self.annotated_samples = []
        
        # Performance tracking
        self.query_history = []
        self.performance_trajectory = []
        self.annotation_efficiency = {
            'total_annotations': 0,
            'performance_gains': [],
            'cost_per_improvement': [],
            'diversity_scores': []
        }
        
        # Advanced selection parameters
        self.diversity_threshold = 0.7
        self.uncertainty_threshold = 0.5
        self.confidence_calibration_window = 100
        
        # Embedding cache for efficiency
        self.embedding_cache = {}
        self.cache_valid = False
    
    def _summarize_per_class_uncertainty(self,
                                         per_class_tensor: torch.Tensor,
                                         top_k: int = 5) -> Dict[str, torch.Tensor]:
        """
        Reduce per-class epistemic uncertainty to sample-level scores and token summaries.
        """
        return summarize_per_class_uncertainty(per_class_tensor, top_k)
    
    def select_samples(self, 
                       encoder_features: Optional[torch.Tensor], 
                       uncertainty_estimates: Optional[Dict[str, torch.Tensor]] = None,
                       budget: int = 10) -> Dict[str, Any]:
        """
        Feature-based sample selection used during on-the-fly training passes.
        """
        result = {
            'selected_samples': [],
            'scores': [],
            'budget_exhausted': self.annotation_budget <= 0
        }
        
        if encoder_features is None or encoder_features.numel() == 0:
            return result
        
        if budget <= 0 or self.annotation_budget <= 0:
            result['budget_exhausted'] = self.annotation_budget <= 0
            return result
        
        features = encoder_features.detach()
        selected_indices: List[int] = []
        selected_scores: List[float] = []
        
        per_class_reports: List[Dict[str, Any]] = []
        
        with torch.no_grad():
            uncertainty_tensor = None
            per_class_summary: Optional[Dict[str, torch.Tensor]] = None
            selected_uncertainty_key = None
            
            if isinstance(uncertainty_estimates, dict):
                priority_keys = [
                    'epistemic_uncertainty_per_class',
                    'evidential_epistemic_uncertainty_per_class',
                    'total_uncertainty',
                    'evidential_total_uncertainty',
                    'epistemic_uncertainty',
                    'evidential_epistemic_uncertainty',
                    'epistemic_score',
                    'aleatoric_uncertainty'
                ]
                for key in priority_keys:
                    if key in uncertainty_estimates:
                        uncertainty_tensor = uncertainty_estimates[key]
                        selected_uncertainty_key = key
                        break
            
            if uncertainty_tensor is None:
                uncertainty_tensor = features.norm(dim=-1)
                selected_uncertainty_key = 'feature_norm'
            
            if selected_uncertainty_key and 'epistemic_uncertainty_per_class' in selected_uncertainty_key:
                per_class_summary = self._summarize_per_class_uncertainty(uncertainty_tensor)
                sample_scores = per_class_summary['sample_scores']
            else:
                scoring_tensor = uncertainty_tensor
                while scoring_tensor.dim() > 1:
                    scoring_tensor = scoring_tensor.mean(dim=-1)
                sample_scores = scoring_tensor
            
            sample_scores = sample_scores.detach()
            if sample_scores.is_cuda:
                sample_scores = sample_scores.cpu()
            
            selectable = min(int(budget), sample_scores.size(0), max(0, self.annotation_budget))
            if selectable <= 0:
                result['budget_exhausted'] = self.annotation_budget <= 0
                return result
            
            scores_values, indices = torch.topk(sample_scores, k=selectable)
            selected_indices = indices.int().tolist()
            selected_scores = scores_values.tolist()
            
            if per_class_summary is not None:
                top_scores = per_class_summary['top_scores'].detach()
                top_indices = per_class_summary['top_indices'].detach()
                if top_scores.is_cuda:
                    top_scores = top_scores.cpu()
                if top_indices.is_cuda:
                    top_indices = top_indices.cpu()
                
                for idx in selected_indices:
                    token_scores = top_scores[idx].tolist()
                    token_indices = top_indices[idx].tolist()
                    per_class_reports.append({
                        'batch_index': int(idx),
                        'top_token_ids': [int(token_id) for token_id in token_indices],
                        'top_token_uncertainty': [float(score) for score in token_scores]
                    })
            else:
                per_class_reports = []
        
        selected = []
        for idx, score in zip(selected_indices, selected_scores):
            selected.append({
                'id': f"feature_sample_{idx}",
                'batch_index': idx,
                'score': float(score)
            })
        
        self.annotation_budget = max(0, self.annotation_budget - len(selected))
        self.annotation_efficiency['total_annotations'] += len(selected)
        
        self.query_history.append({
            'selected_indices': selected_indices,
            'scores': selected_scores,
            'timestamp': time.time(),
            'remaining_budget': self.annotation_budget,
            'mode': 'feature_based',
            'uncertainty_key': selected_uncertainty_key,
            'per_class_top_tokens': per_class_reports
        })
        
        result.update({
            'selected_samples': selected,
            'scores': selected_scores,
            'budget_exhausted': self.annotation_budget <= 0,
            'uncertainty_key': selected_uncertainty_key
        })
        
        if per_class_reports:
            result['per_class_uncertainty'] = per_class_reports
        
        return result
    
    def register_samples(self, sample_ids: List[str], labels: Optional[List[Any]] = None):
        """Register samples in the appropriate pools."""
        if labels is not None:
            # Labeled samples
            for sample_id, label in zip(sample_ids, labels):
                self.labeled_pool.add(sample_id)
                self.annotated_samples.append({
                    'id': sample_id,
                    'label': label,
                    'annotation_round': len(self.query_history),
                    'timestamp': time.time()
                })
        else:
            # Unlabeled samples
            self.unlabeled_pool.update(sample_ids)
        
        # Invalidate embedding cache
        self.cache_valid = False
    
    def query_samples(self, data_loader: DataLoader, num_samples: Optional[int] = None) -> Dict[str, Any]:
        """
        Main query method - select most informative samples for annotation.
        """
        if num_samples is None:
            num_samples = min(self.batch_size, self.annotation_budget)
        
        if num_samples <= 0 or len(self.unlabeled_pool) == 0:
            return {'selected_samples': [], 'query_info': {}, 'budget_exhausted': True}
        
        # Update embedding cache if needed
        if not self.cache_valid:
            self._update_embedding_cache(data_loader)
        
        # Apply enabled query strategies
        strategy_results = {}
        
        if self.query_strategies['uncertainty_sampling']['enabled']:
            strategy_results['uncertainty'] = self._uncertainty_sampling(data_loader, num_samples * 2)
        
        if self.query_strategies['diversity_sampling']['enabled']:
            strategy_results['diversity'] = self._diversity_sampling(data_loader, num_samples * 2)
        
        if self.query_strategies['expected_gradient_length']['enabled']:
            strategy_results['gradient'] = self._expected_gradient_length(data_loader, num_samples * 2)
        
        if self.query_strategies['badge_sampling']['enabled']:
            strategy_results['badge'] = self._badge_sampling(data_loader, num_samples * 2)
        
        # Combine strategies using weighted voting
        selected_samples = self._combine_strategies(strategy_results, num_samples)
        
        # Update pools and budget
        for sample_id in selected_samples:
            self.unlabeled_pool.discard(sample_id)
        
        self.annotation_budget -= len(selected_samples)
        
        # Record query information
        query_info = {
            'strategy_results': strategy_results,
            'num_selected': len(selected_samples),
            'remaining_budget': self.annotation_budget,
            'unlabeled_pool_size': len(self.unlabeled_pool),
            'query_round': len(self.query_history) + 1,
            'timestamp': time.time()
        }
        
        self.query_history.append(query_info)
        
        return {
            'selected_samples': selected_samples,
            'query_info': query_info,
            'budget_exhausted': self.annotation_budget <= 0
        }
    
    def _uncertainty_sampling(self, data_loader: DataLoader, num_candidates: int) -> List[str]:
        """Select samples with highest predictive uncertainty."""
        uncertainty_scores = []
        
        self.model.eval()
        with torch.no_grad():
            for batch in data_loader:
                if isinstance(batch, dict):
                    sample_ids = batch.get('sample_ids', [])
                    inputs = {k: v for k, v in batch.items() if k != 'sample_ids'}
                else:
                    sample_ids = getattr(batch, 'sample_ids', [])
                    inputs = batch
                
                # Skip if samples already labeled
                available_samples = [sid for sid in sample_ids if sid in self.unlabeled_pool]
                if not available_samples:
                    continue
                
                # Get uncertainty estimates
                uncertainty_results = self.uncertainty.forward(
                    self.model, inputs, method='monte_carlo'
                )
                
                # Extract uncertainty measures
                if 'mc_epistemic_uncertainty' in uncertainty_results:
                    epistemic_uncertainty = uncertainty_results['mc_epistemic_uncertainty']
                elif 'epistemic_uncertainty' in uncertainty_results:
                    epistemic_uncertainty = uncertainty_results['epistemic_uncertainty']
                else:
                    # Fallback: use prediction variance
                    epistemic_uncertainty = uncertainty_results.get('mc_predictive_variance', 
                                                                  torch.zeros(len(available_samples)))
                
                # Calculate mutual information if available
                mutual_info = uncertainty_results.get('mc_mutual_information', 
                                                     torch.zeros_like(epistemic_uncertainty))
                
                # Combined uncertainty score
                combined_uncertainty = epistemic_uncertainty + 0.5 * mutual_info
                
                for i, sample_id in enumerate(available_samples):
                    if i < len(combined_uncertainty):
                        uncertainty_scores.append((
                            sample_id, 
                            combined_uncertainty[i].item() if hasattr(combined_uncertainty[i], 'item') 
                            else float(combined_uncertainty[i])
                        ))
        
        # Sort by uncertainty and return top candidates
        uncertainty_scores.sort(key=lambda x: x[1], reverse=True)
        return [sample_id for sample_id, _ in uncertainty_scores[:num_candidates]]
    
    def _diversity_sampling(self, data_loader: DataLoader, num_candidates: int) -> List[str]:
        """Select diverse samples using embedding-based clustering."""
        if not self.embedding_cache:
            return []
        
        # Get embeddings for unlabeled samples
        unlabeled_embeddings = {}
        for sample_id in self.unlabeled_pool:
            if sample_id in self.embedding_cache:
                unlabeled_embeddings[sample_id] = self.embedding_cache[sample_id]
        
        if len(unlabeled_embeddings) < num_candidates:
            return list(unlabeled_embeddings.keys())
        
        # K-means++ initialization for diverse selection
        selected_samples = []
        remaining_samples = list(unlabeled_embeddings.keys())
        
        # Select first sample randomly
        if remaining_samples:
            first_sample = np.random.choice(remaining_samples)
            selected_samples.append(first_sample)
            remaining_samples.remove(first_sample)
        
        # Select subsequent samples based on maximum distance to selected set
        while len(selected_samples) < num_candidates and remaining_samples:
            max_min_distance = -1
            best_candidate = None
            
            for candidate in remaining_samples:
                candidate_embedding = unlabeled_embeddings[candidate]
                
                # Compute minimum distance to selected samples
                min_distance = float('inf')
                for selected in selected_samples:
                    selected_embedding = unlabeled_embeddings[selected]
                    
                    # Cosine distance
                    distance = 1.0 - F.cosine_similarity(
                        candidate_embedding.unsqueeze(0),
                        selected_embedding.unsqueeze(0),
                        dim=1
                    ).item()
                    
                    min_distance = min(min_distance, distance)
                
                # Update best candidate
                if min_distance > max_min_distance:
                    max_min_distance = min_distance
                    best_candidate = candidate
            
            if best_candidate:
                selected_samples.append(best_candidate)
                remaining_samples.remove(best_candidate)
        
        return selected_samples
    
    def _expected_gradient_length(self, data_loader: DataLoader, num_candidates: int) -> List[str]:
        """Select samples with highest expected gradient length."""
        gradient_scores = []
        
        self.model.train()  # Enable gradient computation
        
        for batch in data_loader:
            if isinstance(batch, dict):
                sample_ids = batch.get('sample_ids', [])
                inputs = {k: v for k, v in batch.items() if k != 'sample_ids'}
            else:
                sample_ids = getattr(batch, 'sample_ids', [])
                inputs = batch
            
            # Skip if samples already labeled
            available_samples = [sid for sid in sample_ids if sid in self.unlabeled_pool]
            if not available_samples:
                continue
            
            try:
                # Forward pass
                outputs = self.model(**inputs if isinstance(inputs, dict) else {'input_ids': inputs})
                logits = outputs.get('logits') if isinstance(outputs, dict) else outputs
                
                # Compute expected gradient length for each sample
                for i, sample_id in enumerate(available_samples):
                    if i < logits.size(0):
                        sample_logits = logits[i:i+1]
                        
                        # Sample from predictive distribution
                        probs = F.softmax(sample_logits, dim=-1)
                        sampled_labels = torch.multinomial(probs.view(-1, probs.size(-1)), 1)
                        
                        # Compute loss and gradients
                        loss = F.cross_entropy(sample_logits.view(-1, sample_logits.size(-1)), 
                                             sampled_labels.view(-1))
                        
                        # Compute gradients
                        self.model.zero_grad()
                        loss.backward(retain_graph=True)
                        
                        # Calculate gradient norm
                        total_grad_norm = 0.0
                        for param in self.model.parameters():
                            if param.grad is not None:
                                total_grad_norm += param.grad.norm().item() ** 2
                        
                        gradient_length = total_grad_norm ** 0.5
                        gradient_scores.append((sample_id, gradient_length))
                        
            except Exception as e:
                print(f"Warning: Gradient computation failed: {e}")
                continue
        
        # Sort by gradient length and return top candidates
        gradient_scores.sort(key=lambda x: x[1], reverse=True)
        return [sample_id for sample_id, _ in gradient_scores[:num_candidates]]
    
    def _badge_sampling(self, data_loader: DataLoader, num_candidates: int) -> List[str]:
        """BADGE (Batch Active learning by Diverse Gradient Embeddings) sampling."""
        gradient_embeddings = {}
        
        self.model.train()
        
        for batch in data_loader:
            if isinstance(batch, dict):
                sample_ids = batch.get('sample_ids', [])
                inputs = {k: v for k, v in batch.items() if k != 'sample_ids'}
            else:
                sample_ids = getattr(batch, 'sample_ids', [])
                inputs = batch
            
            # Skip if samples already labeled
            available_samples = [sid for sid in sample_ids if sid in self.unlabeled_pool]
            if not available_samples:
                continue
            
            try:
                # Get embeddings from model (before final layer)
                outputs = self.model(**inputs if isinstance(inputs, dict) else {'input_ids': inputs})
                
                if isinstance(outputs, dict):
                    embeddings = outputs.get('encoder_output')
                    if embeddings is None:
                        embeddings = outputs.get('decoder_output')
                    if embeddings is None:
                        continue
                else:
                    continue
                
                # Use final layer for gradient computation
                if hasattr(self.model, 'output_projection'):
                    final_layer = self.model.output_projection
                else:
                    continue
                
                for i, sample_id in enumerate(available_samples):
                    if i < embeddings.size(0):
                        sample_embedding = embeddings[i]  # (seq_len, d_model)
                        
                        # Pool embedding (mean over sequence)
                        pooled_embedding = sample_embedding.mean(dim=0)  # (d_model,)
                        
                        # Compute gradient of final layer with respect to embedding
                        self.model.zero_grad()
                        
                        # Forward through final layer
                        sample_logits = final_layer(pooled_embedding.unsqueeze(0))
                        
                        # Compute loss with respect to predicted class
                        predicted_class = sample_logits.argmax(dim=-1)
                        loss = F.cross_entropy(sample_logits, predicted_class)
                        
                        # Compute gradient
                        loss.backward(retain_graph=True)
                        
                        # Get gradient embedding
                        if final_layer.weight.grad is not None:
                            grad_embedding = final_layer.weight.grad[predicted_class].clone()
                            gradient_embeddings[sample_id] = grad_embedding.detach()
                        
            except Exception as e:
                print(f"Warning: BADGE computation failed: {e}")
                continue
        
        # Apply k-means++ on gradient embeddings for diverse selection
        if len(gradient_embeddings) < num_candidates:
            return list(gradient_embeddings.keys())
        
        # Convert to tensor for clustering
        sample_ids = list(gradient_embeddings.keys())
        embeddings_tensor = torch.stack([gradient_embeddings[sid] for sid in sample_ids])
        
        # K-means++ selection
        selected_indices = []
        remaining_indices = list(range(len(sample_ids)))
        
        # Select first sample randomly
        if remaining_indices:
            first_idx = np.random.choice(remaining_indices)
            selected_indices.append(first_idx)
            remaining_indices.remove(first_idx)
        
        # Select subsequent samples
        while len(selected_indices) < num_candidates and remaining_indices:
            max_min_distance = -1
            best_idx = None
            
            for candidate_idx in remaining_indices:
                candidate_emb = embeddings_tensor[candidate_idx]
                
                min_distance = float('inf')
                for selected_idx in selected_indices:
                    selected_emb = embeddings_tensor[selected_idx]
                    distance = torch.norm(candidate_emb - selected_emb).item()
                    min_distance = min(min_distance, distance)
                
                if min_distance > max_min_distance:
                    max_min_distance = min_distance
                    best_idx = candidate_idx
            
            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)
        
        return [sample_ids[idx] for idx in selected_indices]
    
    def _combine_strategies(self, strategy_results: Dict[str, List[str]], num_samples: int) -> List[str]:
        """Combine multiple strategy results using weighted voting."""
        sample_scores = {}
        
        # Weight and combine strategy results
        for strategy_name, sample_list in strategy_results.items():
            if strategy_name in self.query_strategies and self.query_strategies[strategy_name]['enabled']:
                weight = self.query_strategies[strategy_name]['weight']
                
                # Assign scores based on rank (higher rank = higher score)
                for rank, sample_id in enumerate(sample_list):
                    score = (len(sample_list) - rank) * weight
                    sample_scores[sample_id] = sample_scores.get(sample_id, 0) + score
        
        # Sort by combined score and select top samples
        sorted_samples = sorted(sample_scores.items(), key=lambda x: x[1], reverse=True)
        return [sample_id for sample_id, _ in sorted_samples[:num_samples]]
    
    def _update_embedding_cache(self, data_loader: DataLoader):
        """Update embedding cache for efficient diversity computation."""
        self.embedding_cache.clear()
        
        self.model.eval()
        with torch.no_grad():
            for batch in data_loader:
                if isinstance(batch, dict):
                    sample_ids = batch.get('sample_ids', [])
                    inputs = {k: v for k, v in batch.items() if k != 'sample_ids'}
                else:
                    sample_ids = getattr(batch, 'sample_ids', [])
                    inputs = batch
                
                # Get model embeddings
                outputs = self.model(**inputs if isinstance(inputs, dict) else {'input_ids': inputs})
                
                if isinstance(outputs, dict):
                    embeddings = outputs.get('encoder_output')
                    if embeddings is None:
                        embeddings = outputs.get('decoder_output')
                    if embeddings is None:
                        continue
                else:
                    continue
                
                # Store embeddings (mean pooled over sequence)
                for i, sample_id in enumerate(sample_ids):
                    if i < embeddings.size(0) and sample_id in self.unlabeled_pool:
                        pooled_embedding = embeddings[i].mean(dim=0)  # Mean over sequence
                        self.embedding_cache[sample_id] = pooled_embedding
        
        self.cache_valid = True
    
    def update_model_performance(self, validation_accuracy: float, 
                               validation_loss: float) -> Dict[str, float]:
        """Update performance tracking after model retraining."""
        performance_record = {
            'round': len(self.query_history),
            'accuracy': validation_accuracy,
            'loss': validation_loss,
            'annotations_used': self.annotation_efficiency['total_annotations'],
            'timestamp': time.time()
        }
        
        self.performance_trajectory.append(performance_record)
        
        # Calculate efficiency metrics
        if len(self.performance_trajectory) > 1:
            prev_accuracy = self.performance_trajectory[-2]['accuracy']
            accuracy_gain = validation_accuracy - prev_accuracy
            
            annotations_since_last = (self.annotation_efficiency['total_annotations'] - 
                                    self.performance_trajectory[-2]['annotations_used'])
            
            if annotations_since_last > 0:
                efficiency = accuracy_gain / annotations_since_last
                self.annotation_efficiency['performance_gains'].append(accuracy_gain)
                self.annotation_efficiency['cost_per_improvement'].append(1.0 / max(efficiency, 1e-6))
        
        return performance_record
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get comprehensive query and performance statistics."""
        stats = {
            'total_annotations': len(self.annotated_samples),
            'remaining_budget': self.annotation_budget,
            'query_rounds': len(self.query_history),
            'unlabeled_pool_size': len(self.unlabeled_pool),
            'labeled_pool_size': len(self.labeled_pool),
            'annotation_efficiency': self.annotation_efficiency.copy(),
            'performance_trajectory': self.performance_trajectory.copy(),
            'strategy_weights': {k: v['weight'] for k, v in self.query_strategies.items()},
            'cache_status': self.cache_valid
        }
        
        # Add efficiency metrics
        if self.annotation_efficiency['performance_gains']:
            stats['average_accuracy_gain'] = np.mean(self.annotation_efficiency['performance_gains'])
            stats['average_cost_per_improvement'] = np.mean(self.annotation_efficiency['cost_per_improvement'])
        
        return stats
    
    def adjust_strategy_weights(self, strategy_performance: Dict[str, float]):
        """Dynamically adjust strategy weights based on performance."""
        total_performance = sum(strategy_performance.values())
        
        if total_performance > 0:
            for strategy_name, performance in strategy_performance.items():
                if strategy_name in self.query_strategies:
                    # Update weight based on relative performance
                    new_weight = performance / total_performance
                    self.query_strategies[strategy_name]['weight'] = new_weight
        
        # Renormalize weights
        total_weight = sum(s['weight'] for s in self.query_strategies.values())
        if total_weight > 0:
            for strategy in self.query_strategies.values():
                strategy['weight'] /= total_weight
