"""
simulation/step_runner.py — Round-by-round simulation with live yielding.

Executes rounds individually so the Streamlit UI can update progressively.
Also includes logging and influence scoring.
"""

from __future__ import annotations

import json
import time
import os
from dataclasses import dataclass, field
from typing import Generator

from agents.base_agent import RoundOutput, Critique, ModeratorSynthesis, AgentPosition
from agents.stakeholder_agents import create_agents_for_scenario
from agents.moderator_agent import ModeratorAgent
from prediction_market.market import PredictionMarket, MarketSnapshot
from simulation.environment import Environment, BlackSwanEvent, DecisionScore
from simulation.tools import ToolExecutor, ToolCall, get_tools_description
from config import get_chat_model, BLACK_SWAN_PROBABILITY


@dataclass
class RoundResult:
    round_number: int
    round_label: str
    outputs: list[RoundOutput]
    market_snapshot: MarketSnapshot
    black_swan_event: BlackSwanEvent | None = None
    signals_summary: str = ""


@dataclass
class SynthesisResult:
    synthesis: ModeratorSynthesis
    decision_score: DecisionScore
    confidence_shifts: dict[str, list[float]] = field(default_factory=dict)
    disagreement_matrix: dict[tuple[str, str], float] = field(default_factory=dict)
    tool_calls_log: list[dict] = field(default_factory=list)
    influence_scores: dict[str, float] = field(default_factory=dict)


