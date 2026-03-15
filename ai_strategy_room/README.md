# ⚡ DecisionLab — Multi-Agent Strategy Simulator

Watch AI agents debate, argue, interrupt, and negotiate strategic decisions.
See who's the loudest — and who's actually right.

## Features

- **11 Scenarios** — Serious (autonomous taxis, startup pivots, geopolitical crises) and fun (family dinner, fantasy kingdom, reality show)
- **Live Debate** — Round-by-round reveal with chat-style arguments, interruptions, and reactions
- **Prediction Market** — Consensus and disagreement tracked across rounds
- **Black Swan Events** — Random disruptions force agents to adapt mid-debate
- **Hidden Ground Truth** — Agents get noisy signals. Truth revealed at the end. Were they right?
- **Bias Detector** — Most influential agent vs most accurate. Loudest ≠ wisest.
- **Chaos Mode** — Toggle extreme agent personalities for chaotic debates
- **Demo Mode** — One-click instant demo, no API key needed
- **Tool Calling** — Agents can call research tools (local simulation or n8n webhook)
- **Random Idea Generator** — Generate absurd startup ideas and watch agents debate them

## Quick Start

```bash
# 1. Clone and install
cd ai_strategy_room
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — add your API key (Gemini free tier works)

# 3. Run
streamlit run ui/app.py
```

**Demo mode works without any API key** — click "Demo" in the sidebar.

## Architecture

```
LangGraph orchestrator
  → Round 1: Agents generate independent positions
  → [Black Swan event may occur]
  → Round 2: Agents critique, interrupt, react
  → [Black Swan event may occur]
  → Round 3: Agents negotiate compromises
  → Moderator synthesizes final verdict
  → Environment scores decision against hidden ground truth
```

## Stack

| Layer | Tech |
|---|---|
| Agent Orchestration | LangGraph |
| LLM | Gemini Flash (default), GPT-4o, Claude, Groq |
| Agent Framework | LangChain + Pydantic |
| Prediction Market | Custom (Shannon entropy, confidence-weighted consensus) |
| Tool Calling | Local Python + optional n8n webhook |
| UI | Streamlit + Plotly |
| Data | Pydantic models, JSON logs |

## n8n Integration (Optional)

Set `N8N_WEBHOOK_URL` in `.env` to route agent tool calls to n8n workflows.
Without it, tools return simulated data derived from the hidden world model.

## LLM Providers

| Provider | Model | Cost |
|---|---|---|
| Gemini (default) | gemini-2.0-flash | Free tier available |
| Groq | llama-3.3-70b | Free tier available |
| OpenAI | gpt-4o | Paid |
| Anthropic | claude-sonnet-4 | Paid |

## Project Structure

```
ai_strategy_room/
├── agents/           # Agent classes + schemas
├── orchestrator/     # LangGraph state graph
├── prediction_market/ # Consensus + disagreement math
├── scenarios/        # 11 scenarios with ground truth
├── simulation/       # Engine, environment, tools, step runner
├── ui/               # Streamlit dashboard
├── data/logs/        # Simulation results
├── config.py         # Provider config
└── main.py           # CLI entry point
```
