"""
simulation/environment.py — Hidden world model and environment signals.

Each scenario has hidden ground-truth parameters that agents cannot see.
Agents receive noisy signals derived from these values.
At simulation end, the environment reveals truth and scores decisions.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroundTruth:
    """Hidden parameters that determine the real outcome."""
    params: dict[str, float]       # e.g. {"true_market_size": 0.35, "true_safety_score": 0.72}
    true_outcome: str              # e.g. "delay", "launch", "failure"
    outcome_explanation: str       # Why this is the true outcome
    scoring_rules: dict[str, str]  # Maps recommendation → result description


@dataclass
class EnvironmentSignal:
    """A noisy observation derived from a hidden parameter."""
    parameter_name: str
    true_value: float
    observed_value: float
    noise_level: float
    label: str  # Human-readable label for UI


@dataclass
class BlackSwanEvent:
    """A disruptive event injected between rounds."""
    name: str
    description: str
    impact: str               # What changes
    severity: str             # "low", "medium", "high", "critical"
    affected_agents: list[str]  # Which agents are most impacted
    parameter_shifts: dict[str, float]  # How hidden params change


@dataclass
class DecisionScore:
    """Final scoring comparing agents' recommendation vs ground truth."""
    recommended: str
    true_outcome: str
    was_correct: bool
    accuracy_explanation: str
    agent_scores: dict[str, dict[str, Any]]  # per-agent accuracy breakdown
    calibration_error: float  # Average |confidence - accuracy|


class Environment:
    """
    Manages the hidden world, generates signals, injects events,
    and scores decisions at the end.
    """

    def __init__(self, ground_truth: GroundTruth, black_swan_pool: list[BlackSwanEvent] | None = None):
        self.ground_truth = ground_truth
        self.black_swan_pool = black_swan_pool or []
        self.active_events: list[BlackSwanEvent] = []
        self.signal_history: list[list[EnvironmentSignal]] = []
        self._current_params = dict(ground_truth.params)

    def generate_signals(self, round_number: int, noise_scale: float = 0.15) -> list[EnvironmentSignal]:
        """
        Generate noisy observations of hidden parameters.
        Noise decreases slightly each round (agents learn more over time).
        """
        round_noise = noise_scale * (1.0 - 0.1 * (round_number - 1))
        signals = []

        for param_name, true_val in self._current_params.items():
            noise = random.gauss(0, round_noise)
            observed = max(0.0, min(1.0, true_val + noise))
            label = param_name.replace("true_", "").replace("_", " ").title()
            signals.append(EnvironmentSignal(
                parameter_name=param_name,
                true_value=true_val,
                observed_value=round(observed, 3),
                noise_level=round(round_noise, 3),
                label=label,
            ))

        self.signal_history.append(signals)
        return signals

    def maybe_trigger_black_swan(self, round_number: int, probability: float = 0.3) -> BlackSwanEvent | None:
        """
        Potentially trigger a black swan event between rounds.
        Returns the event if triggered, None otherwise.
        """
        if not self.black_swan_pool:
            return None
        if random.random() > probability:
            return None

        event = random.choice(self.black_swan_pool)
        self.black_swan_pool.remove(event)
        self.active_events.append(event)

        # Apply parameter shifts
        for param, shift in event.parameter_shifts.items():
            if param in self._current_params:
                self._current_params[param] = max(0.0, min(1.0,
                    self._current_params[param] + shift
                ))

        return event

    def force_black_swan(self, event_name: str) -> BlackSwanEvent | None:
        """Force a specific black swan event by name (for demo mode)."""
        for event in self.black_swan_pool:
            if event.name == event_name:
                self.black_swan_pool.remove(event)
                self.active_events.append(event)
                for param, shift in event.parameter_shifts.items():
                    if param in self._current_params:
                        self._current_params[param] = max(0.0, min(1.0,
                            self._current_params[param] + shift
                        ))
                return event
        return None

    def score_decision(self, final_recommendation: str, agent_outputs: dict[int, list]) -> DecisionScore:
        """
        Score the final decision against ground truth.
        """
        rec_normalized = final_recommendation.lower().strip()
        true_normalized = self.ground_truth.true_outcome.lower().strip()

        # Simple match check
        was_correct = rec_normalized == true_normalized or rec_normalized in true_normalized or true_normalized in rec_normalized

        # Score each agent
        agent_scores = {}
        if 3 in agent_outputs:
            for output in agent_outputs[3]:
                agent_rec = output.position.recommendation.lower().strip()
                agent_correct = agent_rec == true_normalized or agent_rec in true_normalized or true_normalized in agent_rec
                agent_scores[output.agent_name] = {
                    "recommendation": output.position.recommendation,
                    "confidence": output.position.confidence,
                    "was_correct": agent_correct,
                    "calibration_error": round(abs(output.position.confidence - (1.0 if agent_correct else 0.0)), 3),
                }

        # Average calibration error
        cal_errors = [s["calibration_error"] for s in agent_scores.values()]
        avg_cal = round(sum(cal_errors) / len(cal_errors), 3) if cal_errors else 0.0

        explanation = self.ground_truth.scoring_rules.get(
            rec_normalized,
            f"Recommendation '{final_recommendation}' vs true outcome '{self.ground_truth.true_outcome}'"
        )

        return DecisionScore(
            recommended=final_recommendation,
            true_outcome=self.ground_truth.true_outcome,
            was_correct=was_correct,
            accuracy_explanation=explanation,
            agent_scores=agent_scores,
            calibration_error=avg_cal,
        )

    def get_signals_text(self, round_number: int) -> str:
        """Format signals as text for agent prompts."""
        if round_number - 1 >= len(self.signal_history):
            return "No signals available yet."

        signals = self.signal_history[round_number - 1]
        lines = [f"ENVIRONMENT SIGNALS (Round {round_number}):"]
        for s in signals:
            lines.append(f"  {s.label}: {s.observed_value:.1%} (estimated)")
        return "\n".join(lines)

    def get_events_text(self) -> str:
        """Format active events as text for agent prompts."""
        if not self.active_events:
            return ""

        lines = ["BREAKING EVENTS:"]
        for e in self.active_events:
            lines.append(f"  ⚠ {e.name}: {e.description}")
            lines.append(f"    Impact: {e.impact}")
        return "\n".join(lines)
