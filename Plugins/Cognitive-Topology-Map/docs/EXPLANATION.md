# EXPLANATION.md — What CTM-v3 Actually Is

## Short version

**CTM-v3 is not a skill maker.**

That is the wrong way to think about it.

CTM-v3 is a **codebase activation / workspace onboarding system** whose job is to enter a repo and make that repo **living for agents**.

It may create a skill as one artifact, but that is not the main point.

The main point is:

- set up the repo properly,
- install the agent-facing structure,
- create the right `.xyz` folders and files,
- wire in hooks and workflow surfaces,
- establish memory/context/doctrine,
- and leave the codebase in a state where an agent can actually work inside it instead of guessing.

---

## What CTM-v3 is supposed to do

When CTM-v3 is run on a codebase, whether it is:

- an old repo that has been worked on for months, or
- a brand new repo,

it is supposed to do the **full workspace setup pass**.

Not a minimal scaffold.
Not a cute prompt pack.
Not a half-finished starter.

The real idea is:

1. inspect the repo,
2. understand what kind of system it is,
3. create the onboarding and topology surfaces,
4. create the doctrine/context/memory surfaces,
5. build the `.xyz` directories and integration files,
6. set up hooks, workflow, and enforcement surfaces where needed,
7. and turn the repo into a workspace that can be continuously inhabited by agents.

That is why CTM-v3 is better described as **workspace activation** than skill creation.

---

## Why “skill maker” is too small

Calling CTM-v3 a skill maker shrinks the concept down to one output artifact.

That misses the actual point.

A skill is only one possible byproduct.

CTM-v3 is really about making a repo:

- readable,
- navigable,
- stateful,
- doctrine-backed,
- memory-backed,
- topology-aware,
- failure-aware,
- and operational for future agent work.

So even if it creates a skill, the skill is only one part of a much larger activation pass.

The repo itself is the real output.

---

## The real outcome

After a proper CTM-v3 pass, the codebase should stop feeling like a dead folder tree and start feeling like a **living workspace**.

That means the repo has enough structure that an agent can enter it and understand:

- what this codebase is,
- how it is organized,
- what matters most,
- what has already been decided,
- where the risk is,
- what files/folders govern behavior,
- what hooks or automation are active,
- how to continue work without re-deriving the whole repo from scratch.

That “living repo” idea is the center of gravity.

---

## Why plugin form probably fits better

Yes — **plugin form likely fits CTM-v3 better than pure skill form**.

Why:

### 1. CTM-v3 is not just knowledge, it is execution
A skill is good at carrying knowledge, instructions, topology, and entry logic.

But CTM-v3 wants to do more than explain.
It wants to **set things up**.

That makes it feel more like a plugin because plugins can better own behavior such as:

- lifecycle setup,
- install-time actions,
- repo bootstrapping,
- hook registration,
- environment checks,
- structure generation,
- and deeper integration with the working loop.

### 2. CTM-v3 wants to make changes to the workspace itself
The goal is not only to help an agent think.
The goal is to make the repo operational.

That includes things like:

- `.github/`
- `.claude/`
- `.codex/`
- `.sovereign/`
- AGENTS / CONTEXT / MEMORY surfaces
- traversal / architecture docs
- workflow and enforcement files
- possibly CI/CD or hook surfaces

That is bigger than a normal skill posture.

### 3. Plugin form matches “run once, establish environment” behavior
A plugin is a more natural home for something that says:

> enter this repo, configure everything relevant, and leave behind a durable working environment.

That is much closer to a plugin-style system than a text-only skill.

### 4. Skill can remain one layer, plugin can become the engine
The best split may be:

- **plugin = activation engine**
- **skill/docs = cognitive layer and portable topology**

In other words:

- the plugin does the setup and integration work,
- the CTM docs/skill package explain the repo and preserve the topology,
- and together they make the workspace truly agent-operable.

That is a stronger architecture than forcing everything into “skill” form.

---

## Best framing to give Claude

If you are uploading this as a zip and want the concept understood correctly, the framing should be:

> CTM-v3 is not fundamentally a skill generator. It is a codebase onboarding and workspace activation system. Its purpose is to enter a repo, install the full agent-operability structure, create the needed `.xyz` folders/files/hooks/docs/state surfaces, and make the codebase living for ongoing agent work. Skill creation may happen as part of that process, but it is not the primary identity of the system.

---

## One-sentence definition

**CTM-v3 is a workspace activation system that turns a codebase into a living, agent-operable repo — not merely a skill maker.**
