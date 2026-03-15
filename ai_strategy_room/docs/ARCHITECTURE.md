# Architecture — AI Decision Simulation Lab

## Agent Orchestration Flow

```
                    ┌──────────────────────────────────────────────────┐
                    │                 USER INPUT                       │
                    │  "Should a startup launch an AI meal-planning    │
                    │   app in India?"                                 │
                    └──────────────────┬───────────────────────────────┘
                                       │
                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │               LANGGRAPH ORCHESTRATOR                   │
              │                                                        │
              │  SimulationState = {scenario, current_round,           │
              │                     round_outputs, synthesis}          │
              └────────────────────────┬───────────────────────────────┘
                                       │
                    ╔══════════════════╧═══════════════════╗
                    ║         ROUND 1: Initial Positions    ║
                    ╚══════════════════╤═══════════════════╝
                                       │
              ┌────────┬────────┬──────┴──┬──────────┬──────────┐
              ▼        ▼        ▼         ▼          ▼          │
          Founder  Investor  Engineer  Customer  Regulator      │
          Agent    Agent     Agent     Agent     Agent          │
           │        │         │         │          │            │
           └────────┴─────────┴─────────┴──────────┘            │
                              │                                 │
                    ╔════════╧════════════════════════╗         │
                    ║  ROUND 2: Critique & Rebuttal    ║         │
                    ╚════════╤════════════════════════╝         │
                             │                                 │
                    Each agent reads others' Round 1            │
                    positions → generates critiques →           │
                    revises own position                        │
                             │                                 │
                    ╔════════╧════════════════════════╗         │
                    ║  ROUND 3: Negotiation            ║         │
                    ╚════════╤════════════════════════╝         │
                             │                                 │
                    Each agent reads critiques received →       │
                    proposes up to 3 compromises →              │
                    states FINAL position + confidence          │
                             │                                 │
              ┌──────────────┴──────────────┐                   │
              ▼                             ▼                   │
     Prediction Market              Moderator Agent             │
     ┌─────────────────┐    ┌───────────────────────┐          │
     │ Collect forecasts│    │ Read full transcript   │          │
     │ Aggregate probs  │    │ Identify consensus     │          │
     │ Compute consensus│    │ List agreements        │          │
     │ Track shifts     │    │ List disagreements     │          │
     │ Disagreement map │    │ Produce recommendation │          │
     └────────┬────────┘    │ Suggest next steps     │          │
              │              └───────────┬───────────┘          │
              │                          │                      │
              └──────────┬───────────────┘                      │
                         ▼                                      │
              ┌──────────────────────────────────────┐          │
              │          STREAMLIT DASHBOARD          │          │
              │                                      │          │
              │  📜 Debate Timeline                   │          │
              │  📊 Confidence Tracker (line chart)   │          │
              │  🔥 Disagreement Heatmap              │          │
              │  🎯 Prediction Market (gauge + pie)   │          │
              │  📋 Final Synthesis Report            │          │
              └──────────────────────────────────────┘
```

## Agent Design Matrix

| Agent | Role | Primary Incentive | Known Bias | Evaluates By |
|-------|------|-------------------|------------|--------------|
| Founder | CEO / visionary | Ship fast, show traction | Over-optimism, idea attachment | Market size, speed, vision fit |
| Investor | Series A VC | Risk-adjusted 10x return | Exit-comparable thinking | Unit economics, TAM, burn rate |
| Engineer | Tech lead | Reliable, maintainable systems | Over-engineering | Feasibility, cost, maintenance |
| Customer | Target user (India) | Real daily value, affordable | Subscription fatigue, price sensitivity | Usefulness, price, cultural fit |
| Regulator | Gov. regulatory advisor | Consumer protection, compliance | Risk-aversion, slow-walking | DPDPA, FSSAI, liability, transparency |

## Debate Round Logic

### Round 1 — Initial Positions
- Each agent receives ONLY the scenario.
- No visibility into other agents.
- Outputs: recommendation, reasoning, confidence, key concern.

### Round 2 — Critique & Rebuttal
- Each agent receives: its own Round 1 output + all other agents' Round 1 outputs.
- Must critique each other agent (1–3 sentences per critique).
- Must revise its own position based on what it learned.
- Confidence may go up or down.

### Round 3 — Negotiation
- Each agent receives: its Round 2 output + all critiques targeting it + all agents' Round 2 outputs.
- Must propose up to 3 compromise proposals (e.g., "launch pilot in 2 cities").
- Must state FINAL position and confidence.
- This is the agent's last word.

### Synthesis
- Moderator reads the complete 3-round transcript.
- Does NOT participate in the debate.
- Produces: final recommendation, agreements, disagreements, confidence summary, next steps.

## Prediction Market Math

**Consensus Score** = (sum of confidence for agents agreeing with majority) / (total confidence)

**Disagreement Index** = normalized Shannon entropy of recommendation distribution
- 0 = all agents agree
- 1 = every agent has a different recommendation

**Disagreement Matrix** = pairwise score for each agent pair:
- 0.7 × (1 if different recommendation, else 0) + 0.3 × |confidence_a - confidence_b|
