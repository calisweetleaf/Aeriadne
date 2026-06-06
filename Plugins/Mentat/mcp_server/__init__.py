"""Mentat MCP server.

A thin stdio MCP server that exposes the Mentat insight bus, state machine,
and Q-table to the live Claude Code turn. The model can introspect its own
session mid-turn — the mirror of the bb7_ pattern in Muad'Dib.

Tools (all prefixed mentat_ in the tool namespace):

    mentat_state_get        → returns current State, transition_count, chain_depth
    mentat_state_set        → manually transition (e.g., declare REFLECTING)
    mentat_insight_emit     → push a structured insight (DECISION, NOTE, etc.)
    mentat_insight_query    → filter the bus by type / state
    mentat_insight_tail     → last N insights
    mentat_q_route          → recommend a tool for current state (Thompson)
    mentat_q_table          → dump the full Q-table
    mentat_handoff_read     → read the latest pre-compact handoff
    mentat_handoff_write    → manually write a handoff snapshot
    mentat_drift_check      → run drift detection against arbitrary text

The server runs as `python3 -m mentat.mcp_server` from the plugin root, with
stdin/stdout as the transport (Anthropic-recommended for local servers).
"""
