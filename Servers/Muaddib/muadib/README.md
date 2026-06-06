# Archived Modality Files

These files were consolidated into `../unified_modality.py` on 2025-04-24.

## What was kept

### From `structured_data_modalities.py`

- `StructuredDataConfig` — generation config dataclass
- `StructuredDataMode` — format enum (JSON/XML/CSV/SQL/Graph/Table/API_CALL)
- `StructureGenerator` — format-specific generation heads with routing
- `HierarchicalStructureGeneration` — TransformerEncoder for schema planning

### From `code_and_structured_modality.py`

- `CodeGenerationHead` — language-specific code generation with syntax embeddings, error detection
- `StructuredDataHead` — schema prediction with validation (superior to the structured_data version)
- `MetadataExtractor` — metadata extraction from hidden states
- `ModalityOutputHead` → renamed to `UnifiedModalityHead` — top-level modality router

## What was killed

- `ConstitutionalStructuredSafety` — referenced but never defined (dead code)
- Fake memory retrieval stubs (torch.randn placeholders in structured_data)
- `_synthesize_code` / `_simulate_execution` — placeholder codegen stubs
- Duplicate `StructuredDataHead` from structured_data (inferior version)
- `StructuredDataOutputHead` — replaced by `UnifiedModalityHead`
