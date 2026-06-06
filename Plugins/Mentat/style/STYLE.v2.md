<div align="center">

<svg width="900" height="220" viewBox="0 0 900 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="codexGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="codexSub" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#4ecdc4;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#45b7d1;stop-opacity:1" />
    </linearGradient>
    <filter id="codexGlow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="codexSoftGlow">
      <feGaussianBlur stdDeviation="1.2" result="softBlur"/>
      <feMerge>
        <feMergeNode in="softBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="900" height="220" fill="#0d1117" rx="22"/>
  <rect x="14" y="14" width="872" height="192" fill="none" stroke="url(#codexGrad)" stroke-width="1.2" rx="18" opacity="0.55"/>
  <text x="450" y="92" font-family="monospace" font-size="44" fill="url(#codexGrad)" text-anchor="middle" filter="url(#codexGlow)" font-weight="bold">Codex Protocol v2</text>
  <text x="450" y="132" font-family="monospace" font-size="18" fill="url(#codexSub)" text-anchor="middle" filter="url(#codexSoftGlow)">SOTA++ Engineering Standard</text>
  <text x="450" y="166" font-family="monospace" font-size="11" fill="#8b949e" text-anchor="middle">Wrap or Edit, the bar does not move</text>
  <text x="450" y="186" font-family="monospace" font-size="10" fill="#6e7681" text-anchor="middle">supersedes STYLE.v1 (Codex Protocol: Recursive Production Standards)</text>
</svg>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=yellow" alt="Python 3.12+"/>
  <img src="https://img.shields.io/badge/Stdlib--First-no%20heavy%20deps-667eea?style=for-the-badge" alt="Stdlib-First"/>
  <img src="https://img.shields.io/badge/Modular-Architecture-764ba2?style=for-the-badge" alt="Modular Architecture"/>
  <img src="https://img.shields.io/badge/SOTA%2B%2B-verified-f093fb?style=for-the-badge" alt="SOTA++ verified"/>
  <img src="https://img.shields.io/badge/Mode-Edit%20or%20Wrap-4ecdc4?style=for-the-badge" alt="Edit-or-Wrap"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/-Fail%20Loud%20Still%20Continue-ff8a65?style=flat-square" alt="Fail loud still continue"/>
  <img src="https://img.shields.io/badge/-No%20Emojis-6bcf7f?style=flat-square" alt="No emojis"/>
  <img src="https://img.shields.io/badge/-No%20Version%20Pins-ffd93d?style=flat-square" alt="No version pins"/>
  <img src="https://img.shields.io/badge/-Integration%20Over%20Implementation-45b7d1?style=flat-square" alt="Integration Over Implementation"/>
</p>

</div>

---

## Prologue

I am sitting at a desk with a single lamp on. The room is dark. The terminal is dark. The cursor is blinking on a fresh markdown file and I am writing the second version of the standard that governs every line of Python that lands inside one of my projects. I am not rewriting v1. I am extending it. I am loosening exactly one constraint and tightening every other one, because that is the only honest way to evolve a standard without lying about what changed.

For nearly a year I held a single hard rule: never modify production modules. The rule was right for the season it covered. It forced me to build thin wrappers, to keep domain boundaries crisp, to treat any module I imported from another project as a read-only artifact. That rule produced clean snapshots. It also produced friction I no longer want to pay for. I am now at the stage where I am importing my own tools into my own systems, where the line between "production module" and "current project" has dissolved because both halves are mine, and where wrapping a module I wrote two months ago is sometimes more expensive than carefully editing it in place.

So v2 says this. Wrappers are still the default. Direct edits are now allowed, but only if they meet the same bar — strict typing, structured errors, provenance docstrings, integration tests with no mock surfaces, JSON plus MD plus LOG artifacts on every run, no version pins in `requirements.txt`. Edits without an edit-justification docstring are a peer-review trigger, not an auto-reject. The Three Strikes Rule is still here, but it has been retuned to flag for review instead of slamming the door. The aesthetic doctrine for documentation does not relax at all. No emojis. No ASCII art for diagrams. First-person prose. Modernized polish. The bar does not move.

---

## Table of Contents

