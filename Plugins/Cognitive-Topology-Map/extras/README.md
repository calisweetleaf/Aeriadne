# extras/

This directory contains optional reference material for operators who want to extend or
customize CTMv3. Nothing here is part of the canonical engine output. The engine writes
what it writes; this directory shows what those outputs look like after an operator has
filled them in for a real project.

## What is here

`extras/templates/` — Fully populated example artifacts. These are "what good looks like"
references, not scaffolding templates. Each file is a realistic, completed version of
the corresponding artifact the engine scaffolds during a cold-start activation.

| File | What it shows |
|------|--------------|
| `AGENTS.example.md` | A completed AGENTS.md for a hypothetical Python ML service |
| `golden_paths.example.json` | A populated `.sovereign/golden_paths.json` with real entries |
| `topology-enforce.example.yml` | A populated topology-enforce CI workflow configured for a specific repo |
| `CLAUDE.example.md` | A completed CLAUDE.md for the same hypothetical repo |

## How to use these

Read them as references before filling in your own scaffolded artifacts. They show:

- How granular the LBC definitions should be in TOPOLOGY.md (not vague, not encyclopedic)
- What golden path chain entries look like in practice
- How to configure the topology-enforce workflow for a specific project name and file set
- What a CLAUDE.md session history looks like after a few sessions

Do not copy these files directly into your project. They contain fake project names and
imaginary file paths. Use them to calibrate your writing, then write your own.

## What is not here

These are not part of the engine's template system. Editing files in `extras/` does not
affect what `python3 -m ctmv3 activate` produces. The engine's templates live in
`core/ctmv3/core/templates/`. See CONTRIBUTING.md for how to add or modify engine templates.
