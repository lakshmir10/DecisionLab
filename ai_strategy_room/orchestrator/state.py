"""
orchestrator/state.py — Shared simulation state for LangGraph.

This TypedDict is the graph's state schema. Every node reads from and
writes to this state. LangGraph manages the state lifecycle automatically.
"""

from __future__ import annotations
from typing import TypedDict
from agents.base_agent import RoundOutput, ModeratorSynthesis


class SimulationState(TypedDict):
    """
    Full state of one simulation run, threaded through the LangGraph.

    Keys:
        scenario: The user's decision question.
        current_round: Which round is currently executing (1, 2, or 3).
        round_outputs: {round_number: [RoundOutput, ...]} — accumulated outputs.
        synthesis: The moderator's final output (None until the last step).
        error: Any error message (empty string if no error).
    """

    scenario: str
    current_round: int
    round_outputs: dict[int, list[RoundOutput]]
    synthesis: ModeratorSynthesis | None
    error: str
