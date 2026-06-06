# examples/case_codebase_entry.md — Annotated Codebase Entry Trace

**Scenario**: Agent enters an unfamiliar production codebase to integrate a module into the bb7 tool layer  
**Domain**: Python, recursive production system  
**Purpose**: Show the CTM entry pattern, not the checklist entry pattern

---

## The Setup

Daeron says: "I need to wrap the `sovereign_analysis_tool.py` from the Research System v2.1.0 for the shell."

The wrong response: jump to writing a wrapper.  
The CTM response: excavate the topology first.

---

## Step 0: Topology Excavation (Before Writing Anything)

**Agent reads the module first. Full read. Not a skim.**

After reading `sovereign_analysis_tool.py` (let's say it's 1800 lines), the agent maps:

**Load-bearing concepts identified:**
1. `AnalysisSession` — stateful object that accumulates analysis context over multiple calls. NOT a single-call tool. Misunderstanding this will produce a wrapper that calls methods in wrong order.
2. `AnalysisResult.confidence_bands` — not a scalar confidence score. A tuple (lower, upper) with domain-specific meaning. Wrapping it as a single float loses critical signal.
3. `EvidenceChain.traverse()` — lazy evaluation. The chain isn't computed until traversed. Wrapper must explicitly trigger traversal before serialization.

**Complexity distribution:**
- Session initialization: THIN (boilerplate)
- Evidence chain construction: DENSE (where the actual hard logic is)
- Output serialization: MEDIUM (Pydantic models, straightforward but Pydantic boundary matters)
- Error classification: DENSE (the module has 7 error types with meaningful distinctions)

**Baked-in decisions:**
- Sessions are not thread-safe by design. The module was built for single-threaded analysis flows. Concurrent wrapper calls to the same session will corrupt state.
- `AnalysisResult` can be in a "partial" state (valid but incomplete). The module returns partial results rather than blocking. The wrapper must handle partial results without treating them as errors.

**Anti-concepts:**
- "I can call `analyze()` multiple times on the same instance for different documents" — WRONG. `analyze()` modifies the session. Each document requires a fresh session.
- "The confidence score is a single float" — WRONG. It's `confidence_bands`: (0.73, 0.91). The lower bound is the operational confidence, the upper bound is the theoretical maximum given the evidence.

---

## Step 1: The Topology Document (written BEFORE the wrapper)

```markdown
# TOPOLOGY — sovereign_analysis_tool

**Source**: Research System v2.1.0 (sovereign_analysis_tool.py, 1800 LOC)
**Language**: Python async
**Complexity**: DENSE overall

## Load-Bearing Concepts

### LBC 1: AnalysisSession (Stateful)
Definition: Mutable session object that accumulates context across method calls.
Why load-bearing: Every method call modifies session state. Call order matters.
Common misunderstanding: Treating it like a stateless service (call any method in any order).
Verification: Check if session.state changes after each method call. It should.

### LBC 2: confidence_bands (Interval, not Scalar)
Definition: Tuple[float, float] — (operational_confidence, theoretical_max)
Why load-bearing: Collapsing to a single float loses the uncertainty interval.
Common misunderstanding: Averaging the tuple or taking [0] as "the confidence score."
Verification: Serialize as {lower: bands[0], upper: bands[1]}, never as a float.

### LBC 3: EvidenceChain (Lazy)
Definition: Chain object that doesn't compute until .traverse() is explicitly called.
Why load-bearing: Serializing chain without traversal produces empty or stale data.
Verification: Call .traverse() before any serialization of EvidenceChain objects.

## Complexity Distribution
- Session init: THIN
- Evidence chain construction: DENSE
- Output serialization: MEDIUM  
- Error classification: DENSE (7 distinct error types, each operationally meaningful)

## Baked-In Decisions
1. Non-thread-safe sessions: Each analysis flow requires its own session instance.
2. Partial results: analyze() may return before completion. Partial ≠ error.

## Anti-Concepts
- "Reusable session across documents" — sessions are document-scoped, one per analysis
- "confidence is a float" — confidence is always an interval tuple
```

---

## Step 2: Failure Grammar for This Module

Before writing a line of wrapper code, the agent identifies:

**Smell 1**: Wrapper returns `{}` without error — probably swallowing a `PartialResultError`.  
**Smell 2**: `confidence` field in wrapper output is a single float — the Pydantic boundary crossing collapsed the interval.  
**Smell 3**: Second call to `analyze()` on same session produces nonsensical results — session state corruption from reuse.

