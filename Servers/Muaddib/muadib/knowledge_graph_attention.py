class KnowledgeGraphAttention(MultiHeadAttention):
    """
    Production-grade Knowledge Graph Enhanced Attention that injects structured knowledge
    from a knowledge graph into the attention mechanism with improved error handling,
    caching, and performance optimizations.
    """
    def __init__(self, config: NeuralNetConfig, kg_dim: int = 128, num_relations: int = 50, 
                 max_entities: int = 100000, cache_size: int = 10000):
        super().__init__(config)
        self.kg_dim = kg_dim
        self.num_relations = num_relations
        self.max_entities = max_entities
        self.cache_size = cache_size
        
        # Knowledge graph embeddings with proper initialization
        self.relation_embeddings = nn.Embedding(num_relations, kg_dim)
        self.entity_embeddings = nn.Embedding(max_entities, kg_dim)
        
        # Knowledge injection network with residual connections
        self.kg_injector = nn.Sequential(
            nn.Linear(config.d_model + kg_dim, config.d_model * 2),
            nn.LayerNorm(config.d_model * 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model * 2, config.d_model),
            nn.Dropout(config.dropout)
        )
        
        # Knowledge-aware attention bias with improved architecture
        self.kg_attention_bias = nn.Sequential(
            nn.Linear(kg_dim * 2, kg_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(kg_dim, 1)
        )
        
        # Entity-relation cache for performance
        self.entity_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Knowledge graph statistics
        self.kg_stats = {
            'total_queries': 0,
            'successful_lookups': 0,
            'cache_efficiency': 0.0
        }
        
        self._init_kg_weights()
    
    def _init_kg_weights(self):
        """Initialize knowledge graph specific weights with proper scaling."""
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
        
        # Compute entity features
        relations = knowledge_graph[entity_id].get('relations', [])
        if not relations:
            return None
        
        # Convert to tensor if needed
        if isinstance(relations, list):
            relations = torch.tensor(relations, dtype=torch.long, device=self.entity_embeddings.weight.device)
        
        # Get relation embeddings and aggregate
        rel_embeds = self.relation_embeddings(relations)
        entity_features = rel_embeds.mean(dim=0)
        
        # Cache management
        if len(self.entity_cache) >= self.cache_size:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(self.entity_cache))
            del self.entity_cache[oldest_key]
        
        self.entity_cache[cache_key] = entity_features.detach()
        return entity_features
    
    def get_entity_relations(self, entities: torch.Tensor, knowledge_graph: Dict) -> torch.Tensor:
        """
        Enhanced entity relation retrieval with batch processing, error handling,
        and performance optimizations.
        """
        self.kg_stats['total_queries'] += 1
        
        if knowledge_graph is None:
            return torch.zeros(entities.shape + (self.kg_dim,), device=entities.device)
        
        batch_size, seq_len = entities.shape
        kg_features = torch.zeros(batch_size, seq_len, self.kg_dim, device=entities.device)
        
        successful_lookups = 0
        
        # Batch process entities for efficiency
        for b in range(batch_size):
            entity_batch = entities[b]
            unique_entities = torch.unique(entity_batch)
            
            # Pre-compute features for unique entities
            entity_feature_map = {}
            for entity_id in unique_entities:
                if entity_id.item() == 0:  # Skip padding tokens
                    continue
                
                features = self._get_cached_entity_features(entity_id.item(), knowledge_graph)
                if features is not None:
                    entity_feature_map[entity_id.item()] = features
                    successful_lookups += 1
            
            # Assign features to positions
            for i in range(seq_len):
                entity_id = entity_batch[i].item()
                if entity_id in entity_feature_map:
                    kg_features[b, i] = entity_feature_map[entity_id]
        
        self.kg_stats['successful_lookups'] += successful_lookups
        
        # Update cache efficiency
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
        """
        Enhanced forward pass with knowledge graph integration and improved attention.
        """
        # Standard attention computation
        attn_output, attn_weights = super().forward(
            query, key, value, attn_mask, key_padding_mask, position_bias
        )
        
        if input_entities is not None and knowledge_graph is not None:
            try:
                # Inject knowledge features with error handling
                kg_features = self.get_entity_relations(input_entities, knowledge_graph)
                
                # Skip if no knowledge features found
                if kg_features.sum() == 0:
                    return attn_output, attn_weights
                
                # Combine with query features using residual connection
                combined_features = torch.cat([query, kg_features], dim=-1)
                kg_injection = self.kg_injector(combined_features)
                
                # Residual connection for stability
                attn_output = attn_output + kg_injection
                
                # Compute knowledge-aware attention bias
                kg_bias_input = torch.cat([
                    kg_features.unsqueeze(2).expand(-1, -1, kg_features.size(1), -1),
                    kg_features.unsqueeze(1).expand(-1, kg_features.size(1), -1, -1)
                ], dim=-1)
                
                kg_bias = self.kg_attention_bias(kg_bias_input).squeeze(-1)
                
                # Apply bias with proper masking
                if attn_mask is not None:
                    kg_bias = kg_bias.masked_fill(attn_mask == 0, float('-inf'))
                
                # Re-compute attention with knowledge bias
                batch_size, tgt_len, embed_dim = query.size()
                src_len = key.size(1)
                
                Q = self.q_proj(query).view(batch_size, tgt_len, self.nhead, embed_dim // self.nhead).transpose(1, 2)
                K = self.k_proj(key).view(batch_size, src_len, self.nhead, embed_dim // self.nhead).transpose(1, 2)
                V = self.v_proj(value).view(batch_size, src_len, self.nhead, embed_dim // self.nhead).transpose(1, 2)
                
                Q = Q * self.scale
                attn_scores = torch.matmul(Q, K.transpose(-2, -1))
                
                # Add knowledge bias
                attn_scores = attn_scores + kg_bias.unsqueeze(1)
                
                attn_weights = F.softmax(attn_scores, dim=-1)
                attn_weights = self.attn_dropout(attn_weights)
                
                attn_output = torch.matmul(attn_weights, V)
                attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, tgt_len, embed_dim)
                attn_output = self.out_proj(attn_output)
                attn_output = self.proj_dropout(attn_output)
                
            except Exception as e:
                # Graceful fallback to standard attention
                print(f"Warning: Knowledge graph attention failed, falling back to standard attention: {e}")
                pass
        
        return attn_output, attn_weights
    
    def get_kg_statistics(self) -> Dict[str, float]:
        """Get knowledge graph usage statistics."""
        return self.kg_stats.copy()
    
    def clear_cache(self):
        """Clear the entity cache."""
        self.entity_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        
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
            task_embed = self.task_embeddings(torch.tensor([task_id], device=x.device))
            task_embed = task_embed.expand(x.size(0), -1, -1)
            
            # Residual connection with task embedding
            if x.dim() == 3 and task_embed.dim() == 3:
                x = x + task_embed
            elif x.dim() == 2:
                x = x + task_embed.squeeze(1)
        
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
