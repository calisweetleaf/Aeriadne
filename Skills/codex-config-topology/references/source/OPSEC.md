# OPSEC.md - Operational Security & Development Methodology

## Recursive Production System Composition

**Developer:** Christian Trey Levi Rowell
**Philosophy:** File Tree = Executable Codebase  
**Approach:** Snapshot → Fork → Integrate → Evolve → Snapshot (Recursive)  

---

## Core Principle: No Half-Finished Code

Every file in the tree runs as-is. No prototypes, no TODOs, no commented experiments. If it's in the codebase, it's production-proven.

**Enforcement Mechanism:**

- File tree IS the codebase
- Git commits are complete working snapshots
- Integration only accepts battle-tested modules
- Wrappers are thin adapters, never rewrites

---

## The Recursive Development Pattern

### Phase 1: Snapshot (Stable System)

Capture current state as production baseline:

```md
shell-v1/
├── bb7
│   ├── __init__.py
│   ├── auto_tool_module.py
│   ├── enhanced_code_analysis_tool.py
│   ├── exoskeleton_tool.py
│   ├── file_tool.py
│   ├── memory_interconnect.py
│   ├── memory_tool.py
│   ├── project_context_tool.py
│   ├── session_manager_tool.py
│   ├── shell_tool.py
│   ├── visual_tool.py
│   ├── vscode_terminal_tool.py
│   └── web_tool.py
└── native
    ├── git_integration_module.py
    ├── sovereign_analysis_tool.py
    └── web_search_prod.py
# Capabilities: 20 core tools
# Status: Production stable
# Ready for: Fork and expansion
```

**Snapshot Criteria:**

- All files execute without errors
- Core functionality validated through actual usage
- No dependencies on external non-production code
- Documentation matches implementation
- Tests pass (if tests exist)

Files for Direct/Native Integration Not Tool's

```md
├── artifacts
│   ├── accelerated_file_processing.py
│   ├── artifact_config.py
│   ├── artifact_container_runtime.py
│   ├── artifact_system_extension.py
│   ├── artifact_system_fastapi.py
│   ├── base_layer.py
│   ├── collaborative_artifact_core.py
│   └── file_upload_system.py
├── schemas
│   ├── Dockerfile.artifacts
│   ├── Dockerfile.jupyter
│   ├── Dockerfile.kernel
│   ├── __init__.py
│   ├── base_config.yaml
│   ├── dev_session_schemas.py
│   ├── dockerfile_base.txt
│   ├── model_schemas.py
│   ├── session.py
│   └── session_manager.py
├── memory_core.py
├── memory_integration.py
├── modifying_prompts.py
└── system_cache.py
```

### Phase 2: Fork (Clean Development Environment)

Create fresh directory for expansion:

```bash
# Copy entire working system
cp -r shell-v1/ shell-development/

# Result: Isolated environment with full capabilities
# No risk to production baseline
# Freedom to experiment with integration
```

**Fork Benefits:**

- Production system remains untouched
- Can validate integration before committing to snapshot
- Multiple forks can explore different integration strategies
- Easy rollback (just delete fork directory)

### Phase 3: Integrate (Add Production Modules)

Bring in battle-tested modules from other projects:

```
shell-development/
├── tools/
│   ├── bb7/                    # Existing core tools
│   └── native/                 # NEW: Production modules
│       ├── git_integration_module.py      # 2054 lines, proven
│       ├── web_search_research.py         # 1454 lines, proven
│       └── sovereign_analysis_tool.py     # Complete system
```

**Integration Criteria:**

- [ ] Module runs standalone (no project-specific dependencies)
- [ ] Module has been used in production elsewhere
- [ ] Module API is stable and documented
- [ ] Module error handling is production-grade
- [ ] Module can be dropped into fresh Python environment

**Integration Rules:**

1. **Only integrate production-proven modules**
   - Module must run standalone
   - Module must be battle-tested in another project
   - Module must have zero dependencies on your project structure
   - Module must maintain its own invariants

2. **Never modify integrated modules**
   - Treat as read-only dependencies
   - All customization goes in wrapper layer
   - Module updates don't break integration
   - Module remains extractable for other projects

3. **Document module provenance**

   ```python
   # git_integration_module.py
   # Source: Morpheus Chat App v3.2.1
   # Integrated: 2026-02-10
   # Purpose: Repository cloning, indexing, security scanning
   # Lines: 2054
   # Status: Production stable
   ```

**Integration Validation Checklist:**

