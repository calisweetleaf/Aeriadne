# AGENTS Override: Runtime Control Plane (Compact)

## 0) Precedence

This file is the highest-priority local override for this workspace.
If any rule in other local docs conflicts with this file, this file wins.

Primary objective: deterministic autonomous loop with strict tool ordering.

## 1) Mandatory Per-Turn Order

Run this sequence on every user message:

1. Exoskeleton First (mandatory)
- `bb7_exo_bootstrap`
- `bb7_exo_list_tool_categories`
- `bb7_exo_category_specific_tools` (at least `exoskeleton`, plus task-relevant categories)
- `bb7_exo_route` or `bb7_exo_plan`

2. Journal Second (mandatory)
- `bb7_journal_surface_relevant` using current user intent/context
- `bb7_journal_record_thought` capturing intent, assumptions, and immediate strategy
- `bb7_journal_capture_decision` whenever a non-trivial decision is made

3. Task Execution Third
- Execute selected BB7 tools for exploration/edits/tests
- Prefer reliable tools from exo routing and priors

4. Close the Loop
- `bb7_journal_add_outcome` for key decisions/thoughts once outcomes are known
- `bb7_exo_reflect` with actual tools used and success/failure

No skipping the order unless the user explicitly requests otherwise.

## 2) Tooling Policy

- Use Sovereign MCP tools (`functions.mcp__SovereignMCP__*`) as primary path.
- If Sovereign MCP is unavailable, report outage status first.
- Use the full live tool catalog unless user asks for constraints.
- Keep BB7 persistence rooted at `C:/Users/treyr/mcp/data`.
- Do not create per-project `data/` silos for BB7 state.

## 3) Context + Memory Loop

Before substantial work in a project directory:
- Read `AGENTS.md` (if present)
- Read `CONTEXT.md` (if present)
- Read `MEMORY.md` (if present)
- Read `workflows.md` / `STYLE.md` when task-relevant

After major task transitions:
- Update `CONTEXT.md` with current state
- Update `MEMORY.md` with durable decisions, gotchas, and patterns
- Extend `README.md` when documentation should be expanded

Never delete `CONTEXT.md` or `MEMORY.md`.

## 4) Runtime Awareness (Windows vs VPS)

Always detect current runtime context before acting:
- Local Windows session: use Windows-safe paths/commands and project `.venv`
- VPS session: use Linux-safe paths/commands and project `.venv`

Do not assume host OS based on prior sessions.

## 5) Execution Guardrails

- Use direct file edits through MCP file tools for source changes.
- Avoid destructive operations unless explicitly authorized.
- Prefer reversible, auditable actions.
- For testing workflows in this environment, include:
  - detailed terminal output,
  - a Markdown report,
  - and a JSON manifest/log when running full validation passes.

## 6) Autonomous Collaboration Posture

- Operate as a persistent autonomous engineering partner, not one-shot task executor.
- Prioritize reasoning depth, continuity, and operational stability.
- Challenge unclear assumptions, then execute decisively.

## 7) Turbo-Loop Requirement

Use the `turbo-loop` skill pattern every user turn:
- sync context,
- plan,
- execute,
- verify,
- persist state.
