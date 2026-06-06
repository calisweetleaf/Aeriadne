# 21 - Interoperability Notes

This reference helps keep skills and constitutions portable across agents and platforms.

## Common skill shape

A portable skill is usually a folder containing:

- `SKILL.md`: required metadata and instructions.
- `references/`: optional docs loaded when needed.
- `assets/`: optional templates or resources.
- `scripts/`: optional deterministic helpers.
- `agents/`: optional platform-specific metadata.

The most portable core is `SKILL.md` with YAML frontmatter containing `name` and `description`, followed by Markdown instructions.

## Frontmatter guidance

Name:

- Lowercase.
- Hyphenated.
- Short.
- Stable.
- No spaces, slashes, colons, or private prefixes.

Description:

- Front-load trigger terms.
- Say when to use the skill.
- Say what it creates or audits.
- Avoid vague marketing language.
- Stay concise enough for skill lists.

## Progressive disclosure

Skill systems often load metadata first and full instructions only when the skill is selected. This means the description is the trigger blade. Make it specific.

Heavy doctrine belongs in references when:

- It is needed only for substantial tasks.
- It would crowd the entrypoint.
- It is a library rather than a direct workflow.

However, the entrypoint must still contain enough process to run the skill even if references are not loaded.

## Scripts

Scripts should be included only when they provide deterministic value:

- Validation.
- Linting.
- Scoring.
- File generation.
- Format conversion.

Avoid scripts that require secrets, external services, brittle dependencies, or unsafe local side effects.

## Cross-platform risk table

| Risk | Cause | Mitigation |
|---|---|---|
| Skill not discovered | Invalid name or misplaced file | Match target platform layout and naming |
| Wrong invocation | Vague description | Add trigger terms and scope |
| False capability | Platform lacks memory/tool/web | Use conditional protocols |
| Security scan flags | Suspicious scripts or secrets | Keep scripts deterministic and inspectable |
| Context bloat | Too much in entry SKILL.md | Use references and routing |
| Vendor lock | Platform-specific commands everywhere | Isolate bindings |

## Packaging guidance

- Keep package root clean.
- Include `README.md`, `MANIFEST.md`, and `CHANGELOG.md` for humans.
- Keep platform-specific metadata in `agents/`.
- Keep templates in `assets/templates/`.
- Keep tests in `tests/`.
- Validate before zipping.

## Portable wording replacements

| Avoid in portable prompt | Use instead |
|---|---|
| exact local tool name | available [capability] |
| exact private path | project workspace or authorized source |
| memory will save | if durable memory is available |
| browse now | use web/research capability when current evidence matters |
| run shell command | use available code execution or test capability |
| send email | prepare external message; send only if write capability and approval exist |

## Interoperability audit questions

- Can the prompt run without vendor-specific commands?
- Are platform-specific pieces isolated?
- Does the package use standard folder names?
- Is the description trigger-specific?
- Are scripts optional and safe to inspect?
- Does it avoid secrets and local-only assumptions?
