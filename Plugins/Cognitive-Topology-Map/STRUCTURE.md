# STRUCTURE — CTMv3 Plugin Layout Reference

```
ctmv3-plugin/
├── README.md                        Cross-runtime overview, command matrix
├── INSTALL.md                       Step-by-step install for all runtimes
├── CHANGELOG.md                     Version history
├── STRUCTURE.md                     (this file) layout reference
│
├── core/                            Python activation engine (pip-installable)
│   ├── pyproject.toml               Install manifest (name=ctmv3)
│   ├── README.md                    Engine-specific docs
│   └── ctmv3/                       Top-level Python package
│       ├── __init__.py              Public API re-exports
│       ├── __main__.py              python -m ctmv3 entrypoint
│       ├── core/                    Engine subpackage
│       │   ├── __init__.py
│       │   ├── cli.py               argparse CLI surface
│       │   ├── boot.py              BOOT_PROTOCOL discovery sequence
│       │   ├── activate.py          Cold-start orchestrator
│       │   ├── fingerprint.py       SHA-256 drift detector
│       │   ├── sovereign.py         .sovereign/ management
│       │   ├── dot_init.py          .claude/, .codex/, .github/ scaffolders
│       │   ├── architecture_map.py  Traversal map scaffolder
│       │   ├── templates.py         Template loader and renderer
│       │   └── templates/           Bundled artifact templates
│       │       ├── TOPOLOGY.md.template
│       │       ├── FAILURE_GRAMMAR.md.template
│       │       ├── PROVENANCE.md.template
│       │       ├── ARCHITECTURE_MAP.md.template
│       │       ├── AGENTS.md.template
│       │       ├── CLAUDE.md.template
│       │       ├── copilot-instructions.md.template
│       │       ├── topology-enforce.yml.template
│       │       └── extras/          Reference templates (not auto-rendered)
│       │           ├── claude-settings.json.template
│       │           ├── golden_paths.json.template
│       │           ├── pre-commit-config.yaml.template
│       │           └── session_state.json.template
│       └── tests/
│           ├── __init__.py
│           └── test_engine.py
│
├── docs/                            Full CTMv3 cognitive doc set
│   ├── EXPLANATION.md               What CTMv3 actually is
│   ├── SKILL.md                     Semantic router + phase protocol
│   ├── BOOT_PROTOCOL.md             State machine
│   ├── TOPOLOGY.md                  Anatomy of a topology
│   ├── DOT_TOPOLOGY.md              .xyz directories as topology signals
│   ├── ARCHITECTURE_MAP_TEMPLATE.md Traversal map protocol
│   ├── FAILURE_GRAMMAR.md           Failure taxonomy
│   ├── PROVENANCE.md                Decision log doctrine
│   ├── CONSTITUTION.md              Development philosophy
│   ├── AGENTS_ADDENDUM.md           AGENTS.md integration
│   ├── interfaces/
│   │   └── python.md                Python-specific patterns
│   └── examples/
│       └── case_codebase_entry.md   Annotated trace
│
├── claude-code/                     Claude Code adapter
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── settings.json                Permissions block
│   ├── commands/
│   │   ├── ctmv3-activate.md
│   │   ├── ctmv3-boot.md
│   │   ├── ctmv3-warm.md
│   │   ├── ctmv3-architecture-map.md
│   │   ├── ctmv3-sovereign-init.md
│   │   ├── ctmv3-dot-init.md
│   │   ├── ctmv3-session-close.md
│   │   └── ctmv3-status.md
│   ├── hooks/
│   │   └── hooks.json
│   ├── agents/
│   │   └── ctmv3-architect.md
│   ├── skills/
│   │   └── ctmv3/
│   │       └── SKILL.md
│   └── README.md
│
├── codex/                           Codex adapter
│   ├── skills/
│   │   └── ctmv3/
│   │       ├── SKILL.md
│   │       ├── REFERENCES.md
│   │       ├── agents/
│   │       │   └── openai.yaml
│   │       └── scripts/
│   │           ├── ctmv3-boot.sh
│   │           ├── ctmv3-activate.sh
│   │           ├── ctmv3-warm.sh
│   │           ├── ctmv3-architecture-map.sh
│   │           ├── ctmv3-sovereign-init.sh
│   │           ├── ctmv3-dot-init.sh
│   │           ├── ctmv3-session-close.sh
│   │           └── ctmv3-status.sh
│   ├── config-fragments/
│   │   ├── config.toml.fragment
│   │   └── hooks.json.fragment
│   ├── install.sh
│   └── README.md
│
├── opencode/                        opencode adapter
│   ├── agent/
│   │   └── ctmv3-architect.md
│   ├── command/
│   │   ├── ctmv3-activate.md
│   │   ├── ctmv3-boot.md
│   │   ├── ctmv3-warm.md
│   │   ├── ctmv3-architecture-map.md
│   │   ├── ctmv3-sovereign-init.md
│   │   ├── ctmv3-dot-init.md
│   │   ├── ctmv3-session-close.md
│   │   └── ctmv3-status.md
│   ├── plugin/
│   │   └── ctmv3.ts
│   ├── install.sh
│   ├── opencode.json.fragment
│   └── README.md
│
├── gemini-cli/                      Gemini CLI adapter
│   ├── ctmv3/
│   │   ├── gemini-extension.json
│   │   ├── GEMINI.md
│   │   ├── commands/
│   │   │   └── ctmv3/               Gemini namespaces commands by subdir
│   │   │       ├── boot.toml
│   │   │       ├── activate.toml
│   │   │       ├── warm.toml
│   │   │       ├── architecture-map.toml
│   │   │       ├── sovereign-init.toml
│   │   │       ├── dot-init.toml
│   │   │       ├── session-close.toml
│   │   │       └── status.toml
│   │   └── scripts/
│   │       ├── ctmv3-wrap.sh
│   │       └── ctmv3-session-start.sh
│   ├── install.sh
│   └── README.md
│
├── research/
│   └── RUNTIME_FORMATS.md           Cross-runtime plugin format reference
│
├── examples/                        End-to-end demo runs
│   └── (populated post-install)
│
└── tests/                           End-to-end smoke tests
    └── smoke.sh
```

## Notable Asymmetries

- **Claude Code** uses `commands/*.md` with YAML front-matter, hooks in
  `hooks/hooks.json`, subagents in `agents/*.md`.
- **Codex** uses `skills/<name>/` with `SKILL.md` + `agents/openai.yaml` +
  shell scripts. Hooks live in global `~/.codex/hooks.json`.
- **opencode** uses `agent/*.md`, `command/*.md`, `plugin/*.ts`. No plugin
  manifest; TypeScript files are dropped into the directory.
- **Gemini CLI** uses `gemini-extension.json` manifest, `GEMINI.md` context,
  and TOML slash commands at `commands/<namespace>/<name>.toml`. Path
  becomes command name with slashes converted to colons.

Despite these surface asymmetries, every adapter delegates to the same
engine: `python3 -m ctmv3 <command>`. Command semantics stay consistent.
