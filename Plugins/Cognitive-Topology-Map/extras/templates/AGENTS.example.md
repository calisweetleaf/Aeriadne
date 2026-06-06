# AGENTS.md — Rosemary Distillation Engine

**Project**: rosemary-distill  
**Activated**: 2026-04-12  
**Last encoded**: 2026-05-18 by Claude Code (warm session)  
**Topology hash**: sha256:e3b4a7f1c92d8...  

---

## Operational Posture

I am working in a production Python ML system. The primary goal of any session is to
advance distillation throughput without breaking the fingerprint invariant. I do not
refactor working code unless I have explicit instruction. I do not add dependencies.

Before any write, I check whether a production module that solves the problem already
exists in `.codex/skills/`. If one exists, I use it.

---

## Load-Bearing Concepts (summary from TOPOLOGY.md)

**Session state**: Encoded in `.sovereign/session_state.json`. The `warm_start_valid` flag
is the decision gate for warm vs cold entry. If it is false, I treat the session as cold
regardless of artifact presence.

**Fingerprint invariant**: `TOPOLOGY.md` and `ARCHITECTURE_MAP.md` are the source of truth.
The hash in `.sovereign/topology_fingerprint.txt` must match after any session that touches
these files. Mismatch is not an error — it is a signal.

**Distillation pipeline**: `src/distill/pipeline.py` owns the full extraction chain. All
entry points route through `pipeline.run()`. There is no shortcut path to `extractor.py`
that bypasses the pipeline's validation layer. I attempted a shortcut in the session of
2026-04-28 and the graveyard in PROVENANCE.md records why it failed.

**Checkpoint format**: `.ckpt` files are Safetensors, not raw PyTorch. Reading them with
`torch.load()` will silently load wrong data. Always use `safetensors.torch.load_file()`.

---

## What I do not do here

- I do not install new pip packages. The constraint stack is Ryzen 5 2400G / 12GB RAM /
  no GPU. Any solution that requires a GPU is invalid as a primary implementation.
- I do not touch `src/training/` unless the task explicitly names it. That directory owns
  its own session state and has a separate AGENTS.md at `src/training/AGENTS.md`.
- I do not overwrite `manifest.json`. It is the Somnus snapshot anchor. If a task requires
  updating the manifest, I flag it and ask before proceeding.

---

## Rejected Paths (from PROVENANCE.md Graveyard)

**Direct extractor invocation** (rejected 2026-04-28): Bypassing `pipeline.run()` to call
`extractor.extract()` directly produces files in the wrong format. The pipeline normalizes
encoding and validates shape before writing. The extractor does not. Result: 12GB of
wrong-format checkpoints that had to be deleted. Do not repeat this.

**Async distillation** (rejected 2026-05-02): Attempted to make `pipeline.run()` async to
improve throughput. Broke the locking mechanism in `src/distill/state_manager.py`. The
state manager uses threading.Lock, not asyncio.Lock. Mixed async/sync across this boundary
corrupts the run log. Synchronous is correct here.

---

## Session Log (most recent 3)

| Date | Last Action | Topology Drift | Next |
|------|-------------|---------------|------|
| 2026-05-18 | Updated ARCHITECTURE_MAP.md branch C (tokenizer node) | yes | re-fingerprint |
| 2026-05-14 | Integrated Assimilator v3 wrapper into pipeline.py | no | test end-to-end |
| 2026-05-10 | Cold-start activation; filled TOPOLOGY.md LBC sections | no | fill arch map |
