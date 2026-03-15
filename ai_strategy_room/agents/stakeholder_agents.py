"""
agents/stakeholder_agents.py — Concrete stakeholder agents + dynamic factory.

Default agents: Founder, Investor, Engineer, Customer, Regulator.
Fun scenarios can define custom agents via agents_config.
Chaos mode amplifies personality biases.
"""

from langchain_core.language_models import BaseChatModel
from agents.base_agent import StakeholderAgent
from scenarios.examples import CHAOS_OVERRIDES


class FounderAgent(StakeholderAgent):
    name = "Founder Agent"
    role_description = "Startup founder/CEO. Thinks about PMF, speed, morale, vision. Limited runway."
    incentives = "Ship fast, capture market, generate metrics for next fundraise."
    biases = "Over-optimism about market size. Underestimates execution risk. Emotional attachment to idea."
    evaluation_criteria = "Speed to launch, market size, competitive moat, vision alignment, team capability."

    def __init__(self, llm: BaseChatModel, chaos_mode: bool = False):
        super().__init__(llm, chaos_mode)
        if chaos_mode and self.name in CHAOS_OVERRIDES:
            self.chaos_biases = CHAOS_OVERRIDES[self.name]["biases"]
            self.chaos_instruction = CHAOS_OVERRIDES[self.name]["extra_instruction"]


class InvestorAgent(StakeholderAgent):
    name = "Investor Agent"
    role_description = "Series A VC. Cares about unit economics, TAM, defensibility, risk-adjusted returns."
    incentives = "Maximize portfolio return. Avoid losses. Find 10x+ breakout opportunities."
    biases = "Over-indexing on comparable exits. Skeptical of unproven markets. Prefers asset-light models."
    evaluation_criteria = "Unit economics (LTV/CAC), TAM/SAM/SOM, competitive landscape, burn vs milestones."

    def __init__(self, llm: BaseChatModel, chaos_mode: bool = False):
        super().__init__(llm, chaos_mode)
        if chaos_mode and self.name in CHAOS_OVERRIDES:
            self.chaos_biases = CHAOS_OVERRIDES[self.name]["biases"]
            self.chaos_instruction = CHAOS_OVERRIDES[self.name]["extra_instruction"]


class EngineerAgent(StakeholderAgent):
    name = "Engineer Agent"
    role_description = "Senior engineer/tech lead. Thinks about architecture, reliability, tech debt, bandwidth."
    incentives = "Build reliable, maintainable systems. Avoid unrealistic timelines."
    biases = "Over-engineering. Underestimates 'good enough'. Prefers elegance over business impact."
    evaluation_criteria = "Feasibility, infra cost, data availability, model accuracy, build time, scalability."

    def __init__(self, llm: BaseChatModel, chaos_mode: bool = False):
        super().__init__(llm, chaos_mode)
        if chaos_mode and self.name in CHAOS_OVERRIDES:
            self.chaos_biases = CHAOS_OVERRIDES[self.name]["biases"]
            self.chaos_instruction = CHAOS_OVERRIDES[self.name]["extra_instruction"]


class CustomerAgent(StakeholderAgent):
    name = "Customer Agent"
    role_description = "Target customer. Working professional 25-40, health-conscious, time-constrained."
    incentives = "Product that saves time, affordable, respects preferences, integrates with local culture."
    biases = "Subscription fatigue. Skepticism about AI for cultural food. Price sensitivity."
    evaluation_criteria = "Daily usefulness, price, cultural relevance, trust in AI, ease of use, privacy."

    def __init__(self, llm: BaseChatModel, chaos_mode: bool = False):
        super().__init__(llm, chaos_mode)
        if chaos_mode and self.name in CHAOS_OVERRIDES:
            self.chaos_biases = CHAOS_OVERRIDES[self.name]["biases"]
            self.chaos_instruction = CHAOS_OVERRIDES[self.name]["extra_instruction"]


class RegulatorAgent(StakeholderAgent):
    name = "Regulator Agent"
    role_description = "Regulatory advisor. Knows DPDPA 2023, FSSAI, AI governance frameworks."
    incentives = "Protect consumer data, ensure claims aren't misleading, enforce compliance."
    biases = "Risk-aversion. Slow-walks approvals. Overestimates barriers with workarounds."
    evaluation_criteria = "Data privacy, health claim accuracy, food safety, liability, AI transparency."

    def __init__(self, llm: BaseChatModel, chaos_mode: bool = False):
        super().__init__(llm, chaos_mode)
        if chaos_mode and self.name in CHAOS_OVERRIDES:
            self.chaos_biases = CHAOS_OVERRIDES[self.name]["biases"]
            self.chaos_instruction = CHAOS_OVERRIDES[self.name]["extra_instruction"]


# ── Dynamic Agent from Config ────────────────────────────────────────────────

class DynamicAgent(StakeholderAgent):
    """Agent created from scenario config dict (for fun scenarios)."""

    def __init__(self, llm: BaseChatModel, config: dict, chaos_mode: bool = False):
        self.name = config["name"]
        self.role_description = config["role_description"]
        self.incentives = config["incentives"]
        self.biases = config["biases"]
        self.evaluation_criteria = config["evaluation_criteria"]
        super().__init__(llm, chaos_mode)


# ── Factories ────────────────────────────────────────────────────────────────

def create_default_agents(llm: BaseChatModel, chaos_mode: bool = False) -> list[StakeholderAgent]:
    """Create the standard 5 stakeholder agents."""
    return [
        FounderAgent(llm, chaos_mode),
        InvestorAgent(llm, chaos_mode),
        EngineerAgent(llm, chaos_mode),
        CustomerAgent(llm, chaos_mode),
        RegulatorAgent(llm, chaos_mode),
    ]


def create_agents_from_config(
    llm: BaseChatModel, agents_config: list[dict], chaos_mode: bool = False,
) -> list[StakeholderAgent]:
    """Create dynamic agents from scenario config."""
    return [DynamicAgent(llm, cfg, chaos_mode) for cfg in agents_config]


def create_all_agents(llm: BaseChatModel, chaos_mode: bool = False) -> list[StakeholderAgent]:
    """Backwards-compatible factory — creates default agents."""
    return create_default_agents(llm, chaos_mode)


def create_agents_for_scenario(
    llm: BaseChatModel, scenario_config: dict, chaos_mode: bool = False,
) -> list[StakeholderAgent]:
    """Create agents appropriate for a given scenario."""
    agents_config = scenario_config.get("agents_config")
    if agents_config:
        return create_agents_from_config(llm, agents_config, chaos_mode)
    return create_default_agents(llm, chaos_mode)