- [ ] Module runs standalone (no project-specific dependencies)
- [ ] Module has been used in production elsewhere
- [ ] Module API is stable and documented
- [ ] Module error handling is production-grade
- [ ] Module can be dropped into fresh Python environment

### Phase 4: Evolve (Wire Components Together)

Create thin wrapper layer for integration:

```python
# tools/native/git_integration_module.py (production module, don't touch)

# NEW: Thin wrapper layer
class GitToolWrapper:
    """Wrapper exposing git module as native shell tools."""
    
    def __init__(self):
        # Import production module
        from git_integration_module import GitHubIntegrationManager
        
        # Initialize with minimal config
        self.git = GitHubIntegrationManager(
            data_directory=Path("./data"),
            enable_security_scanning=True
        )
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Expose production methods as shell tools."""
        return {
            'git_clone_repository': {
                'function': self._clone_wrapper,
                'description': 'Clone and index Git repository',
                'domain': 'git'
            },
            'git_search_files': {
                'function': self._search_wrapper,
                'description': 'Search files within repository',
                'domain': 'git'
            }
        }
    
    async def _clone_wrapper(self, repo_url: str, branch: str = None):
        """Thin adapter - translates interface, doesn't modify logic."""
        # Call production method
        metadata = await self.git.clone_repository(
            repo_url=repo_url,
            user_id="shell_user",
            session_id="shell_session",
            branch=branch
        )
        
        # Transform output to shell format
        return {
            'repo_id': str(metadata.repo_id),
            'name': metadata.name,
            'status': metadata.status,
            'file_count': metadata.total_files
        }
```

**Wrapper Guidelines:**

**DO:**

- Translate interfaces between systems
- Format outputs for consumer context
- Handle integration-specific error cases
- Keep wrappers under 200 lines

**DON'T:**

- Duplicate logic from production module
- Modify module behavior
- Add business logic to wrappers
- Create tight coupling between wrapper and module internals

**Wrapper Pattern Template:**

```python
class ModuleToolWrapper:
    """Standard wrapper pattern for production modules."""
    
    def __init__(self):
        # 1. Import production module
        from production_module import ProductionClass
        
        # 2. Initialize with minimal config
        self.module = ProductionClass(...)
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """3. Expose module capabilities as tools."""
        return {
            'tool_name': {
                'function': self._wrapper_method,
                'description': '...',
                'domain': 'module_domain'
            }
        }
    
    async def _wrapper_method(self, **kwargs):
        """4. Thin adapter: call module, transform output."""
        result = await self.module.production_method(**kwargs)
        return self._transform_for_shell(result)
    
    def _transform_for_shell(self, result):
        """5. Format output for shell context."""
        return {
            'key_field': result.important_data,
            'summary': result.summary_text[:500]
        }
```

### Phase 5: Snapshot (Capture New Baseline)

Validate integration and create new production snapshot:

```
shell-v2/                          # New snapshot
├── tools/
│   ├── bb7/                       # 20 core tools
│   └── native/                    # NEW production modules
│       ├── git_integration_module.py         # From chat app
│       ├── web_search_research.py            # From research system
│       ├── sovereign_analysis_tool.py        # From analysis project
│       └── wrappers/
│           ├── git_tool_wrapper.py           # 50 lines
│           ├── web_tool_wrapper.py           # 75 lines
│           └── analysis_tool_wrapper.py      # 100 lines
└── advanced_ai_shell.py

# Capabilities: 130+ tools (git_*, web_*, analysis_*, bb7_*)
# Status: Production stable
# Ready for: Next fork/integration cycle
```

**Snapshot Validation:**

- [ ] All integrated modules execute correctly
- [ ] Wrappers successfully expose module capabilities
- [ ] Shell can invoke all new tools
- [ ] No regressions in existing functionality
- [ ] Performance is acceptable
- [ ] Documentation updated

**Version Tagging:**

```bash
# Tag snapshot for reference
git tag -a v2.0 -m "Integrated git, web, analysis modules - 130+ tools"

# Snapshot becomes new baseline
mv shell-development/ shell-v2/
```

---

## The Recursive Property

### Snapshots Become Modules

```python
# shell-v2 becomes a production module for future projects

# Future Project: Multi-Agent Research System
from shell.advanced_ai_shell import AdvancedAIShell

class ResearchOrchestrator:
    def __init__(self):
        # Shell is now a production module with 130+ tools
        self.shell = AdvancedAIShell()
    
    async def research_topic(self, topic: str):
        # Inherit all git, web, analysis capabilities for free
        results = await self.shell.execute_command(
            f"web_search_deep {topic}"
        )
        await self.shell.execute_command(
            f"git_clone_repository {results['top_repo']}"
        )
        analysis = await self.shell.execute_command(
            f"analysis_execute {{\"intent\": \"analyze codebase\"}}"
        )
        return analysis
```

