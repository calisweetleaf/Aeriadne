#!/usr/bin/env python3
"""
Unified Modality System — Consolidated modality heads for the Muad'Dib substrate.

Merges the real components from structured_data_modalities.py and
code_and_structured_modality.py into a single clean module:

  - ModalityOutputHead: Top-level router selecting code vs structured vs tool
  - CodeGenerationHead: Language-specific code generation with syntax embeddings
  - StructuredDataHead: Schema-aware structured output with validation
  - StructureGenerator: JSON/XML/CSV/SQL/Graph type routing + generation heads
  - HierarchicalStructureGeneration: TransformerEncoder for schema planning
  - MetadataExtractor: Metadata extraction from hidden states

Killed: ConstitutionalStructuredSafety (never defined), fake memory stubs
(torch.randn), placeholder codegen stubs, duplicate StructuredDataHead.

Source: Sovereign MCP Server — Muad'Dib Neural Substrate
"""

from __future__ import annotations

import json
import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  TYPE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════


class StructuredDataMode(Enum):
    """Supported structured output formats."""
    JSON = auto()
    XML = auto()
    CSV = auto()
    SQL = auto()
    GRAPH = auto()
    TABLE = auto()
    API_CALL = auto()


class OutputModality(Enum):
    """Output modality routing targets."""
    CODE = "code"
    STRUCTURED_DATA = "structured_data"
    NATURAL_LANGUAGE = "natural_language"
    TOOL = "tool"
    MIXED = "mixed"


class CodeLanguage(Enum):
    """Supported programming languages for code modality."""
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
    """Supported structured data types."""
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


@dataclass
class CodeOutput:
    """Structured representation of code generation output."""
    code: str
    language: str
    execution_status: Optional[bool] = None
    execution_result: Optional[Any] = None
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StructuredData:
    """Structured data output with type information."""
    data: Any
    schema: Dict[str, Any]
    data_type: str
    confidence: float = 0.0
    validation_errors: Optional[List[str]] = None


@dataclass
class StructuredDataConfig:
    """Configuration for structured data generation."""
    output_format: StructuredDataMode = StructuredDataMode.JSON
    max_depth: int = 10
    max_items: int = 10000
    include_schema: bool = True
    validate_output: bool = True
    hierarchical_generation: bool = True
    enable_streaming: bool = False
    chunk_size: int = 1000
    use_fp16: bool = True


# ═══════════════════════════════════════════════════════════════════════════
#  STRUCTURE GENERATOR (from structured_data_modalities.py)
# ═══════════════════════════════════════════════════════════════════════════


class StructureGenerator(nn.Module):
    """
    Core structure generation from hidden states.

    Routes to format-specific generation heads based on the target
    StructuredDataMode. Produces logits for keys, values, schemas,
    and graph structures.
    """

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.hidden_size = hidden_size

        # Structure type router
        self.structure_classifier = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, len(StructuredDataMode)),
            nn.Softmax(dim=-1),
        )

        # JSON/object generators
        self.json_key_generator = nn.Linear(hidden_size, 50000)
        self.json_value_generator = nn.Linear(hidden_size, 50000)
        self.json_type_predictor = nn.Linear(hidden_size, 6)  # str, int, float, bool, null, object

        # Table generators
        self.table_schema_generator = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1000),
        )
        self.cell_value_generator = nn.Linear(hidden_size, 50000)

        # SQL generators
        self.sql_clause_generator = nn.Linear(hidden_size, 20)
        self.sql_table_generator = nn.Linear(hidden_size, 10000)
        self.sql_column_generator = nn.Linear(hidden_size, 10000)

        # Graph generators
        self.node_generator = nn.Linear(hidden_size, 50000)
        self.edge_generator = nn.Linear(hidden_size, 50000)
        self.graph_type_predictor = nn.Linear(hidden_size, 5)

        # Depth controller
        self.depth_controller = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        hidden_states: torch.Tensor,
        structure_mode: StructuredDataMode,
        depth_level: int = 0,
    ) -> Dict[str, torch.Tensor]:
        batch_size, seq_len, hidden_dim = hidden_states.shape
        pooled = hidden_states.mean(dim=1)

        structure_probs = self.structure_classifier(pooled)
        depth_factor = self.depth_controller(pooled)

        outputs: Dict[str, torch.Tensor] = {
            "structure_probs": structure_probs,
            "depth_factor": depth_factor,
        }

        if structure_mode == StructuredDataMode.JSON:
            outputs.update(
                {
                    "key_logits": self.json_key_generator(pooled),
                    "value_logits": self.json_value_generator(pooled),
                    "type_logits": self.json_type_predictor(pooled),
                }
            )
        elif structure_mode == StructuredDataMode.TABLE:
            outputs.update(
                {
                    "schema_logits": self.table_schema_generator(pooled),
                    "cell_logits": self.cell_value_generator(pooled),
                }
            )
        elif structure_mode == StructuredDataMode.SQL:
            outputs.update(
                {
                    "clause_logits": self.sql_clause_generator(pooled),
                    "table_logits": self.sql_table_generator(pooled),
                    "column_logits": self.sql_column_generator(pooled),
                }
            )
        elif structure_mode == StructuredDataMode.GRAPH:
            outputs.update(
                {
                    "node_logits": self.node_generator(pooled),
                    "edge_logits": self.edge_generator(pooled),
                    "graph_type_logits": self.graph_type_predictor(pooled),
                }
            )

        return outputs


