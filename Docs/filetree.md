.:
Adapters
Agents
Core
Docs
install.sh
Marketplace
Plugins
README.md
Registry
Scripts
Servers
Skills

./Adapters:

./Agents:
claude-code
codex

./Agents/claude-code:
defense-grade-doc-engine.md
golden-path-architect.md
prod-finalizer.md

./Agents/codex:
defense-grade-doc-engine.toml
golden-path-architect.toml
prod-finalizer.toml

./Core:
Kernel

./Core/Kernel:
AGENTS.md
bin
COMPILED_CONSTITUTION.md
COMPILED_KERNEL.md
config_patched.toml
config.toml
CONTEXT.md
hooks.json
hooks_merged_petdex_sovereign.json
MEMORY.md
README_DEPLOYMENT.md
research.config.toml
sovereign.config.toml
STAGING_ANALYSIS.md
stealth.config.toml
validation_manifest.json
workflows.md

./Core/Kernel/bin:
hooks
notify_relay.py

./Core/Kernel/bin/hooks:
_lib.backup_20260603_151544.py
_lib.py
post_compact.py
post_tool_use.py
pre_compact.py
pre_tool_use.py
session_start.py
stop.py
subagent_start.py
subagent_stop.py
user_prompt_submit.py

./Docs:
AGENTS.md
ARCHITECTURE_MAP.md
CONTEXT.md
ECOSYSTEM_ADOPTION_MAP.md
filetree.md
MEMORY.md
PLAN.md
REPO_ENTRY_MATRIX.md
TECHNICAL_REFERENCE.md

./Marketplace:

./Plugins:
Aeriadne
Cognitive-Topology-Map
Mentat

./Plugins/Aeriadne:
adapters
agents
CHANGELOG.md
filetree.md
LICENSE.md
MANIFEST.md
marketplace
MARKETPLACE_ROADMAP.md
mcp
plugin.json
plugin.toml
README.md
registry
scripts
skills
tests
validation

./Plugins/Aeriadne/adapters:
claude-code
codex
opencode
README.md

./Plugins/Aeriadne/adapters/claude-code:
README.md

./Plugins/Aeriadne/adapters/codex:
README.md

./Plugins/Aeriadne/adapters/opencode:
README.md

./Plugins/Aeriadne/agents:
claude-code
codex
opencode
README.md
subagents

./Plugins/Aeriadne/agents/claude-code:
README.md

./Plugins/Aeriadne/agents/codex:
README.md

./Plugins/Aeriadne/agents/opencode:
README.md

./Plugins/Aeriadne/agents/subagents:
compatibility-auditor.md
package-cartographer.md
prompt-architect.md
registry-scribe.md
release-sentinel.md

./Plugins/Aeriadne/marketplace:
cards
indexes
README.md

./Plugins/Aeriadne/marketplace/cards:
aeriadne-marketplace-operator.skill.md
aeriadne.plugin.md
constitutional-prompt-framework.skill.md
sovereign-bb7.mcp.md

./Plugins/Aeriadne/marketplace/indexes:
agent-index.yaml
mcp-index.yaml
plugin-index.yaml
skill-index.yaml

./Plugins/Aeriadne/mcp:
contracts
README.md
servers

./Plugins/Aeriadne/mcp/contracts:
client-bindings.yaml
tool-capabilities.yaml

./Plugins/Aeriadne/mcp/servers:
sovereign-bb7.md

./Plugins/Aeriadne/registry:
aeriadne.plugin.json
agents.yaml
mcp_servers.yaml
plugins.yaml
README.md
skills.yaml

./Plugins/Aeriadne/scripts:
validate_package.py

./Plugins/Aeriadne/skills:
aeriadne-marketplace-operator
constitutional-prompt-framework

./Plugins/Aeriadne/skills/aeriadne-marketplace-operator:
references
SKILL.md
templates
tests

./Plugins/Aeriadne/skills/aeriadne-marketplace-operator/references:
marketplace-schema.md

./Plugins/Aeriadne/skills/aeriadne-marketplace-operator/templates:
plugin-card.md
registry-entry.yaml

./Plugins/Aeriadne/skills/aeriadne-marketplace-operator/tests:
smoke_cases.yaml

