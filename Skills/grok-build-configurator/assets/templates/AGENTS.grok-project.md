# Grok Project Rules

## Operating mode

- Treat this repository as the source of truth.
- Read existing patterns before changing code.
- Prefer small, reviewable patches.
- Do not introduce new dependencies without explaining why.
- Before editing security-sensitive, auth, payment, infra, or deletion logic, state the intended change first.

## Build and validation

Replace these placeholders with real commands for the repo:

- Install: `TODO`
- Lint: `TODO`
- Typecheck: `TODO`
- Test: `TODO`
- Build: `TODO`

When possible, run the narrowest validation that proves the change, then the broader suite if the change is cross-cutting.

## Style

- Follow existing file organization and naming.
- Keep public APIs stable unless the task asks for an API change.
- Prefer explicit errors over silent failure.
- Add tests for behavior changes.

## Safety

- Never print secrets, tokens, credentials, or private keys.
- Never modify `.env`, key files, deployment secrets, or auth material unless explicitly requested.
- Do not run destructive commands such as `rm -rf`, `git reset --hard`, or force pushes without explicit approval.