# ═══════════════════════════════════════════════════════════════════════════
#  HIERARCHICAL STRUCTURE GENERATION (from structured_data_modalities.py)
# ═══════════════════════════════════════════════════════════════════════════


class HierarchicalStructureGeneration(nn.Module):
    """
    Hierarchical generation for complex structured data.

    Uses TransformerEncoders for schema planning and content generation,
    with level-specific generators for schema → container → field → value.
    """

    def __init__(self, hidden_size: int, nhead: int = 8) -> None:
        super().__init__()
        self.hidden_size = hidden_size

        # Schema planning
        self.schema_planner = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 512),
            nn.Softmax(dim=-1),
        )

        # Hierarchical encoders
        self.schema_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(hidden_size, nhead, batch_first=True),
            num_layers=2,
        )
        self.content_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(hidden_size, nhead, batch_first=True),
            num_layers=3,
        )

        # Level-specific generators
        self.level_generators = nn.ModuleDict(
            {
                "schema": nn.Linear(hidden_size, 50000),
                "container": nn.Linear(hidden_size, 50000),
                "field": nn.Linear(hidden_size, 50000),
                "value": nn.Linear(hidden_size, 50000),
            }
        )

    def forward(
        self, hidden_states: torch.Tensor, target_structure: Dict[str, Any]
    ) -> Dict[str, torch.Tensor]:
        schema_plan = self.schema_planner(hidden_states.mean(1))
        schema_repr = self.schema_encoder(hidden_states)
        content_repr = self.content_encoder(hidden_states)

        outputs: Dict[str, torch.Tensor] = {}
        for level, generator in self.level_generators.items():
            if level == "schema":
                outputs[f"{level}_logits"] = generator(schema_repr.mean(1))
            else:
                outputs[f"{level}_logits"] = generator(content_repr.mean(1))

        outputs["schema_plan"] = schema_plan
        return outputs


# ═══════════════════════════════════════════════════════════════════════════
#  CODE GENERATION HEAD (from code_and_structured_modality.py)
# ═══════════════════════════════════════════════════════════════════════════


