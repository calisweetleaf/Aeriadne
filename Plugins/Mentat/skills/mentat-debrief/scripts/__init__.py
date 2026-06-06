"""Mentat debrief renderer package.

Deterministic Python renderer for the end-of-session debrief artifact.
The skill invokes scripts/render.py, which reads the insight bus + Q-table
+ session record from disk and produces a self-contained HTML artifact.

Modules:
    aggregate  — pure-function aggregators over the raw insight/Q-table stream
    render     — argparse entry-point + template interpolation
    template   — master HTML template (string.Template placeholders)
    test_smoke — synthesize fake input and assert basic invariants
"""
