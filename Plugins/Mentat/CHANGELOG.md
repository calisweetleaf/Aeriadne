# Mentat Plugin — Distribution Changelog

---

## Release stamp — 2026-05-11 (plugin v0.1.0 tarball)

**Tarball:** `mentat-plugin.tar.gz`
**Size:** 186,843 bytes (182.4 KB)
**sha256:** `9605621f5f08cad279b535c6cfc1d87691fe669e6e97eaf143fd62f63f59f897`
**sha512:** `c8c137c0cb180bff3cd7621de2709cb36d92cd6c1c158babdff287659838d2a3e22ad3cc91dd8c8cc2c1b3b52a9aba980973e6430933dfd410ce216f359409cb`

### What changed in this build (relative to previous tarball)

- `hooks/hooks.json` — patched to CC-required schema: added `"description"` / `"hooks"` wrapper (11 event types, all wired).
- `docs/` directory added inside `plugin/` — `STYLE.v2.md`, `SOTA_CHECKLIST.md`, `PROVENANCE.md`.
- `webhooks.json` — default endpoint updated from `http://localhost:4000` to `https://localhost:8443/events`.
- `monitors/monitors.json` — per the operator's intent, this file should be removed (CC 2.1.126 does not support that schema yet). However, the file is still present on disk at `plugin/monitors/monitors.json` and ships in this tarball. The operator should delete the file from the source tree and rebuild before the next public distribution. The file is dormant — CC will ignore or reject it, but it will not break the install.

### Smoke result

49 pass / 0 fail / 0 skip (all 49 checks green)

Subsystems exercised: state_machine compile (6), hooks compile (11), mcp_server compile (1), CLI end-to-end, FSA end-to-end, drift detection end-to-end, webhook_engine smoke + compile (6), evals compile + dry-run (6), debrief smoke + compile (3), monitors smoke + compile (4), adapters compile (9).

### LOC summary (Python only)

| Subsystem                        | LOC  |
|----------------------------------|------|
| state_machine                    |  696 |
| hooks                            |  920 |
| webhook_engine                   |  971 |
| evals                            | 2282 |
| monitors                         |  817 |
| adapters/codex                   |  822 |
| adapters/gemini                  | 1066 |
| skills/mentat-debrief/scripts    | 1567 |
| mcp_server                       |  378 |
| scripts                          |  392 |
| **Total**                        | **9,911** |

### Manifest (plugin.json)

- name: `mentat`
- version: `0.1.0`
- description: present (177 chars)
- license: `MIT`
- author: Daeron Blackfyre / Somnus-Sovereign-Systems

### Note on version

`plugin.json` records `v0.1.0`. `plugin/CHANGELOG.md` describes a v0.2.0 in-progress ship. The manifest was not modified (source files are not touched by the packaging step). The operator should bump `plugin.json` to `v0.2.0` and rebuild before the next public distribution.

### Helpers (outside plugin/)

The `helpers/` directory (`mentat-conductor.md`, `mentat-medic.md`, `mentat-quartermaster.md`, `HELPERS.md`) is intentionally outside `plugin/` and is NOT included in the tarball. These agent definition files install separately to `~/.claude/agents/`, not inside the plugin tree. They are maintained alongside the plugin at `/home/daeron/.claude/plugins/mentat-plugin/helpers/`.

### Install

```bash
tar -xzf mentat-plugin.tar.gz -C ~/.claude/plugins/
mv ~/.claude/plugins/plugin ~/.claude/plugins/mentat
mv ~/.claude/plugins/mentat/mcp.json ~/.claude/plugins/mentat/.mcp.json
claude plugin marketplace add file://$HOME/.claude/plugins/mentat
```

Install helpers separately:

```bash
cp /path/to/helpers/*.md ~/.claude/agents/
```