1. [Engagement Modes — Wrap, Edit, Compose](#1-engagement-modes--wrap-edit-compose)
2. [Naming and Typing Conventions](#2-naming-and-typing-conventions)
3. [Docstrings and Provenance](#3-docstrings-and-provenance)
4. [Modular Architecture](#4-modular-architecture)
5. [Wrappers — The Preferred Default](#5-wrappers--the-preferred-default)
6. [Direct Edits — When and How](#6-direct-edits--when-and-how)
7. [SOTA++ Test Suite](#7-sota-test-suite)
8. [Aesthetic Doctrine for Documentation](#8-aesthetic-doctrine-for-documentation)
9. [Modified Three Strikes (v2)](#9-modified-three-strikes-v2)
10. [The Velocity Equation](#10-the-velocity-equation)
11. [Anti-Patterns](#11-anti-patterns)
12. [Prime Directive](#12-prime-directive)
13. [Closing](#13-closing)

---

## 1. Engagement Modes — Wrap, Edit, Compose

Every change against a Daeron-owned codebase belongs to exactly one of three engagement modes. Mode must be declared at the top of any planning artifact — a `SCOPE.md`, a PR description, a commit message preamble. If a single change crosses mode boundaries, it must be split.

The three modes are:

- **Wrap.** Author a thin adapter (`< 200` LOC) that exposes an existing production module through a new interface. The module itself is not touched. This is the preferred default for any new capability whose underlying logic already exists somewhere I have written.
- **Edit.** Modify a production module's source directly. Requires an edit-justification docstring block (see [§3.2](#32-direct-edit-provenance)) and a paired provenance entry in the snapshot manifest. Reserved for cases where wrapping is genuinely impossible or where wrapping would duplicate substantial logic.
- **Compose.** Stitch two or more existing modules together inside a new domain directory without modifying either of them. The new directory holds composition logic plus optional thin wrappers. The constituent modules remain read-only.

### 1.1. Decision Tree

I run this check in my head before I open the file:

<div align="center">

<svg width="780" height="440" viewBox="0 0 780 440" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="modeWrap" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4ecdc4;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#45b7d1;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="modeEdit" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#f093fb;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#ff8a65;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="modeCompose" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
    <filter id="modeGlow">
      <feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge>
        <feMergeNode in="b"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="780" height="440" fill="#0d1117" rx="14"/>
  <rect x="290" y="20" width="200" height="56" rx="10" fill="none" stroke="#8b949e" stroke-width="1.4"/>
  <text x="390" y="53" font-family="monospace" font-size="14" fill="#c9d1d9" text-anchor="middle">does the logic already exist?</text>
  <line x1="390" y1="76" x2="180" y2="118" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="390" y1="76" x2="600" y2="118" stroke="#8b949e" stroke-width="1.2"/>
  <text x="270" y="100" font-family="monospace" font-size="11" fill="#7eda28">yes</text>
  <text x="500" y="100" font-family="monospace" font-size="11" fill="#ff8a65">no</text>
  <rect x="60" y="120" width="240" height="56" rx="10" fill="none" stroke="#8b949e" stroke-width="1.4"/>
  <text x="180" y="153" font-family="monospace" font-size="13" fill="#c9d1d9" text-anchor="middle">can a thin adapter expose it?</text>
  <line x1="180" y1="176" x2="100" y2="220" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="180" y1="176" x2="260" y2="220" stroke="#8b949e" stroke-width="1.2"/>
  <text x="110" y="200" font-family="monospace" font-size="11" fill="#7eda28">yes</text>
  <text x="250" y="200" font-family="monospace" font-size="11" fill="#ff8a65">no</text>
  <rect x="20" y="222" width="160" height="50" rx="10" fill="url(#modeWrap)" filter="url(#modeGlow)"/>
  <text x="100" y="252" font-family="monospace" font-size="16" fill="#0d1117" text-anchor="middle" font-weight="bold">WRAP</text>
  <rect x="200" y="222" width="160" height="50" rx="10" fill="url(#modeEdit)" filter="url(#modeGlow)"/>
  <text x="280" y="252" font-family="monospace" font-size="16" fill="#0d1117" text-anchor="middle" font-weight="bold">EDIT</text>
  <rect x="480" y="120" width="240" height="56" rx="10" fill="none" stroke="#8b949e" stroke-width="1.4"/>
  <text x="600" y="153" font-family="monospace" font-size="13" fill="#c9d1d9" text-anchor="middle">stitching two domains together?</text>
  <line x1="600" y1="176" x2="520" y2="220" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="600" y1="176" x2="680" y2="220" stroke="#8b949e" stroke-width="1.2"/>
  <text x="528" y="200" font-family="monospace" font-size="11" fill="#7eda28">yes</text>
  <text x="675" y="200" font-family="monospace" font-size="11" fill="#ff8a65">no</text>
  <rect x="440" y="222" width="160" height="50" rx="10" fill="url(#modeCompose)" filter="url(#modeGlow)"/>
  <text x="520" y="252" font-family="monospace" font-size="16" fill="#0d1117" text-anchor="middle" font-weight="bold">COMPOSE</text>
  <rect x="620" y="222" width="140" height="50" rx="10" fill="none" stroke="#ff8a65" stroke-width="1.4"/>
  <text x="690" y="252" font-family="monospace" font-size="13" fill="#ff8a65" text-anchor="middle">new module</text>
  <rect x="120" y="320" width="540" height="80" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="390" y="350" font-family="monospace" font-size="12" fill="#8b949e" text-anchor="middle">Edit mode is allowed but not free. It demands an edit-justification docstring,</text>
  <text x="390" y="370" font-family="monospace" font-size="12" fill="#8b949e" text-anchor="middle">a provenance entry, and a paired snapshot manifest line. Wrappers remain the default.</text>
  <text x="390" y="390" font-family="monospace" font-size="11" fill="#6e7681" text-anchor="middle">A change that crosses mode boundaries must be split into separate commits.</text>
</svg>

</div>

### 1.2. Mode Declaration in a SCOPE File

Every project I open declares its mode at the top of `SCOPE.md`. The block looks like this:

<div class="code-block-header">
<span class="filename">SCOPE.md</span>
<span class="language">Markdown</span>
</div>

```markdown
## Engagement Mode

- mode: WRAP
- target_module: tools/native/git/git_integration_module.py
- target_module_provenance: Morpheus Chat v3.2.1
- justification: existing module fully covers the required surface
- author: daeron
- date: 2026-05-10
```

If `mode: EDIT`, the block expands with the edit-justification protocol from [§6.2](#62-edit-justification-protocol).

---

## 2. Naming and Typing Conventions

I inherit these directly from v1. They are non-negotiable and unchanged.[^v1-naming]

- **Classes** use `PascalCase`. Examples I have shipped: `ProductionModuleWrapper`, `SnapshotManager`, `SystemOrchestrator`, `StateMachine`, `DislerEnvelope`.
- **Functions and methods** use `snake_case`. Examples: `integrate_module`, `validate_snapshot`, `clone_repository`, `compute_idempotency_key`, `build_envelope`.
- **Variables** use `snake_case`. Examples: `module_path`, `execution_context`, `wrapper_instance`, `session_id`, `event_class`.
- **Constants** use `UPPER_SNAKE_CASE`. Examples: `MAX_RECURSION_DEPTH`, `DEFAULT_SNAPSHOT_DIR`, `PLUGIN_ROOT`.
- **Private members** prefix with a single underscore. Examples: `_load_internal_state`, `_transform_output`, `_summarize`.
- **Modules** use `snake_case`. Examples: `git_integration_module.py`, `system_core.py`, `webhook_engine/envelope.py`.

### 2.1. Strict Type Hinting

Every function and method signature carries type hints. I import from `typing` and from `collections.abc` where the modern type aliases live. `Callable`, `Union`, `Optional`, `List`, `Dict`, `Tuple`, `Iterable`, `Mapping`, `Sequence` — whatever describes the signature precisely. I prefer concrete types over `Any`. `Any` is permitted only when the type is genuinely dynamic and cannot be narrowed.

When a function returns a structured payload, I use a `dataclass` (or a `TypedDict`) rather than a bare `dict`. The webhook engine `DislerEnvelope` dataclass is the exemplar — it carries six fields with explicit types, a `to_json` method, and field-level provenance comments.

### 2.2. Module Imports

I order imports as `stdlib`, then `third-party`, then local relative. Each group separated by a blank line. `from __future__ import annotations` lives at the very top of every module that uses type hints internally (which is every module). The webhook engine `__init__.py` opens with that exact line.

---

## 3. Docstrings and Provenance

Documentation is part of the binary. A module that ships without a docstring fails the snapshot check at startup.

### 3.1. Every Module, Class, Public Method

Every module begins with a module-level docstring that names the purpose in the first sentence. Every class has a class-level docstring that includes origin (wrapper, native, or composition). Every public method has a docstring with `Args` and `Returns` blocks when the signature is non-trivial.

The wrapper docstring template, inherited from v1:[^v1-docstrings]

<div class="code-block-header">
<span class="filename">git_wrapper.py</span>
<span class="language">Python</span>
</div>

```python
class GitToolWrapper:
    """
    Wrapper exposing git module as native shell tools.

    Source: Morpheus Chat App v3.2.1 (git_integration_module.py)
    Integrated: 2026-02-10
    Purpose: Adapts the production git manager for the current shell environment.
    """

    def __init__(self):
        """Initializes the wrapper and loads the underlying production module."""

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Exposes production methods as standardized shell tools.

        Returns:
            Dict mapping tool names to their function definitions and metadata.
        """
```

### 3.2. Direct-Edit Provenance

When a module is edited in place (mode: EDIT), the module docstring is extended with a `Modified` block. The block carries date, justification, and a back-link to the snapshot manifest entry. Every edit is dated and every edit names the engineer.

<div class="code-block-header">
<span class="filename">git_integration_module.py</span>
<span class="language">Python</span>
</div>

```python
"""
Git integration module — production-proven git toolset.

Source: Morpheus Chat App v3.2.1
Integrated: 2026-02-10

Modified: 2026-05-10
Modified by: daeron
Justification: added structured timeout error returns to align with v0.2 webhook
    engine's DLQ schema. Wrapping in a translator would have duplicated the
    seven exception classes already defined here. In-place edit preserves
    single-source-of-truth for git error taxonomy.
Provenance: see snapshots/v0.3/manifest.json -> domains.git.edits[0]
"""
```

The block is mandatory. A module that lives under `tools/native/<domain>/` and shows a `git log` history of edits without a matching `Modified:` block fails the SOTA++ check.

### 3.3. Provenance in Snapshots

The snapshot manifest schema (v1 §2.1) is extended in v2 to carry per-domain edit history. The minimum shape:

```json
{
  "snapshot_version": "2.0.0",
  "timestamp": "2026-05-10T20:00:00Z",
  "domains": {
    "git": {
      "module": "git_integration_module.py",
      "wrapper": "git_wrapper.py",
      "tool_count": 15,
      "provenance": "Morpheus Chat v3.2.1",
      "edits": [
        {
          "date": "2026-05-10",
          "author": "daeron",
          "summary": "added structured timeout error returns",
          "files": ["git_integration_module.py"],
          "justification_ref": "docstring:Modified"
        }
      ]
    }
  },
  "total_capabilities": 130,
  "system_hash": "sha256:..."
}
```

A wrapper-only change leaves `edits` empty. A direct edit adds an entry. The manifest is the ground truth — if the docstring and the manifest disagree, the snapshot is rejected.

---

## 4. Modular Architecture

The directory hierarchy from v1 carries over verbatim. The File Tree IS the Executable Codebase — that doctrine stands.[^v1-hierarchy]

```text
project_root/
├── tools/
│   ├── core/                       # Core Orchestration (Immutable Kernel)
│   │   └── ...
│   └── native/                     # Integrated Domains
│       ├── [domain_name]/          # e.g. 'git', 'web', 'analysis'
│       │   ├── [production_module].py
│       │   └── [wrapper_name].py
├── snapshots/                      # Frozen System States
│   └── v[Major].[Minor]/
│       ├── manifest.json           # Cryptographic state verification
│       └── ...
├── docs/
├── visuals/                        # .png and .svg graphs
├── test/                           # Direct Python tests, not pytest
├── .gitignore
├── README.md
├── requirements.txt                # No version pins. Just names.
└── SNAPSHOT.md                     # Human-readable state doc
```

### 4.1. Domain-Scoped Modularity

Tools are organized by domain. The Mentat plugin shows this in action — `plugin/state_machine/` holds the FSA, Q-table, drift detection, insight bus, and SQLite session persistence in one folder, and `plugin/webhook_engine/` holds the envelope, signing, retries, and DLQ in another. No flat structures. Wrappers and modules coexist inside the same domain directory.

### 4.2. Lazy Loading

A domain module loads on demand. The kernel registers domain factories at startup and instantiates them only when a tool inside that domain is first invoked. Memory budget for the idle kernel is the kernel's startup imports plus the registry — nothing else. The Mentat plugin's `__init__.py` files demonstrate the `__all__` discipline that keeps lazy imports honest.

### 4.3. No Version Pins in requirements.txt

This is one of Daeron's hard rules and v2 does not relax it. `requirements.txt` carries package names only, no version specifiers. Not `numpy>=1.8`. Not `numpy==1.26`. Just `numpy`. The justification: my systems are not built for speed, they are built for survivability across Python versions. Pins lock me into broken combinations. Names let pip resolve the latest compatible set.

```text
numpy
scikit-learn
torch
torchvision
torchaudio
```

The install line, written as a single command:

```bash
pip install numpy scikit-learn torch torchvision torchaudio
```

---

## 5. Wrappers — The Preferred Default

Wrappers remain the first choice. They are cheap to write, cheap to review, cheap to revert, and they preserve the read-only contract of the underlying module. I default to wrapping for one reason: it preserves my optionality. A wrapper can be deleted without touching the substrate.

### 5.1. The Thin-Wrapper Test

A wrapper passes if and only if:

1. **Under 200 LOC.** The wrapper translates interfaces, formats outputs, handles errors. It does not duplicate logic.
2. **Stateless or near-stateless.** A wrapper may cache a single underlying module instance. It does not carry domain state.
3. **No business logic.** Validation, transformation rules, retries, idempotency keys — these live in the underlying module. The wrapper transports.
4. **Exposes `get_tools()`.** Every wrapper exposes a `get_tools() -> Dict[str, Dict[str, Any]]` method whose return value maps tool names to function definitions and metadata. This is the contract the kernel reads.

### 5.2. The `get_tools()` Pattern

The pattern from v1 §1.3 stands. The wrapper exposes the underlying module's surface through a single `get_tools` entry point so the kernel can register tools uniformly:

<div class="code-block-header">
<span class="filename">git_wrapper.py</span>
<span class="language">Python</span>
</div>

```python
from typing import Any, Dict
from tools.native.git import git_integration_module as gim


class GitToolWrapper:
    """
    Wrapper exposing git module as native shell tools.

    Source: Morpheus Chat App v3.2.1 (git_integration_module.py)
    Integrated: 2026-02-10
    """

    def __init__(self) -> None:
        self._mgr = gim.GitManager()

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Returns the wrapper's tool surface as a kernel-loadable mapping."""
        return {
            "git_status": {
                "fn": self._mgr.status,
                "args": {"path": "str"},
                "returns": "dict",
                "description": "Return working-tree status for a repo path.",
            },
            "git_log": {
                "fn": self._mgr.log,
                "args": {"path": "str", "limit": "int"},
                "returns": "list[dict]",
                "description": "Return last N commits as dict rows.",
            },
        }
```

The wrapper above is approximately 30 LOC. That is the target.

### 5.3. Wrapper Anti-Patterns

The wrapper exists to translate. It does not exist to think. The following patterns indicate the wrapper is doing too much:

- Reaching into `module._private_attr`. Private members of the module are off-limits. If the wrapper needs that field, the module's public surface is incomplete and the module needs a feature, not the wrapper.
- Importing from inside a method body to dodge a circular import. Imports live at the top of the file. A circular import is a design problem and must be solved at the module boundary, not papered over.
- Catching `Exception` broadly and returning `{"error": str(e)}`. The wrapper catches module-specific exceptions and translates them into user-readable shell responses with a suggested remediation. Bare `Exception` is a SOTA++ failure.
- Adding retries, rate limiting, or memoization. Those live in the module. The wrapper transports.

---

## 6. Direct Edits — When and How

v1 banned this. v2 allows it on condition. The condition is provenance plus discipline.

### 6.1. When to Edit Instead of Wrap

I open the source file directly when at least one of these is true:

1. **Wrapping would duplicate substantial logic.** If the wrapper has to recreate validation, retries, or schema translation that already exists in the module, it stops being a wrapper and starts being a fork. Better to extend the module in place with provenance.
2. **The interface change is structural.** A method needs a new keyword argument that propagates through three call sites inside the module. A wrapper cannot inject that — only the module can.
3. **A new domain needs to be added next to an existing one.** Adding a new state class to a `StateMachine` is an edit, not a wrap. Adding a new event type to an `Event` enum is an edit, not a wrap.
4. **The module has a defect that affects every caller.** A typo, a wrong default, a missing `None` guard. Wrapping around a bug is a code smell. Fix the bug, annotate the fix.

### 6.2. Edit-Justification Protocol

Every direct edit requires the `Modified` block in the module docstring (see [§3.2](#32-direct-edit-provenance)). The block must include all five fields:

- `Modified:` ISO date of the edit, in `YYYY-MM-DD` form.
- `Modified by:` the engineer's handle. For my own edits, `daeron`. For an AI agent edit, the agent's name plus the operator's handle in parentheses.
- `Justification:` one paragraph in the first person. Why the edit, not what the edit. The diff explains what.
- `Provenance:` pointer to the snapshot manifest entry that records this edit.
- `Files:` the relative paths touched, if more than one file participated in the edit.

A second edit to the same module appends a new block, it does not overwrite the first. The docstring is the audit log. Every block stays.

### 6.3. Surgical-Edit Checklist

Before I save the file:

- [ ] The edit is scoped to the smallest possible region. No drive-by refactors. No "while I'm here, let me also..."
- [ ] All new code carries types. Existing code in the file that touched the edit region is not retroactively type-hinted unless that was the explicit purpose.
- [ ] All new error paths return structured error objects, never raw exceptions to the caller.
- [ ] The `Modified` docstring block is present and complete.
- [ ] The snapshot manifest entry is updated to match.
- [ ] The test suite under `test/` exercises the new path with real integration, not mocks.
- [ ] The change is captured in a single commit with a message that starts with `edit(<domain>):` and references the snapshot version that will hold it.

### 6.4. The Edit-vs-Rewrite Ladder

There are four rungs and they ascend in cost. I climb only when the rung below cannot carry the change.

1. **Wrap.** Cheapest. Default. Adds a thin adapter, no source modification.
2. **Surgical edit.** Modifies a single function or class inside the module. Adds the `Modified` block. Touches one file.
3. **Module refactor.** Restructures the internal layout of a module without changing its public surface. The module's `__all__` stays the same. Touches one file. Requires a `Modified` block plus a manifest entry that flags `internal_only: true`.
4. **Module rewrite.** A new implementation that replaces the existing one. New file, new docstring, new provenance. The old file is moved to `snapshots/v<prev>/` and the manifest records the transition. Reserved for cases where surgery would leave more scar tissue than starting fresh.

---

## 7. SOTA++ Test Suite

Whether the change is a wrap, an edit, or a compose, the resulting module must satisfy the same bar. The SOTA++ test suite is a single checklist that every module passes regardless of mode.

### 7.1. Typing

- All function and method signatures carry type hints from `typing` or `collections.abc`.
- `Any` is permitted only where the type is genuinely dynamic.
- Return types for public methods are explicit, never inferred.
- Structured payloads use `dataclass` or `TypedDict`, never bare `dict`.

### 7.2. Error Returns

- Public methods that can fail return a structured result object (`dataclass` or `TypedDict` with a discriminated `status` field) or raise a domain-specific exception. They do not raise bare `Exception`.
- Wrappers translate domain exceptions into user-readable shell responses with a suggested remediation action. A raw stack trace at the user surface is a SOTA++ failure.[^v1-errors]
- The error doctrine is **fail loud, still continue**. The system logs the failure with full context but does not exit unless the failure is truly unrecoverable. The integration smoke pattern under `plugin/scripts/integration_smoke.py` demonstrates this — it captures stderr and a non-zero exit, prints the failure, and continues running the remaining subsystem checks.

### 7.3. Explicit IO

- Modules declare their IO surface in the docstring. Reads, writes, network calls, environment variables.
- Pure functions where possible. Side effects pushed to the edges.
- File paths are absolute when crossing a process boundary. Relative paths only inside a known cwd contract.

### 7.4. Integration Tests Over Mock-Driven Unit Tests

I do not mock the substrate. Tests under `test/` exercise the real module against real fixtures. If the module hits a network, the test hits a local test double that runs the same protocol. If the module hits SQLite, the test hits a temp `.sqlite` file. The Mentat plugin demonstrates this — `webhook_engine/test_smoke.py` runs the real envelope, the real signing, the real HMAC, against a localhost echo server.

The justification, in my voice: I do not trust mocks. A mocked test passes when the mock is wrong. An integration test fails when the substrate moves. I want my tests to fail when the substrate moves.

### 7.5. Test Output: JSON + MD + LOG

Every test run writes three artifacts to a timestamped subfolder under `test/<module>/runs/<timestamp>/`:

- `result.json` — structured result payload, machine-readable.
- `result.md` — first-person narrative summary of what ran and what it produced.
- `result.log` — full stdout plus stderr captured from the run.

The `.md` is not optional. The test is also documentation. The `.md` reads as if I wrote it after the test finished. It says what the test ran, what it found, what was surprising.

### 7.6. No Premature Optimization

- The first cut is correct and readable. The second cut, if there is one, is fast.
- Profiling output is captured in `visuals/` only when an optimization is shipping with the change.
- The default loop is sequential. Concurrency is added only when a specific test demonstrates the need.

### 7.7. No Version Pins in requirements.txt

Restated for emphasis. Names only.

### 7.8. Stdlib-First

I prefer the standard library. The Mentat webhook engine is stdlib-only — `json`, `time`, `hmac`, `hashlib`, `urllib`, `sqlite3`. A new dependency must justify its weight against the cost of carrying it across Python versions.

---

## 8. Aesthetic Doctrine for Documentation

The aesthetic doctrine does not relax in v2. The rules are absolute and they hold for every document that ships next to the code.

### 8.1. The Hard Rules

- **No emojis.** Anywhere. The snippet library is explicit: "Emojis are forbidden." That holds.[^snip-emoji]
- **No ASCII art for diagrams.** Replace ASCII trees, box-drawn architecture diagrams, and pipe-character flowcharts with inline SVG. The SVG carries a gradient and a `feGaussianBlur` glow filter. The snippet library is the reference.
- **First-person narrative.** "I treat", "I learned", "I require". Not "the user", not "developers should". The reader is behind my eyes at the desk with the lamp on.
- **Modernized polish.** Gradient SVG headers, terminal chrome with traffic-light dots, code-block headers with filename and language tabs, `details/summary` collapsibles, shields.io badges, footnotes for citations.

### 8.2. Canonical Patterns

Each of these patterns is pulled from the rolling markdown snippet library and reproduced here verbatim. Use them as drop-in components.

#### 8.2.1. Gradient SVG Header with feGaussianBlur Glow

The header sits at the top of every README, every doc, every standalone artifact. It carries the gradient definition, the glow filter, and the title in monospace.

<div class="code-block-header">
<span class="filename">header.html</span>
<span class="language">HTML</span>
</div>

```html
<svg width="400" height="200" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="400" height="200" fill="#0d1117" rx="20"/>
  <text x="200" y="100" font-family="monospace" font-size="48" fill="url(#logoGrad)" text-anchor="middle" filter="url(#glow)" font-weight="bold">Eclogue Ø</text>
  <text x="200" y="140" font-family="monospace" font-size="12" fill="#8b949e" text-anchor="middle">Dense Cognitive Architecture · 3.5T Active · 4M Context</text>
</svg>
```

#### 8.2.2. Terminal Simulation Block with Traffic-Light Chrome

The terminal block shows a command, a progress fill, and a result list. The chrome carries three dots (red, yellow, green) and a title bar. This is how I render an executable run inside a markdown doc.

<div class="code-block-header">
<span class="filename">terminal.html</span>
<span class="language">HTML</span>
</div>

```html
<div class="terminal">
  <div class="terminal-header">
    <span class="terminal-button red"></span>
    <span class="terminal-button yellow"></span>
    <span class="terminal-button green"></span>
    <span class="terminal-title">sovereign-terminal</span>
  </div>
  <div class="terminal-body">
    <div class="command"><span class="prompt">user@sovereign:~$</span> ./benchmark.sh --model=ngsst --dataset=multimodal</div>
    <div class="output">Initializing benchmark suite v3.2.1</div>
    <div class="output">Loading NGSST model (3.5T parameters)...</div>
    <div class="output">Loading MultiModal evaluation dataset (2,458 samples)...</div>
    <div class="output progress-line">
      <span class="progress-text">Running: </span>
      <span class="progress-bar"><span class="progress-fill"></span></span>
      <span class="progress-percent">100%</span>
    </div>
    <div class="output">Results:</div>
    <div class="output result">● Visual Reasoning: 97.8%</div>
    <div class="output result">● Temporal Coherence: 94.2%</div>
    <div class="output result">● Causal Inference: 92.5%</div>
    <div class="output result">● Multi-step Planning: 89.7%</div>
    <div class="command"><span class="prompt">user@sovereign:~$</span> <span class="cursor">_</span></div>
  </div>
</div>
```

The stylesheet is reproduced in the snippet library; I do not duplicate it here. The CSS uses `#1e1e1e` for the body, `#323232` for the header, `#ff5f56` red, `#ffbd2e` yellow, `#27c93f` green.

#### 8.2.3. Code Block Header with Filename and Language Tabs

Every code fence carries a header above it. The header gives the filename in bold and the language tag in a blue accent. This anchors the reader.

<div class="code-block-header">
<span class="filename">code_header.html</span>
<span class="language">HTML</span>
</div>

```html
<div class="code-block-header">
  <span class="filename">quantum_circuit.py</span>
  <span class="language">Python</span>
</div>
```

The matching stylesheet:

<div class="code-block-header">
<span class="filename">code_header.css</span>
<span class="language">CSS</span>
</div>

```css
.code-block-header {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 8px 16px;
  font-family: monospace;
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
}
.filename { font-weight: bold; }
.language { color: #569cd6; }
```

#### 8.2.4. Collapsible Details Block

Long architecture diagrams and side-channel logs go inside a `details` element so the page does not become a wall of content. The `summary` carries the click target.

<div class="code-block-header">
<span class="filename">collapsible.html</span>
<span class="language">HTML</span>
</div>

```html
<details>
  <summary><strong>SYSTEM ARCHITECTURE DIAGRAM</strong> (click to expand)</summary>
  <!-- inline SVG goes here -->
</details>
```

A second pattern from the snippet library shows an internal log readout in a collapsible, which I use for verbose run output that should not dominate the page:

<div class="code-block-header">
<span class="filename">internal_log.html</span>
<span class="language">HTML</span>
</div>

```html
<details>
  <summary><i>Internal Log: Observation on Entropy-Driven Routing</i></summary>
  <code>[LOG 04:22] HSGM Achieved Conversion of 12 tokens into 1 summary node...</code>
</details>
```

### 8.3. Shields and Badges

A doc opens with a row of shields.io badges that summarize the artifact at a glance. The columns I always include: language version, license, status, and one or two domain-specific facts. I use the `for-the-badge` style for the headline row and `flat-square` for the secondary row. The colors map to my gradient palette — `#667eea`, `#764ba2`, `#f093fb`, `#4ecdc4`, `#45b7d1`, `#ff8a65`, `#ffd93d`, `#6bcf7f`.

### 8.4. Footnotes for Citations

Every claim that traces to v1 or to the snippet library gets a footnote. The footnote points to the specific section. The reader can audit the lineage.

---

## 9. Modified Three Strikes (v2)

v1's Three Strikes Rule auto-rejected. v2's is a review trigger. The bones are the same, the consequence is softer, and the rationale is that direct edits are now allowed when justified — so a strike is no longer a kill signal, it is a peer-review signal.

### 9.1. The Three Strikes (v2)

- **Strike 1 (v2): Direct edit without an edit-justification docstring.**
  Trigger: a `git diff` shows a modification under `tools/native/<domain>/` but the module docstring carries no matching `Modified` block.
  Consequence: peer review. The reviewer either approves the edit and asks for the docstring to be added, or asks for the edit to be re-implemented as a wrapper.
- **Strike 2 (v2): Wrapper exceeds 200 LOC AND does not pull in a new domain.**
  Trigger: a wrapper grows past the LOC ceiling without integrating a new external module that justifies the bulk.
  Consequence: peer review. The reviewer asks whether the wrapper is doing real work (translating a new domain) or whether it has accreted logic that belongs in the underlying module.
- **Strike 3 (v2): Tests rely on mocks instead of real integration.**
  Trigger: the test suite for the module imports `unittest.mock`, `pytest-mock`, or stubs the underlying module's surface.
  Consequence: peer review. The reviewer asks for the mock to be replaced with a real test double — a local SQLite file, a localhost echo server, an in-memory queue.

None of the strikes auto-reject. All three open a review-then-discuss loop.[^v1-strikes]

### 9.2. What Did Not Change

The strike triggers themselves are nearly identical to v1. What changed is the consequence and the framing. v1's strikes shut the door. v2's strikes open a conversation. The bar is the same; the failure mode is different.

---

## 10. The Velocity Equation

The V-Equation from v1 §3.4 carries over without algebraic change.[^v1-velocity]

$$ V(t) = V(t-1) + \sum_{i=1}^{n} (C_i \times I_{eff}) $$

Where:

- $V(t)$: System velocity at cycle $t$, measured in capabilities per cycle.
- $V(t-1)$: Previous snapshot velocity, the baseline carried forward.
- $C_i$: Capability count of integrated module $i$. A module that exposes 12 tools contributes $C_i = 12$.
- $I_{eff}$: Integration efficiency, a coefficient in $[0.0, 1.0]$ driven by wrapper thinness.

The operational directive holds: maximize $I_{eff}$ by keeping wrappers minimal. v1 said an integration with $I_{eff} < 0.8$ was rejected. v2 keeps the same numeric threshold but treats $I_{eff} < 0.8$ as a review trigger rather than an auto-reject. The strike model in §9 governs the consequence.

### 10.1. Edit-Velocity Footnote

v2 extends the V-Equation accounting to include edit-velocity, not just wrap-velocity.[^v2-edit-velocity] A direct edit that adds a new capability counts toward $V(t)$ at the same weight as a wrapper-driven integration, provided the edit carries a valid `Modified` block and a matching manifest entry. The arithmetic does not change; the accounting does.

I treat edit-velocity as a first-class citizen because the alternative — pretending that only wrapped integrations count — would penalize honest in-place evolution. v2 measures motion, not method.

---

## 11. Anti-Patterns

The v1 anti-pattern list carries forward with one substitution. v1 said "modifying production modules" was a never-do. v2 replaces that with a narrower prohibition: modifying production modules without a provenance trail or justification.

The list:

- **Modifying production modules without a provenance trail or justification.** An edit without a `Modified` block is forbidden. An edit without a manifest entry is forbidden. An edit with both is permitted under §6.
- **Duplicating logic.** Do not reimplement validation, retries, or transformation rules in the wrapper. Trust the module.
- **Tight coupling.** Do not access private `_attributes` of the module from the wrapper. Private members are private.
- **Half-finished integrations.** Do not commit wrappers with `TODO: implement later`. The wrapper is either complete or it does not ship.
- **Mocking the substrate.** Do not stub the underlying module in tests. Use real test doubles or real fixtures.
- **Version-pinning in requirements.txt.** Names only.
- **Catching `Exception` broadly.** Catch domain-specific exception classes. If a class does not exist, define it in the module and import it.
- **Premature optimization.** Profile after correctness, not before.
- **Emojis in documentation.** Forbidden across all surfaces.[^snip-emoji]
- **ASCII art for diagrams.** Use inline SVG. The library carries the canonical patterns.

The v1 list (§5.2) appears in the footnote for reference.[^v1-antipatterns]

---

## 12. Prime Directive

The Prime Directive from v1 §6 carries over without change.[^v1-prime]

The Recursive Production System is not just code. It is a Computational Substrate. The four obligations:

1. **Self-Preservation.** The system verifies its own integrity at startup via `manifest.json`. A corrupt manifest is a startup failure, not a warning.
2. **Recursive Evolution.** The system is capable of generating the scaffolding for its next iteration. The plugin's CHANGELOG plus snapshot manifest plus this style document are the artifacts that make the next cycle possible.
3. **Non-Interference.** Tools do not hardcode constraints that artificially limit the system's future growth or cognitive horizon.
4. **Traceability.** Every autonomous action leaves a cryptographic or logging trace. Ghost actions are forbidden.

A v2 edit does not weaken any of the four. The `Modified` block is part of the traceability obligation. The manifest entry is part of self-preservation. The justification paragraph is part of recursive evolution — it tells the next iteration why the substrate looks the way it does.

---

## 13. Closing

I am back at the desk. The lamp is still on. The terminal is still dark. I have just written down what v2 means and what it does not mean, and I want to be precise about the shape of the bar I am setting.

v2 lowers exactly one wall: I can now edit a production module in place, provided I leave a paper trail. It raises every other wall. The aesthetic doctrine does not relax. The test suite does not relax. The provenance requirement gets stricter, not looser, because every edit creates a new piece of audit surface that has to stay coherent with the snapshot manifest. The Three Strikes Rule does not disappear — it becomes a peer-review trigger so the system can have a conversation instead of slamming a door.

What this means for the dev tools coming in from outside my own corpus: the bar is set by this document. A tool that wants to land in my tree as a wrapper passes the wrapper test. A tool that wants to land as an edit passes the edit test plus the provenance test plus the manifest test plus the SOTA++ test suite. A tool that does not pass either path is not shipped. I am ready to bring those tools in. I am not ready to lower the bar.

I will revisit this document in roughly six months, when the next snapshot generation is in motion. If v3 is needed, I will write it the same way — name what changed, name what did not, leave the reader behind my eyes at the desk.

---

[^v1-naming]: See v1 §1.1 *Naming Conventions* and §1.2 *Typing*. Verbatim inheritance, no modifications. Path: [STYLE.v1.md](./STYLE.v1.md).
[^v1-docstrings]: See v1 §1.3 *Docstrings & Provenance*. v2 extends this with the `Modified` block; the original template stands. Path: [STYLE.v1.md](./STYLE.v1.md).
[^v1-hierarchy]: See v1 §1.5 *Mandatory Directory Hierarchy*. Path: [STYLE.v1.md](./STYLE.v1.md).
[^v1-errors]: See v1 §3.5 *Error Handling Doctrine: Fail Fast, Recover Clean*. v2 keeps the wrapper translation contract and adds the fail-loud-still-continue rule for orchestrators. Path: [STYLE.v1.md](./STYLE.v1.md).
[^v1-strikes]: See v1 §4.2 *Integration Checklist & The Three Strikes Rule*. v2 keeps the triggers, softens the consequence to peer review. Path: [STYLE.v1.md](./STYLE.v1.md).
[^v1-velocity]: See v1 §3.4 *Velocity via Compounding (The V-Equation)*. Algebra unchanged in v2; accounting extended. Path: [STYLE.v1.md](./STYLE.v1.md).
[^v2-edit-velocity]: v2 addition. The V-Equation accounts for edit-velocity at the same weight as wrap-velocity provided the edit passes the provenance test.
[^v1-antipatterns]: See v1 §5.2 *Anti-Patterns*. v2 replaces the "modifying production modules" line with "modifying production modules without provenance trail or justification". The other four lines pass through unchanged. Path: [STYLE.v1.md](./STYLE.v1.md).
[^v1-prime]: See v1 §6 *Prime Directive: System Autonomy & Integrity*. Verbatim inheritance, no modifications. Path: [STYLE.v1.md](./STYLE.v1.md).
[^snip-emoji]: See `README_MdFormat_Rolling_Snippet_Library.md`: "Emojis are forbidden, artistic freedom is encouraged, and user become more invested in what they enage with." The rule is absolute across all my documentation surfaces.
