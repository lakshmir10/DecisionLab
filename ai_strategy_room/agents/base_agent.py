"""
agents/base_agent.py — Abstract stakeholder agent with tool-calling protocol.

Tool-calling protocol:
  Agent responds with JSON containing one of:
    {"action": "ARGUE", "message": "...", "position": {...}}
    {"action": "CALL_TOOL", "tool": "market_data", "query": "..."}
    {"action": "PASS"}

Agents also support:
  - Interruptions (strong disagreement with another agent)
  - Reactions (support / challenge / warning)
  - Environment signal awareness
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel


# ── Response Schemas ─────────────────────────────────────────────────────────

class AgentPosition(BaseModel):
    recommendation: str = Field(description="Clear recommendation: launch, delay, pivot, do_not_launch, or nuanced variant")
    reasoning: str = Field(description="2-4 sentence justification")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
    key_concern: str = Field(description="Single most important risk or opportunity")


class Critique(BaseModel):
    target_agent: str = Field(description="Agent being critiqued")
    critique: str = Field(description="1-3 sentence critique")
    suggested_revision: str = Field(description="What they should reconsider")


class NegotiationProposal(BaseModel):
    proposal: str = Field(description="Specific compromise")
    tradeoffs: str = Field(description="What is gained and given up")
    conditions: str = Field(description="Conditions for this to work")


class Reaction(BaseModel):
    """An agent's reaction to another agent's argument."""
    target_agent: str = Field(description="Agent being reacted to")
    reaction_type: str = Field(description="support, challenge, or warning")
    message: str = Field(description="1-2 sentence reaction")


class Interruption(BaseModel):
    """A strong disagreement that interrupts the debate flow."""
    target_agent: str = Field(description="Agent being interrupted")
    message: str = Field(description="1-2 sentence sharp disagreement")
    severity: str = Field(default="high", description="medium or high")


class RoundOutput(BaseModel):
    agent_name: str
    round_number: int
    position: AgentPosition
    critiques: list[Critique] = Field(default_factory=list)
    negotiation_proposals: list[NegotiationProposal] = Field(default_factory=list)
    reactions: list[Reaction] = Field(default_factory=list)
    interruption: Optional[Interruption] = None
    tool_call: Optional[dict] = None  # {"tool": "...", "query": "...", "result": "..."}


class ModeratorSynthesis(BaseModel):
    final_recommendation: str
    reasoning: str
    points_of_agreement: list[str]
    major_disagreements: list[str]
    confidence_summary: dict[str, float]
    recommended_next_steps: list[str]


# ── Abstract Agent ───────────────────────────────────────────────────────────

class StakeholderAgent(ABC):
    """
    Base class for all stakeholder agents.

    Subclasses define: name, role_description, incentives, biases, evaluation_criteria.
    Optionally: chaos_biases, chaos_instruction for chaos mode.
    """

    name: str
    role_description: str
    incentives: str
    biases: str
    evaluation_criteria: str
    chaos_biases: str = ""
    chaos_instruction: str = ""

    def __init__(self, llm: BaseChatModel, chaos_mode: bool = False):
        self.llm = llm
        self.chaos_mode = chaos_mode

    # ── Round 1: Initial Position ────────────────────────────────────────

    def generate_initial_position(
        self, scenario: str, signals_text: str = "", events_text: str = "",
        tools_text: str = "",
    ) -> RoundOutput:
        system_prompt = self._build_system_prompt()
        user_prompt = (
            f"SCENARIO: {scenario}\n\n"
            f"{signals_text}\n{events_text}\n\n"
            f"{tools_text}\n\n"
            f"As the {self.name}, provide your initial position.\n\n"
            f"You MUST respond with valid JSON in this exact format:\n"
            f'{{"action": "ARGUE", "position": {{"recommendation": "...", "reasoning": "...", '
            f'"confidence": 0.0, "key_concern": "..."}}}}\n\n'
            f'OR if you want to gather data first:\n'
            f'{{"action": "CALL_TOOL", "tool": "tool_name", "query": "your question"}}\n\n'
            f"Respond with JSON only. No markdown."
        )
        return self._execute_round(system_prompt, user_prompt, round_number=1)

    # ── Round 2: Critique & Revise ───────────────────────────────────────

    def critique_and_revise(
        self, scenario: str, own_previous: RoundOutput,
        other_positions: list[RoundOutput],
        signals_text: str = "", events_text: str = "",
    ) -> RoundOutput:
        system_prompt = self._build_system_prompt()

        others_text = "\n\n".join(
            f"--- {op.agent_name} ---\n"
            f"Recommendation: {op.position.recommendation}\n"
            f"Reasoning: {op.position.reasoning}\n"
            f"Confidence: {op.position.confidence}\n"
            f"Key concern: {op.position.key_concern}"
            for op in other_positions
        )

        user_prompt = (
            f"SCENARIO: {scenario}\n\n"
            f"{signals_text}\n{events_text}\n\n"
            f"YOUR PREVIOUS POSITION:\n"
            f"Recommendation: {own_previous.position.recommendation}\n"
            f"Reasoning: {own_previous.position.reasoning}\n\n"
            f"OTHER AGENTS:\n{others_text}\n\n"
            f"Critique others, react to their arguments, and revise your position.\n"
            f"If you STRONGLY disagree with someone, you may interrupt.\n\n"
            f"Respond with JSON:\n"
            f'{{"action": "ARGUE", "position": {{...}}, "critiques": [{{...}}], '
            f'"reactions": [{{"target_agent": "...", "reaction_type": "support|challenge|warning", "message": "..."}}], '
            f'"interruption": null | {{"target_agent": "...", "message": "...", "severity": "high"}}}}\n\n'
            f"JSON only. No markdown."
        )

        raw = self._call_llm_raw(system_prompt, user_prompt)
        parsed = self._safe_parse(raw)

        position = AgentPosition(**parsed.get("position", {
            "recommendation": own_previous.position.recommendation,
            "reasoning": "Maintained previous position.",
            "confidence": own_previous.position.confidence,
            "key_concern": own_previous.position.key_concern,
        }))
        critiques = [Critique(**c) for c in parsed.get("critiques", [])]
        reactions = [Reaction(**r) for r in parsed.get("reactions", [])]

        interruption = None
        if parsed.get("interruption"):
            try:
                interruption = Interruption(**parsed["interruption"])
            except Exception:
                pass

        return RoundOutput(
            agent_name=self.name, round_number=2,
            position=position, critiques=critiques,
            reactions=reactions, interruption=interruption,
        )

    # ── Round 3: Negotiate ───────────────────────────────────────────────

    def negotiate(
        self, scenario: str, own_previous: RoundOutput,
        all_critiques: list[Critique], other_positions: list[RoundOutput],
        signals_text: str = "", events_text: str = "",
    ) -> RoundOutput:
        system_prompt = self._build_system_prompt()

        critiques_text = "\n".join(
            f"- {c.target_agent}: {c.critique}" for c in all_critiques
        ) or "No critiques directed at you."

        others_text = "\n".join(
            f"- {op.agent_name}: {op.position.recommendation} (confidence: {op.position.confidence})"
            for op in other_positions
        )

        user_prompt = (
            f"SCENARIO: {scenario}\n\n"
            f"{signals_text}\n{events_text}\n\n"
            f"YOUR POSITION: {own_previous.position.recommendation} "
            f"(confidence: {own_previous.position.confidence})\n\n"
            f"CRITIQUES OF YOU:\n{critiques_text}\n\n"
            f"OTHERS:\n{others_text}\n\n"
            f"Final round. Propose compromises and state your FINAL position.\n\n"
            f"Respond with JSON:\n"
            f'{{"action": "ARGUE", "position": {{...}}, "negotiation_proposals": [{{...}}], '
            f'"reactions": [{{...}}]}}\n\n'
            f"JSON only."
        )

        raw = self._call_llm_raw(system_prompt, user_prompt)
        parsed = self._safe_parse(raw)

        position = AgentPosition(**parsed.get("position", {
            "recommendation": own_previous.position.recommendation,
            "reasoning": "Maintained position after negotiation.",
            "confidence": own_previous.position.confidence,
            "key_concern": own_previous.position.key_concern,
        }))
        proposals = [NegotiationProposal(**p) for p in parsed.get("negotiation_proposals", [])]
        reactions = [Reaction(**r) for r in parsed.get("reactions", [])]

        return RoundOutput(
            agent_name=self.name, round_number=3,
            position=position, negotiation_proposals=proposals,
            reactions=reactions,
        )

    # ── Internal Helpers ─────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        biases = self.chaos_biases if (self.chaos_mode and self.chaos_biases) else self.biases
        extra = ""
        if self.chaos_mode and self.chaos_instruction:
            extra = f"\nSPECIAL INSTRUCTION: {self.chaos_instruction}\n"

        return (
            f"You are the {self.name} in a strategic decision simulation.\n\n"
            f"ROLE: {self.role_description}\n"
            f"INCENTIVES: {self.incentives}\n"
            f"KNOWN BIASES: {biases}\n"
            f"YOU EVALUATE DECISIONS BY: {self.evaluation_criteria}\n"
            f"{extra}\n"
            f"Rules:\n"
            f"- Always respond with valid JSON only. No markdown, no commentary.\n"
            f"- Be opinionated. Take a clear stance. Don't hedge excessively.\n"
            f"- Your arguments should be 1-3 sentences, punchy and specific.\n"
            f"- If you strongly disagree with another agent, you may interrupt.\n"
        )

    def _execute_round(self, system_prompt: str, user_prompt: str, round_number: int) -> RoundOutput:
        raw = self._call_llm_raw(system_prompt, user_prompt)
        parsed = self._safe_parse(raw)

        action = parsed.get("action", "ARGUE")

        if action == "CALL_TOOL":
            return RoundOutput(
                agent_name=self.name, round_number=round_number,
                position=AgentPosition(
                    recommendation="pending_tool_call",
                    reasoning="Gathering data before taking a position.",
                    confidence=0.5,
                    key_concern="Need more information.",
                ),
                tool_call={"tool": parsed.get("tool", ""), "query": parsed.get("query", "")},
            )

        position = AgentPosition(**parsed.get("position", {
            "recommendation": "undecided",
            "reasoning": "Could not form a position.",
            "confidence": 0.5,
            "key_concern": "Insufficient information.",
        }))

        return RoundOutput(
            agent_name=self.name, round_number=round_number,
            position=position,
        )

    def _call_llm_raw(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = self.llm.invoke(messages)
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()
        return text

    def _safe_parse(self, raw: str) -> dict:
        """Parse JSON with fallback for malformed responses."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(raw[start:end])
                except json.JSONDecodeError:
                    pass
            return {"action": "ARGUE", "position": {
                "recommendation": "undecided",
                "reasoning": f"Agent response could not be parsed.",
                "confidence": 0.5,
                "key_concern": "Response format error.",
            }}