class CodeGenerationHead(nn.Module):
    """
    Specialized head for code generation with language-specific processing.

    Features:
      - Language-specific preprocessing layers
      - Syntax embedding for common code patterns
      - Indentation/formatting prediction
      - Error detection head
    """

    def __init__(
        self,
        hidden_dim: int,
        vocab_size: int,
        max_length: int,
        num_layers: int,
        dropout: float,
        language: CodeLanguage,
    ) -> None:
        super().__init__()
        self.language = language
        self.max_length = max_length

        # Language-specific preprocessing
        layers: List[nn.Module] = []
        for _ in range(num_layers):
            layers.extend(
                [
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                ]
            )
        self.preprocess_layers = nn.ModuleList(layers)

        # Code syntax embedding
        self.syntax_embed = nn.Embedding(1000, hidden_dim)

        # Output projection
        self.output_projection = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, vocab_size),
        )

        # Indentation and formatting head
        self.format_head = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 4),
        )

        # Error detection head
        self.error_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs: Any,
    ) -> Dict[str, torch.Tensor]:
        """Forward pass — produces code token logits + formatting + error probs."""
        x = hidden_states
        for layer in self.preprocess_layers:
            x = layer(x)

        # Syntax conditioning
        syntax_ids = torch.zeros(
            x.shape[:2], dtype=torch.long, device=x.device
        )
        x = x + self.syntax_embed(syntax_ids)

        logits = self.output_projection(x)
        formatting_logits = self.format_head(x.mean(dim=1))
        error_probs = self.error_detector(x.mean(dim=1))

        return {
            "logits": logits,
            "formatting_logits": formatting_logits,
            "error_probs": error_probs,
            "language": self.language,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  STRUCTURED DATA HEAD (from code_and_structured_modality.py — better ver)
# ═══════════════════════════════════════════════════════════════════════════


class StructuredDataHead(nn.Module):
    """
    Specialized head for structured data generation with schema validation.

    Produces schema logits, data token logits, and validation scores
    for a given DataType target.
    """

    def __init__(
        self,
        hidden_dim: int,
        vocab_size: int,
        max_length: int,
        num_layers: int,
        dropout: float,
        data_type: DataType,
    ) -> None:
        super().__init__()
        self.data_type = data_type
        self.max_length = max_length

        # Type-specific preprocessing
        layers: List[nn.Module] = []
        for _ in range(num_layers):
            layers.extend(
                [
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                ]
            )
        self.preprocess_layers = nn.ModuleList(layers)

        # Schema prediction head
        self.schema_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 256),
            nn.Softmax(dim=-1),
        )

        # Data generation head
        self.data_projection = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, vocab_size),
        )

        # Type validation head
        self.validation_head = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs: Any,
    ) -> Dict[str, torch.Tensor]:
        """Forward pass for structured data generation."""
        x = hidden_states
        for layer in self.preprocess_layers:
            x = layer(x)

        schema_logits = self.schema_head(x.mean(dim=1))
        data_logits = self.data_projection(x)
        validation_scores = self.validation_head(x.mean(dim=1))

        return {
            "data_logits": data_logits,
            "schema_logits": schema_logits,
            "validation_scores": validation_scores,
            "data_type": self.data_type,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  METADATA EXTRACTOR (from code_and_structured_modality.py)
# ═══════════════════════════════════════════════════════════════════════════


class MetadataExtractor(nn.Module):
    """Extracts metadata and execution context from hidden states."""

    def __init__(self, hidden_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.metadata_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 128),
        )
        self.context_classifier = nn.Linear(128, 8)

    def forward(
        self, hidden_states: torch.Tensor, modality: str
    ) -> Dict[str, Any]:
        features = self.metadata_proj(hidden_states.mean(dim=1))
        context_logits = self.context_classifier(features)
        context_probs = F.softmax(context_logits, dim=-1)

        return {
            "features": features,
            "context_probs": context_probs,
            "modality": modality,
            "sequence_length": hidden_states.shape[1],
        }


# ═══════════════════════════════════════════════════════════════════════════
#  UNIFIED MODALITY OUTPUT HEAD (the router)
# ═══════════════════════════════════════════════════════════════════════════