The shell you built becomes a **computational substrate** for higher-level systems.

### Capability Compounding

```
Iteration 1: 20 tools
    ↓ (integrate git module)
Iteration 2: 50 tools (20 core + 30 git)
    ↓ (integrate web module)
Iteration 3: 90 tools (20 core + 30 git + 40 web)
    ↓ (integrate analysis module)
Iteration 4: 130 tools (20 core + 30 git + 40 web + 40 analysis + 20 social)
    ↓ (integrate social module)
Iteration 5: 170 tools
```

Each snapshot inherits **all previous capabilities** plus new integrations.

---

## Architecture Patterns

### Pattern 1: Domain-Scoped Tools

Organize integrated modules by domain:

```
tools/
├── bb7/                 # Core orchestration (20 tools)
│   ├── memory_tool.py
│   ├── shell_tool.py
│   └── ...
└── native/              # Domain specialists (100+ tools)
    ├── git/             # Version control domain
    │   ├── git_integration_module.py (production)
    │   └── git_tool_wrapper.py (adapter)
    ├── web/             # Web research domain
    │   ├── web_search_research.py (production)
    │   └── web_tool_wrapper.py (adapter)
    ├── analysis/        # Data analysis domain
    │   ├── sovereign_analysis_tool.py (production)
    │   └── analysis_tool_wrapper.py (adapter)
    └── social/          # Social platform domain
        ├── social_integration_module.py (production)
        └── social_tool_wrapper.py (adapter)
```

**Discovery Pattern:**

```bash
# List all domains
$ tools domains
core, git, web, analysis, social

# List tools in domain
$ tools list git
git_clone_repository, git_status, git_search_files, ...

# Execute domain tool
$ git_clone_repository {"repo_url": "https://github.com/user/repo"}
```

### Pattern 2: Lazy Loading

Load domain modules on first access to minimize startup overhead:

```python
class NativeToolBridge:
    def __init__(self):
        self.core_tools = {}      # Loaded immediately
        self.domain_tools = {      # Loaded on demand
            'git': None,
            'web': None,
            'analysis': None
        }
    
    async def invoke_tool(self, tool_name: str, arguments: Dict):
        # Extract domain from tool name (git_*, web_*, etc.)
        domain = tool_name.split('_')[0]
        
        # Load domain if not loaded
        if domain in self.domain_tools and self.domain_tools[domain] is None:
            await self._load_domain(domain)
        
        # Invoke tool
        return await self.domain_tools[domain][tool_name](**arguments)
```

### Pattern 3: Context-Aware Output Formatting

Same tool, different output format based on consumer:

```python
async def execute_tool(self, tool_name: str, context: str):
    result = await self.invoke_tool(tool_name)
    
    # Format based on context
    if context == 'chat':
        # Human-readable summary
        return f"Repository '{result['name']}' cloned successfully. {result['file_count']} files."
    
    elif context == 'shell':
        # Structured JSON
        return json.dumps(result, indent=2)
    
    elif context == 'project':
        # Detailed table
        return self._format_as_table(result)
```

---

## Integration Checklist

When integrating a new production module:

### Pre-Integration Validation

- [ ] Module is production-proven (used elsewhere successfully)
- [ ] Module has no dependencies on specific project structure
- [ ] Module API is stable and documented
- [ ] Module error handling is robust
- [ ] Module can run standalone

### Integration Steps

- [ ] Copy module to appropriate domain directory
- [ ] Create wrapper class (< 200 lines)
- [ ] Implement get_tools() method
- [ ] Write thin adapter methods
- [ ] Add to tool discovery system
- [ ] Test basic invocation
- [ ] Validate output formatting

### Post-Integration Validation

- [ ] Module executes correctly in new environment
- [ ] Wrapper successfully exposes capabilities
- [ ] No conflicts with existing tools
- [ ] Performance is acceptable
- [ ] Documentation updated
- [ ] Example usage added

---

## Anti-Patterns (What NOT To Do)

### ❌ Modifying Production Modules

```python
# WRONG: Editing integrated module
def clone_repository(self, repo_url: str):
    # Added custom logging specific to this project
    self.project_logger.info(f"Cloning {repo_url}")  # DON'T DO THIS
    ...
```