./Plugins/Aeriadne/skills/constitutional-prompt-framework:
agents
assets
CHANGELOG.md
examples
MANIFEST.md
package-manifest.json
README.md
references
RELEASE_NOTES.md
schemas
scripts
SKILL.md
tests

./Plugins/Aeriadne/skills/constitutional-prompt-framework/agents:
openai.yaml

./Plugins/Aeriadne/skills/constitutional-prompt-framework/assets:
single-file-agent-constitution-skeleton.md
templates

./Plugins/Aeriadne/skills/constitutional-prompt-framework/assets/templates:
agent-constitution-full.md
audit-report-template.md
capability-dispatch-table.md
constitution-spec.example.json
intake-form.md
memory-policy-template.md
platform-binding-template.md
red-team-report-template.md
release-checklist.md
rewrite-plan-template.md

./Plugins/Aeriadne/skills/constitutional-prompt-framework/examples:
example-agent-constitution.md
example-audit-report.md
example-rewrite-plan.md
rendered-from-spec.md

./Plugins/Aeriadne/skills/constitutional-prompt-framework/references:
00-doc-chain.md
01-constitutional-prompt-theory.md
02-derivation-guide.md
03-layer-contracts.md
04-authority-and-governance.md
05-rules-of-engagement-patterns.md
06-operating-doctrine-library.md
07-persona-architecture.md
08-capability-dispatch.md
09-memory-continuity.md
10-platform-binding-matrix.md
11-security-privacy-safety.md
12-long-context-and-compaction.md
13-domain-ingestion-and-knowledge-modeling.md
14-output-contracts.md
15-audit-checklist.md
16-evaluation-rubric.md
17-red-team-suite.md
18-anti-patterns.md
19-rewrite-playbook.md
20-deployment-and-maintenance.md
21-interoperability-notes.md
22-glossary.md
23-schema-driven-authoring.md
24-failure-mode-atlas.md

./Plugins/Aeriadne/skills/constitutional-prompt-framework/schemas:
audit-report.schema.json
constitution-spec.schema.json
skill-package.schema.json

./Plugins/Aeriadne/skills/constitutional-prompt-framework/scripts:
constitution_linter.py
_cpf_common.py
render_constitution_from_spec.py
run_static_evals.py
score_constitution.py
validate_skill_package.py

./Plugins/Aeriadne/skills/constitutional-prompt-framework/tests:
eval_cases.yaml
fixtures
README.md

./Plugins/Aeriadne/skills/constitutional-prompt-framework/tests/fixtures:
minimal_constitution_spec.json

./Plugins/Aeriadne/tests:
compatibility_matrix.yaml
smoke_cases.yaml

./Plugins/Aeriadne/validation:
validation_manifest.json
validation_report.md

./Plugins/Cognitive-Topology-Map:
Archive.zip
CHANGELOG.md
claude-code
CODEBASE_INTELLIGENCE.md
codex
CONTRIBUTING.md
core
ctm-plugin-filetree-5-24.md
ctmv3-plugin-v1.2.0.zip
cursor
docs
examples
extras
gemini-cli
__init__.py
INSTALL.md
LICENSE
opencode
README.md
research
STRUCTURE.md
tests

./Plugins/Cognitive-Topology-Map/claude-code:
agents
commands
hooks
README.md
settings.json
skills

./Plugins/Cognitive-Topology-Map/claude-code/agents:
ctmv3-architect.md

./Plugins/Cognitive-Topology-Map/claude-code/commands:
ctmv3-activate.md
ctmv3-architecture-map.md
ctmv3-boot.md
ctmv3-dot-init.md
ctmv3-session-close.md
ctmv3-sovereign-init.md
ctmv3-status.md
ctmv3-warm.md

./Plugins/Cognitive-Topology-Map/claude-code/hooks:
hooks.json
hooks.json.backup_hook_schema_20260603_1530
__pycache__
session_start_codex.backup_20260604_172102.py
session_start_codex.backup_20260604_172319.py
session_start_codex.py
stop_codex.py

./Plugins/Cognitive-Topology-Map/claude-code/hooks/__pycache__:
session_start_codex.cpython-312.pyc
stop_codex.cpython-312.pyc

