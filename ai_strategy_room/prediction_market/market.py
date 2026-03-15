"""
prediction_market/market.py — Forecast aggregation and consensus scoring.

Implements a simple prediction market that:
  1. Collects each agent's confidence-weighted forecast.
  2. Aggregates into a consensus probability using confidence-weighted averaging.
  3. Computes disagreement metrics.
  4. Tracks confidence shifts across rounds.

No exotic dependencies — just standard math and dataclasses.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from agents.base_agent import RoundOutput


@dataclass
class AgentForecast:
    """A single agent's forecast at a point in time."""

    agent_name: str
    recommendation: str
    confidence: float  # 0–1
    round_number: int


@dataclass
class MarketSnapshot:
    """Aggregated market state at a given point."""

    round_number: int
    forecasts: list[AgentForecast]
    consensus_score: float        # Weighted average confidence in majority position
    disagreement_index: float     # 0 = full agreement, 1 = maximum disagreement
    majority_recommendation: str
    recommendation_distribution: dict[str, int]  # recommendation → count


@dataclass
class PredictionMarket:
    """
    Collects agent forecasts and computes market-level metrics.

    Usage:
        market = PredictionMarket()
        market.record_round(round_outputs)  # call after each round
        snapshot = market.get_snapshot(round_number)
        shifts = market.compute_confidence_shifts()
    """

    snapshots: dict[int, MarketSnapshot] = field(default_factory=dict)

    # ── Core API ─────────────────────────────────────────────────────────

    def record_round(self, round_outputs: list[RoundOutput]) -> MarketSnapshot:
        """
        Record all agent outputs for a round and compute the snapshot.

        Args:
            round_outputs: List of RoundOutput for every agent in this round.

        Returns:
            MarketSnapshot for this round.
        """
        round_number = round_outputs[0].round_number
        forecasts = [
            AgentForecast(
                agent_name=o.agent_name,
                recommendation=self._normalize_recommendation(o.position.recommendation),
                confidence=o.position.confidence,
                round_number=round_number,
            )
            for o in round_outputs
        ]

        # Count recommendations
        rec_dist: dict[str, int] = {}
        for f in forecasts:
            rec_dist[f.recommendation] = rec_dist.get(f.recommendation, 0) + 1

        majority_rec = max(rec_dist, key=rec_dist.get)  # type: ignore[arg-type]

        consensus_score = self._compute_consensus(forecasts, majority_rec)
        disagreement = self._compute_disagreement(forecasts)

        snapshot = MarketSnapshot(
            round_number=round_number,
            forecasts=forecasts,
            consensus_score=consensus_score,
            disagreement_index=disagreement,
            majority_recommendation=majority_rec,
            recommendation_distribution=rec_dist,
        )
        self.snapshots[round_number] = snapshot
        return snapshot

    def get_snapshot(self, round_number: int) -> MarketSnapshot | None:
        return self.snapshots.get(round_number)

    def compute_confidence_shifts(self) -> dict[str, list[float]]:
        """
        Track how each agent's confidence changed across rounds.

        Returns:
            {agent_name: [round_1_conf, round_2_conf, round_3_conf]}
        """
        shifts: dict[str, list[float]] = {}
        for round_num in sorted(self.snapshots.keys()):
            for forecast in self.snapshots[round_num].forecasts:
                shifts.setdefault(forecast.agent_name, []).append(forecast.confidence)
        return shifts

    def compute_disagreement_matrix(self) -> dict[tuple[str, str], float]:
        """
        Pairwise disagreement between agents in the final round.

        Returns:
            {(agent_a, agent_b): disagreement_score} where 0 = agree, 1 = fully disagree.
        """
        final_round = max(self.snapshots.keys()) if self.snapshots else None
        if final_round is None:
            return {}

        forecasts = self.snapshots[final_round].forecasts
        matrix = {}
        for i, a in enumerate(forecasts):
            for j, b in enumerate(forecasts):
                if i < j:
                    # Disagreement = 1 if different recommendation, scaled by confidence gap
                    rec_diff = 0.0 if a.recommendation == b.recommendation else 1.0
                    conf_diff = abs(a.confidence - b.confidence)
                    score = 0.7 * rec_diff + 0.3 * conf_diff
                    matrix[(a.agent_name, b.agent_name)] = round(score, 3)
        return matrix

    # ── Internal math ────────────────────────────────────────────────────

    @staticmethod
    def _compute_consensus(forecasts: list[AgentForecast], majority_rec: str) -> float:
        """
        Confidence-weighted consensus score.

        Agents agreeing with the majority contribute positively;
        dissenters subtract, weighted by their confidence.
        """
        total_weight = sum(f.confidence for f in forecasts)
        if total_weight == 0:
            return 0.0

        agreement_weight = sum(
            f.confidence for f in forecasts if f.recommendation == majority_rec
        )
        return round(agreement_weight / total_weight, 3)

    @staticmethod
    def _compute_disagreement(forecasts: list[AgentForecast]) -> float:
        """
        Disagreement index based on recommendation entropy.

        0 = all agents agree, 1 = maximum disagreement (each agent different).
        Uses normalized Shannon entropy.
        """
        n = len(forecasts)
        if n <= 1:
            return 0.0

        rec_counts: dict[str, int] = {}
        for f in forecasts:
            rec_counts[f.recommendation] = rec_counts.get(f.recommendation, 0) + 1

        # Shannon entropy
        entropy = 0.0
        for count in rec_counts.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log2(p)

        # Normalize: max entropy = log2(n)
        max_entropy = math.log2(n)
        return round(entropy / max_entropy, 3) if max_entropy > 0 else 0.0

    @staticmethod
    def _normalize_recommendation(rec: str) -> str:
        """Normalize recommendation to a canonical form for comparison."""
        rec_lower = rec.lower().strip()
        if "launch" in rec_lower and "pilot" in rec_lower:
            return "launch_pilot"
        elif "launch" in rec_lower and ("delay" not in rec_lower and "not" not in rec_lower):
            return "launch"
        elif "delay" in rec_lower:
            return "delay"
        elif "pivot" in rec_lower:
            return "pivot"
        elif "not" in rec_lower or "don't" in rec_lower or "against" in rec_lower:
            return "do_not_launch"
        else:
            return rec_lower[:30]  # fallback: truncated original
