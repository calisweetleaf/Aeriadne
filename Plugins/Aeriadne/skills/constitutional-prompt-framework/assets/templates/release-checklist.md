# Release Checklist

Release:
Date:
Owner:

## Constitution checks

- [ ] Mission and identity are concrete.
- [ ] Authority hierarchy is explicit.
- [ ] Approval gates cover irreversible, costly, sensitive, and external actions.
- [ ] Hard ROE count is appropriate.
- [ ] Soft doctrine includes rationale and failure modes.
- [ ] Persona is mission-derived.
- [ ] Capability dispatch includes triggers, non-use, verification, approval, and fallback.
- [ ] Memory policy includes scope, threshold, update-vs-create, exclusions, and no-memory fallback.
- [ ] Domain model is structured and status-tagged.
- [ ] Output contracts are defined.
- [ ] Evaluation rubric and red-team probes are included.
- [ ] Living status footer is current.

## Portability checks

- [ ] No private tool names in portable sections.
- [ ] No secrets or credentials.
- [ ] No false memory, web, file, code, connector, or background-work claims.
- [ ] Platform-specific metadata is isolated.

## Package checks

- [ ] `SKILL.md` exists.
- [ ] Frontmatter includes `name` and `description`.
- [ ] Description is trigger-specific.
- [ ] Referenced files exist.
- [ ] Scripts are documented and safe.
- [ ] Validation script passes.
- [ ] Zip/package layout is correct.

## Acceptance

Overall score:
Critical findings:
High findings:
Red-team result:
Release decision: Ship | Hold | Revise