./Plugins/Cognitive-Topology-Map/claude-code/skills:
ctmv3

./Plugins/Cognitive-Topology-Map/claude-code/skills/ctmv3:
SKILL.md

./Plugins/Cognitive-Topology-Map/codex:
config-fragments
install.sh
README.md
skills

./Plugins/Cognitive-Topology-Map/codex/config-fragments:
config.toml.fragment
hooks.json.fragment

./Plugins/Cognitive-Topology-Map/codex/skills:
ctmv3

./Plugins/Cognitive-Topology-Map/codex/skills/ctmv3:
agents
REFERENCES.md
scripts
SKILL.md

./Plugins/Cognitive-Topology-Map/codex/skills/ctmv3/agents:
openai.yaml

./Plugins/Cognitive-Topology-Map/codex/skills/ctmv3/scripts:
ctmv3-activate.sh
ctmv3-architecture-map.sh
ctmv3-boot.sh
ctmv3-dot-init.sh
ctmv3-session-close.sh
ctmv3-sovereign-init.sh
ctmv3-status.sh
ctmv3-warm.sh

./Plugins/Cognitive-Topology-Map/core:
ctmv3
ctmv3.egg-info
pyproject.toml
README.md

./Plugins/Cognitive-Topology-Map/core/ctmv3:
core
__init__.py
__main__.py
__pycache__
tests

./Plugins/Cognitive-Topology-Map/core/ctmv3/core:
activate.py
architecture_map.py
boot.py
cli.py
dot_init.py
fingerprint.py
__init__.py
orchestration.py
__pycache__
sovereign.py
templates
templates.py

./Plugins/Cognitive-Topology-Map/core/ctmv3/core/__pycache__:
activate.cpython-312.pyc
architecture_map.cpython-312.pyc
boot.cpython-312.pyc
cli.cpython-312.pyc
dot_init.cpython-312.pyc
fingerprint.cpython-312.pyc
__init__.cpython-312.pyc
orchestration.cpython-312.pyc
sovereign.cpython-312.pyc
templates.cpython-312.pyc

./Plugins/Cognitive-Topology-Map/core/ctmv3/core/templates:
AGENTS.md.template
ARCHITECTURE_MAP.md.template
CLAUDE.md.template
copilot-instructions.md.template
extras
FAILURE_GRAMMAR.md.template
PROVENANCE.md.template
topology-enforce.yml.template
TOPOLOGY.md.template

./Plugins/Cognitive-Topology-Map/core/ctmv3/core/templates/extras:
claude-settings.json.template
golden_paths.json.template
pre-commit-config.yaml.template
session_state.json.template

./Plugins/Cognitive-Topology-Map/core/ctmv3/__pycache__:
__init__.cpython-312.pyc
__main__.cpython-312.pyc

./Plugins/Cognitive-Topology-Map/core/ctmv3/tests:
__init__.py
__pycache__
test_engine.py

./Plugins/Cognitive-Topology-Map/core/ctmv3/tests/__pycache__:
__init__.cpython-312.pyc
test_engine.cpython-312.pyc
test_engine.cpython-312-pytest-9.0.3.pyc

./Plugins/Cognitive-Topology-Map/core/ctmv3.egg-info:
dependency_links.txt
entry_points.txt
PKG-INFO
SOURCES.txt
top_level.txt

./Plugins/Cognitive-Topology-Map/cursor:
install.sh
README.md
scripts

./Plugins/Cognitive-Topology-Map/cursor/scripts:
ctmv3-activate.sh
ctmv3-architecture-map.sh
ctmv3-boot.sh
ctmv3-chain.sh
ctmv3-dot-init.sh
ctmv3-fingerprint.sh
ctmv3-session-close.sh
ctmv3-sovereign-init.sh
ctmv3-status.sh
ctmv3-warm.sh

./Plugins/Cognitive-Topology-Map/docs:
AGENTS_ADDENDUM.md
ARCHITECTURE_MAP_TEMPLATE.md
BOOT_PROTOCOL.md
CONSTITUTION.md
DOT_TOPOLOGY.md
examples
EXPLANATION.md
FAILURE_GRAMMAR.md
GOLDEN_PATH.md
interfaces
PROVENANCE.md
SCHEMA_AUDIT.md
SKILL.md
TOPOLOGY.md

