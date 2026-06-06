import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from abc import ABC, abstractmethod

# Type definitions for structured outputs
@dataclass
class CodeOutput:
    """Structured representation of code generation output"""
    code: str
    language: str
    execution_status: Optional[bool] = None
    execution_result: Optional[Any] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class StructuredData:
    """Structured data output with type information"""
    data: Any
    schema: Dict[str, Any]
    data_type: str
    confidence: float = 0.0
    validation_errors: List[str] = None

class OutputModality(Enum):
    """Enum for different output modalities"""
    CODE = "code"
    STRUCTURED_DATA = "structured_data"
    NATURAL_LANGUAGE = "natural_language"
    MIXED = "mixed"

class CodeLanguage(Enum):
    """Supported programming languages for code modality"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    RUST = "rust"
    GO = "go"
    SQL = "sql"
    BASH = "bash"
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"

class DataType(Enum):
    """Supported structured data types"""
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    XML = "xml"
    TABLE = "table"
    GRAPH = "graph"
    TREE = "tree"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"

class ModalityOutputHead(nn.Module):
    """
    Multi-modality output head that separates code generation from natural language
    Designed to enable "thinking in code" while maintaining clean structured outputs
    """
    
    def __init__(
        self,
        hidden_dim: int = 1024,
        num_layers: int = 2,
        dropout: float = 0.1,
        max_code_length: int = 2048,
        max_structured_length: int = 1024,
        vocab_size_code: int = 50257,  # Code-specific vocabulary
        vocab_size_structured: int = 50257,  # Structured data vocabulary
        code_languages: List[CodeLanguage] = None,
        data_types: List[DataType] = None,
        temperature: float = 0.7,
        top_p: float = 0.9
    ):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.max_code_length = max_code_length
        self.max_structured_length = max_structured_length
        self.temperature = temperature
        self.top_p = top_p
        
        # Default supported types if not specified
        self.code_languages = code_languages or list(CodeLanguage)
        self.data_types = data_types or list(DataType)
        
        # Language and type embeddings
        self.code_lang_embedding = nn.Embedding(
            len(self.code_languages), hidden_dim
        )
        self.data_type_embedding = nn.Embedding(
            len(self.data_types), hidden_dim
        )
        
        # Modality routing network
        self.modality_router = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, len(OutputModality)),
            nn.Softmax(dim=-1)
        )
        
        # Code generation head
        self.code_head = nn.ModuleDict({
            lang.value: CodeGenerationHead(
                hidden_dim, vocab_size_code, max_code_length, 
                num_layers, dropout, lang
            ) for lang in self.code_languages
        })
        
        # Structured data head
        self.structured_head = nn.ModuleDict({
            dtype.value: StructuredDataHead(
                hidden_dim, vocab_size_structured, max_structured_length,
                num_layers, dropout, dtype
            ) for dtype in self.data_types
        })
        
        # Confidence scoring network
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        
        # Metadata extraction network
        self.metadata_extractor = MetadataExtractor(hidden_dim, dropout)
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0, std=0.02)
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        modality_prompt: Optional[str] = None,
        language: Optional[CodeLanguage] = None,
        data_type: Optional[DataType] = None,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Forward pass through the modality output head
        
        Args:
            hidden_states: Model's hidden states [batch_size, seq_len, hidden_dim]
            modality_prompt: String indicating desired output modality
            language: Target programming language for code generation
            data_type: Target data type for structured output
            attention_mask: Attention mask for the sequence
            **kwargs: Additional arguments for specific heads
            
        Returns:
            Dictionary containing outputs for different modalities
        """
        batch_size, seq_len, _ = hidden_states.shape
        
        # Get modality probabilities
        modality_logits = self.modality_router(hidden_states.mean(dim=1))
        modality_probs = torch.softmax(modality_logits, dim=-1)
        
        outputs = {
            'modality_probs': modality_probs,
            'code_outputs': {},
            'structured_outputs': {},
            'metadata': {}
        }
        
        # Process code generation
        if modality_prompt == OutputModality.CODE.value or language is not None:
            lang = language or CodeLanguage.PYTHON
            if lang.value in self.code_head:
                code_hidden = self._prepare_code_input(
                    hidden_states, lang, attention_mask
                )
                code_output = self.code_head[lang.value](
                    code_hidden, attention_mask=attention_mask, **kwargs
                )
                outputs['code_outputs'][lang.value] = code_output
                
                # Extract confidence and metadata
                confidence = self.confidence_head(
                    torch.cat([hidden_states.mean(dim=1), 
                             code_hidden.mean(dim=1), 
                             code_output['logits'].mean(dim=1)], dim=-1)
                )
                code_output['confidence'] = confidence
                
                metadata = self.metadata_extractor(
                    hidden_states, modality=OutputModality.CODE.value
                )
                outputs['metadata'][lang.value] = metadata
        
        # Process structured data generation
        if modality_prompt == OutputModality.STRUCTURED_DATA.value or data_type is not None:
            dtype = data_type or DataType.JSON
            if dtype.value in self.structured_head:
                struct_hidden = self._prepare_structured_input(
                    hidden_states, dtype, attention_mask
                )
                struct_output = self.structured_head[dtype.value](
                    struct_hidden, attention_mask=attention_mask, **kwargs
                )
                outputs['structured_outputs'][dtype.value] = struct_output
                
                # Extract confidence and metadata
                confidence = self.confidence_head(
                    torch.cat([hidden_states.mean(dim=1), 
                             struct_hidden.mean(dim=1), 
                             struct_output['logits'].mean(dim=1)], dim=-1)
                )
                struct_output['confidence'] = confidence
                
                metadata = self.metadata_extractor(
                    hidden_states, modality=OutputModality.STRUCTURED_DATA.value
                )
                outputs['metadata'][dtype.value] = metadata
        
        return outputs
    
    def _prepare_code_input(
        self,
        hidden_states: torch.Tensor,
        language: CodeLanguage,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Prepare input specifically for code generation"""
        batch_size, seq_len, _ = hidden_states.shape
        
        # Add language embedding
        lang_idx = self.code_languages.index(language)
        lang_emb = self.code_lang_embedding(
            torch.full((batch_size,), lang_idx, device=hidden_states.device)
        )
        lang_emb = lang_emb.unsqueeze(1).expand(-1, seq_len, -1)
        
        # Combine with hidden states
        code_input = hidden_states + lang_emb
        
        # Apply code-specific projection
        code_proj = nn.Linear(self.hidden_dim, self.hidden_dim).to(hidden_states.device)
        code_input = code_proj(code_input)
        
        return code_input
    
    def _prepare_structured_input(
        self,
        hidden_states: torch.Tensor,
        data_type: DataType,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Prepare input specifically for structured data generation"""
        batch_size, seq_len, _ = hidden_states.shape
        
        # Add data type embedding
        dtype_idx = self.data_types.index(data_type)
        dtype_emb = self.data_type_embedding(
            torch.full((batch_size,), dtype_idx, device=hidden_states.device)
        )
        dtype_emb = dtype_emb.unsqueeze(1).expand(-1, seq_len, -1)
        
        # Combine with hidden states
        struct_input = hidden_states + dtype_emb
        
        # Apply structured data projection
        struct_proj = nn.Linear(self.hidden_dim, self.hidden_dim).to(hidden_states.device)
        struct_input = struct_proj(struct_input)
        
        return struct_input
    
    def generate(
        self,
        hidden_states: torch.Tensor,
        modality: OutputModality,
        language: Optional[CodeLanguage] = None,
        data_type: Optional[DataType] = None,
        max_length: int = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Union[CodeOutput, StructuredData, Dict[str, Any]]:
        """
        Generate output for specific modality
        
        Args:
            hidden_states: Model hidden states
            modality: Target output modality
            language: Programming language for code generation
            data_type: Data type for structured output
            max_length: Maximum generation length
            temperature: Sampling temperature
            
        Returns:
            Generated output in the specified modality
        """
        if modality == OutputModality.CODE:
            return self._generate_code(
                hidden_states, language or CodeLanguage.PYTHON,
                max_length=max_length, temperature=temperature, **kwargs
            )
        elif modality == OutputModality.STRUCTURED_DATA:
            return self._generate_structured(
                hidden_states, data_type or DataType.JSON,
                max_length=max_length, temperature=temperature, **kwargs
            )
        else:
            raise ValueError(f"Unsupported modality: {modality}")

class CodeGenerationHead(nn.Module):
    """Specialized head for code generation with language-specific processing"""
    
    def __init__(
        self,
        hidden_dim: int,
        vocab_size: int,
        max_length: int,
        num_layers: int,
        dropout: float,
        language: CodeLanguage
    ):
        super().__init__()
        self.language = language
        self.max_length = max_length
        
        # Language-specific preprocessing layers
        self.preprocess_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        ] * num_layers)
        
        # Code syntax embedding (for common code patterns)
        self.syntax_embed = nn.Embedding(1000, hidden_dim)  # Common code tokens
        
        # Language-specific output projection
        self.output_projection = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, vocab_size)
        )
        
        # Indentation and formatting head
        self.format_head = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 4)  # Predict indentation level (0-3 spaces)
        )
        
        # Error detection head
        self.error_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """Forward pass for code generation"""
        # Preprocess for language-specific features
        x = hidden_states
        for layer in self.preprocess_layers:
            x = layer(x)
        
        # Add syntax information (simplified)
        syntax_ids = torch.zeros(x.shape[:2], dtype=torch.long, device=x.device)
        syntax_emb = self.syntax_embed(syntax_ids)
        x = x + syntax_emb
        
        # Generate code tokens
        logits = self.output_projection(x)
        
        # Predict formatting
        formatting_logits = self.format_head(x.mean(dim=1))
        
        # Detect potential errors
        error_probs = self.error_detector(x.mean(dim=1))
        
        return {
            'logits': logits,
            'formatting_logits': formatting_logits,
            'error_probs': error_probs,
            'language': self.language
        }
    
    def generate_code(
        self,
        hidden_states: torch.Tensor,
        prompt: str = "",
        max_length: int = None,
        temperature: float = 0.7,
        **kwargs
    ) -> CodeOutput:
        """Generate complete code output"""
        max_length = max_length or self.max_length
        device = hidden_states.device
        
        # Simplified generation (in practice, would use full autoregressive decoding)
        with torch.no_grad():
            outputs = self.forward(hidden_states)
            logits = outputs['logits'][:, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            
            # Use nucleus sampling
            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
            cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
            sorted_indices_to_remove = cumulative_probs > self.top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0
            indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
            probs[indices_to_remove] = 0
            probs = probs / probs.sum(dim=-1, keepdim=True)
            
            next_token_ids = torch.multinomial(probs, num_samples=1)
            
            # For demo, we'll create a synthetic code output
            # In real implementation, this would be full autoregressive generation
            generated_code = self._synthesize_code(
                prompt, next_token_ids, outputs['language']
            )
            
            # Simulate execution (in practice, would actually execute)
            execution_status, execution_result = self._simulate_execution(generated_code)
            
            confidence = outputs['error_probs'].mean().item()
            
        return CodeOutput(
            code=generated_code,
            language=outputs['language'].value,
            execution_status=execution_status,
            execution_result=execution_result,
            confidence=1.0 - confidence,  # Invert error probability
            metadata={
                'temperature': temperature,
                'max_length': max_length,
                'formatting': F.softmax(outputs['formatting_logits'], dim=-1).cpu().numpy()
            }
        )
    
    def _synthesize_code(self, prompt: str, token_ids: torch.Tensor, language: CodeLanguage) -> str:
        """Synthesize code based on prompt and tokens (placeholder)"""
        # This is a simplified version - real implementation would decode tokens properly
        base_code = {
            CodeLanguage.PYTHON: f"# {prompt}\ndef generated_function():\n    return 'Hello from {language.value}!'",
            CodeLanguage.JAVASCRIPT: f"// {prompt}\nfunction generatedFunction() {{\n  return `Hello from {language.value}!`;\n}}",
            CodeLanguage.SQL: f"-- {prompt}\nSELECT 'Hello from {language.value}' AS greeting;"
        }.get(language, f"# {prompt}\n// Generated code for {language.value}")
        
        return base_code
    
    def _simulate_execution(self, code: str) -> Tuple[Optional[bool], Optional[Any]]:
        """Simulate code execution for validation"""
        try:
            if self.language == CodeLanguage.PYTHON:
                # Safe execution in real implementation would use restricted environment
                exec_globals = {}
                exec(code, exec_globals)
                return True, "Executed successfully"
            return True, "Simulated success"
        except Exception as e:
            return False, str(e)

class StructuredDataHead(nn.Module):
    """Specialized head for structured data generation with schema validation"""
    
    def __init__(
        self,
        hidden_dim: int,
        vocab_size: int,
        max_length: int,
        num_layers: int,
        dropout: float,
        data_type: DataType
    ):
        super().__init__()
        self.data_type = data_type
        self.max_length = max_length
        
        # Type-specific preprocessing
        self.preprocess_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        ] * num_layers)
        
        # Schema prediction head
        self.schema_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 256),  # Schema vocabulary
            nn.Softmax(dim=-1)
        )
        
        # Data generation head
        self.data_projection = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, vocab_size)
        )
        
        # Type validation head
        self.validation_head = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """Forward pass for structured data generation"""
        # Preprocess for data type
        x = hidden_states
        for layer in self.preprocess_layers:
            x = layer(x)
        
        # Predict schema
        schema_logits = self.schema_head(x.mean(dim=1))
        
        # Generate data tokens
        data_logits = self.data_projection(x)
        
        # Validate type consistency
        validation_scores = self.validation_head(x.mean(dim=1))
        
        return {
            'data_logits': data_logits,
            'schema_logits': schema_logits,
            'validation_scores': validation_scores,
            'data_type': self.data_type
        }
    
    def generate_structured(
        self,
        hidden_states: torch.Tensor,
        schema_prompt: Optional[Dict] = None,
        max_length: int = None,
        temperature: float = 0.7,
        **kwargs
    ) -> StructuredData:
        """Generate structured data output"""
        max_length = max_length or self.max_length
        device = hidden_states.device
        
        with torch.no_grad():
            outputs = self.forward(hidden_states)
            
            # Generate schema if not provided
            if schema_prompt is None:
                schema_prompt = self._generate_schema(outputs['schema_logits'])
            
            # Generate data based on schema and type
            generated_data = self._generate_data_by_type(
                outputs['data_logits'], schema_prompt, temperature
            )
            
            # Validate structure
            validation_score = outputs['validation_scores'].mean().item()
            validation_errors = self._validate_structure(generated_data, schema_prompt)
            
            confidence = validation_score
        
        return StructuredData(
            data=generated_data,
            schema=schema_prompt,
            data_type=self.data_type.value,
            confidence=confidence,
            validation_errors=validation_errors
        )
    
    def _generate_schema(self, schema_logits: torch.Tensor) -> Dict[str, Any]:
        """Generate schema based on logits (simplified)"""
        # In practice, this would decode schema tokens
        base_schema = {
            DataType.JSON: {
                "type": "object",
                "properties": {
                    "generated_field": {"type": "string"},
                    "value": {"type": "number"}
                },
                "required": ["generated_field", "value"]
            },
            DataType.CSV: {
                "columns": ["id", "name", "value"],
                "types": ["integer", "string", "float"]
            },
            DataType.YAML: {
                "structure": {
                    "generated_data": {
                        "key": "value"
                    }
                }
            }
        }.get(self.data_type, {"type": "object"})
        
        return base_schema
    
    def _generate_data_by_type(
        self,
        data_logits: torch.Tensor,
        schema: Dict[str, Any],
        temperature: float
    ) -> Any:
        """Generate data specific to the data type"""
        if self.data_type == DataType.JSON:
            # Generate JSON structure
            sample_data = {
                "generated_field": f"Data from {self.data_type.value}",
                "value": 42.0,
                "timestamp": "2025-09-08T12:00:00Z"
            }
            return json.dumps(sample_data, indent=2)
        
        elif self.data_type == DataType.CSV:
            return "id,name,value\n1,Sample,42.0\n2,Another,99.9"
        
        elif self.data_type == DataType.YAML:
            yaml_data = {
                "generated_data": {
                    "key": "value",
                    "type": self.data_type.value,
                    "confidence": 0.95
                }
            }
            return yaml_data  # Would need proper YAML serialization
        
        elif self.data_type == DataType.TABLE:
            return {
                "headers": ["Field", "Value", "Type"],
                "rows": [
                    ["generated", "sample_data", "string"],
                    ["confidence", 0.95, "float"],
                    ["timestamp", "2025-09-08", "date"]
                ]
            }
        
        else:
            # Default to simple dictionary
            return {"type": self.data_type.value, "generated": True, "value": "sample"}
    
    def _validate_structure(self, data: Any, schema: Dict[str, Any]) -> List[str]:
        """Validate generated structure against schema"""
        errors = []
        
        if self.data_type == DataType.JSON:
            try:
                json.loads(data)
            except json.JSONDecodeError as e:
                errors.append(f"JSON parsing error: {str(e)}")
        
        elif self.data_type == DataType.CSV:
            if not isinstance(data, str) or '\n' not in data:
                errors.append("CSV must be string with newlines")
        
        # Add more validation for other types...
        
        return errors