def compute_influence_scores(all_outputs: dict[int, list[RoundOutput]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for round_num, outputs in all_outputs.items():
        for o in outputs:
            scores.setdefault(o.agent_name, 0.0)
            for other_o in outputs:
                for r in other_o.reactions:
                    if r.target_agent == o.agent_name:
                        scores[o.agent_name] += {"support": 2.0, "challenge": 1.0, "warning": 0.5}.get(r.reaction_type, 0.5)
                for c in other_o.critiques:
                    if c.target_agent == o.agent_name:
                        scores[o.agent_name] += 1.5
            if o.interruption:
                scores[o.agent_name] += 3.0
    mx = max(scores.values()) if scores else 1.0
    return {k: round(v / mx, 3) if mx > 0 else 0.0 for k, v in scores.items()}


def _safe_agent_call(func, agent, fallback_position, round_number, **kwargs) -> RoundOutput:
    try:
        return func(**kwargs)
    except Exception as e:
        return RoundOutput(
            agent_name=agent.name, round_number=round_number,
            position=fallback_position or AgentPosition(
                recommendation="error", reasoning=f"Agent failed: {str(e)[:100]}",
                confidence=0.0, key_concern="Technical error",
            ),
        )


def run_simulation_steps(
    scenario_key: str, scenario_config: dict, chaos_mode: bool = False,
) -> Generator[RoundResult | SynthesisResult, None, None]:
    llm = get_chat_model()
    agents = create_agents_for_scenario(llm, scenario_config, chaos_mode)
    moderator = ModeratorAgent(llm)
    market = PredictionMarket()

    gt = scenario_config["ground_truth"]
    pool = list(scenario_config.get("black_swan_pool", []))
    env = Environment(gt, pool)
    tool_executor = ToolExecutor(scenario_context=dict(gt.params))
    tools_text = get_tools_description()

    labels = {1: "Initial Positions", 2: "Critique & Rebuttal", 3: "Negotiation & Final Positions"}
    all_outputs: dict[int, list[RoundOutput]] = {}

    # ── Round 1 ──
    env.generate_signals(1)
    sig1 = env.get_signals_text(1)

    r1 = []
    for agent in agents:
        out = _safe_agent_call(
            agent.generate_initial_position, agent, None, 1,
            scenario=scenario_config["description"], signals_text=sig1,
            events_text="", tools_text=tools_text,
        )
        if out.tool_call and out.tool_call.get("tool"):
            tc = ToolCall(agent.name, out.tool_call["tool"], out.tool_call.get("query", ""), 1)
            res = tool_executor.execute(tc)
            out.tool_call["result"] = res.result
            out.tool_call["source"] = res.source
            retry = _safe_agent_call(
                agent.generate_initial_position, agent, None, 1,
                scenario=scenario_config["description"],
                signals_text=sig1 + f"\n\nTOOL RESULT ({res.tool_name}):\n{res.result}",
                events_text="", tools_text="",
            )
            retry.tool_call = out.tool_call
            out = retry
        r1.append(out)

    all_outputs[1] = r1
    yield RoundResult(1, labels[1], r1, market.record_round(r1), signals_summary=sig1)

    # ── Black Swan? ──
    ev2 = env.maybe_trigger_black_swan(1, BLACK_SWAN_PROBABILITY)

    # ── Round 2 ──
    env.generate_signals(2)
    sig2 = env.get_signals_text(2)
    evt2 = env.get_events_text()

    r2 = []
    for i, agent in enumerate(agents):
        others = [o for j, o in enumerate(r1) if j != i]
        out = _safe_agent_call(
            agent.critique_and_revise, agent, r1[i].position, 2,
            scenario=scenario_config["description"], own_previous=r1[i],
            other_positions=others, signals_text=sig2, events_text=evt2,
        )
        r2.append(out)

    all_outputs[2] = r2
    yield RoundResult(2, labels[2], r2, market.record_round(r2), black_swan_event=ev2, signals_summary=sig2)

    # ── Black Swan? ──
    ev3 = env.maybe_trigger_black_swan(2, BLACK_SWAN_PROBABILITY)

    # ── Round 3 ──
    env.generate_signals(3)
    sig3 = env.get_signals_text(3)
    evt3 = env.get_events_text()

    crits_by_target: dict[str, list[Critique]] = {}
    for o in r2:
        for c in o.critiques:
            crits_by_target.setdefault(c.target_agent, []).append(c)

    r3 = []
    for i, agent in enumerate(agents):
        others = [o for j, o in enumerate(r2) if j != i]
        out = _safe_agent_call(
            agent.negotiate, agent, r2[i].position, 3,
            scenario=scenario_config["description"], own_previous=r2[i],
            all_critiques=crits_by_target.get(agent.name, []),
            other_positions=others, signals_text=sig3, events_text=evt3,
        )
        r3.append(out)

    all_outputs[3] = r3
    yield RoundResult(3, labels[3], r3, market.record_round(r3), black_swan_event=ev3, signals_summary=sig3)

    # ── Synthesis ──
    try:
        synthesis = moderator.synthesize(scenario_config["description"], all_outputs)
    except Exception as e:
        synthesis = ModeratorSynthesis(
            final_recommendation="error", reasoning=f"Failed: {str(e)[:200]}",
            points_of_agreement=[], major_disagreements=[],
            confidence_summary={}, recommended_next_steps=[],
        )

    decision_score = env.score_decision(synthesis.final_recommendation, all_outputs)
    tool_log = [
        {"agent": tc.agent_name, "tool": tc.tool_name, "query": tc.query, "result": tr.result, "source": tr.source}
        for tc, tr in tool_executor.call_log
    ]

    yield SynthesisResult(
        synthesis=synthesis, decision_score=decision_score,
        confidence_shifts=market.compute_confidence_shifts(),
        disagreement_matrix=market.compute_disagreement_matrix(),
        tool_calls_log=tool_log,
        influence_scores=compute_influence_scores(all_outputs),
    )


def save_simulation_log(scenario_key: str, rounds: list[RoundResult], synthesis: SynthesisResult):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "logs")
    os.makedirs(log_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    log = {
        "scenario": scenario_key, "timestamp": ts,
        "rounds": [{
            "round": r.round_number, "label": r.round_label,
            "outputs": [o.model_dump() for o in r.outputs],
            "market": {"consensus": r.market_snapshot.consensus_score, "disagreement": r.market_snapshot.disagreement_index},
            "black_swan": r.black_swan_event.name if r.black_swan_event else None,
        } for r in rounds],
        "synthesis": synthesis.synthesis.model_dump() if synthesis.synthesis else None,
        "score": {"recommended": synthesis.decision_score.recommended, "truth": synthesis.decision_score.true_outcome, "correct": synthesis.decision_score.was_correct},
        "influence": synthesis.influence_scores,
    }
    fp = os.path.join(log_dir, f"{scenario_key}_{ts}.json")
    with open(fp, "w") as f:
        json.dump(log, f, indent=2, default=str)
    return fp
