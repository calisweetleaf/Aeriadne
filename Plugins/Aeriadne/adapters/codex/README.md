# Codex Adapter — Aeriadne

## Goal

Expose the bundled `constitutional-prompt-framework` and `aeriadne-marketplace-operator` skills through a Codex plugin namespace while keeping the direct authoring skill intact.

## Canonical source

```text
/home/daeron/Repositories/Somnus-Intellligence-Stack/plugins/Aeriadne
```

## Expected exposure after local install

```text
aeriadne:constitutional-prompt-framework
aeriadne:aeriadne-marketplace-operator
```

## Install pattern to mirror

Use the already-proven `codex-config-topology@local` pattern, but do not restore deleted legacy descriptors:

```text
Somnus-Intellligence-Stack source package -> local marketplace package -> ~/.codex/plugins/cache/local/aeriadne/1.0.0 -> config.toml plugin entry -> prompt-input evidence
```

## Verification commands

```bash
python3 -m json.tool plugin.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 scripts/validate_package.py .
python3 skills/constitutional-prompt-framework/scripts/validate_skill_package.py skills/constitutional-prompt-framework
codex plugin list | grep aeriadne
codex debug prompt-input 'probe $aeriadne plugin visibility'
```

## Boundary

Do not remove `/home/daeron/.codex/skills/custom/constitutional-prompt-framework` during install validation. Direct authoring and plugin distribution can coexist. Do not install legacy `cpf-plugin-ariadne` beside `aeriadne` unless duplicate CPF exposure is explicitly desired.
