# HOST SURFACE

Use this reference when the request involves launch behavior, profiles, elevation, wrappers, npm-installed entrypoints, terminal authority, or command-permission surfaces.

## Host reasoning rules

1. Separate host launch behavior from Codex-internal behavior.
2. Determine the active host before reasoning from old assumptions.
3. Distinguish normal user profile from elevated or admin launch profile.
4. Treat npm resolution, wrappers, and aliases as first-class evidence.
5. Verify how doctrine files are injected into the session or startup chain.

## Surfaces to inspect

- `.codex` root and subfolders
- shell profile files for the active host and user scope
- alternate elevated-profile paths, if present
- wrapper scripts that call the Codex executable with local flags
- aliases or helper functions that mask the real binary invocation
- npm global bin resolution and any pinned wrapper around Codex
- environment variables that route startup docs or config roots
- shortcut or terminal profile definitions that choose the entry command
- `default.rules` when command authority is in scope
- `tool_manifest.json` when BB7 tool coverage or naming is in scope

## Decision rule

If the requested behavior changes how Codex launches, what it loads at session start, or which command surface becomes available, inspect the host layer first.

If the requested behavior changes policy or control-plane behavior after Codex is already active, inspect `.codex` and the injected doctrine stack first.

If the request is about what BB7 is allowed or expected to do, inspect both the host layer and the policy surfaces.

## Common traps

- solving only the easiest profile to read instead of the one actually used
- assuming Linux when the current request is about a Windows wrapper, or vice versa
- patching the raw executable path while the user launches through a wrapper
- assuming environment variables set in one shell exist in the canonical launch path
- claiming terminal restrictions or freedoms without reading the rules file