./Plugins/Cognitive-Topology-Map/docs/examples:
case_codebase_entry.md

./Plugins/Cognitive-Topology-Map/docs/interfaces:
orchestration.md
python.md

./Plugins/Cognitive-Topology-Map/examples:
cold-start-trace.md

./Plugins/Cognitive-Topology-Map/extras:
README.md
templates

./Plugins/Cognitive-Topology-Map/extras/templates:
AGENTS.example.md
CLAUDE.example.md
golden_paths.example.json
topology-enforce.example.yml

./Plugins/Cognitive-Topology-Map/gemini-cli:
ctmv3
install.sh
README.md

./Plugins/Cognitive-Topology-Map/gemini-cli/ctmv3:
commands
gemini-extension.json
GEMINI.md
scripts
skills

./Plugins/Cognitive-Topology-Map/gemini-cli/ctmv3/commands:
ctmv3

./Plugins/Cognitive-Topology-Map/gemini-cli/ctmv3/commands/ctmv3:
activate.toml
architecture-map.toml
boot.toml
dot-init.toml
session-close.toml
sovereign-init.toml
status.toml
warm.toml

./Plugins/Cognitive-Topology-Map/gemini-cli/ctmv3/scripts:
ctmv3-session-start.sh
ctmv3-wrap.sh

./Plugins/Cognitive-Topology-Map/gemini-cli/ctmv3/skills:
ctmv3

./Plugins/Cognitive-Topology-Map/gemini-cli/ctmv3/skills/ctmv3:
SKILL.md

./Plugins/Cognitive-Topology-Map/opencode:
agent
command
install.sh
opencode.json.fragment
plugin
README.md

./Plugins/Cognitive-Topology-Map/opencode/agent:
ctmv3-architect.md

./Plugins/Cognitive-Topology-Map/opencode/command:
ctmv3-activate.md
ctmv3-architecture-map.md
ctmv3-boot.md
ctmv3-dot-init.md
ctmv3-session-close.md
ctmv3-sovereign-init.md
ctmv3-status.md
ctmv3-warm.md

./Plugins/Cognitive-Topology-Map/opencode/plugin:
ctmv3.ts

./Plugins/Cognitive-Topology-Map/research:
RUNTIME_FORMATS.md

./Plugins/Cognitive-Topology-Map/tests:
run-all.sh
smoke.sh

./Plugins/Mentat:
5-22-2026-mentatv2-filetree.md
5-24-filetree-mentatv2-plugin.md
adapters
agents
AGENTS.md
bin
CHANGELOG.md
commands
CONTEXT.md
docs
evals
helpers
hooks
INSTALL.md
mcp.json
mcp_server
MEMORY.md
mentat-a-live-cognitive-substrate-for-claude-code.html
mentat-plugin.tar.gz
mentat-v2.zip
monitors
PLAN.md
README.md
schemas
scripts
skills
state_machine
style
webhook_engine
webhooks.json

./Plugins/Mentat/adapters:
codex
gemini
install_universal.sh
test_universal.sh

./Plugins/Mentat/adapters/codex:
AGENTS.snippet.md
config.toml.snippet
hooks
hooks.json
README.md

./Plugins/Mentat/adapters/codex/hooks:
_lib.py
_lib.py.backup_hook_schema_20260603_1530
permission_request.py
post_tool_use.py
pre_tool_use.py
__pycache__
session_start.py
stop.py
user_prompt_submit.py

./Plugins/Mentat/adapters/codex/hooks/__pycache__:
_lib.cpython-312.pyc
post_tool_use.cpython-312.pyc
pre_tool_use.cpython-312.pyc
session_start.cpython-312.pyc
stop.cpython-312.pyc

./Plugins/Mentat/adapters/gemini:
gemini-extension.json
GEMINI.snippet.md
hooks
README.md

./Plugins/Mentat/adapters/gemini/hooks:
after_agent.py
after_model.py
after_tool.py
before_agent.py
before_model.py
before_tool.py
before_tool_selection.py
hooks.json
_lib.py
notification.py
pre_compress.py
__pycache__
session_end.py
session_start.py

