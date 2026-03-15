"""
simulation/runner.py — High-level simulation executor.

Provides a simple run_simulation() function that wires up agents,
the graph, and the prediction market, then returns all results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.base_agent import RoundOutput, ModeratorSynthesis
from agents.stakeholder_agents import create_all_agents
from agents.moderator_agent import ModeratorAgent
from orchestrator.graph import build_simulation_graph
from orchestrator.state import SimulationState
from prediction_market.market import PredictionMarket, MarketSnapshot
from config import get_chat_model


@dataclass
class SimulationResult:
    """Complete result of a simulation run."""

    scenario: str
    round_outputs: dict[int, list[RoundOutput]]
    synthesis: ModeratorSynthesis
    market_snapshots: dict[int, MarketSnapshot]
    confidence_shifts: dict[str, list[float]]
    disagreement_matrix: dict[tuple[str, str], float]
    error: str | None = None


def run_simulation(
    scenario: str,
    *,
    verbose: bool = True,
) -> SimulationResult:
    """
    Execute a full 3-round debate simulation.

    Args:
        scenario: The decision question to simulate.
        verbose: If True, print progress to stdout.

    Returns:
        SimulationResult with all outputs, market data, and synthesis.
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"  AI DECISION SIMULATION LAB")
        print(f"{'='*70}")
        print(f"  Scenario: {scenario[:80]}...")
        print(f"{'='*70}\n")

    # Initialize
    llm = get_chat_model()
    agents = create_all_agents(llm)
    moderator = ModeratorAgent(llm)
    graph = build_simulation_graph(agents, moderator)

    # Run the graph
    initial_state: SimulationState = {
        "scenario": scenario,
        "current_round": 1,
        "round_outputs": {},
        "synthesis": None,
        "error": "",
    }

    if verbose:
        print("▶ Running debate simulation (3 rounds + synthesis)...")
        print("  This calls the LLM 5 agents × 3 rounds + 1 moderator = 16 times.\n")

    final_state = graph.invoke(initial_state)

    # Check for errors
    if final_state.get("error"):
        return SimulationResult(
            scenario=scenario,
            round_outputs=final_state.get("round_outputs", {}),
            synthesis=final_state.get("synthesis"),  # type: ignore
            market_snapshots={},
            confidence_shifts={},
            disagreement_matrix={},
            error=final_state["error"],
        )

    # Run prediction market analysis
    market = PredictionMarket()
    round_outputs = final_state["round_outputs"]
    for round_num in sorted(round_outputs.keys()):
        snapshot = market.record_round(round_outputs[round_num])
        if verbose:
            print(
                f"  Round {round_num}: Consensus={snapshot.consensus_score:.2f}  "
                f"Disagreement={snapshot.disagreement_index:.2f}  "
                f"Majority={snapshot.majority_recommendation}"
            )

    confidence_shifts = market.compute_confidence_shifts()
    disagreement_matrix = market.compute_disagreement_matrix()

    if verbose:
        print(f"\n{'─'*70}")
        print(f"  FINAL SYNTHESIS")
        print(f"{'─'*70}")
        synthesis = final_state["synthesis"]
        print(f"  Recommendation: {synthesis.final_recommendation}")
        print(f"  Agreement points: {len(synthesis.points_of_agreement)}")
        print(f"  Disagreements: {len(synthesis.major_disagreements)}")
        print(f"  Confidence scores: {synthesis.confidence_summary}")
        print(f"{'─'*70}\n")

    return SimulationResult(
        scenario=scenario,
        round_outputs=round_outputs,
        synthesis=final_state["synthesis"],
        market_snapshots=market.snapshots,
        confidence_shifts=confidence_shifts,
        disagreement_matrix=disagreement_matrix,
    )
