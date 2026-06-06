// CTMv3 opencode plugin
//
// Hook: session.created -> run `ctmv3 boot --json` so the agent has the signal
// inventory in context before the first message is processed.
//
// Contract note: this file targets the plugin API as documented at
// https://opencode.ai/docs/plugins (as of 2026-05). The canonical shape is a
// named-export async function receiving { project, client, $, directory, worktree }
// and returning an object mapping event name strings directly to handler functions.
// The `Plugin` type is imported for type safety; if @opencode-ai/plugin is not
// installed, remove the import and the `: Plugin` annotation — the runtime does
// not require the type annotation to load the plugin.
//
// SCHEMA_AUDIT.md note: the event handler is registered as "session.created"
// directly (per RUNTIME_FORMATS.md Section 4.3 canonical pattern). The prior
// version used a generic `event:` key with internal type filtering — that
// pattern is not in the canonical API spec.

import type { Plugin } from "@opencode-ai/plugin"

export const CTMv3Plugin: Plugin = async ({ worktree, $ }) => {
  return {
    "session.created": async () => {
      try {
        // Run the boot discovery so the session context includes the signal
        // inventory. Failures are silent: ctmv3 may not be installed, or the
        // project root may not be a repo. Either way, the session should not
        // be blocked.
        await $`python3 -m ctmv3 boot --json --project-root ${worktree} 2>/dev/null`
      } catch {
        // ctmv3 not installed or discovery failed — proceed silently.
        // The user can install the engine and run /ctmv3-boot manually.
      }
    },
  }
}

export default CTMv3Plugin