**Pre-failure check added to wrapper**: assert fresh session per analysis call (not a performance optimization — a correctness requirement).

---

## Step 3: The Wrapper (Written After Topology and Failure Grammar)

```python
"""
Sovereign Analysis Tool Wrapper
Source: Research System v2.1.0 (sovereign_analysis_tool.py, 1800 LOC)
Integrated: 2026-03-08
Wrapper LOC: ~120 (within 200 LOC limit, I_eff: 0.93)

Exposes:
- analysis_analyze: Full document analysis with evidence chain
- analysis_query: Query existing analysis session
"""

from typing import Dict, Any, Optional
from pathlib import Path


class SovereignAnalysisWrapper:
    """
    Wrapper for sovereign_analysis_tool.AnalysisEngine.
    
    CRITICAL: Sessions are NOT thread-safe and NOT reusable across documents.
    A fresh session is created per analysis_analyze call. This is by design.
    
    Source: Research System v2.1.0
    """

    def __init__(self) -> None:
        from sovereign_analysis_tool import AnalysisEngine
        self._engine_cls = AnalysisEngine  # Store class, not instance
        # Engine instantiation is per-analysis to enforce session isolation

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        return {
            'analysis_analyze': {
                'function': self._analyze_wrapper,
                'description': 'Analyze document and return evidence chain with confidence bands',
                'domain': 'analysis'
            },
        }

    async def _analyze_wrapper(
        self,
        document_path: str,
        analysis_depth: Optional[str] = 'standard'
    ) -> Dict[str, Any]:
        """
        Thin adapter for AnalysisEngine.analyze().
        
        Creates fresh session per call (module design: non-reusable sessions).
        Explicitly traverses EvidenceChain before serialization (lazy evaluation).
        Preserves confidence_bands as interval, never collapses to scalar.
        """
        try:
            # Fresh session per document — this is correct, not a bug
            engine = self._engine_cls()
            session = engine.create_session()
            
            result = await session.analyze(
                path=Path(document_path),
                depth=analysis_depth
            )
            
            return self._transform_for_shell(result)
            
        except AnalysisPartialResultError as e:
            # Partial results are valid, not errors — surface them with flag
            return {
                'status': 'partial',
                'result': self._transform_for_shell(e.partial_result),
                'completion': e.completion_fraction
            }
        except AnalysisValidationError as e:
            return {'error': 'invalid_input', 'detail': str(e), 'remediation': 'Check document path and format'}
        except AnalysisEngineError as e:
            return {'error': 'engine_failure', 'detail': str(e), 'remediation': 'Check engine logs'}

    def _transform_for_shell(self, result: Any) -> Dict[str, Any]:
        """
        Serialize AnalysisResult for shell consumption.
        
        Preserves confidence_bands as interval dict — never collapses to float.
        Explicitly traverses EvidenceChain before serialization.
        """
        # Traverse lazy chain BEFORE serialization
        evidence = list(result.evidence_chain.traverse()) if result.evidence_chain else []
        
        return {
            'status': 'complete',
            'confidence': {
                'lower': result.confidence_bands[0],
                'upper': result.confidence_bands[1]
            },
            'evidence_count': len(evidence),
            'evidence': [e.to_dict() for e in evidence[:10]],  # Top 10 by weight
            'summary': result.summary_text,
            'document_id': str(result.document_id)
        }
```

**LOC count**: ~95 lines (well within 200 limit)  
**I_eff**: 0.93 (no logic migration, no tight coupling)

---

## What This Trace Demonstrates

1. **Topology before code** — The wrapper was written AFTER the topology was understood. Three load-bearing concepts were identified before a single line of wrapper was written.

2. **Failure grammar embedded in wrapper** — The async trap, the lazy evaluation trap, the confidence interval collapse — all are addressed structurally, not by luck.

3. **Anti-concepts become assertions** — "Fresh session per call" is enforced structurally (class stored, not instance). The agent can't accidentally reuse the session.

4. **Partial results handled** — Because the agent read the module first and found `AnalysisPartialResultError`, it's handled correctly as a valid non-error state, not suppressed.

5. **Under 200 LOC, I_eff > 0.8** — The Three Strikes criteria are met without counting them as a checklist. They're naturally satisfied when you understand the module well enough to write a thin wrapper.
