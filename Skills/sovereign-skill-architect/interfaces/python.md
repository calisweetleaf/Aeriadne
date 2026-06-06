# interfaces/python.md — Python Codebase Topology Patterns

**Loaded by**: SKILL.md when domain involves Python codebase  
**Purpose**: Python-specific failure modes, integration patterns, type doctrine

---

## Python-Specific Load-Bearing Concepts

### LBC-PY-1: Module Import Side Effects

Python executes module-level code on import. A production module that does heavy initialization at import time (DB connections, model loading, network calls) will behave differently in wrapper context than in its original deployment context.

**Common misunderstanding**: "I can just import it and it'll work like before."  
**Reality**: The module may expect specific environment variables, file paths, or initialized dependencies that exist in its native context but not in yours.  
**Verification**: Read the module's `__init__` and any module-level code before wrapping. Identify every external dependency touched before the first method call.

### LBC-PY-2: Async Boundary

An async module wrapped in a sync context (or vice versa) fails in ways that are not immediately obvious. `await` inside a regular function produces a coroutine object silently — it doesn't error, it just doesn't execute.

**Common misunderstanding**: "The wrapper returned something, so it worked."  
**Reality**: The wrapper returned an unawaited coroutine. The actual module function never ran.  
**Verification**: All wrapper methods that call async module methods must themselves be `async def`. The bb7 tool layer must be capable of handling async tool functions.

### LBC-PY-3: Exception Taxonomy

Production modules define their own exception hierarchies. A wrapper that catches `Exception` is catching everything — including `KeyboardInterrupt`, `SystemExit`, and memory errors — and translating them to "structured error responses." This is wrong.

**Correct pattern**: Catch the module's specific exception types. Let unexpected exceptions propagate. A bare `except Exception` in a wrapper is a Three Strikes violation in spirit if not in letter.

```python
# WRONG — swallows everything
try:
    result = await self.module.operation()
except Exception as e:
    return {"error": str(e)}

# RIGHT — catches expected, propagates unexpected
try:
    result = await self.module.operation()
except ModuleSpecificError as e:
    return {"error": "operation_failed", "detail": e.user_message, "code": e.error_code}
except ModuleValidationError as e:
    return {"error": "invalid_input", "detail": str(e)}
# Unexpected exceptions propagate naturally
```

### LBC-PY-4: Pydantic Boundary Crossing

Many production modules use Pydantic models for internal data representation. When these cross the wrapper boundary, they should be serialized — not passed as Pydantic objects to the bb7 layer. The bb7 layer expects dicts, not Pydantic instances.

**Pattern**:
```python
def _transform_for_shell(self, result: ModuleDataModel) -> Dict[str, Any]:
    """Serialize Pydantic model to shell-compatible dict."""
    return result.model_dump(exclude_none=True, mode='json')
```

---

## Type Doctrine (from STYLE.md)

All function signatures must have complete type hints. No exceptions. No `Any` unless the type is genuinely dynamic.

```python
# WRONG
def integrate_module(self, path, config=None):
    ...

# RIGHT  
from typing import Optional, Dict, Any
from pathlib import Path

def integrate_module(
    self,
    path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    ...
```

For production module wrappers, the return type of `get_tools()` is always:
```python
def get_tools(self) -> Dict[str, Dict[str, Any]]:
```

---

## Provenance Docstring Standard

Every module and wrapper in the tree must have provenance documented:

```python
class ProductionModuleWrapper:
    """
    Wrapper exposing [Module Name] as native bb7 tools.
    
    Source: [Project name, version] ([filename])
    Integrated: [YYYY-MM-DD]
    Wrapper LOC: [count] (must be < 200)
    Integration Efficiency: [I_eff estimate, e.g., 0.92]
    Purpose: [What this wrapper exposes and why]
    
    Module capabilities exposed:
    - [tool_name]: [one line description]
    - [tool_name]: [one line description]
    
    Module capabilities NOT exposed (and why):
    - [method]: [reason — e.g., "admin-only, not needed in shell context"]
    """
```

---

## Wrapper Template (Python)

