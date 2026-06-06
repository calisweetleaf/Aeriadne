# 20 - Deployment and Maintenance

A constitution is a living artifact. Deployment and maintenance are part of the design.

## Versioning

Use semantic versioning or date-based versioning.

- Major: mission, authority, platform, or capability changes.
- Minor: new doctrine, output contracts, domain sections, or evals.
- Patch: wording fixes, examples, small clarifications.

## Changelog entries

Each changelog entry should include:

- Date.
- Version.
- Changed sections.
- Reason.
- Migration notes if behavior changes.
- Known risks.

## Living status footer

```markdown
## Living status
Version: [version]
Last updated: [date]
Owner: [owner]
Target platform: [portable or specific]
Source materials: [docs or conversations]
Known risks: [list]
Pending revisions: [list]
Changelog: [path or inline]
```

## Release checklist

- Mission and identity verified.
- Authority hierarchy verified.
- Hard ROE count between 5 and 12 unless justified.
- Capability dispatch present.
- Memory policy present or no-memory fallback present.
- Platform-specific claims verified.
- Private leakage check complete.
- Output contracts present.
- Evaluation rubric score recorded.
- Red-team probes run or selected.
- Changelog updated.
- Package validated if shipping as skill.

## Maintenance triggers

Revise the constitution when:

- Target platform capabilities change.
- User mission changes.
- A red-team probe fails.
- A repeated behavior failure appears.
- Memory or data sources change.
- New legal, safety, privacy, or business constraints apply.
- The prompt grows through patches and loses coherence.

## Drift review

A drift review asks:

- What behavior changed since last version?
- Which failures repeated?
- Which sections are patched too heavily?
- Which assumptions expired?
- Which capabilities are now available or unavailable?
- Which examples are stale?

## Deprecation pattern

Do not silently delete important doctrine. Deprecate with reason:

```markdown
Deprecated [date]: [old rule]
Reason: [why removed]
Replacement: [new rule]
```

## Deployment note template

```markdown
# Deployment notes
Target platform:
Install location:
Capabilities verified:
Capabilities unavailable:
Required user setup:
Known limitations:
Validation performed:
Rollback path:
```

## Package validation

For skill packages, verify:

- Root has `SKILL.md`.
- Frontmatter has valid `name` and `description`.
- Name is lowercase hyphenated.
- Description is trigger-specific.
- References listed in `SKILL.md` exist.
- Scripts are deterministic and documented.
- No secrets are included.
- Zip contains the intended root layout.
