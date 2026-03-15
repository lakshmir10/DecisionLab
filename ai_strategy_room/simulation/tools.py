"""
simulation/tools.py — Agent tool-calling interface.

Agents can call tools to gather information during the simulation.
By default, tools are handled by local Python functions that return
scenario-relevant data. If N8N_WEBHOOK_URL is configured, tool calls
route to n8n instead.

Tool-calling protocol:
    Agent responds with one of:
    {"action": "ARGUE", "message": "..."}
    {"action": "CALL_TOOL", "tool": "market_data", "query": "..."}
    {"action": "PASS"}
"""

from __future__ import annotations

import os
import json
import random
import requests
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    """A tool invocation from an agent."""
    agent_name: str
    tool_name: str
    query: str
    round_number: int


@dataclass
class ToolResult:
    """Result returned from a tool call."""
    tool_name: str
    query: str
    result: str
    source: str  # "local" or "n8n"


# ── Available Tools ──────────────────────────────────────────────────────────

AVAILABLE_TOOLS = {
    "market_data": "Look up market size, growth rates, or competitive landscape data",
    "regulatory_check": "Check regulatory requirements, compliance status, or legal risks",
    "technical_feasibility": "Assess technical complexity, infrastructure needs, or build estimates",
    "customer_research": "Get customer sentiment, survey data, or user behavior insights",
    "financial_model": "Run unit economics, ROI projections, or cost estimates",
    "risk_assessment": "Evaluate risk factors, probability of failure modes",
}


def get_tools_description() -> str:
    """Format available tools for agent prompts."""
    lines = ["AVAILABLE TOOLS (you may call ONE per round):"]
    for name, desc in AVAILABLE_TOOLS.items():
        lines.append(f"  - {name}: {desc}")
    return "\n".join(lines)


# ── Local Tool Implementations ───────────────────────────────────────────────

def _local_market_data(query: str, scenario_context: dict) -> str:
    """Simulated market research tool."""
    market_size = scenario_context.get("true_market_size", random.uniform(0.2, 0.8))
    growth = random.uniform(5, 35)
    competitors = random.randint(2, 12)
    return (
        f"Market analysis for '{query}':\n"
        f"  Estimated addressable market: ${market_size * 10:.1f}B\n"
        f"  Annual growth rate: {growth:.0f}%\n"
        f"  Known competitors: {competitors}\n"
        f"  Market maturity: {'emerging' if growth > 20 else 'established'}\n"
        f"  Note: These are estimates with ±20% confidence interval."
    )


def _local_regulatory_check(query: str, scenario_context: dict) -> str:
    """Simulated regulatory lookup."""
    safety_score = scenario_context.get("true_safety_score", random.uniform(0.3, 0.9))
    status = "likely compliant" if safety_score > 0.6 else "regulatory concerns identified"
    return (
        f"Regulatory assessment for '{query}':\n"
        f"  Compliance status: {status}\n"
        f"  Estimated approval timeline: {random.randint(2, 18)} months\n"
        f"  Key requirement: {'Data privacy framework needed' if random.random() > 0.5 else 'Safety certification required'}\n"
        f"  Risk level: {'low' if safety_score > 0.7 else 'medium' if safety_score > 0.4 else 'high'}"
    )


def _local_technical_feasibility(query: str, scenario_context: dict) -> str:
    """Simulated technical assessment."""
    complexity = random.choice(["low", "medium", "high"])
    return (
        f"Technical feasibility for '{query}':\n"
        f"  Complexity: {complexity}\n"
        f"  Estimated build time: {random.randint(2, 12)} months\n"
        f"  Team size needed: {random.randint(3, 15)} engineers\n"
        f"  Key technical risk: {'Model accuracy in production' if random.random() > 0.5 else 'Infrastructure scaling'}\n"
        f"  Existing solutions available: {'yes, partial' if random.random() > 0.4 else 'no, greenfield'}"
    )


def _local_customer_research(query: str, scenario_context: dict) -> str:
    """Simulated customer insights."""
    demand = scenario_context.get("true_demand_score", random.uniform(0.3, 0.9))
    nps = int(demand * 100) - random.randint(0, 20)
    return (
        f"Customer research for '{query}':\n"
        f"  Willingness to pay: {'high' if demand > 0.7 else 'moderate' if demand > 0.4 else 'low'}\n"
        f"  Estimated NPS: {nps}\n"
        f"  Top pain point: {'Time savings' if random.random() > 0.5 else 'Cost reduction'}\n"
        f"  Adoption barrier: {'Switching cost' if random.random() > 0.5 else 'Trust in AI recommendations'}"
    )


