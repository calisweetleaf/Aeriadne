"""Mentat state machine — the cognitive substrate that watches a Claude Code session.

Eight states, six event classes, one persistent Q-table.

States:
    PLANNING    — synthesizing approach, choosing tools, no side effects yet
    EXPLORING   — read-only research, codebase mapping, search, file reads
    EXECUTING   — write / edit / run with side effects
    VERIFYING   — running tests, lints, type checks, validation
    REFLECTING  — assessing results, deciding next move
    BLOCKED     — waiting on external answer, stuck on a tool failure
    DRIFTING    — scope creep detected — a deferred topic was re-injected
    COMPACTING  — pre/post compaction handoff state

The state machine is reconstructed from the ~/.mentat/state.sqlite session table
on every hook invocation (hooks are independent processes, so no in-memory state
survives across firings — disk is the only durable medium).
"""
from .machine import StateMachine, State, Event, EventClass
from .q_table import QTable, Reward
from .insights import InsightBus, Insight, InsightType
from .session import Session, load_session, save_session

__all__ = [
    "StateMachine",
    "State",
    "Event",
    "EventClass",
    "QTable",
    "Reward",
    "InsightBus",
    "Insight",
    "InsightType",
    "Session",
    "load_session",
    "save_session",
]
