"""
agents/moderator_agent.py — Moderator that synthesizes the final decision.

The Moderator does NOT participate in the debate. It reads all three rounds
of agent outputs and produces an impartial synthesis.
"""

import json
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import RoundOutput, ModeratorSynthesis


MODERATOR_SYSTEM_PROMPT = """\
You are the Moderator Agent in a strategic decision simulation.

Your job:
1. Read the full debate transcript (3 rounds × 5 agents).
2. Identify the consensus recommendation (or lack thereof).
3. Summarize the major points of agreement and disagreement.
4. Produce a final decision recommendation with reasoning.
5. Report each agent's final confidence score.
6. Suggest concrete next steps.

You are impartial. You do not advocate for any single stakeholder.
You weigh arguments by their reasoning quality, not by the agent's role.

Always respond with valid JSON only. No markdown, no commentary.
"""


class ModeratorAgent:
    """Produces the final synthesis after all debate rounds."""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def synthesize(
        self,
        scenario: str,
        all_rounds: dict[int, list[RoundOutput]],
    ) -> ModeratorSynthesis:
        """
        Produce final synthesis from the full debate history.

        Args:
            scenario: The original decision question.
            all_rounds: {round_number: [RoundOutput, ...]} for rounds 1–3.

        Returns:
            ModeratorSynthesis with final recommendation.
        """
        transcript = self._format_transcript(all_rounds)

        user_prompt = (
            f"DECISION SCENARIO:\n{scenario}\n\n"
            f"FULL DEBATE TRANSCRIPT:\n{transcript}\n\n"
            f"Produce your final synthesis.\n"
            f"Respond ONLY with valid JSON matching this schema:\n"
            f"{ModeratorSynthesis.model_json_schema()}"
        )

        messages = [
            SystemMessage(content=MODERATOR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = self.llm.invoke(messages)
        text = response.content.strip()

        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        return ModeratorSynthesis.model_validate_json(text)

    def _format_transcript(self, all_rounds: dict[int, list[RoundOutput]]) -> str:
        """Convert all rounds into a human-readable transcript string."""
        sections = []
        for round_num in sorted(all_rounds.keys()):
            round_label = {1: "INITIAL POSITIONS", 2: "CRITIQUE & REBUTTAL", 3: "NEGOTIATION & FINAL POSITIONS"}
            sections.append(f"\n{'='*60}")
            sections.append(f"ROUND {round_num}: {round_label.get(round_num, 'UNKNOWN')}")
            sections.append(f"{'='*60}")

            for output in all_rounds[round_num]:
                sections.append(f"\n--- {output.agent_name} ---")
                sections.append(f"Recommendation: {output.position.recommendation}")
                sections.append(f"Reasoning: {output.position.reasoning}")
                sections.append(f"Confidence: {output.position.confidence}")
                sections.append(f"Key concern: {output.position.key_concern}")

                if output.critiques:
                    sections.append("Critiques:")
                    for c in output.critiques:
                        sections.append(f"  → {c.target_agent}: {c.critique}")

                if output.negotiation_proposals:
                    sections.append("Negotiation proposals:")
                    for p in output.negotiation_proposals:
                        sections.append(f"  → {p.proposal} (tradeoffs: {p.tradeoffs})")

        return "\n".join(sections)
