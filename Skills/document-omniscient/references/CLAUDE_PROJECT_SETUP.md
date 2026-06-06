# CLAUDE PROJECT SETUP

**Purpose**: Make this skill usable inside Claude Projects on claude.ai without MCP.

## Recommended deployment

1. Create a Claude Project.
2. Turn on extended thinking for the chat or workflow when available.
3. Upload `SKILL.md` plus the files in `references/` into project knowledge.
4. Paste the body of `SKILL.md` into Project Instructions if you want the strongest behavioral steering.
5. Invoke explicitly with `use the xyz skill` or `use the document-omniscient skill`.

## Recommended knowledge files

Minimum upload set:
- `SKILL.md`
- `references/TOPOLOGY.md`
- `references/TOOLING_PLAYBOOK.md`
- `references/FAILURE_GRAMMAR.md`
- `references/OUTPUT_CONTRACTS.md`
- `references/claude_tool_pack.md`

Optional but useful:
- `references/codebase_omniscient_source.md`

## Operational notes

- Use Projects rather than one-off chats when the corpus is large or long-lived.
- If the project becomes retrieval-backed, be explicit about filenames when asking follow-up questions.
- If mobile lacks a needed file-creation feature, run the heavy analysis on web and use mobile for follow-up questioning or review.
- If memory is unavailable, ask for `MEMORY_CANDIDATES.md` instead of a direct memory write.