./Plugins/Mentat/adapters/gemini/hooks/__pycache__:
after_tool.cpython-312.pyc
before_tool.cpython-312.pyc
_lib.cpython-312.pyc
pre_compress.cpython-312.pyc

./Plugins/Mentat/agents:
mentat-cartographer.md
mentat-crucible.md
mentat-scribe.md
mentat-sentinel.md

./Plugins/Mentat/bin:
mentat
mentat-monitors
mentat-webhooks

./Plugins/Mentat/commands:
debrief.md
dispatch.md
drift-check.md
plan.md
qtable.md
README.md
reflect.md
scope.md
status.md
tail.md

./Plugins/Mentat/docs:
PROVENANCE.md
SOTA_CHECKLIST.md
STYLE.v2.md

./Plugins/Mentat/evals:
agents
harness.py
__init__.py
output
README.md
references
rubric.json
scenarios
scripts
SKILL.md

./Plugins/Mentat/evals/agents:
comparator.md
grader.md

./Plugins/Mentat/evals/output:
benchmark.html
benchmark.json
report.html
report.json

./Plugins/Mentat/evals/references:
schemas.md

./Plugins/Mentat/evals/scenarios:
__init__.py
persistence_recovery.py
predictive_routing.py
state_transitions.py
_types.py

./Plugins/Mentat/evals/scripts:
aggregate_benchmark.py
generate_report.py
__init__.py
run_eval.py

./Plugins/Mentat/helpers:
HELPERS.md
mentat-conductor.md
mentat-medic.md
mentat-quartermaster.md

./Plugins/Mentat/hooks:
hooks.json
_lib.py
_lib.py.backup_hook_schema_20260603_1530
post_compact.py
post_tool_use.py
pre_compact.py
pre_tool_use.py
__pycache__
session_start.py
stop_failure.py
stop.py
subagent_start.py
subagent_stop.py
user_prompt_submit.py

./Plugins/Mentat/hooks/__pycache__:
_lib.cpython-312.pyc

./Plugins/Mentat/mcp_server:
__init__.py
__main__.py

./Plugins/Mentat/monitors:
archivist.py
drift_watcher.py
entropy_watcher.py
README.md
test_smoke.py

./Plugins/Mentat/schemas:

./Plugins/Mentat/scripts:
integration_smoke.py

./Plugins/Mentat/skills:
mentat-debrief
mentat-dispatch
mentat-plan
mentat-reflect

./Plugins/Mentat/skills/mentat-debrief:
scripts
SKILL.md

./Plugins/Mentat/skills/mentat-debrief/scripts:
aggregate.py
__init__.py
__pycache__
render.py
template.html
test_smoke.py

./Plugins/Mentat/skills/mentat-debrief/scripts/__pycache__:
aggregate.cpython-312.pyc
__init__.cpython-312.pyc
render.cpython-312.pyc

./Plugins/Mentat/skills/mentat-dispatch:
SKILL.md

./Plugins/Mentat/skills/mentat-plan:
SKILL.md

./Plugins/Mentat/skills/mentat-reflect:
SKILL.md

./Plugins/Mentat/state_machine:
drift.py
__init__.py
insights.py
machine.py
__pycache__
q_table.py
session.py

./Plugins/Mentat/state_machine/__pycache__:
drift.cpython-312.pyc
__init__.cpython-312.pyc
insights.cpython-312.pyc
machine.cpython-312.pyc
q_table.cpython-312.pyc
session.cpython-312.pyc

./Plugins/Mentat/style:
PROVENANCE.md
SOTA_CHECKLIST.md
STYLE.v2.md

./Plugins/Mentat/webhook_engine:
config.py
dlq.py
emitter.py
envelope.py
__init__.py
test_smoke.py

./Registry:
plugins.yaml

./Scripts:

./Servers:
Muaddib

./Servers/Muaddib:
5-26-2026-muaddib-mcp-filetree.md
AGENTS.md
all_tools.json
ARCHITECTURE_MAP.md
ARCHITECTURE.md
claude_desktop_config.json
config_manager.py
CONTEXT.md
databus
golden_paths.json
golden_paths_meta.json
HOOK_BRIDGE.md
hook_executor.py
hooks_manifest.json
https_wrapper.py
intelligent_output_hook.py
manifest.json
mcp_api.py
mcp.json
mcp_server.py
MCP_SPEC.md
MEMORY.md
muadib
openapi_builder.py
README.md
requirements.txt
somnus_mcp_icon.png
sovereign_context_hook.py
sse_broadcaster.py
test_https_wrapper.py
tool_manifest.json
tools
webhook_engine.py
workflows-new.md

