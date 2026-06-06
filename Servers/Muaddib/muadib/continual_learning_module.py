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
