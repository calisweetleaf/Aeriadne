# ARCHITECTURE_MAP_TEMPLATE.md — Traversal Map Construction Protocol

**Loaded by**: SKILL.md for [BUILD_ARCHITECTURE_MAP] or Phase 5 ecosystem construction  
**Purpose**: Formalize the traversal map pattern. An ARCHITECTURE_MAP is not a README,
not a summary, and not a diagram. It is a navigable question graph: each node answers
one question and points to the next level — file, line number, what to look for.
An agent can enter it cold and reach any system component within 3 hops.

---

## The Distinction That Matters

| Summary (what NOT to build) | Traversal Map (what to build) |
|-----------------------------|-------------------------------|
| Describes the system | Navigates the system |
| Readable by humans unfamiliar with the code | Executable by agents cold-entering |
| Paragraphs | Branches and nodes |
| Requires prior knowledge to interpret | Requires zero prior knowledge to follow |
| Answers "what is this?" | Answers "where is X?" and "how does Y work?" |

The ARCHITECTURE_MAP in Daeron's Somnus-MCP is the canonical example.
Note its structure: "ROOT: What is the Lisan Al Ghaib?" → "BRANCH A: How does a tool
call flow?" → specific file + line number + what to look for next.
This is the pattern. Replicate it.

---

## ARCHITECTURE_MAP.md Structure

```markdown
# [Project Name] Architecture Map

**How to use this document:** Start at the question that matches what you're trying 
to understand. Each node answers one question and points you to the next level — 
file, line number, what to look for. This is a traversal map, not a summary. 
Follow the branches.

---

## ROOT: What is [Project Name]?

[2–3 sentences. The most precise answer to "what is this system" that an agent
needs before any navigation begins. NOT a marketing description. Operational
description: what it does, how it does it, what drives it.]

**Three layers, read in this order:**
[If the system has architectural layers, name them here with primary files + line anchors]

---

## BRANCH A: [Core flow question — "How does X happen?"]

**Entry point:** `{file.py}:{line}` → `{function_name}()`

[Step-by-step trace of the flow. Each step: what happens, what file/line, 
what to look for next. Use → arrows for navigation.]

**→ If you want to understand [sub-topic]:** Go to BRANCH B.
**→ If you want to understand [other sub-topic]:** Go to BRANCH C.

---

## BRANCH B: [Second flow question]
...

## BRANCH C: [Third flow question]
...

---

## BRANCH [N]: Where is X? (Quick Reference)

| Question | Go to |
|---------|-------|
| [Question 1] | `{file}:{line}` |
| [Question 2] | `{file}:{line}` |
...
```

---

## Construction Protocol

### Step 1: Identify the ROOT question

The root question is the question an agent asks when first entering this codebase:
"What IS this thing and what drives it?"

The ROOT answer must be 2–3 sentences, operational, and precise. It should tell the
agent: what category of system this is, what the primary mechanism is, and what
activates it. Everything else branches from this.

### Step 2: Enumerate the primary navigation questions

What are the 5–8 most important questions an agent would ask when working in this system?
Examples from different system types:

*For a symbolic tool server:*
- How does a tool call flow?
- How does routing intelligence work?
- How do learned paths persist?
- How does telemetry capture happen?
- Where is X?

*For a Python research library:*
- How does inference work?
- How do modules communicate?
- How is training triggered?
- What's the data path?
- Where is X?

*For an agent kernel:*
- How does session boot happen?
- How does tool selection work?
- How does memory persist?
- How do agents communicate?
- Where is X?

Each becomes a BRANCH. The last BRANCH is always the Quick Reference table.

### Step 3: Trace each branch to file + line anchors

For each BRANCH question, trace the actual code path:
1. Entry point: which file, which function, which line number
2. What happens at that point (brief, precise — not a code dump)
3. What calls what, in what order
4. Where the flow terminates or hands off

**Line numbers are non-optional.** "See exoskeleton_tool.py" is a summary.
"exoskeleton_tool.py:1781 → bb7_exo_bootstrap()" is a traversal node.

### Step 4: Add lateral navigation pointers

At the end of each branch, add "→ If you want to understand [related thing]: Go to BRANCH X."
These are the edges of the navigation graph. They prevent dead ends.

### Step 5: Build the Quick Reference table

The last BRANCH is always a quick reference table: question → file:line.
This is the index. Every significant function, class, config file, and data
artifact that an agent might look for should have an entry.

### Step 6: Add the anomaly note section (optional but valuable)

For complex systems with non-obvious behaviors:
```markdown
## ANOMALIES AND GOTCHAS

These are things that look wrong but are intentional, or things that look right
but have subtle requirements.

- **[Anomaly name]**: [What it looks like vs. what it actually is. Why it's not a bug.]
```

---

## Quality Gates for ARCHITECTURE_MAP.md

Before considering it complete:

- [ ] ROOT answers "what is this system" in ≤ 3 sentences, operationally
- [ ] Every branch starts with a file + line anchor (not just a filename)
- [ ] Every branch has at least one lateral navigation pointer to another branch
- [ ] Quick Reference table covers all primary classes, entry points, and data files
- [ ] An agent reading only the ROOT can determine which branch to follow next
- [ ] No branch is longer than 40 lines of prose (if it is, split into sub-branches)
- [ ] No branch is a summary (summaries describe; branches navigate)

---

## Maintenance Protocol

ARCHITECTURE_MAP.md drifts when code changes without updating the map.
The topology_fingerprint.txt in .sovereign/ detects this.

**When to update ARCHITECTURE_MAP.md:**
- New module or significant class added → new branch or Quick Reference entry
- Function moved or renamed → update line anchors in all branches that reference it
- Architectural layer added or removed → update ROOT + affected branches
- New data artifact → add to Quick Reference table

**When NOT to update ARCHITECTURE_MAP.md:**
- Internal refactor with no interface change → line numbers change but structure doesn't,
  update only the Quick Reference table line anchors
- Bugfix with no architectural impact → no update needed

---

## Example: Minimal ARCHITECTURE_MAP.md for a Python Module

```markdown
# MyModule Architecture Map

**How to use this document:** Start at the question that matches what you need.
Each node points to a file and line number. This is a traversal map, not a summary.

---

## ROOT: What is MyModule?

A Python library for [X]. It [primary mechanism]. Activation requires [trigger condition].
Without [condition], it is [state]. With it, it [behavior].

Entry: `src/mymodule/core.py:1` → `class MyModuleCore`

---

## BRANCH A: How does a [primary operation] happen?

**Entry point:** `src/mymodule/core.py:47` → `def process()`

1. Receives [input type] at line 52
2. Calls `_validate()` at line 58 → raises `ValidationError` if [condition]
3. Invokes `_compute()` at line 71 — **DENSE**: subtle edge case at line 89
4. Returns structured result dict

**→ If you want to understand validation logic:** Go to BRANCH B.
**→ If you want to understand the compute layer:** Go to BRANCH C.

---

## BRANCH B: How does validation work?
...

## BRANCH C: What is the compute layer?
...

---

## BRANCH D: Where is X?

| Question | Go to |
|---------|-------|
| Core class | `src/mymodule/core.py:1` |
| Validation | `src/mymodule/validators.py:1` |
| Config | `pyproject.toml:[tool.mymodule]` |
| Tests | `tests/test_core.py` |
```
