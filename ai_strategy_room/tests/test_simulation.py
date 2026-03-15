"""
tests/test_simulation.py — Unit tests for the simulation components.

Run with:  python -m pytest tests/ -v
"""

import pytest
from agents.base_agent import (
    AgentPosition,
    Critique,
    NegotiationProposal,
    RoundOutput,
    ModeratorSynthesis,
)
from prediction_market.market import PredictionMarket, AgentForecast


# ── Schema Tests ─────────────────────────────────────────────────────────────

class TestSchemas:
    def test_agent_position_valid(self):
        pos = AgentPosition(
            recommendation="launch",
            reasoning="Market is ready.",
            confidence=0.85,
            key_concern="Competition from Swiggy.",
        )
        assert pos.confidence == 0.85

    def test_agent_position_clamps_confidence(self):
        with pytest.raises(Exception):
            AgentPosition(
                recommendation="launch",
                reasoning="...",
                confidence=1.5,  # out of range
                key_concern="...",
            )

    def test_round_output(self):
        pos = AgentPosition(
            recommendation="delay",
            reasoning="Need more data.",
            confidence=0.5,
            key_concern="Data availability.",
        )
        output = RoundOutput(agent_name="Founder Agent", round_number=1, position=pos)
        assert output.round_number == 1
        assert output.critiques == []

    def test_moderator_synthesis(self):
        syn = ModeratorSynthesis(
            final_recommendation="Launch pilot in Bangalore",
            reasoning="Balanced risk/reward.",
            points_of_agreement=["Market exists", "AI is feasible"],
            major_disagreements=["Timeline", "Pricing model"],
            confidence_summary={"Founder Agent": 0.8, "Investor Agent": 0.6},
            recommended_next_steps=["Run 4-week pilot", "Measure retention"],
        )
        assert len(syn.points_of_agreement) == 2


# ── Prediction Market Tests ──────────────────────────────────────────────────

class TestPredictionMarket:
    def _make_outputs(self, round_num: int, recs_and_confs: list[tuple[str, float]]) -> list[RoundOutput]:
        """Helper: create RoundOutputs from (recommendation, confidence) tuples."""
        agents = ["Founder Agent", "Investor Agent", "Engineer Agent", "Customer Agent", "Regulator Agent"]
        outputs = []
        for i, (rec, conf) in enumerate(recs_and_confs):
            pos = AgentPosition(
                recommendation=rec,
                reasoning="Test reasoning.",
                confidence=conf,
                key_concern="Test concern.",
            )
            outputs.append(RoundOutput(agent_name=agents[i], round_number=round_num, position=pos))
        return outputs

    def test_full_agreement(self):
        market = PredictionMarket()
        outputs = self._make_outputs(1, [
            ("launch", 0.9), ("launch", 0.8), ("launch", 0.7),
            ("launch", 0.85), ("launch", 0.75),
        ])
        snapshot = market.record_round(outputs)
        assert snapshot.consensus_score == 1.0
        assert snapshot.disagreement_index == 0.0
        assert snapshot.majority_recommendation == "launch"

    def test_split_decision(self):
        market = PredictionMarket()
        outputs = self._make_outputs(1, [
            ("launch", 0.9), ("launch", 0.8), ("delay", 0.7),
            ("delay", 0.85), ("do not launch", 0.75),
        ])
        snapshot = market.record_round(outputs)
        assert 0 < snapshot.disagreement_index <= 1.0
        assert snapshot.consensus_score < 1.0

    def test_confidence_shifts(self):
        market = PredictionMarket()

        r1 = self._make_outputs(1, [
            ("launch", 0.9), ("launch", 0.5), ("delay", 0.7),
            ("launch", 0.6), ("delay", 0.8),
        ])
        r2 = self._make_outputs(2, [
            ("launch", 0.85), ("launch pilot", 0.65), ("launch pilot", 0.6),
            ("launch", 0.7), ("delay", 0.75),
        ])
        market.record_round(r1)
        market.record_round(r2)

        shifts = market.compute_confidence_shifts()
        assert "Founder Agent" in shifts
        assert len(shifts["Founder Agent"]) == 2

    def test_disagreement_matrix(self):
        market = PredictionMarket()
        outputs = self._make_outputs(1, [
            ("launch", 0.9), ("delay", 0.8), ("launch", 0.7),
            ("delay", 0.6), ("do not launch", 0.5),
        ])
        market.record_round(outputs)
        matrix = market.compute_disagreement_matrix()
        # Should have C(5,2) = 10 pairs
        assert len(matrix) == 10
        # Agents with same recommendation should have lower disagreement
        assert matrix[("Founder Agent", "Engineer Agent")] < matrix[("Founder Agent", "Investor Agent")]