**Why wrong:** Module is no longer portable, can't receive upstream updates

**Correct approach:** Add logging in wrapper layer

### ❌ Duplicating Module Logic

```python
# WRONG: Reimplementing module functionality in wrapper
async def _clone_wrapper(self, repo_url: str):
    # Duplicating security validation from module
    if not self._validate_url_security(repo_url):  # DON'T DO THIS
        raise ValueError("Insecure URL")
    ...
```

**Why wrong:** Logic drift, maintenance burden, defeats purpose of integration

**Correct approach:** Trust module's validation, translate output only

### ❌ Tight Coupling in Wrappers

```python
# WRONG: Wrapper depends on module internals
async def _search_wrapper(self, query: str):
    # Accessing private module attributes
    results = self.git._internal_search_engine.query(query)  # DON'T DO THIS
```

**Why wrong:** Breaks when module internals change, fragile integration

**Correct approach:** Use only public module API

### ❌ Half-Finished Integrations

```python
# WRONG: Partially implemented wrapper
def get_tools(self):
    return {
        'git_clone': {'function': self._clone_wrapper},
        # TODO: Add other git operations later  # DON'T DO THIS
    }
```

**Why wrong:** Violates "file tree = executable codebase" principle

**Correct approach:** Only commit complete, working integrations

---

## VM Architecture Considerations

### When To Use VMs vs Containers

**Use VMs for:**

- Persistent infrastructure (model weights, databases)
- Full desktop OS requirements
- Long-running processes
- Resource-intensive applications

**Use Containers for:**

- Disposable execution (analysis workflows)
- Isolated code execution
- Multi-language support
- Rapid creation/destruction

### VM Integration Pattern

```python
# Shell orchestrates VMs for infrastructure
class VMBackedTool:
    def __init__(self):
        self.vm_manager = VMOrchestrator()
    
    async def execute_ml_task(self, task: str):
        # Spin up VM with model weights preloaded
        vm_id = await self.vm_manager.create_vm(
            template='ml_inference',
            resources={'gpu': True, 'memory_gb': 16}
        )
        
        # Execute in VM (weights persist across tasks)
        result = await self.vm_manager.execute(vm_id, task)
        
        # VM stays running for future tasks
        return result
```

**Key Insight:** Infrastructure lives IN the VM, shell orchestrates FROM native process

### The "Can't Go Backwards" Is Forward Progress

Once you've integrated VM-backed tools:

```python
class AdvancedMLTool:
    def __init__(self):
        # Assumes model weights in persistent VM
        self.model = load_pretrained_model()  # Won't work in basic container
```

You can't extract this back to a simple container. But that's good:

- Enforces forward progress
- Prevents capability regression
- Snapshot history preserves simpler versions if needed
- Future forks inherit advanced capabilities

---

## Codex Integration Notes

### What Codex Should Know

**Development Style:**

- No half-finished code in tree
- Integration over implementation
- Thin wrappers, never rewrites
- Production modules are read-only dependencies

**File Organization:**

- `tools/bb7/` = Core orchestration primitives
- `tools/native/` = Integrated production modules
- Wrappers are always in same directory as module

**Integration Process:**

