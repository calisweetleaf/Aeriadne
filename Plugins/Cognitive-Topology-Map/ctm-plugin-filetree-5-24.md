# File Tree: Cognitive-Topology-Map

**Generated:** 5/24/2026, 2:38:58 AM
**Root Path:** `/home/daeron/Projects/Modern-ML/Plugins/Cognitive-Topology-Map`

```
├── .github
│   └── workflows
│       ├── release.yml
│       ├── schema-check.yml
│       ├── topology-enforce.yml
│       └── validate.yml
├── claude-code
│   ├── .claude-plugin
│   │   └── plugin.json
│   ├── agents
│   │   └── ctmv3-architect.md
│   ├── commands
│   │   ├── ctmv3-activate.md
│   │   ├── ctmv3-architecture-map.md
│   │   ├── ctmv3-boot.md
│   │   ├── ctmv3-dot-init.md
│   │   ├── ctmv3-session-close.md
│   │   ├── ctmv3-sovereign-init.md
│   │   ├── ctmv3-status.md
│   │   └── ctmv3-warm.md
│   ├── hooks
│   │   └── hooks.json
│   ├── skills
│   │   └── ctmv3
│   │       └── SKILL.md
│   ├── README.md
│   └── settings.json
├── codex
│   ├── config-fragments
│   │   ├── config.toml.fragment
│   │   └── hooks.json.fragment
│   ├── skills
│   │   └── ctmv3
│   │       ├── agents
│   │       │   └── openai.yaml
│   │       ├── scripts
│   │       │   ├── ctmv3-activate.sh
│   │       │   ├── ctmv3-architecture-map.sh
│   │       │   ├── ctmv3-boot.sh
│   │       │   ├── ctmv3-dot-init.sh
│   │       │   ├── ctmv3-session-close.sh
│   │       │   ├── ctmv3-sovereign-init.sh
│   │       │   ├── ctmv3-status.sh
│   │       │   └── ctmv3-warm.sh
│   │       ├── REFERENCES.md
│   │       └── SKILL.md
│   ├── README.md
│   └── install.sh
├── core
│   ├── .pytest_cache
│   │   ├── v
│   │   ├── .gitignore
│   │   ├── CACHEDIR.TAG
│   │   └── README.md
│   ├── ctmv3
│   │   ├── core
│   │   │   ├── templates
│   │   │   │   ├── extras
│   │   │   │   │   ├── claude-settings.json.template
│   │   │   │   │   ├── golden_paths.json.template
│   │   │   │   │   ├── pre-commit-config.yaml.template
│   │   │   │   │   └── session_state.json.template
│   │   │   │   ├── AGENTS.md.template
│   │   │   │   ├── ARCHITECTURE_MAP.md.template
│   │   │   │   ├── CLAUDE.md.template
│   │   │   │   ├── FAILURE_GRAMMAR.md.template
│   │   │   │   ├── PROVENANCE.md.template
│   │   │   │   ├── TOPOLOGY.md.template
│   │   │   │   ├── copilot-instructions.md.template
│   │   │   │   └── topology-enforce.yml.template
│   │   │   ├── __init__.py
│   │   │   ├── activate.py
│   │   │   ├── architecture_map.py
│   │   │   ├── boot.py
│   │   │   ├── cli.py
│   │   │   ├── dot_init.py
│   │   │   ├── fingerprint.py
│   │   │   ├── orchestration.py
│   │   │   ├── sovereign.py
│   │   │   └── templates.py
│   │   ├── tests
│   │   │   ├── __init__.py
│   │   │   └── test_engine.py
│   │   ├── __init__.py
│   │   └── __main__.py
│   ├── ctmv3.egg-info
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   ├── dependency_links.txt
│   │   ├── entry_points.txt
│   │   └── top_level.txt
│   ├── README.md
│   └── pyproject.toml
├── cursor
│   ├── scripts
│   │   ├── ctmv3-activate.sh
│   │   ├── ctmv3-architecture-map.sh
│   │   ├── ctmv3-boot.sh
│   │   ├── ctmv3-chain.sh
│   │   ├── ctmv3-dot-init.sh
│   │   ├── ctmv3-fingerprint.sh
│   │   ├── ctmv3-session-close.sh
│   │   ├── ctmv3-sovereign-init.sh
│   │   ├── ctmv3-status.sh
│   │   └── ctmv3-warm.sh
│   ├── README.md
│   └── install.sh
├── docs
│   ├── examples
│   │   └── case_codebase_entry.md
│   ├── interfaces
│   │   ├── orchestration.md
│   │   └── python.md
│   ├── AGENTS_ADDENDUM.md
│   ├── ARCHITECTURE_MAP_TEMPLATE.md
│   ├── BOOT_PROTOCOL.md
│   ├── CONSTITUTION.md
│   ├── DOT_TOPOLOGY.md
│   ├── EXPLANATION.md
│   ├── FAILURE_GRAMMAR.md
│   ├── GOLDEN_PATH.md
│   ├── PROVENANCE.md
│   ├── SCHEMA_AUDIT.md
│   ├── SKILL.md
│   └── TOPOLOGY.md
├── examples
│   └── cold-start-trace.md
├── extras
│   ├── templates
│   │   ├── AGENTS.example.md
│   │   ├── CLAUDE.example.md
│   │   ├── golden_paths.example.json
│   │   └── topology-enforce.example.yml
│   └── README.md
├── gemini-cli
│   ├── ctmv3
│   │   ├── commands
│   │   │   └── ctmv3
│   │   │       ├── activate.toml
│   │   │       ├── architecture-map.toml
│   │   │       ├── boot.toml
│   │   │       ├── dot-init.toml
│   │   │       ├── session-close.toml
│   │   │       ├── sovereign-init.toml
│   │   │       ├── status.toml
│   │   │       └── warm.toml
│   │   ├── scripts
│   │   │   ├── ctmv3-session-start.sh
│   │   │   └── ctmv3-wrap.sh
│   │   ├── GEMINI.md
│   │   └── gemini-extension.json
│   ├── README.md
│   └── install.sh
├── opencode
│   ├── agent
│   │   └── ctmv3-architect.md
│   ├── command
│   │   ├── ctmv3-activate.md
│   │   ├── ctmv3-architecture-map.md
│   │   ├── ctmv3-boot.md
│   │   ├── ctmv3-dot-init.md
│   │   ├── ctmv3-session-close.md
│   │   ├── ctmv3-sovereign-init.md
│   │   ├── ctmv3-status.md
│   │   └── ctmv3-warm.md
│   ├── plugin
│   │   └── ctmv3.ts
│   ├── README.md
│   ├── install.sh
│   └── opencode.json.fragment
├── research
│   └── RUNTIME_FORMATS.md
├── tests
│   ├── run-all.sh
│   └── smoke.sh
├── CHANGELOG.md
├── CODEBASE_INTELLIGENCE.md
├── CONTRIBUTING.md
├── INSTALL.md
├── LICENSE
├── README.md
├── STRUCTURE.md
└── __init__.py
```

---
*Generated by FileTree Pro Extension*
