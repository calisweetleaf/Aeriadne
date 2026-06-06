# BB7 EXO LOOP

Load this when the request is about per-turn orchestration, tool order, or how Codex should enter the MCP surface.

## Hard rule

After every user input, the first BB7 actions must be exoskeleton actions.

## Canonical order

1. `bb7_exo_bootstrap`
2. `bb7_exo_list_tool_categories`
3. `bb7_exo_category_specific_tools` for `exoskeleton` and task-relevant categories
4. `bb7_exo_route` or `bb7_exo_plan`
5. `bb7_journal_surface_relevant`
6. `bb7_journal_record_thought`
7. execute selected BB7 tools
8. `bb7_journal_add_outcome`
9. `bb7_exo_reflect`

## Why this matters

- exo establishes the active tool surface and reliability priors
- route or plan comes before execution so the task enters through the control plane, not through convenience calls
- journal comes after exo so reasoning is grounded in the active tool surface
- reflect closes the learning loop so priors and execution history update continuously

## Invalid entry examples

- starting with `bb7_terminal_run_command`
- starting with `bb7_read_file`
- starting with `bb7_memory_search`
- starting with `bb7_journal_record_thought`

Those may all be valid later, but they are not the first BB7 move.