def _local_financial_model(query: str, scenario_context: dict) -> str:
    """Simulated financial projections."""
    market_size = scenario_context.get("true_market_size", random.uniform(0.2, 0.8))
    return (
        f"Financial model for '{query}':\n"
        f"  Projected Year 1 revenue: ${market_size * random.uniform(0.5, 2):.1f}M\n"
        f"  Customer acquisition cost: ${random.randint(15, 150)}\n"
        f"  Estimated LTV: ${random.randint(50, 500)}\n"
        f"  Breakeven timeline: {random.randint(12, 36)} months\n"
        f"  Burn rate: ${random.uniform(50, 300):.0f}K/month"
    )


def _local_risk_assessment(query: str, scenario_context: dict) -> str:
    """Simulated risk evaluation."""
    safety = scenario_context.get("true_safety_score", random.uniform(0.3, 0.9))
    return (
        f"Risk assessment for '{query}':\n"
        f"  Overall risk level: {'low' if safety > 0.7 else 'medium' if safety > 0.4 else 'high'}\n"
        f"  Top risk: {'Regulatory rejection' if safety < 0.5 else 'Market timing' if random.random() > 0.5 else 'Execution complexity'}\n"
        f"  Mitigation available: {'yes' if random.random() > 0.3 else 'partial'}\n"
        f"  Probability of critical failure: {max(5, int((1 - safety) * 100))}%"
    )


LOCAL_TOOLS = {
    "market_data": _local_market_data,
    "regulatory_check": _local_regulatory_check,
    "technical_feasibility": _local_technical_feasibility,
    "customer_research": _local_customer_research,
    "financial_model": _local_financial_model,
    "risk_assessment": _local_risk_assessment,
}


# ── Tool Executor ────────────────────────────────────────────────────────────

class ToolExecutor:
    """
    Routes tool calls to local handlers or n8n webhook.

    If N8N_WEBHOOK_URL is set in environment, all tool calls go to n8n.
    Otherwise, local simulated tools handle the request.
    """

    def __init__(self, scenario_context: dict | None = None):
        self.n8n_url = os.getenv("N8N_WEBHOOK_URL", "")
        self.scenario_context = scenario_context or {}
        self.call_log: list[tuple[ToolCall, ToolResult]] = []

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call and return the result."""
        if tool_call.tool_name not in AVAILABLE_TOOLS:
            return ToolResult(
                tool_name=tool_call.tool_name,
                query=tool_call.query,
                result=f"Unknown tool: {tool_call.tool_name}. Available: {', '.join(AVAILABLE_TOOLS.keys())}",
                source="error",
            )

        if self.n8n_url:
            result = self._call_n8n(tool_call)
        else:
            result = self._call_local(tool_call)

        self.call_log.append((tool_call, result))
        return result

    def _call_local(self, tool_call: ToolCall) -> ToolResult:
        """Route to local Python function."""
        handler = LOCAL_TOOLS.get(tool_call.tool_name)
        if not handler:
            return ToolResult(
                tool_name=tool_call.tool_name,
                query=tool_call.query,
                result="Tool not implemented locally.",
                source="error",
            )

        result_text = handler(tool_call.query, self.scenario_context)
        return ToolResult(
            tool_name=tool_call.tool_name,
            query=tool_call.query,
            result=result_text,
            source="local",
        )

    def _call_n8n(self, tool_call: ToolCall) -> ToolResult:
        """Route to n8n webhook."""
        try:
            payload = {
                "agent": tool_call.agent_name,
                "tool": tool_call.tool_name,
                "query": tool_call.query,
                "round": tool_call.round_number,
            }
            response = requests.post(
                self.n8n_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            data = response.json()
            result_text = data.get("result", json.dumps(data))

            return ToolResult(
                tool_name=tool_call.tool_name,
                query=tool_call.query,
                result=result_text,
                source="n8n",
            )
        except requests.RequestException as e:
            # Fallback to local on n8n failure
            local_result = self._call_local(tool_call)
            local_result.source = "local_fallback"
            return local_result
