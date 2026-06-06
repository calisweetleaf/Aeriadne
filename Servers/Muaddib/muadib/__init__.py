"""
Muad'Dib — Neural-Symbolic Substrate Package.

The learned neural substrate for the Sovereign MCP tool server.
Lisan al-Gaib (tools/lisan_al_gaib.py) is the runtime; Muad'Dib is the
substrate that learns, adapts, and persists neural state.

Core components:
  - DigitalTwinTool: bb7_ surface (server-registered)
  - NeuralSubstrateTokenizer: Full neural pipeline (when backbone available)
  - ToolSubstrateTokenizer: Phase 1 fallback (single-head attention stub)
  - NeuralMemoryNetwork: Persistent external memory with R/W heads
  - KnowledgeGraphAttention: KG-enhanced GQA + RoPE attention
  - ContinualLearningModule: EWC anti-forgetting with task embeddings
"""

from __future__ import annotations

# Core twin tool (always available — backbone is pure Python)
from .muaddib import (
    DigitalTwinTool,
    DigitalTwinBackbone,
    SubstrateConfig,
)

# Neural config (always importable — requires torch but defines the dataclass)
try:
    from .neural_config import (
        NeuralNetConfig,
        SelfPlayConfig,
        MuadDibSelfPlayHead,
        AeronRMSNorm,
        AeronRotaryEmbedding,
        apply_rotary_pos_emb,
    )
except ImportError:
    pass  # torch not available

# Full neural backbone (requires torch + neural_config)
try:
    from .aeron_neural_memory import (
        MultiHeadAttention,
        KnowledgeGraphAttention,
        FeedForwardNetwork,
        TransformerEncoderLayer,
        TransformerDecoderLayer,
        NeuralMemoryNetwork,
        ContinualLearningModule,
        UncertaintyQuantification,
        ActiveLearningManager,
    )
except (ImportError, NameError):
    pass  # torch or neural_config not available

# Tool modality (requires torch + may have unresolved deps)
try:
    from .tool_modality import (
        GraphNeuralNetwork,
        ToolSynthesisEngine,
    )
except (ImportError, NameError):
    pass  # MemorySystem or other deps not available

# Unified modality (requires torch)
try:
    from .unified_modality import (
        UnifiedModalityHead,
        StructureGenerator,
        CodeGenerationHead,
        StructuredDataHead,
        MetadataExtractor,
    )
except ImportError:
    pass
