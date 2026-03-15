"""
orchestrator/graph.py — LangGraph state graph for the debate simulation.

Defines a graph with nodes for each debate round and the moderator synthesis.
The graph executes: round_1 → round_2 → round_3 → synthesize.

LangGraph Docs: https://langchain-ai.github.io/langgraph/
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from agents.base_agent import StakeholderAgent, RoundOutput, Critique
from agents.moderator_agent import ModeratorAgent
from orchestrator.state import SimulationState


def build_simulation_graph(
    agents: list[StakeholderAgent],
    moderator: ModeratorAgent,
) -> StateGraph:
    """
    Build and compile the LangGraph state graph for the full simulation.

    Graph topology:
        round_1 → round_2 → round_3 → synthesize → END

    Args:
        agents: The five stakeholder agents.
        moderator: The moderator agent.

    Returns:
        A compiled LangGraph that can be invoked with a SimulationState.
    """

    # ── Node functions ───────────────────────────────────────────────────

    def round_1_node(state: SimulationState) -> dict:
        """Each agent generates an initial position independently."""
        scenario = state["scenario"]
        outputs: list[RoundOutput] = []
        for agent in agents:
            try:
                output = agent.generate_initial_position(scenario)
                outputs.append(output)
            except Exception as e:
                return {"error": f"{agent.name} failed in Round 1: {e}"}

        round_outputs = dict(state.get("round_outputs", {}))
        round_outputs[1] = outputs
        return {"current_round": 2, "round_outputs": round_outputs}

    def round_2_node(state: SimulationState) -> dict:
        """Each agent critiques others and revises its position."""
        scenario = state["scenario"]
        r1_outputs = state["round_outputs"][1]
        outputs: list[RoundOutput] = []

        for i, agent in enumerate(agents):
            own_previous = r1_outputs[i]
            others = [o for j, o in enumerate(r1_outputs) if j != i]
            try:
                output = agent.critique_and_revise(scenario, own_previous, others)
                outputs.append(output)
            except Exception as e:
                return {"error": f"{agent.name} failed in Round 2: {e}"}

        round_outputs = dict(state["round_outputs"])
        round_outputs[2] = outputs
        return {"current_round": 3, "round_outputs": round_outputs}

    def round_3_node(state: SimulationState) -> dict:
        """Each agent negotiates compromises and finalizes its position."""
        scenario = state["scenario"]
        r2_outputs = state["round_outputs"][2]

        # Collect ALL critiques from Round 2 targeting each agent
        all_critiques_by_target: dict[str, list[Critique]] = {}
        for output in r2_outputs:
            for critique in output.critiques:
                all_critiques_by_target.setdefault(critique.target_agent, []).append(critique)

        outputs: list[RoundOutput] = []
        for i, agent in enumerate(agents):
            own_previous = r2_outputs[i]
            others = [o for j, o in enumerate(r2_outputs) if j != i]
            critiques_received = all_critiques_by_target.get(agent.name, [])
            try:
                output = agent.negotiate(scenario, own_previous, critiques_received, others)
                outputs.append(output)
            except Exception as e:
                return {"error": f"{agent.name} failed in Round 3: {e}"}

        round_outputs = dict(state["round_outputs"])
        round_outputs[3] = outputs
        return {"round_outputs": round_outputs}

    def synthesize_node(state: SimulationState) -> dict:
        """Moderator reads the full transcript and produces a synthesis."""
        try:
            synthesis = moderator.synthesize(
                state["scenario"],
                state["round_outputs"],
            )
            return {"synthesis": synthesis}
        except Exception as e:
            return {"error": f"Moderator synthesis failed: {e}"}

    # ── Build the graph ──────────────────────────────────────────────────

    graph = StateGraph(SimulationState)

    graph.add_node("round_1", round_1_node)
    graph.add_node("round_2", round_2_node)
    graph.add_node("round_3", round_3_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("round_1")
    graph.add_edge("round_1", "round_2")
    graph.add_edge("round_2", "round_3")
    graph.add_edge("round_3", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()
