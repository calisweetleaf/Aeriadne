# File Tree: Mentat

**Generated:** 5/22/2026, 10:06:03 PM
**Root Path:** `/home/daeron/Projects/Modern-ML/Plugins/Mentat`

```filetree
├── helpers
│   ├── HELPERS.md
│   ├── mentat-conductor.md
│   ├── mentat-medic.md
│   └── mentat-quartermaster.md
├── plugin
│   ├── .claude-plugin
│   │   └── plugin.json
│   ├── adapters
│   │   ├── codex
│   │   │   ├── hooks
│   │   │   │   ├── _lib.py
│   │   │   │   ├── permission_request.py
│   │   │   │   ├── post_tool_use.py
│   │   │   │   ├── pre_tool_use.py
│   │   │   │   ├── session_start.py
│   │   │   │   ├── stop.py
│   │   │   │   └── user_prompt_submit.py
│   │   │   ├── AGENTS.snippet.md
│   │   │   ├── README.md
│   │   │   ├── config.toml.snippet
│   │   │   └── hooks.json
│   │   ├── gemini
│   │   │   ├── hooks
│   │   │   │   ├── _lib.py
│   │   │   │   ├── after_agent.py
│   │   │   │   ├── after_model.py
│   │   │   │   ├── after_tool.py
│   │   │   │   ├── before_agent.py
│   │   │   │   ├── before_model.py
│   │   │   │   ├── before_tool.py
│   │   │   │   ├── before_tool_selection.py
│   │   │   │   ├── hooks.json
│   │   │   │   ├── notification.py
│   │   │   │   ├── pre_compress.py
│   │   │   │   ├── session_end.py
│   │   │   │   └── session_start.py
│   │   │   ├── GEMINI.snippet.md
│   │   │   ├── README.md
│   │   │   └── gemini-extension.json
│   │   ├── install_universal.sh
│   │   └── test_universal.sh
│   ├── agents
│   │   ├── mentat-cartographer.md
│   │   ├── mentat-crucible.md
│   │   ├── mentat-scribe.md
│   │   └── mentat-sentinel.md
│   ├── commands
│   │   ├── README.md
│   │   ├── debrief.md
│   │   ├── dispatch.md
│   │   ├── drift-check.md
│   │   ├── plan.md
│   │   ├── qtable.md
│   │   ├── reflect.md
│   │   ├── scope.md
│   │   ├── status.md
│   │   └── tail.md
│   ├── docs
│   │   ├── PROVENANCE.md
│   │   ├── SOTA_CHECKLIST.md
│   │   └── STYLE.v2.md
│   ├── evals
│   │   ├── agents
│   │   │   ├── comparator.md
│   │   │   └── grader.md
│   │   ├── output
│   │   │   ├── benchmark.html
│   │   │   ├── benchmark.json
│   │   │   ├── report.html
│   │   │   └── report.json
│   │   ├── references
│   │   │   └── schemas.md
│   │   ├── scenarios
│   │   │   ├── __init__.py
│   │   │   ├── _types.py
│   │   │   ├── persistence_recovery.py
│   │   │   ├── predictive_routing.py
│   │   │   └── state_transitions.py
│   │   ├── scripts
│   │   │   ├── __init__.py
│   │   │   ├── aggregate_benchmark.py
│   │   │   ├── generate_report.py
│   │   │   └── run_eval.py
│   │   ├── .gitignore
│   │   ├── README.md
│   │   ├── SKILL.md
│   │   ├── __init__.py
│   │   ├── harness.py
│   │   └── rubric.json
│   ├── hooks
│   │   ├── _lib.py
│   │   ├── hooks.json
│   │   ├── post_compact.py
│   │   ├── post_tool_use.py
│   │   ├── pre_compact.py
│   │   ├── pre_tool_use.py
│   │   ├── session_start.py
│   │   ├── stop.py
│   │   ├── stop_failure.py
│   │   ├── subagent_start.py
│   │   ├── subagent_stop.py
│   │   └── user_prompt_submit.py
│   ├── mcp_server
│   │   ├── __init__.py
│   │   └── __main__.py
│   ├── monitors
│   │   ├── README.md
│   │   ├── archivist.py
│   │   ├── drift_watcher.py
│   │   ├── entropy_watcher.py
│   │   └── test_smoke.py
│   ├── schemas
│   ├── scripts
│   │   └── integration_smoke.py
│   ├── skills
│   │   ├── mentat-debrief
│   │   │   ├── scripts
│   │   │   │   ├── __init__.py
│   │   │   │   ├── aggregate.py
│   │   │   │   ├── render.py
│   │   │   │   ├── template.html
│   │   │   │   └── test_smoke.py
│   │   │   └── SKILL.md
│   │   ├── mentat-dispatch
│   │   │   └── SKILL.md
│   │   ├── mentat-plan
│   │   │   └── SKILL.md
│   │   └── mentat-reflect
│   │       └── SKILL.md
│   ├── state_machine
│   │   ├── __init__.py
│   │   ├── drift.py
│   │   ├── insights.py
│   │   ├── machine.py
│   │   ├── q_table.py
│   │   └── session.py
│   ├── webhook_engine
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── dlq.py
│   │   ├── emitter.py
│   │   ├── envelope.py
│   │   └── test_smoke.py
│   ├── CHANGELOG.md
│   ├── INSTALL.md
│   ├── README.md
│   ├── mcp.json
│   └── webhooks.json
├── style
│   ├── PROVENANCE.md
│   ├── SOTA_CHECKLIST.md
│   └── STYLE.v2.md
├── Archive.zip
├── CHANGELOG.md
├── mentat-a-live-cognitive-substrate-for-claude-code.html
├── mentat-file-tree.md
└── mentat-plugin.tar.gz
```

---
*Generated by FileTree Pro Extension*