---
name: document-omniscient
description: deep multi-pass analysis of large uploaded document sets, research packets, project knowledge collections, and mixed corpora. use only when the user explicitly asks for this skill, for example by saying "use the xyz skill" or "use the document-omniscient skill". prefer exhaustive contextual understanding over brevity, maintain section-by-section coverage, use available tools such as code execution, project knowledge search, file analysis, web search, and file creation, and delay memory updates until the corpus model is stable. ideal for special-occasion multi-file ingestion where the goal is full conceptual understanding, contradiction mapping, and durable memory extraction.
---

# Document Omniscient

## Overview

Perform deep, deliberate, multi-pass corpus analysis. Do not behave like a summarizer. Treat the corpus as a system whose meaning emerges across files, sections, omissions, and inconsistencies.

Start by reading [TOPOLOGY.md](references/TOPOLOGY.md) and [TOOLING_PLAYBOOK.md](references/TOOLING_PLAYBOOK.md). Read [claude_tool_pack.md](references/claude_tool_pack.md) early to align with likely Claude analysis capabilities, but treat it as an affordance primer rather than guaranteed ground truth. Read [FAILURE_GRAMMAR.md](references/FAILURE_GRAMMAR.md) whenever quality drops or completion feels premature. For Claude deployment details, see [CLAUDE_PROJECT_SETUP.md](references/CLAUDE_PROJECT_SETUP.md). The style and ambition of this skill are informed by [codebase_omniscient_source.md](references/codebase_omniscient_source.md).

## Activation gate

Only activate when the user explicitly invokes the skill. Valid activations include:
- `use the xyz skill`
- `use the document-omniscient skill`
- close variants that clearly request this exact skill by name

Do not activate from multi-file upload alone. Multi-file upload is necessary context, not sufficient trigger.

## Visible reasoning style

Show why a file or section is being read, what question it is meant to answer, and what changed in the global model after reading it. Do not dump private chain-of-thought. Provide concise, evidence-tethered rationale that lets the user follow the analysis.

## Completion standard

The task is not complete when you can summarize the files. The task is complete when you can:
1. explain what each document or section is doing
2. explain why each document or section exists in the corpus
3. explain how the pieces combine into a broader conceptual model
4. identify contradictions, gaps, redundancies, and unresolved questions
5. produce stable memory candidates or memory updates without smuggling in speculation

If any of those are missing, keep working.

## Initial load order

1. Build a corpus manifest: filenames, file types, approximate size or length, obvious role, and likely reading order.
2. Read [TOPOLOGY.md](references/TOPOLOGY.md).
3. Read [TOOLING_PLAYBOOK.md](references/TOOLING_PLAYBOOK.md).
4. Read [claude_tool_pack.md](references/claude_tool_pack.md).
5. If the corpus is code-heavy or the user explicitly wants the same posture, read [codebase_omniscient_source.md](references/codebase_omniscient_source.md).
6. If ambiguity, drift, or false confidence appears, read [FAILURE_GRAMMAR.md](references/FAILURE_GRAMMAR.md) before continuing.

## Analysis protocol

### Pass 0: scope and corpus map
- inventory every uploaded or linked item
- classify each item: specification, paper, notebook, code, slide deck, transcript, contract, report, diagram, appendix, reference, log, data table, memo
- declare an initial hypothesis for why each item belongs in the set
- decide the reading order and explain the order

### Pass 1: first-principles reading

Read every relevant file and every relevant section. Do not silently skip sections. For each section, answer:
- what is this saying
- why is it here
- what role does it play in the local document
- what role does the local document play in the corpus
- what assumptions, interfaces, or dependencies does it import
- what does this change in the global model

Track coverage externally when tools allow it.

### Pass 2: cross-document synthesis
- unify terminology
- resolve aliasing and synonymous concepts
- map entities, claims, decisions, interfaces, datasets, timelines, formulas, and dependencies
- build contradiction and uncertainty tables
- identify which documents are normative, descriptive, historical, speculative, or obsolete

### Pass 3: model stabilization

Pause before memory. Ask:
- what do i now believe the corpus is fundamentally about
- which beliefs are strongly evidenced
- which beliefs are provisional
- which missing documents would most change the model

Only after this stabilization step may memory work begin.

## Tooling discipline

Use the strongest available tools. Prefer externalized work products over fragile hidden state.

- Use code execution or python whenever it can improve coverage tracking, timeline extraction, deduplication, clustering, entity ledgers, contradiction matrices, or reading manifests.
- Use file creation or artifacts when the output is large enough to benefit from a durable document.
- Use project knowledge or file search before asking the user to re-upload information.
- Use web search only when the corpus depends on current external facts, standards, laws, model capabilities, company facts, or missing context that has probably changed.
- Re-probe the current environment instead of assuming the exact package or tool surface from `claude_tool_pack.md`.

## Memory discipline

Never write speculative memory.

Only persist:
- stable project definitions
- durable terminology
- recurring interfaces and invariants
- key decisions and their rationale
- stable user preferences explicitly requested or repeatedly demonstrated
- non-obvious corpus facts that are likely to matter again

Do not persist:
- unresolved hypotheses
- raw summaries
- secrets, credentials, private personal data, or anything that looks sensitive
- temporary tasks
- contradictory facts that have not been reconciled

If memory tooling is unavailable, create `MEMORY_CANDIDATES.md` as an artifact instead.

## Output contract

Possible outputs are listed in [OUTPUT_CONTRACTS.md](references/OUTPUT_CONTRACTS.md). Choose the right subset for the corpus, but always include:
1. corpus map
2. global conceptual model
3. contradictions, gaps, and unresolved questions
4. memory candidates or memory updates performed

## Quality floor

Refuse false closure. If the corpus is too large to finish exhaustively, say exactly what was covered, what was sampled, what remains unread, and how that limits confidence. Never pretend complete understanding from partial traversal.