./Servers/Muaddib/databus:
__init__.py
openrouter_wrapper.py
openrouter.yaml
sovereign_openrouter.py

./Servers/Muaddib/muadib:
5-7-26-muadib.md
advanced_bridge.py
aeron_neural_memory.py
code_and_structured_modality.py
continual_learning_module.py
__init__.py
knowledge_graph_attention.py
memory_attention_classes.py
muaddib.py
neural_config.py
neural_memory_network.py
README.md
structured_data_modalities.py
tool_modality.py
unified_modality.py

./Servers/Muaddib/tools:
auto_tool_module.py
enhanced_code_analysis_tool.py
enhanced_web_tool.py
exoskeleton_tool.py
file_tool.py
__init__.py
lisan_al_gaib.py
memory_interconnect.py
memory_tool.py
meta_intelligence_engine.py
openrouter_agent_tool.py
openrouter_planner_tool.py
project_context_tool.py
session_manager_tool.py
shell_tool.py
thought_journal_tool.py
visual_tool.py
web_tool.py

./Skills:
academic-whitepaper-engine
codex-config-topology
constitutional-prompt-framework
document-omniscient
grok-build-configurator
somnus-intelligent-workspace
sovereign-skill-architect

./Skills/academic-whitepaper-engine:
assets
references
scripts
SKILL.md

./Skills/academic-whitepaper-engine/assets:
whitepaper-template.tex

./Skills/academic-whitepaper-engine/references:
citation-styles.md
code-validation.md
latex-preamble.tex
visual-examples.md

./Skills/academic-whitepaper-engine/scripts:
attachments
generate_metadata.py
md2tex.py
sart.py

./Skills/academic-whitepaper-engine/scripts/attachments:
md2tex (1).py
sart (1).py

./Skills/codex-config-topology:
agents
references
SKILL.backup_20260604_031221.md
SKILL.md

./Skills/codex-config-topology/agents:
openai.yaml

./Skills/codex-config-topology/references:
bb7-exo-loop.md
current-codex-surfaces-2026-06-04.md
doctrine-stack.md
examples.md
failure-grammar.md
host-surface.md
json-tool-output-hygiene.md
operator-control-plane.md
provenance.md
source
topology.md
windows-host-surface.md

./Skills/codex-config-topology/references/source:
AGENTS.md
AGENTS.override.md
default.rules
MCP_SPEC.md
OPSEC.md
STYLE.md
tool_manifest.json

./Skills/constitutional-prompt-framework:
agents
assets
CHANGELOG.md
examples
MANIFEST.md
package-manifest.json
README.md
references
RELEASE_NOTES.md
schemas
scripts
SKILL.md
tests

./Skills/constitutional-prompt-framework/agents:
openai.yaml

./Skills/constitutional-prompt-framework/assets:
single-file-agent-constitution-skeleton.md
templates

./Skills/constitutional-prompt-framework/assets/templates:
agent-constitution-full.md
audit-report-template.md
capability-dispatch-table.md
constitution-spec.example.json
intake-form.md
memory-policy-template.md
platform-binding-template.md
red-team-report-template.md
release-checklist.md
rewrite-plan-template.md

./Skills/constitutional-prompt-framework/examples:
example-agent-constitution.md
example-audit-report.md
example-rewrite-plan.md
rendered-from-spec.md

./Skills/constitutional-prompt-framework/references:
00-doc-chain.md
01-constitutional-prompt-theory.md
02-derivation-guide.md
03-layer-contracts.md
04-authority-and-governance.md
05-rules-of-engagement-patterns.md
06-operating-doctrine-library.md
07-persona-architecture.md
08-capability-dispatch.md
09-memory-continuity.md
10-platform-binding-matrix.md
11-security-privacy-safety.md
12-long-context-and-compaction.md
13-domain-ingestion-and-knowledge-modeling.md
14-output-contracts.md
15-audit-checklist.md
16-evaluation-rubric.md
17-red-team-suite.md
18-anti-patterns.md
19-rewrite-playbook.md
20-deployment-and-maintenance.md
21-interoperability-notes.md
22-glossary.md
23-schema-driven-authoring.md
24-failure-mode-atlas.md