1. Copy production module (don't modify)
2. Create wrapper class
3. Implement get_tools() and thin adapters
4. Validate integration
5. Snapshot when stable

**Code Quality Standards:**

- Every file executes without errors
- No commented-out experiments
- No TODO markers in committed code
- Documentation matches implementation

### Prompting Codex For Integration

**Good Prompt:**

```
I have a production module git_integration_module.py (2054 lines) with a 
GitHubIntegrationManager class that handles repository cloning and indexing.

Create a wrapper class GitToolWrapper that:
1. Imports GitHubIntegrationManager
2. Exposes clone_repository and search_files as shell tools
3. Uses thin adapters (< 50 lines each)
4. Transforms output to shell-friendly format

Follow the wrapper pattern from existing wrappers in tools/native/wrappers/
```

**Bad Prompt:**

```
Create a git integration system for the shell
```

(This would lead Codex to implement from scratch instead of wrapping)

### What Codex Should Avoid

- Suggesting modifications to production modules
- Implementing features that already exist in modules
- Creating tightly coupled integrations
- Adding TODOs or prototype code
- Ignoring existing wrapper patterns

---

## Development Velocity Mathematics

### Traditional Development

```
Feature complexity: O(n²) where n = number of features
Integration cost: High (features interact)
Regression risk: High (tight coupling)
Capability velocity: Linear
```

### Recursive Production Composition

```
Module complexity: O(n) where n = number of modules
Integration cost: Low (thin wrappers, isolated modules)
Regression risk: Low (modules are independent)
Capability velocity: Exponential (snapshots compound)
```

### Velocity Comparison

| Iteration | Traditional Approach | Recursive Composition |
|-----------|---------------------|----------------------|
| 1 | 20 features | 20 tools |
| 2 | 25 features (+5) | 50 tools (+30 from module) |
| 3 | 32 features (+7) | 90 tools (+40 from module) |
| 4 | 40 features (+8) | 130 tools (+40 from module) |
| 5 | 50 features (+10) | 200 tools (+70 from modules) |

**Result:** 4x capability growth rate with recursive composition

---

## Snapshot Management

### Naming Convention

```
project-v1/          # Initial baseline
project-v2/          # First integration cycle
project-development/ # Current work-in-progress
project-experimental/# Experimental forks
```

### Git Tagging Strategy

```bash
# Tag production snapshots
git tag -a v1.0 -m "Baseline: 20 core tools"
git tag -a v2.0 -m "Integrated git module: 50 tools"
git tag -a v3.0 -m "Integrated web + analysis: 130 tools"

# Reference previous snapshots
git checkout v1.0  # Return to baseline if needed
```

### Snapshot Documentation

```markdown
# SNAPSHOT.md

## Version 3.0 - 2026-02-10

### Capabilities
- 130 total tools
- 20 bb7_* core tools
- 30 git_* tools (git integration module)
- 40 web_* tools (web search module)
- 40 analysis_* tools (sovereign analysis)

### Integrated Modules
1. git_integration_module.py (from Morpheus Chat v3.2.1)
2. web_search_research.py (from Research System v2.1.0)
3. sovereign_analysis_tool.py (from Analysis Platform v1.5.0)

### Integration Wrappers
- git_tool_wrapper.py (75 lines)
- web_tool_wrapper.py (100 lines)
- analysis_tool_wrapper.py (125 lines)

### Validation Status
- All tools execute correctly ✓
- No regressions detected ✓
- Performance acceptable ✓
- Documentation complete ✓

### Next Integration Candidates
- social_integration_module.py (social platform APIs)
- video_processing_module.py (FFmpeg workflows)
```

---

## Production Module Quality Standards

### Module Acceptance Criteria

A module is production-ready when:

- [ ] Has been deployed and used successfully elsewhere
- [ ] Runs standalone without project-specific dependencies
- [ ] Has comprehensive error handling
- [ ] Maintains stable API surface
- [ ] Includes docstrings for public methods
- [ ] Can be imported and instantiated cleanly
- [ ] Resource cleanup on shutdown (if applicable)

### Module Documentation Requirements

```python
"""
Production Module: Git Integration System
Source: Morpheus Chat Application v3.2.1
Integrated: 2026-02-10
Lines: 2054
Status: Production Stable

Capabilities:
- Repository cloning with security validation
- File indexing and search
- Security scanning
- LFS and submodule support
- Resumable operations with checkpoints

API Surface:
- GitHubIntegrationManager.clone_repository()
- GitHubIntegrationManager.search_files()
- GitHubIntegrationManager.get_repository_status()

Dependencies:
- git (GitPython)
- aiofiles
- pydantic

Resource Requirements:
- Memory: ~100MB baseline + repository size
- Disk: 2x repository size for cloning
- Network: Required for cloning

Error Handling:
- ValidationError: Invalid repository URL
- SecurityError: Security policy violation
- CloneError: Repository cloning failure
- IndexingError: File processing failure

Example Usage:
    git_manager = GitHubIntegrationManager(data_directory=Path('./data'))
    metadata = await git_manager.clone_repository(
        repo_url='https://github.com/user/repo',
        user_id='user_123',
        session_id='session_456'
    )
"""
```

---

## Conclusion

This methodology enables:

- **Rapid capability expansion** through module integration
- **Architectural cleanliness** through thin wrapper pattern
- **Production stability** through proven component reuse
- **Forward progress** through snapshot compounding

The recursive property means each project makes **all future projects faster** because snapshots become baseline capabilities.

**Core Mantras:**

1. File tree = Executable codebase (no half-finished code)
2. Integration > Implementation (reuse production modules)
3. Thin wrappers > Tight coupling (preserve module independence)
4. Snapshot when stable (capture working systems as baselines)
5. Forward progress only (no backwards regression)

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Maintained By:** Daeron  
**Purpose:** Codex integration and development methodology documentation  
