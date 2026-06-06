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
        self.memory_values = nn.Parameter(torch.randn(memory_size, config.d_model) * 0.02)
        
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
        self.value_projection = nn.Linear(config.d_model, config.d_model)
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
          