# WINDOWS HOST SURFACE

Use this reference when the request involves Windows launch behavior, profiles, elevation, wrappers, or npm-installed entrypoints.

## Windows-first reasoning rules

1. Separate host launch behavior from Codex-internal behavior.
2. Distinguish normal user profile from elevated or admin launch profile.
3. Treat shortcut targets, shell invocation flags, and wrapper scripts as first-class evidence.
4. Verify how the npm-installed Codex executable is resolved on the current host.

## Common host surfaces to inspect

- PowerShell profile files for the active host and user scope
- alternate elevated-profile paths, if the user maintains one
- wrapper scripts that call the Codex executable with local flags
- aliases or helper functions that mask the real binary invocation
- environment variables that route startup documents or config roots
- shortcut or terminal profile definitions that choose the entry command

## Decision rule

If the requested behavior changes how Codex launches, what it loads at session start, or which command surface becomes available, inspect the host layer first.

If the requested behavior changes only policy or defaults after Codex is already active, inspect `.codex` first.

## Windows-specific traps

- solving only the profile that is easiest to read instead of the one actually used
- patching the raw executable path while the user launches through a wrapper
- assuming environment variables set in one shell exist in the canonical launch path
- forgetting that admin and non-admin launches may route through different profiles or wrappers
