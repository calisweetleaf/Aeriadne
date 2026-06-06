# Agent Directory: Mentat

Welcome, agent. This is the entry point for the **Mentat** repository.

## Map of the Substrate
- **[Memory & Milestones](file:///home/daeron/Projects/Modern-ML/Plugins/Mentat/MEMORY.md)**: Current status, log of changes, and active tasks.
- **[Context & Architecture](file:///home/daeron/Projects/Modern-ML/Plugins/Mentat/CONTEXT.md)**: Technical architecture, directory layouts, and execution rules.

## Core Purpose
Mentat is a session-scoped state machine and Q-table running as a Gemini CLI extension. It acts as an observer for the agent loop to record insights and shape the state transitions (planning, exploring, executing, verifying, reflecting, blocked, drifting, compacting).

## Project Guidelines
1. **Loud Failures**: Never fail silently. All exceptions and error codes must be logged clearly.
2. **Virtual Environment**: Run all tasks within the designated python environment and ensure dependencies are installed.
3. **No Drift**: Pay close attention to `.mentat/scope.md`. Avoid out-of-scope discussion topics to prevent triggering FSA drift blocks.
