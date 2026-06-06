"""The state machine itself.

Transitions are deterministic given (current_state, event_class, tool_name, prompt_features).
Non-deterministic flavor (the Thompson-bandit-style softness) lives in the Q-table —
the state machine itself is a hard FSA. That separation matters: when something goes
wrong, you can replay the FSA from the event log and get the exact same trace, and
debug the Q-table separately.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class State(str, enum.Enum):
    PLANNING = "planning"
    EXPLORING = "exploring"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    REFLECTING = "reflecting"
    BLOCKED = "blocked"
    DRIFTING = "drifting"
    COMPACTING = "compacting"


class EventClass(str, enum.Enum):
    """Coarse classification of a hook event for transition logic."""
    PROMPT_SUBMIT = "prompt_submit"
    READ_TOOL = "read_tool"          # Read, Grep, Glob, LS, WebFetch, ExaSearch
    WRITE_TOOL = "write_tool"        # Edit, Write, MultiEdit, NotebookEdit
    EXEC_TOOL = "exec_tool"          # Bash (anything with side effects)
    AGENT_TOOL = "agent_tool"        # Agent / Task — sub-agent dispatch
    VERIFY_TOOL = "verify_tool"      # Bash with test/lint signature, or pytest hook
    TOOL_SUCCESS = "tool_success"
    TOOL_ERROR = "tool_error"
    SUBAGENT_RETURN = "subagent_return"
    SCOPE_DRIFT_DETECTED = "scope_drift_detected"
    PRE_COMPACT = "pre_compact"
    POST_COMPACT = "post_compact"
    SESSION_START = "session_start"
    STOP = "stop"
    STOP_FAILURE = "stop_failure"
    IDLE = "idle"                    # heartbeat / no-op tick


@dataclass
class Event:
    event_class: EventClass
    tool_name: Optional[str] = None
    payload: dict = field(default_factory=dict)
    timestamp: float = 0.0


# Transition table: (current_state, event_class) -> next_state
# Default fallback: stay in current state (no transition).
TRANSITIONS: dict[tuple[State, EventClass], State] = {
    # SESSION_START always lands in PLANNING (or COMPACTING if resume-after-compact)
    (State.PLANNING, EventClass.SESSION_START): State.PLANNING,
    (State.EXPLORING, EventClass.SESSION_START): State.PLANNING,
    (State.EXECUTING, EventClass.SESSION_START): State.PLANNING,
    (State.VERIFYING, EventClass.SESSION_START): State.PLANNING,
    (State.REFLECTING, EventClass.SESSION_START): State.PLANNING,
    (State.BLOCKED, EventClass.SESSION_START): State.PLANNING,
    (State.DRIFTING, EventClass.SESSION_START): State.PLANNING,
    (State.COMPACTING, EventClass.POST_COMPACT): State.REFLECTING,

    # PLANNING — first read or agent dispatch starts EXPLORING; first write goes to EXECUTING
    (State.PLANNING, EventClass.READ_TOOL): State.EXPLORING,
    (State.PLANNING, EventClass.AGENT_TOOL): State.EXPLORING,
    (State.PLANNING, EventClass.WRITE_TOOL): State.EXECUTING,
    (State.PLANNING, EventClass.EXEC_TOOL): State.EXECUTING,
    (State.PLANNING, EventClass.VERIFY_TOOL): State.VERIFYING,
    (State.PLANNING, EventClass.PROMPT_SUBMIT): State.PLANNING,

    # EXPLORING — keep reading, escalate on write/exec, drop to BLOCKED on error
    (State.EXPLORING, EventClass.READ_TOOL): State.EXPLORING,
    (State.EXPLORING, EventClass.AGENT_TOOL): State.EXPLORING,
    (State.EXPLORING, EventClass.WRITE_TOOL): State.EXECUTING,
    (State.EXPLORING, EventClass.EXEC_TOOL): State.EXECUTING,
    (State.EXPLORING, EventClass.VERIFY_TOOL): State.VERIFYING,
    (State.EXPLORING, EventClass.SUBAGENT_RETURN): State.REFLECTING,
    (State.EXPLORING, EventClass.TOOL_ERROR): State.BLOCKED,

    # EXECUTING — writes / shell commands. Verify cleanly transitions, errors block.
    (State.EXECUTING, EventClass.WRITE_TOOL): State.EXECUTING,
    (State.EXECUTING, EventClass.EXEC_TOOL): State.EXECUTING,
    (State.EXECUTING, EventClass.VERIFY_TOOL): State.VERIFYING,
    (State.EXECUTING, EventClass.READ_TOOL): State.EXECUTING,
    (State.EXECUTING, EventClass.TOOL_ERROR): State.BLOCKED,
    (State.EXECUTING, EventClass.TOOL_SUCCESS): State.EXECUTING,

    # VERIFYING — test / lint / typecheck. Success → reflect, failure → execute (fix loop).
    (State.VERIFYING, EventClass.TOOL_SUCCESS): State.REFLECTING,
    (State.VERIFYING, EventClass.TOOL_ERROR): State.EXECUTING,
    (State.VERIFYING, EventClass.WRITE_TOOL): State.EXECUTING,
    (State.VERIFYING, EventClass.READ_TOOL): State.VERIFYING,

    # REFLECTING — fork into next iteration. Prompt submit re-plans.
    (State.REFLECTING, EventClass.PROMPT_SUBMIT): State.PLANNING,
    (State.REFLECTING, EventClass.READ_TOOL): State.EXPLORING,
    (State.REFLECTING, EventClass.WRITE_TOOL): State.EXECUTING,
    (State.REFLECTING, EventClass.AGENT_TOOL): State.EXPLORING,

    # BLOCKED — only prompt or successful retry escapes
    (State.BLOCKED, EventClass.TOOL_SUCCESS): State.EXECUTING,
    (State.BLOCKED, EventClass.PROMPT_SUBMIT): State.PLANNING,
    (State.BLOCKED, EventClass.AGENT_TOOL): State.EXPLORING,

    # DRIFTING — universal escape only via explicit prompt. Sentinel emits the entry event.
    (State.DRIFTING, EventClass.PROMPT_SUBMIT): State.PLANNING,

    # COMPACTING — only POST_COMPACT escapes
    (State.COMPACTING, EventClass.POST_COMPACT): State.REFLECTING,
}

# Drift trumps everything: any state + SCOPE_DRIFT_DETECTED → DRIFTING
for s in State:
    TRANSITIONS[(s, EventClass.SCOPE_DRIFT_DETECTED)] = State.DRIFTING
    TRANSITIONS[(s, EventClass.PRE_COMPACT)] = State.COMPACTING


@dataclass
class StateMachine:
    """Pure FSA over the state space. No I/O. Caller persists the state."""
    state: State = State.PLANNING
    last_event: Optional[Event] = None
    transition_count: int = 0

    def step(self, event: Event) -> tuple[State, State, bool]:
        """Apply event, return (prev_state, next_state, transitioned).

        Tool-name-aware refinements happen here too. Example: a Bash event whose
        command starts with 'pytest', 'cargo test', 'npm test', 'mocha', 'go test',
        'pylint', 'ruff', 'mypy', 'tsc' is reclassified into VERIFY_TOOL even if
        the hook layer tagged it generic EXEC_TOOL.
        """
        prev = self.state
        ec = event.event_class
        if ec is EventClass.EXEC_TOOL and event.tool_name == "Bash":
            cmd = (event.payload or {}).get("command", "")
            if _looks_like_verify(cmd):
                ec = EventClass.VERIFY_TOOL
        nxt = TRANSITIONS.get((prev, ec), prev)
        self.state = nxt
        self.last_event = event
        if nxt is not prev:
            self.transition_count += 1
        return prev, nxt, nxt is not prev


_VERIFY_PREFIXES = (
    "pytest", "cargo test", "npm test", "yarn test", "pnpm test",
    "mocha", "jest", "go test", "ruff", "pylint", "mypy", "tsc",
    "eslint", "flake8", "black --check", "cargo check", "cargo clippy",
    "rspec", "phpunit", "make test", "bun test",
)


def _looks_like_verify(cmd: str) -> bool:
    s = cmd.strip().lower()
    return any(s.startswith(p) for p in _VERIFY_PREFIXES)
