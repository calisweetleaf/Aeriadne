# CLAUDE.md — rosemary-distill

**For Claude Code sessions in this repository.**

---

## What this repo is

Rosemary-distill is the distillation pipeline for the Rosemary consciousness substrate.
It ingests model weights from the Assimilator output, runs a frequency-based distillation
pass, and writes compressed representations to `.distill/checkpoints/`. It is not a
training system. It does not update weights. It reads and compresses.

The constraint stack is Ryzen 5 2400G / 12GB RAM / no GPU. Every design decision must be
evaluated against this. If a solution requires more than 10GB resident memory or a GPU,
it is not a valid primary implementation.

---

## Operational constraints

I follow the CONSTITUTION.md posture: Integration > Implementation. Before writing new
code, I check whether a production module already solves the problem. The skills are in
`.codex/skills/`. If one applies, I use it.

I do not touch `src/training/` in this session. That directory has its own AGENTS.md and
its own session state. Cross-directory work requires explicit operator instruction.

I do not overwrite `manifest.json`. It is the Somnus snapshot anchor.

I do not install new packages. If a solution requires a new package, I flag it and ask.

---

## Session history

### 2026-05-18 — Warm session (Claude Code)

- Task: Add file:line anchors to ARCHITECTURE_MAP.md branch C (tokenizer node)
- Outcome: Completed. Updated ARCHITECTURE_MAP.md with anchors to `src/tokenizer/bpe.py:88`
  and `src/tokenizer/vocab.py:34`.
- Topology drift: yes (ARCHITECTURE_MAP.md changed)
- Fingerprint updated: yes
- Next: Test the warm-start entry in the next session to confirm the new branch reads correctly.

### 2026-05-14 — Warm session (Claude Code)

- Task: Integrate Assimilator v3 wrapper into `src/distill/pipeline.py`
- Outcome: Completed. The Assimilator's public API surface changed in v3 — the
  `extract_weights()` call now returns a generator, not a list. The pipeline's integration
  point at `pipeline.py:214` was updated to handle both for backwards compatibility during
  the transition window. See PROVENANCE.md for the full integration note.
- Topology drift: no
- Next: Run end-to-end smoke test once the Assimilator v3 deployment lands.

### 2026-05-10 — Cold-start session (Claude Code)

- Task: Initial CTMv3 activation; fill TOPOLOGY.md LBC sections
- Outcome: All four LBC sections filled. Graveyard seeded with the two failed approaches
  (async pipeline, direct extractor invocation). AGENTS.md written with project-specific
  posture. arch map has ROOT node and three branches; file anchors are stubs — fill in
  next warm session.
- Topology drift: no (initial scaffold)
- Next: Add file:line anchors to ARCHITECTURE_MAP.md. Anchor at minimum: pipeline.py
  entry point, extractor.py public API, state_manager.py lock acquisition.

---

## Quick reference

| Thing | Where |
|-------|-------|
| Pipeline entry point | `src/distill/pipeline.py:run()` |
| Checkpoint writer | `src/distill/writer.py:CheckpointWriter.write()` |
| Session state | `.sovereign/session_state.json` |
| Fingerprint | `.sovereign/topology_fingerprint.txt` |
| Skills | `.codex/skills/` |
| Graveyard (rejected paths) | `PROVENANCE.md` → Graveyard section |
| Warm start validity | `.sovereign/session_state.json` → `warm_start_valid` |
