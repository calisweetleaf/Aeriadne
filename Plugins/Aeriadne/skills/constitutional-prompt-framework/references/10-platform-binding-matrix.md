# 10 - Platform Binding Matrix

Use this document when adapting a constitution to a target environment. Platform capabilities change, so treat this as a binding method, not a static guarantee.

## Binding principles

1. Start portable.
2. Identify actual target capabilities.
3. Replace abstract capabilities with concrete tool names only where needed.
4. Preserve graceful degradation.
5. Do not claim unavailable memory, browsing, code execution, file access, connectors, or background execution.
6. Keep platform-specific metadata separate from the constitution when possible.

## Portable baseline

Portable language:

- `available tools`
- `file-reading capability`
- `workspace`
- `web or research capability`
- `code execution capability`
- `connectors`
- `memory`
- `subagents or reviewers`
- `approval gate`
- `handoff artifact`

Avoid local runtime names in portable outputs.

## ChatGPT-style web agent

Likely strengths:

- Conversational interaction.
- File analysis when files are provided.
- Web retrieval when enabled.
- Artifact generation depending on environment.
- Memory depending on user settings and platform availability.

Binding guidance:

- Write memory as conditional unless durable memory is explicitly enabled.
- Do not promise future background work unless automation capability exists and is invoked.
- Use citation protocols for web-based claims.
- Add user-facing clarification rules because the interaction is direct.

## Codex-style coding agent

Likely strengths:

- Repository inspection.
- File editing.
- Tests and command execution.
- Skill activation.
- Patch generation.

Binding guidance:

- Require file inspection before code changes.
- Require tests or static validation when feasible.
- Gate destructive commands and broad rewrites.
- Include changelog, diff summary, and validation output.
- Use `agents/openai.yaml` for OpenAI UI metadata when packaging a skill.

## Claude or general skill-capable agent

Likely strengths:

- SKILL.md-style folder packages.
- References, assets, and scripts.
- Strong long-context reasoning depending on model.

Binding guidance:

- Keep core format simple: folder with `SKILL.md` and optional resources.
- Avoid target-specific metadata unless isolated.
- Use references for heavy doctrine.

## GitHub Copilot or IDE agent

Likely strengths:

- Code context.
- Editor integration.
- Repository-aware assistance.

Binding guidance:

- Name should be lowercase hyphenated and match folder if required by target.
- Make description trigger-specific.
- Add codebase inspection and test protocols.
- Avoid assuming web, memory, or external connectors.

## Cursor or local IDE agent

Likely strengths:

- Project files.
- Local code context.
- Manual rule files or imported skills depending on version.

Binding guidance:

- Favor repository-local instructions.
- Keep local commands conditional.
- Add no-destructive-action gates.
- Include manual fallback if skill discovery is not automatic.

## API agent

Likely strengths:

- Explicit tool schemas.
- Application-controlled memory and orchestration.
- Deterministic wrapper logic.

Binding guidance:

- Separate model instructions from application policy.
- Do not encode secrets in prompts.
- Route irreversible actions through server-side approval.
- Keep memory writes outside the model unless explicitly exposed as a tool.
- Define tool preconditions and postconditions.

## Local CLI agent

Likely strengths:

- Shell commands.
- File system access.
- Scripts and tests.

Binding guidance:

- Add command safety rules.
- Require dry runs for destructive operations.
- Prefer standard library scripts for portability.
- Do not assume network access.

## Multi-agent runtime

Likely strengths:

- Delegation.
- Parallel workstreams.
- Specialist review.

Binding guidance:

- Define subagent roles and context boundaries.
- Require synthesis and conflict reconciliation.
- Do not let subagents override authority hierarchy.
- Add handoff formats.

## Platform binding table

| Feature | Portable wording | Platform-bound wording | Risk if wrong |
|---|---|---|---|
| Files | `file-reading capability` | specific file tool | False inspection claims |
| Web | `web/research capability` | browser or search tool | Stale facts |
| Code | `code execution capability` | shell, notebook, test runner | Untested claims |
| Memory | `durable memory if available` | named memory system | False persistence |
| Connectors | `connected private sources` | Gmail, Drive, Calendar, finance, CRM | Privacy and authorization risk |
| Subagents | `independent reviewer` | named subagent runtime | Fake delegation |
| External actions | `write/action capability` | email send, publish, deploy | Unauthorized impact |

## Porting procedure

1. Mark every capability claim in the source prompt.
2. Classify each as portable, target-specific, or false.
3. Replace false claims with conditional behavior.
4. Move target-specific metadata outside general doctrine when possible.
5. Add platform-specific output and validation protocols.
6. Run audit for leakage and false affordances.

## Platform leakage checklist

Flag:

- Local code names.
- Private folder paths.
- Tool names unknown to target platform.
- Hidden infrastructure descriptions.
- Secrets or credentials.
- Assumptions about memory, browsing, or write access.
- UI-specific commands in a portable constitution.
- Vendor-specific syntax not requested by the user.
