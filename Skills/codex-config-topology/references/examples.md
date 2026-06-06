# EXAMPLES

## Example 1: Enforce first-mission doctrine loading

Request pattern: "make codex always read my injected stack on first mission"

Response pattern:
- identify where startup or session injection is controlled
- place the load order in the owning surface
- preserve the separate roles of `AGENTS.md`, override, `OPSEC.md`, `STYLE.md`, and `MCP_SPEC.md`
- explain which parts change at chat start versus per-turn execution

## Example 2: Make exo the first BB7 move

Request pattern: "after user input, exo must always be first"

Response pattern:
- map the current per-turn chain
- identify the first BB7 tool currently being called
- patch the owning surface so exo bootstrap and routing happen first
- verify journal and reflect still bracket execution correctly

## Example 3: Reason about full terminal posture

Request pattern: "I want full terminal permissions"

Response pattern:
- inspect `default.rules`, terminal tools, wrappers, and host runtime
- distinguish intended broad authority from hard host or policy boundaries
- recommend the narrowest edit that preserves operator intent without misrepresenting actual authority