```python
"""
[Module Name] Wrapper
Source: [Project, version, file]
Integrated: [date]
Wrapper LOC: [count]
"""

from typing import Dict, Any, Optional
from pathlib import Path


class [Domain]ToolWrapper:
    """
    [Module Name] wrapper for bb7 tool layer.
    
    Source: [provenance]
    """

    def __init__(self) -> None:
        """Initialize wrapper with production module."""
        # Late import to avoid import-time side effects bleeding into caller
        from [module_path] import [ClassName]
        
        self.module = [ClassName](
            # Minimal config — only what the module requires
            # Never inject caller-context values at init time
        )

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Expose production capabilities as bb7-compatible tools."""
        return {
            '[domain]_[operation]': {
                'function': self._[operation]_wrapper,
                'description': '[One line, operator-facing description]',
                'domain': '[domain]'
            },
            # Add additional tools here
        }

    async def _[operation]_wrapper(
        self,
        [param]: [type],
        [optional_param]: Optional[[type]] = None
    ) -> Dict[str, Any]:
        """
        Thin adapter for [Module].[method]().
        
        Translates interface, formats output. No logic duplication.
        """
        try:
            result = await self.module.[method](
                [param]=[param],
                # Map wrapper params to module params explicitly
            )
            return self._transform_for_shell(result)
        except [ModuleSpecificError] as e:
            return {
                'error': '[error_category]',
                'detail': str(e),
                'remediation': '[What the operator should do]'
            }

    def _transform_for_shell(self, result: Any) -> Dict[str, Any]:
        """Serialize module output to shell-compatible dict."""
        # If result is Pydantic model:
        if hasattr(result, 'model_dump'):
            return result.model_dump(exclude_none=True, mode='json')
        # If result is a custom dataclass or object:
        return {
            '[field]': result.[attribute],
            # Map only the fields the bb7 layer needs
            # Do not pass through entire module data structures
        }
```

---

## Common Python Integration Failure Modes

### Failure: The Async Trap
```python
# WRONG — get_tools returns non-async function that calls async module
def get_tools(self):
    return {'tool': {'function': self._sync_wrapper, ...}}

def _sync_wrapper(self, **kwargs):
    return self.module.async_method(...)  # Returns coroutine, never runs
```
```python
# RIGHT — async wrapper for async module
async def _async_wrapper(self, **kwargs) -> Dict[str, Any]:
    return await self.module.async_method(...)
```

### Failure: The Config Leak
```python
# WRONG — wrapper init requires caller-context config
def __init__(self, project_root: Path, user_id: str):  
    self.module = ProductionModule(root=project_root, user=user_id)
```
```python
# RIGHT — wrapper init is self-contained
def __init__(self) -> None:
    self.module = ProductionModule(
        root=Path('./data'),  # Module's own data dir
        # No caller-context dependencies
    )
```

### Failure: The Logic Migration
```python
# WRONG — business logic in wrapper (I_eff → 0)
async def _clone_wrapper(self, repo_url: str) -> Dict[str, Any]:
    # Validating the URL ourselves — this belongs in the module
    if not repo_url.startswith('https://'):
        return {'error': 'must use https'}
    # Checking permissions ourselves — this belongs in the module
    if self._check_permissions(repo_url):
        ...
```
```python
# RIGHT — let the module handle its own invariants
async def _clone_wrapper(self, repo_url: str) -> Dict[str, Any]:
    try:
        result = await self.module.clone_repository(repo_url=repo_url, ...)
        return self._transform_for_shell(result)
    except ModuleValidationError as e:
        return {'error': 'validation_failed', 'detail': str(e)}
```

---

## LOC Counter (Run Before Marking Integration Complete)

```bash
# Count wrapper LOC (must be < 200)
wc -l [wrapper_file].py

# Count non-comment, non-blank lines (stricter measure)
grep -c "^[^#[:space:]]" [wrapper_file].py
```

If either count approaches 180 lines: stop. Audit the wrapper for logic migration. Anything that looks like it's doing work belongs in the module, not the wrapper.

---

## Production Module Acceptance Check (Python)

```bash
# Test 1: Standalone import (no project deps)
cd /tmp && python3 -c "from [module_path] import [ClassName]; m = [ClassName](); print('PASS')"

# Test 2: No modification required (read-only check)
# Review module file - any TODO, FIXME, or raise NotImplementedError? REJECT

# Test 3: Can be instantiated cleanly
python3 -c "
from [module_path] import [ClassName]
m = [ClassName]()
print(dir(m))
print('INSTANTIATION: PASS')
"
```

All three must pass before wrapping begins.