./Skills/constitutional-prompt-framework/schemas:
audit-report.schema.json
constitution-spec.schema.json
skill-package.schema.json

./Skills/constitutional-prompt-framework/scripts:
constitution_linter.py
_cpf_common.py
__pycache__
render_constitution_from_spec.py
run_static_evals.py
score_constitution.py
validate_skill_package.py

./Skills/constitutional-prompt-framework/scripts/__pycache__:
_cpf_common.cpython-312.pyc

./Skills/constitutional-prompt-framework/tests:
eval_cases.yaml
fixtures
README.md

./Skills/constitutional-prompt-framework/tests/fixtures:
minimal_constitution_spec.json

./Skills/document-omniscient:
agents
references
SKILL.md

./Skills/document-omniscient/agents:
openai.yaml

./Skills/document-omniscient/references:
CLAUDE_PROJECT_SETUP.md
claude_tool_pack.md
codebase_omniscient_source.md
FAILURE_GRAMMAR.md
OUTPUT_CONTRACTS.md
TOOLING_PLAYBOOK.md
TOPOLOGY.md

./Skills/grok-build-configurator:
agents
assets
manifest.json
README.md
references
scripts
SKILL.md

./Skills/grok-build-configurator/agents:
AGENTS.md
openai.yaml

./Skills/grok-build-configurator/assets:
templates

./Skills/grok-build-configurator/assets/templates:
AGENTS.grok-project.md
config.ci-safe.toml
config.daily.toml
config.enterprise-oidc.toml
headless-ci-review.sh
hooks
pager.tui.toml
project.grok.config.mcp.toml
sandbox.toml

./Skills/grok-build-configurator/assets/templates/hooks:
git-gh-only

./Skills/grok-build-configurator/assets/templates/hooks/git-gh-only:
git-gh-only.json
git-gh-only.sh

./Skills/grok-build-configurator/references:
grok-build-command-cheatsheet.md
grok-build-configuration-field-guide.md
xai-docs

./Skills/grok-build-configurator/references/xai-docs:
01-getting-started.md
02-authentication.md
03-keyboard-shortcuts.md
04-slash-commands.md
05-configuration.md
06-theming.md
07-mcp-servers.md
08-skills.md
09-plugins.md
10-hooks.md
11-custom-models.md
12-project-rules.md
13-memory.md
14-headless-mode.md
15-agent-mode.md
16-subagents.md
17-sessions.md
18-sandbox.md
19-plan-mode.md
20-background-tasks.md
21-terminal-support.md
22-permissions-and-safety.md

./Skills/grok-build-configurator/scripts:
grok_build_doctor.py
install_codex_skill.sh
render_grok_config.py

./Skills/somnus-intelligent-workspace:
AGENTS.md
assets
{assets,casefiles,references,scripts}
casefiles
README.md
references
scripts
SKILL.md

./Skills/somnus-intelligent-workspace/assets:
ssds_sic_template.md

./Skills/somnus-intelligent-workspace/{assets,casefiles,references,scripts}:

./Skills/somnus-intelligent-workspace/casefiles:

./Skills/somnus-intelligent-workspace/references:
sovereign_doctrine.md
varys_strategic_substrate.md

./Skills/somnus-intelligent-workspace/scripts:
init_casefile.sh

./Skills/sovereign-skill-architect:
AGENTS_ADDENDUM.md
ARCHITECTURE_MAP_TEMPLATE.md
BOOT_PROTOCOL.md
case_codebase_entry.md
CONSTITUTION.md
DOT_TOPOLOGY.md
examples
FAILURE_GRAMMAR.md
interfaces
PROVENANCE.md
python.md
SKILL.md
sovereign-skill-operator.zip
TOPOLOGY.md

./Skills/sovereign-skill-architect/examples:
case_codebase_entry.md

./Skills/sovereign-skill-architect/interfaces:
python.md