class MetadataExtractor(nn.Module):
    """Extracts metadata and execution context from hidden states"""
    
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.metadata_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 128)
        )
        
        # Context type classifier
        self.context_classifier = nn.Linear(128, 8)  # Different context types
    
    def forward(
        self,
        hidden_states: torch.Tensor,
        modality: str
    ) -> Dict[str, Any]:
        """Extract metadata features"""
        batch_size = hidden_states.shape[0]
        
        # Extract features
        features = self.metadata_proj(hidden_states.mean(dim=1))
        
        # Classify context
        context_logits = self.context_classifier(features)
        context_probs = F.softmax(context_logits, dim=-1)
        
        return {
            'features': features.cpu().numpy(),
            'context_probs': context_probs.cpu().numpy(),
            'modality': modality,
            'timestamp': '2025-09-08T12:00:00Z',  # Would be dynamic
            'sequence_length': hidden_states.shape[1]
        }

# Example usage and testing
def test_modality_head():
    """Test the modality output head with sample inputs"""
    
    # Initialize the head
    head = ModalityOutputHead(
        hidden_dim=768,  # BERT-base size
        num_layers=2,
        dropout=0.1,
        max_code_length=512,
        max_structured_length=256
    )
    
    # Create sample hidden states (batch_size=2, seq_len=10, hidden_dim=768)
    hidden_states = torch.randn(2, 10, 768)
    attention_mask = torch.ones(2, 10)
    
    print("Testing Code Generation...")
    # Test code generation
    code_output = head.generate(
        hidden_states,
        modality=OutputModality.CODE,
        language=CodeLanguage.PYTHON,
        max_length=100,
        temperature=0.8
    )
    print(f"Generated Python code: {code_output.code[:100]}...")
    print(f"Confidence: {code_output.confidence:.3f}")
    print(f"Language: {code_output.language}")
    
    print("\nTesting Structured Data Generation...")
    # Test structured data generation
    structured_output = head.generate(
        hidden_states,
        modality=OutputModality.STRUCTURED_DATA,
        data_type=DataType.JSON,
        max_length=50,
        temperature=0.7
    )
    print(f"Generated JSON: {structured_output.data}")
    print(f"Data type: {structured_output.data_type}")
    print(f"Confidence: {structured_output.confidence:.3f}")
    print(f"Validation errors: {structured_output.validation_errors}")
    
    # Test forward pass
    print("\nTesting Forward Pass...")
    outputs = head(hidden_states, modality_prompt="code", language=CodeLanguage.JAVASCRIPT)
    print(f"Modality probabilities: {outputs['modality_probs'].shape}")
    print(f"Code outputs available for: {list(outputs['code_outputs'].keys())}")
    print(f"Structured outputs available for: {list(outputs['structured_outputs'].keys())}")

if __name__ == "__main__":
    test_modality_head()
