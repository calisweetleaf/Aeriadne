# Changelog

## 10.0.0 - 2026-06-05

Initial v10 release.

### Added

- Rebuilt `SKILL.md` as a mode-selecting operational router for new builds, audits, hardening, patching, platform binding, and prompt-to-skill conversion.
- Added a chained reference library with 23 numbered documents covering theory, derivation, layers, authority, ROE, doctrine, persona, capability dispatch, memory, platform binding, security, long-context survival, domain ingestion, outputs, audits, scoring, red-team probes, anti-patterns, rewrites, deployment, interoperability, and glossary.
- Added full templates for agent constitutions, audit reports, rewrite plans, platform bindings, memory policies, capability dispatch, intake, red-team reports, and releases.
- Added deterministic helper scripts for package validation, constitution linting, rubric scoring, and static evals.
- Added examples and test fixtures.

### Hardened

- Frontmatter description is explicit enough for automatic invocation while staying within typical metadata limits.
- Package avoids claiming unavailable memory, tools, browsing, write access, subagents, or platform-specific behavior.
- Platform-specific binding is isolated into dedicated docs rather than smeared through general instructions.
- Security and privacy constraints are first-class layers, not an afterthought.

### Known limits

- Static scripts are heuristic and cannot replace human or model-based review.
- The framework can preserve and structure domain doctrine, but it cannot verify private facts unless the user provides evidence or a connected source is available.
- Platform capabilities change. Use `references/10-platform-binding-matrix.md` and current target platform docs before final deployment.