class UnifiedModalityHead(nn.Module):
    """
    Top-level multi-modality output head.

    Routes hidden states to the appropriate generation head based on
    detected or requested output modality. Supports code generation
    (per-language), structured data (per-type), and tool synthesis.

    This is the unified entry point that tool_modality.py imports to
    bridge code/structured generation into the tool pipeline.
    """

    def __init__(
        self,
        hidden_dim: int = 512,
        num_layers: int = 2,
        dropout: float = 0.1,
        max_code_length: int = 2048,
        max_structured_length: int = 1024,
        vocab_size_code: int = 50257,
        vocab_size_structured: int = 50257,
        code_languages: Optional[List[CodeLanguage]] = None,
        data_types: Optional[List[DataType]] = None,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim

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
            nn.Softmax(dim=-1),
        )

        # Per-language code heads
        self.code_heads = nn.ModuleDict(
            {
                lang.value: CodeGenerationHead(
                    hidden_dim,
                    vocab_size_code,
                    max_code_length,
                    num_layers,
                    dropout,
                    lang,
                )
                for lang in self.code_languages
            }
        )

        # Per-type structured data heads
        self.structured_heads = nn.ModuleDict(
            {
                dtype.value: StructuredDataHead(
                    hidden_dim,
                    vocab_size_structured,
                    max_structured_length,
                    num_layers,
                    dropout,
                    dtype,
                )
                for dtype in self.data_types
            }
        )

        # Structure generator (JSON/XML/CSV/SQL/Graph)
        self.structure_generator = StructureGenerator(hidden_dim)

        # Hierarchical planner
        self.hierarchical_generator = HierarchicalStructureGeneration(
            hidden_dim, nhead=min(8, hidden_dim // 64)
        )

        # Confidence scoring
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

        # Metadata extraction
        self.metadata_extractor = MetadataExtractor(hidden_dim, dropout)

        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(
        self,
        hidden_states: torch.Tensor,
        modality_prompt: Optional[str] = None,
        language: Optional[CodeLanguage] = None,
        data_type: Optional[DataType] = None,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Route hidden states through the appropriate modality head.

        Returns a dict with modality_probs, code_outputs, structured_outputs,
        and metadata.
        """
        batch_size, seq_len, _ = hidden_states.shape

        # Modality routing
        modality_probs = self.modality_router(hidden_states.mean(dim=1))

        outputs: Dict[str, Any] = {
            "modality_probs": modality_probs,
            "code_outputs": {},
            "structured_outputs": {},
            "metadata": {},
        }

        # Code generation path
        if modality_prompt == OutputModality.CODE.value or language is not None:
            lang = language or CodeLanguage.PYTHON
            if lang.value in self.code_heads:
                code_hidden = self._prepare_code_input(
                    hidden_states, lang, attention_mask
                )
                code_output = self.code_heads[lang.value](
                    code_hidden, attention_mask=attention_mask, **kwargs
                )
                outputs["code_outputs"][lang.value] = code_output

                # Confidence
                confidence = self.confidence_head(
                    torch.cat(
                        [
                            hidden_states.mean(dim=1),
                            code_hidden.mean(dim=1),
                            code_output["logits"].mean(dim=1),
                        ],
                        dim=-1,
                    )
                )
                code_output["confidence"] = confidence

                metadata = self.metadata_extractor(
                    hidden_states, modality=OutputModality.CODE.value
                )
                outputs["metadata"][lang.value] = metadata

        # Structured data path
        if (
            modality_prompt == OutputModality.STRUCTURED_DATA.value
            or data_type is not None
        ):
            dtype = data_type or DataType.JSON
            if dtype.value in self.structured_heads:
                struct_hidden = self._prepare_structured_input(
                    hidden_states, dtype, attention_mask
                )
                struct_output = self.structured_heads[dtype.value](
                    struct_hidden, attention_mask=attention_mask, **kwargs
                )
                outputs["structured_outputs"][dtype.value] = struct_output

                confidence = self.confidence_head(
                    torch.cat(
                        [
                            hidden_states.mean(dim=1),
                            struct_hidden.mean(dim=1),
                            struct_output["data_logits"].mean(dim=1),
                        ],
                        dim=-1,
                    )
                )
                struct_output["confidence"] = confidence

                metadata = self.metadata_extractor(
                    hidden_states, modality=OutputModality.STRUCTURED_DATA.value
                )
                outputs["metadata"][dtype.value] = metadata

        return outputs

    def _prepare_code_input(
        self,
        hidden_states: torch.Tensor,
        language: CodeLanguage,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Add language embedding to hidden states for code generation."""
        batch_size, seq_len, _ = hidden_states.shape
        lang_idx = self.code_languages.index(language)
        lang_emb = self.code_lang_embedding(
            torch.full((batch_size,), lang_idx, device=hidden_states.device)
        )
        return hidden_states + lang_emb.unsqueeze(1).expand(-1, seq_len, -1)

    def _prepare_structured_input(
        self,
        hidden_states: torch.Tensor,
        data_type: DataType,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Add data type embedding to hidden states for structured generation."""
        batch_size, seq_len, _ = hidden_states.shape
        dtype_idx = self.data_types.index(data_type)
        dtype_emb = self.data_type_embedding(
            torch.full((batch_size,), dtype_idx, device=hidden_states.device)
        )
        return hidden_states + dtype_emb.unsqueeze(1).expand(-1, seq_len, -1)


__all__ = [
    "UnifiedModalityHead",
    "StructureGenerator",
    "HierarchicalStructureGeneration",
    "CodeGenerationHead",
    "StructuredDataHead",
    "MetadataExtractor",
    "StructuredDataConfig",
    "StructuredDataMode",
    "OutputModality",
    "CodeLanguage",
    "DataType",
    "CodeOutput",
    "StructuredData",
]
