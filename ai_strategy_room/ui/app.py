"""
ui/app.py — DecisionLab: Multi-Agent Strategy Simulator

Run with:  cd ai_strategy_room && streamlit run ui/app.py

An engaging war-room experience where users watch AI agents
debate strategic decisions in real-time.
"""

import sys, os, time, random, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from scenarios.examples import (
    ALL_SCENARIOS, SCENARIOS, FUN_SCENARIOS,
    get_random_startup_idea, list_serious_scenarios, list_fun_scenarios,
)
from simulation.step_runner import (
    run_simulation_steps, save_simulation_log, RoundResult, SynthesisResult,
)

# ── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="DecisionLab", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ── Theme CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

.stApp { background: #0a0b0f; font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background: #0f1016; border-right: 1px solid #1a1b25; }
[data-testid="stSidebar"] * { color: #c0c4d0 !important; }

/* Hero banner */
.hero { text-align: center; padding: 1.5rem 0 0.5rem; }
.hero h1 { font-size: 2.2rem; font-weight: 900; letter-spacing: -1px;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
.hero p { color: #64748b; font-size: 0.85rem; margin-top: 0.3rem; }

/* Agent cards */
.agent-grid { display: flex; gap: 0.6rem; flex-wrap: wrap; margin: 0.8rem 0; }
.agent-card { flex: 1; min-width: 150px; background: #12131a; border: 1px solid #1e2030;
    border-radius: 10px; padding: 0.8rem; transition: all 0.3s; position: relative; overflow: hidden; }
.agent-card:hover { border-color: #3b82f6; transform: translateY(-2px); box-shadow: 0 4px 20px rgba(59,130,246,0.15); }
.agent-name { font-weight: 700; font-size: 0.9rem; color: #e2e8f0; margin-bottom: 0.3rem; }
.agent-role { font-size: 0.7rem; color: #64748b; line-height: 1.4; }
.agent-stance { margin-top: 0.5rem; padding: 0.3rem 0.6rem; border-radius: 6px;
    font-size: 0.7rem; font-weight: 600; display: inline-block; }
.stance-launch { background: #064e3b; color: #6ee7b7; }
.stance-delay { background: #78350f; color: #fbbf24; }
.stance-pivot { background: #312e81; color: #a5b4fc; }
.stance-error, .stance-undecided { background: #1e1b2e; color: #64748b; }
.confidence-bar { height: 4px; border-radius: 2px; background: #1e2030; margin-top: 0.4rem; overflow: hidden; }
.confidence-fill { height: 100%; border-radius: 2px; transition: width 0.5s ease; }

/* Debate feed */
.debate-msg { background: #12131a; border: 1px solid #1e2030; border-radius: 10px;
    padding: 0.9rem 1rem; margin: 0.5rem 0; position: relative; }
.debate-msg .agent-label { font-weight: 700; font-size: 0.8rem; margin-bottom: 0.3rem; }
.debate-msg .msg-text { font-size: 0.82rem; color: #c0c4d0; line-height: 1.5; }
.debate-msg .meta { font-size: 0.68rem; color: #475569; margin-top: 0.4rem; }

/* Interruption */
.interruption { background: linear-gradient(135deg, #1a0505, #2d0a0a); border: 1px solid #7f1d1d;
    border-radius: 10px; padding: 0.9rem 1rem; margin: 0.6rem 0;
    animation: shake 0.4s ease-in-out; }
@keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-4px)} 75%{transform:translateX(4px)} }
.interruption .label { color: #fca5a5; font-weight: 800; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }

/* Reactions */
.reaction { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.5rem;
    border-radius: 12px; font-size: 0.68rem; font-weight: 600; margin: 0.15rem; }
.reaction-support { background: #064e3b; color: #6ee7b7; }
.reaction-challenge { background: #7f1d1d; color: #fca5a5; }
.reaction-warning { background: #78350f; color: #fbbf24; }

/* Black swan alert */
.black-swan { background: linear-gradient(135deg, #1a0f05, #2d1a0a); border: 2px solid #b45309;
    border-radius: 12px; padding: 1rem 1.2rem; margin: 1rem 0;
    animation: pulse-border 2s ease-in-out infinite; }
@keyframes pulse-border { 0%,100%{border-color:#b45309} 50%{border-color:#f59e0b} }
.black-swan .bs-title { color: #fbbf24; font-weight: 800; font-size: 0.9rem; margin-bottom: 0.3rem; }
.black-swan .bs-desc { color: #d4a373; font-size: 0.8rem; }

/* Ground truth reveal */
.reveal-box { border-radius: 12px; padding: 1.2rem; margin: 1rem 0; text-align: center; }
.reveal-correct { background: linear-gradient(135deg, #042f1a, #064e3b); border: 2px solid #10b981; }
.reveal-wrong { background: linear-gradient(135deg, #2d0a0a, #450a0a); border: 2px solid #ef4444; }
.reveal-title { font-size: 1.1rem; font-weight: 800; margin-bottom: 0.5rem; }
.reveal-detail { font-size: 0.82rem; color: #94a3b8; line-height: 1.5; }

/* Round header */
.round-hdr { background: linear-gradient(135deg, #0f1729, #162040); border-left: 4px solid #3b82f6;
    padding: 0.7rem 1rem; border-radius: 0 8px 8px 0; margin: 1.2rem 0 0.6rem;
    font-weight: 700; color: #93c5fd; font-size: 0.9rem; }

/* Metric cards */
.metric-row { display: flex; gap: 0.6rem; margin: 0.8rem 0; }
.metric-card { flex: 1; background: #12131a; border: 1px solid #1e2030; border-radius: 10px;
    padding: 0.8rem; text-align: center; }
.metric-val { font-size: 1.4rem; font-weight: 800; color: #e2e8f0; }
.metric-label { font-size: 0.68rem; color: #64748b; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.05em; }

/* Bias table */
.bias-alert { background: #2d1a0a; border: 1px solid #b45309; border-radius: 8px;
    padding: 0.6rem 0.8rem; margin: 0.5rem 0; font-size: 0.78rem; color: #fbbf24; }

/* Orchestration flow */
.orch-flow { display: flex; align-items: center; gap: 0; margin: 1rem 0; padding: 0.6rem 1rem;
    background: #0c0d14; border: 1px solid #1e2030; border-radius: 10px; overflow-x: auto; }
.orch-step { padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.68rem; font-weight: 600;
    white-space: nowrap; transition: all 0.3s; color: #475569; background: #12131a; border: 1px solid #1e2030; }
.orch-step.active { color: #60a5fa; background: #172554; border-color: #3b82f6;
    box-shadow: 0 0 12px rgba(59,130,246,0.3); animation: orch-pulse 1.5s ease-in-out infinite; }
.orch-step.done { color: #4ade80; background: #052e16; border-color: #166534; }
.orch-step.event { color: #fbbf24; background: #422006; border-color: #b45309; }
.orch-arrow { color: #334155; margin: 0 0.3rem; font-size: 0.7rem; }
@keyframes orch-pulse { 0%,100%{box-shadow:0 0 12px rgba(59,130,246,0.3)} 50%{box-shadow:0 0 20px rgba(59,130,246,0.5)} }

/* Tool call in debate */
.tool-call { background: #0f0f1a; border: 1px solid #312e81; border-left: 3px solid #6366f1;
    border-radius: 8px; padding: 0.7rem 0.9rem; margin: 0.3rem 0 0.5rem 1.5rem; }
.tool-call .tool-label { font-size: 0.7rem; font-weight: 700; color: #818cf8; margin-bottom: 0.2rem; }
.tool-call .tool-result { font-size: 0.72rem; color: #94a3b8; font-family: 'Courier New', monospace; }

/* Typing cursor for demo */
.typing-indicator { display: inline-block; width: 8px; height: 14px; background: #60a5fa;
    animation: blink 0.8s ease-in-out infinite; border-radius: 1px; margin-left: 4px; vertical-align: middle; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
</style>
""", unsafe_allow_html=True)


# ── Agent Color Map ──────────────────────────────────────────────────────────

AGENT_COLORS = {
    "Founder Agent": "#3b82f6", "Investor Agent": "#8b5cf6", "Engineer Agent": "#10b981",
    "Customer Agent": "#f59e0b", "Regulator Agent": "#ef4444",
    "Mom 👩‍🍳": "#ec4899", "Dad 👨‍💼": "#3b82f6", "Teenager 🎮": "#a855f7", "Grandma 👵": "#f59e0b",
    "King Aldric 👑": "#fbbf24", "General Thorne ⚔️": "#ef4444", "Economist Sera 📊": "#10b981",
    "Spymaster Vale 🕵️": "#8b5cf6", "High Priestess Yara 🙏": "#ec4899",
    "Risk-Taker Rachel 🎰": "#ef4444", "Cautious Carlos 🛡️": "#3b82f6",
    "Strategist Sana 🧠": "#10b981", "Influencer Isha 📱": "#ec4899",
    "Alliance-Builder Alex 🤝": "#a855f7",
}


def get_color(name: str) -> str:
    return AGENT_COLORS.get(name, "#6366f1")


def stance_class(rec: str) -> str:
    r = rec.lower()
    if "launch" in r and "not" not in r: return "stance-launch"
    if "delay" in r: return "stance-delay"
    if "pivot" in r: return "stance-pivot"
    return "stance-undecided"


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ DecisionLab")
    st.markdown("*Multi-Agent Strategy Simulator*")
    st.markdown("---")

    # Scenario selection with categories
    cat = st.radio("Category", ["🎯 Serious", "🎪 Fun", "🎲 Random Idea"], horizontal=True)

    if cat == "🎯 Serious":
        keys = list_serious_scenarios()
        labels = {k: ALL_SCENARIOS[k]["title"] for k in keys}
        chosen = st.selectbox("Scenario", keys, format_func=lambda k: labels[k])
    elif cat == "🎪 Fun":
        keys = list_fun_scenarios()
        labels = {k: ALL_SCENARIOS[k]["title"] for k in keys}
        chosen = st.selectbox("Scenario", keys, format_func=lambda k: labels[k])
    else:
        if st.button("🎲 Generate Random Idea", use_container_width=True):
            st.session_state["random_idea"] = get_random_startup_idea()
        idea = st.session_state.get("random_idea", "Click to generate!")
        st.info(idea)
        chosen = "startup_pitch"  # Use startup pitch agents for random ideas

    st.markdown("---")

    chaos = st.toggle("😈 Chaos Mode", value=False,
                       help="Agents become extreme personalities")

    st.markdown("---")

    # Bring Your Own Key — visitors can paste their own key
    with st.expander("🔑 API Key (for Run mode)", expanded=False):
        st.caption("Demo works without a key. Run mode needs one.")
        byok_provider = st.selectbox("Provider", ["groq", "gemini", "openai", "anthropic"], index=0)
        byok_key = st.text_input("API Key", type="password", placeholder="Paste your key here")
        if byok_key:
            # Override environment vars at runtime
            os.environ["LLM_PROVIDER"] = byok_provider
            provider_key_map = {"groq": "GROQ_API_KEY", "gemini": "GOOGLE_API_KEY", "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
            os.environ[provider_key_map[byok_provider]] = byok_key
            st.success(f"Using your {byok_provider} key")
        st.caption("[Free Groq key](https://console.groq.com) · [Free Gemini key](https://aistudio.google.com/app/apikey)")

    st.markdown("---")

    col_run, col_demo = st.columns(2)
    with col_run:
        run_btn = st.button("▶ Run", type="primary", use_container_width=True)
    with col_demo:
        demo_btn = st.button("👀 Demo", use_container_width=True, help="Watch a pre-built simulation")

    if st.session_state.get("mode"):
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.pop("mode", None)
            st.rerun()

    # Persist button state across reruns
    if run_btn:
        st.session_state["mode"] = "run"
    if demo_btn:
        st.session_state["mode"] = "demo"

    active_mode = st.session_state.get("mode", None)
    # Reset if scenario changes
    if "last_scenario" in st.session_state and st.session_state["last_scenario"] != chosen:
        active_mode = None
        st.session_state.pop("mode", None)
    st.session_state["last_scenario"] = chosen

    st.markdown("---")
    st.caption("LangGraph · Gemini/GPT · Streamlit · Plotly")
    st.caption(f"~16 LLM calls per simulation")


# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>DecisionLab</h1>
    <p>Watch AI agents debate, disagree, and decide — in real time</p>
</div>
""", unsafe_allow_html=True)

# ── Scenario Card ────────────────────────────────────────────────────────────

scenario_cfg = ALL_SCENARIOS[chosen]
# Handle random idea override
if cat == "🎲 Random Idea" and "random_idea" in st.session_state:
    scenario_cfg = dict(scenario_cfg)
    scenario_cfg["description"] = (
        f"Should a startup build: {st.session_state['random_idea']}? "
        f"They have $3M in funding, a 3-person team, and 12 months of runway."
    )
    scenario_cfg["title"] = f"🎲 {st.session_state['random_idea'][:50]}..."

st.markdown(f"### {scenario_cfg['title']}")
st.markdown(f"> {scenario_cfg['description']}")


# ── Helper: Render Agent Cards ───────────────────────────────────────────────

def render_agent_cards(agents_info: list[dict], outputs: list | None = None):
    """Render the agent war room panel."""
    output_map = {}
    if outputs:
        output_map = {o.agent_name: o for o in outputs}

    cards_html = '<div class="agent-grid">'
    for info in agents_info:
        name = info["name"]
        color = get_color(name)
        out = output_map.get(name)

        stance_html = ""
        conf_html = '<div class="confidence-bar"><div class="confidence-fill" style="width:0%;background:#374151;"></div></div>'

        if out:
            rec = out.position.recommendation
            conf = out.position.confidence
            sc = stance_class(rec)
            stance_html = f'<div class="agent-stance {sc}">{rec.replace("_", " ").title()}</div>'
            conf_html = f'<div class="confidence-bar"><div class="confidence-fill" style="width:{conf*100:.0f}%;background:{color};"></div></div>'

        cards_html += f'''
        <div class="agent-card" style="border-top: 3px solid {color};">
            <div class="agent-name" style="color:{color};">{name}</div>
            <div class="agent-role">{info.get("role_description", info.get("biases", ""))[:80]}...</div>
            {stance_html}{conf_html}
        </div>'''
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


def get_agents_info(scenario_config: dict) -> list[dict]:
    """Extract agent info for display."""
    if scenario_config.get("agents_config"):
        return scenario_config["agents_config"]
    return [
        {"name": "Founder Agent", "role_description": "Startup CEO. Speed, vision, PMF.", "biases": "Over-optimistic"},
        {"name": "Investor Agent", "role_description": "VC. Unit economics, TAM, returns.", "biases": "Exit-focused"},
        {"name": "Engineer Agent", "role_description": "Tech lead. Feasibility, architecture.", "biases": "Over-engineers"},
        {"name": "Customer Agent", "role_description": "Target user. Value, price, trust.", "biases": "Price-sensitive"},
        {"name": "Regulator Agent", "role_description": "Compliance. Privacy, safety, law.", "biases": "Risk-averse"},
    ]


# ── Helper: Render Orchestration Flow ───────────────────────────────────────

ORCH_STEPS = [
    ("signals_1", "📡 Signals"),
    ("round_1", "💬 Round 1"),
    ("event_check_1", "🦢 Event?"),
    ("signals_2", "📡 Signals"),
    ("round_2", "⚔️ Round 2"),
    ("event_check_2", "🦢 Event?"),
    ("signals_3", "📡 Signals"),
    ("round_3", "🤝 Round 3"),
    ("synthesize", "🏛 Verdict"),
    ("reveal", "🎯 Truth"),
]

def render_orchestration_flow(active_step: str = "", completed: set | None = None, events_fired: set | None = None):
    """Render the live orchestration state machine visualization."""
    completed = completed or set()
    events_fired = events_fired or set()

    html = '<div class="orch-flow">'
    for i, (step_id, label) in enumerate(ORCH_STEPS):
        if i > 0:
            html += '<span class="orch-arrow">→</span>'

        if step_id == active_step:
            css = "orch-step active"
        elif step_id in completed:
            if step_id in events_fired:
                css = "orch-step event"
            else:
                css = "orch-step done"
        else:
            css = "orch-step"

        html += f'<span class="{css}">{label}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── Helper: Render Debate Message ────────────────────────────────────────────

def render_debate_message(output, show_critiques=True, show_reactions=True):
    color = get_color(output.agent_name)

    # Main argument
    st.markdown(f'''
    <div class="debate-msg" style="border-left: 3px solid {color};">
        <div class="agent-label" style="color:{color};">{output.agent_name}</div>
        <div class="msg-text">
            <strong>{output.position.recommendation.replace("_"," ").title()}</strong> —
            {output.position.reasoning}
        </div>
        <div class="meta">
            Confidence: {output.position.confidence:.0%} · Key concern: {output.position.key_concern}
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Tool call
    if output.tool_call and output.tool_call.get("tool"):
        st.markdown(f'''
        <div class="debate-msg" style="border-left: 3px solid #6366f1; background: #0f0f1a;">
            <div class="agent-label" style="color:#6366f1;">🔧 Tool Call — {output.tool_call["tool"]}</div>
            <div class="msg-text" style="font-size:0.75rem;">Query: {output.tool_call.get("query","")}</div>
            <div class="msg-text" style="font-size:0.75rem;color:#94a3b8;">{output.tool_call.get("result","")[:200]}</div>
        </div>
        ''', unsafe_allow_html=True)

    # Interruption
    if output.interruption:
        st.markdown(f'''
        <div class="interruption">
            <div class="label">⚠ INTERRUPTION — {output.agent_name} disputes {output.interruption.target_agent}</div>
            <div class="msg-text" style="color:#fca5a5;">{output.interruption.message}</div>
        </div>
        ''', unsafe_allow_html=True)

    # Reactions
    if show_reactions and output.reactions:
        rxn_html = ""
        for r in output.reactions:
            emoji = {"support": "👍", "challenge": "⚔️", "warning": "⚠️"}.get(r.reaction_type, "💬")
            cls = f"reaction-{r.reaction_type}"
            rxn_html += f'<span class="reaction {cls}">{emoji} {r.target_agent.split(" ")[0]}: {r.message[:60]}</span> '
        st.markdown(rxn_html, unsafe_allow_html=True)

    # Critiques
    if show_critiques and output.critiques:
        with st.expander(f"💬 Critiques ({len(output.critiques)})", expanded=False):
            for c in output.critiques:
                st.markdown(f"**→ {c.target_agent}:** {c.critique}")

    # Proposals
    if output.negotiation_proposals:
        with st.expander(f"🤝 Proposals ({len(output.negotiation_proposals)})", expanded=False):
            for p in output.negotiation_proposals:
                st.markdown(f"**{p.proposal}**")
                st.caption(f"Tradeoffs: {p.tradeoffs}")


# ── Helper: Render Black Swan ────────────────────────────────────────────────

def render_black_swan(event):
    if not event:
        return
    st.markdown(f'''
    <div class="black-swan">
        <div class="bs-title">🦢 BLACK SWAN EVENT: {event.name}</div>
        <div class="bs-desc">{event.description}</div>
        <div class="bs-desc" style="margin-top:0.4rem;color:#94a3b8;">
            Impact: {event.impact} · Severity: {event.severity.upper()}
        </div>
    </div>
    ''', unsafe_allow_html=True)


# ── Helper: Render Charts ────────────────────────────────────────────────────

def render_market_chart(rounds_data: list[RoundResult]):
    """Prediction market consensus + disagreement over rounds."""
    if not rounds_data:
        return

    r_nums = [r.round_number for r in rounds_data]
    consensus = [r.market_snapshot.consensus_score for r in rounds_data]
    disagree = [r.market_snapshot.disagreement_index for r in rounds_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[f"R{r}" for r in r_nums], y=consensus,
        mode="lines+markers", name="Consensus", line=dict(color="#10b981", width=3), marker=dict(size=10)))
    fig.add_trace(go.Scatter(x=[f"R{r}" for r in r_nums], y=disagree,
        mode="lines+markers", name="Disagreement", line=dict(color="#ef4444", width=3), marker=dict(size=10)))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 1.05], title="Score", gridcolor="#1e2030"),
        xaxis=dict(gridcolor="#1e2030"), height=280, margin=dict(l=40, r=20, t=30, b=30),
        legend=dict(orientation="h", yanchor="top", y=1.12),
        font=dict(family="Inter", color="#94a3b8"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_confidence_chart(synthesis: SynthesisResult):
    """Confidence evolution per agent."""
    if not synthesis.confidence_shifts:
        return

    fig = go.Figure()
    for agent_name, confs in synthesis.confidence_shifts.items():
        fig.add_trace(go.Scatter(
            x=["R1", "R2", "R3"][:len(confs)], y=confs,
            mode="lines+markers", name=agent_name.replace(" Agent", ""),
            line=dict(color=get_color(agent_name), width=2), marker=dict(size=8),
        ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 1.05], title="Confidence", gridcolor="#1e2030"),
        xaxis=dict(gridcolor="#1e2030"), height=280, margin=dict(l=40, r=20, t=30, b=30),
        legend=dict(orientation="h", yanchor="top", y=1.15, font=dict(size=10)),
        font=dict(family="Inter", color="#94a3b8"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_bias_detector(synthesis: SynthesisResult):
    """Show influence vs accuracy — highlight when most influential ≠ most accurate."""
    score = synthesis.decision_score
    influence = synthesis.influence_scores
    if not score.agent_scores or not influence:
        return

    rows = []
    for agent_name, data in score.agent_scores.items():
        rows.append({
            "Agent": agent_name,
            "Influence": f"{influence.get(agent_name, 0):.0%}",
            "Confidence": f"{data['confidence']:.0%}",
            "Correct?": "✅" if data["was_correct"] else "❌",
            "Cal. Error": f"{data['calibration_error']:.2f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Alert if most influential agent was wrong
    if influence:
        top_influencer = max(influence, key=influence.get)
        top_data = score.agent_scores.get(top_influencer, {})
        if top_data and not top_data.get("was_correct", True):
            st.markdown(f'''
            <div class="bias-alert">
                ⚠ <strong>Bias Alert:</strong> The most influential agent ({top_influencer}) made
                the wrong recommendation. Persuasion ≠ Accuracy.
            </div>
            ''', unsafe_allow_html=True)


def render_ground_truth(synthesis: SynthesisResult):
    """The big reveal."""
    ds = synthesis.decision_score
    cls = "reveal-correct" if ds.was_correct else "reveal-wrong"
    icon = "✅" if ds.was_correct else "❌"
    st.markdown(f'''
    <div class="reveal-box {cls}">
        <div class="reveal-title">{icon} GROUND TRUTH REVEALED</div>
        <div class="reveal-detail">
            <strong>Decision:</strong> {ds.recommended.replace("_"," ").title()}<br>
            <strong>True Outcome:</strong> {ds.true_outcome.replace("_"," ").title()}<br>
            <strong>Verdict:</strong> {"CORRECT" if ds.was_correct else "INCORRECT"}<br><br>
            {ds.accuracy_explanation}
        </div>
    </div>
    ''', unsafe_allow_html=True)


# ── Main Simulation Runner ───────────────────────────────────────────────────

agents_info = get_agents_info(scenario_cfg)

if active_mode == "run":
    st.markdown("---")

    # Orchestration flow — live state machine
    orch_placeholder = st.empty()
    completed_steps = set()
    events_fired = set()

    with orch_placeholder:
        render_orchestration_flow("signals_1", completed_steps, events_fired)

    # Agent cards — will update each round
    agent_panel = st.empty()
    agent_panel.markdown("#### 🎖 Agents")
    render_agent_cards(agents_info)

    # Containers for progressive reveal
    debate_container = st.container()
    chart_col1, chart_col2 = st.columns(2)

    rounds_data: list[RoundResult] = []
    synthesis_data: SynthesisResult | None = None

    status_placeholder = st.empty()
    status_placeholder.info("⏳ Running simulation... agents are thinking (this takes 30-90 seconds)")

    try:
        with debate_container:
            for step in run_simulation_steps(chosen, scenario_cfg, chaos_mode=chaos):
                if isinstance(step, RoundResult):
                    rnd = step.round_number
                    rounds_data.append(step)

                    status_placeholder.info(f"⏳ Round {rnd} complete. {'Waiting for next round...' if rnd < 3 else 'Synthesizing verdict...'}")

                    # Update orchestration flow
                    completed_steps.add(f"signals_{rnd}")
                    completed_steps.add(f"round_{rnd}")
                    if step.black_swan_event:
                        events_fired.add(f"event_check_{rnd}")
                    completed_steps.add(f"event_check_{rnd}")

                    next_active = f"signals_{rnd+1}" if rnd < 3 else "synthesize"
                    with orch_placeholder:
                        render_orchestration_flow(next_active, completed_steps, events_fired)

                    # Round header
                    st.markdown(f'<div class="round-hdr">Round {step.round_number} — {step.round_label}</div>', unsafe_allow_html=True)

                    # Black swan event (dramatic reveal)
                    if step.black_swan_event:
                        render_black_swan(step.black_swan_event)

                    # Each agent's argument
                    for output in step.outputs:
                        render_debate_message(
                            output,
                            show_critiques=(step.round_number >= 2),
                            show_reactions=(step.round_number >= 2),
                        )

                    # Update agent cards with latest stances
                    agent_panel.empty()
                    with agent_panel:
                        st.markdown("#### 🎖 Agents")
                        render_agent_cards(agents_info, step.outputs)

                    # Show market chart so far
                    with chart_col1:
                        st.markdown("##### 📊 Prediction Market")
                        render_market_chart(rounds_data)

                elif isinstance(step, SynthesisResult):
                    synthesis_data = step
                    completed_steps.add("synthesize")
                    with orch_placeholder:
                        render_orchestration_flow("reveal", completed_steps, events_fired)

        status_placeholder.empty()

    except Exception as e:
        status_placeholder.empty()
        st.error(f"**Simulation failed:** {type(e).__name__}: {e}")
        st.markdown("**Troubleshooting:**")
        st.markdown("1. Check your `.env` file has `LLM_PROVIDER` and the matching API key")
        st.markdown("2. Check the terminal running `streamlit run ui/app.py` for full traceback")
        st.markdown("3. Try `LLM_PROVIDER=groq` with a free Groq key from console.groq.com")
        import traceback
        with st.expander("Full traceback"):
            st.code(traceback.format_exc())

    # ── Final Synthesis ──
    if synthesis_data:
        st.markdown("---")
        st.markdown("### 🏛 Moderator's Verdict")

        syn = synthesis_data.synthesis
        st.success(f"**Recommendation:** {syn.final_recommendation}")
        st.write(syn.reasoning)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**✅ Agreement**")
            for p in syn.points_of_agreement:
                st.write(f"• {p}")
        with col_b:
            st.markdown("**⚠️ Disagreements**")
            for p in syn.major_disagreements:
                st.write(f"• {p}")

        if syn.recommended_next_steps:
            st.markdown("**Next Steps**")
            for i, s in enumerate(syn.recommended_next_steps, 1):
                st.write(f"{i}. {s}")

        # Ground truth reveal
        st.markdown("---")
        st.markdown("### 🔍 Ground Truth Reveal")
        render_ground_truth(synthesis_data)

        # Mark orchestration complete
        completed_steps.add("reveal")
        with orch_placeholder:
            render_orchestration_flow("", completed_steps, events_fired)

        # Confidence chart
        with chart_col2:
            st.markdown("##### 📈 Confidence Evolution")
            render_confidence_chart(synthesis_data)

        # Bias detector
        st.markdown("---")
        st.markdown("### 🔬 Bias Detector — Influence vs Accuracy")
        render_bias_detector(synthesis_data)

        # Save log
        try:
            log_path = save_simulation_log(chosen, rounds_data, synthesis_data)
            st.caption(f"📁 Simulation logged to {log_path}")
        except Exception:
            pass


# ── Demo Autoplay Mode ───────────────────────────────────────────────────────

elif active_mode == "demo":
    st.markdown("---")
    st.markdown("### 👀 Demo Mode — Family Dinner: Where to Vacation?")
    st.caption("🎬 Pre-generated data — no API key needed. Watch the agents argue!")

    # Orchestration flow for demo
    demo_orch = st.empty()
    demo_completed = set()
    demo_events_fired = set()

    with demo_orch:
        render_orchestration_flow("signals_1", demo_completed, demo_events_fired)

    # Pre-baked demo for family dinner
    demo_agents = [
        {"name": "Mom 👩‍🍳", "rec": "Rajasthan", "conf": [0.6, 0.7, 0.85], "concern": "Photo opportunities"},
        {"name": "Dad 👨‍💼", "rec": "Rajasthan", "conf": [0.5, 0.6, 0.80], "concern": "Budget control"},
        {"name": "Teenager 🎮", "rec": "Bali", "conf": [0.9, 0.7, 0.55], "concern": "FOMO from friends"},
        {"name": "Grandma 👵", "rec": "Rajasthan", "conf": [0.8, 0.85, 0.95], "concern": "Temple visits"},
    ]

    demo_events = [
        None,
        {"name": "Best Friend Going to Bali", "desc": "Teenager's best friend announces family Bali trip. FOMO intensifies.", "severity": "MEDIUM"},
        {"name": "Grandma's Temple Dream", "desc": "Grandma mentions wanting to see Ranakpur Jain Temple 'before her time comes.'", "severity": "HIGH"},
    ]

    demo_debates = [
        [ # Round 1
            ("Mom 👩‍🍳", "Rajasthan", "Rajasthan has the best palace hotels and photo spots. We can do a heritage walk in Jaipur and sunset at Udaipur — my feed will thank me.", 0.60),
            ("Dad 👨‍💼", "Goa", "Goa is the cheapest option and I know the routes. We stayed at that nice place last time, remember? Why fix what works.", 0.50),
            ("Teenager 🎮", "Bali", "Bali is literally where everyone goes. My friend's family went and got 10K likes on their reel. India vacations are boring.", 0.90),
            ("Grandma 👵", "Rajasthan", "Rajasthan has beautiful temples and the food is proper vegetarian. My knees can't handle Manali and I'm not sitting on a beach for 7 days.", 0.80),
        ],
        [ # Round 2
            ("Mom 👩‍🍳", "Rajasthan", "Dad, Goa is getting too commercialized. And beta, Bali will blow our entire budget on flights alone — Rajasthan heritage hotels are half the price.", 0.70),
            ("Dad 👨‍💼", "Rajasthan", "Fine, I looked it up. Rajasthan is actually cheaper than Goa this season. Those palace hotels have pools. I can relax.", 0.60),
            ("Teenager 🎮", "Bali", "But EVERYONE is going to Bali! Can't we just do Bali for 5 days and skip the fancy hotels? I'll share a room!", 0.70),
            ("Grandma 👵", "Rajasthan", "Beta, Bali doesn't have proper food. Last time your uncle went abroad he ate bread for a week. Rajasthan has dal baati churma.", 0.85),
        ],
        [ # Round 3
            ("Mom 👩‍🍳", "Rajasthan", "Final answer: Rajasthan. Jaipur → Udaipur → Jodhpur. Teenager gets the zip line at Mehrangarh Fort. Dad gets pool. Grandma gets temples. I get photos. Done.", 0.85),
            ("Dad 👨‍💼", "Rajasthan", "I'm sold. The MakeMyTrip deal on Udaipur lake palace is too good. Under budget with money left for shopping.", 0.80),
            ("Teenager 🎮", "Rajasthan", "FINE. But only if we do the camel safari AND the zip line. And I need good WiFi for posting.", 0.55),
            ("Grandma 👵", "Rajasthan", "Ranakpur temple, then Nathdwara. And proper thali meals. This is going to be wonderful.", 0.95),
        ],
    ]

    demo_interruptions = [
        [],
        [("Grandma 👵", "Teenager 🎮", "Beta, I went to Bali in 1985. The temples there are ALSO Hindu temples. You want temples? We have better ones at home for free.")],
        [("Teenager 🎮", "Dad 👨‍💼", "Dad you ALWAYS pick the same boring trips! At least Rajasthan has zip lines!")],
    ]

    # Render demo agents
    st.markdown("#### 🎖 Agents")
    demo_info = [{"name": a["name"], "role_description": "", "biases": ""} for a in demo_agents]

    for round_idx in range(3):
        round_num = round_idx + 1

        # Update orchestration flow
        demo_completed.add(f"signals_{round_num}")
        with demo_orch:
            render_orchestration_flow(f"round_{round_num}", demo_completed, demo_events_fired)

        # Timed pause between rounds for drama
        time.sleep(0.15)

        round_labels = {1: "Initial Positions", 2: "Critique & Rebuttal", 3: "Negotiation & Final Positions"}
        st.markdown(f'<div class="round-hdr">Round {round_num} — {round_labels[round_num]}</div>', unsafe_allow_html=True)

        # Black swan
        ev = demo_events[round_idx]
        if ev:
            demo_events_fired.add(f"event_check_{round_num}")
            st.markdown(f'''
            <div class="black-swan">
                <div class="bs-title">🦢 BLACK SWAN: {ev["name"]}</div>
                <div class="bs-desc">{ev["desc"]}</div>
                <div class="bs-desc" style="color:#94a3b8;">Severity: {ev["severity"]}</div>
            </div>
            ''', unsafe_allow_html=True)

        demo_completed.add(f"event_check_{round_num}")

        # Interruptions
        for interrupter, target, msg in demo_interruptions[round_idx]:
            time.sleep(0.08)
            st.markdown(f'''
            <div class="interruption">
                <div class="label">⚠ INTERRUPTION — {interrupter} disputes {target}</div>
                <div class="msg-text" style="color:#fca5a5;">{msg}</div>
            </div>
            ''', unsafe_allow_html=True)

        # Arguments — each agent appears with a brief delay
        for name, rec, reasoning, conf in demo_debates[round_idx]:
            time.sleep(0.1)
            color = get_color(name)
            st.markdown(f'''
            <div class="debate-msg" style="border-left: 3px solid {color};">
                <div class="agent-label" style="color:{color};">{name}</div>
                <div class="msg-text"><strong>{rec}</strong> — {reasoning}</div>
                <div class="meta">Confidence: {conf:.0%}</div>
            </div>
            ''', unsafe_allow_html=True)

        # Mark round complete in orch flow
        demo_completed.add(f"round_{round_num}")
        with demo_orch:
            next_step = f"signals_{round_num+1}" if round_num < 3 else "synthesize"
            render_orchestration_flow(next_step, demo_completed, demo_events_fired)

    # Final reveal
    time.sleep(0.15)

    # Synthesize step
    demo_completed.add("synthesize")
    with demo_orch:
        render_orchestration_flow("reveal", demo_completed, demo_events_fired)

    st.markdown("---")
    st.markdown("### 🏛 Verdict: Rajasthan wins!")
    st.success("**The Kumar family is going to Rajasthan.** Jaipur → Udaipur → Jodhpur, 7 days.")

    time.sleep(0.1)

    # Truth reveal
    demo_completed.add("reveal")
    with demo_orch:
        render_orchestration_flow("", demo_completed, demo_events_fired)

    st.markdown(f'''
    <div class="reveal-box reveal-correct">
        <div class="reveal-title">✅ GROUND TRUTH: RAJASTHAN WAS CORRECT</div>
        <div class="reveal-detail">
            Rajasthan balanced everyone's needs: temples for Grandma, palaces for Mom's photos,
            affordable for Dad, adventure activities for Teenager. Bali would have blown the budget.
            Goa was too party for Grandma. Manali too strenuous for her knees.
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Demo confidence chart
    fig = go.Figure()
    for a in demo_agents:
        fig.add_trace(go.Scatter(
            x=["R1", "R2", "R3"], y=a["conf"],
            mode="lines+markers", name=a["name"],
            line=dict(color=get_color(a["name"]), width=2), marker=dict(size=8),
        ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 1.05], title="Confidence", gridcolor="#1e2030"),
        height=300, font=dict(family="Inter", color="#94a3b8"),
        legend=dict(orientation="h", yanchor="top", y=1.12),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f'''
    <div class="bias-alert">
        ⚠ <strong>Insight:</strong> Teenager was most confident (90%) but ended up wrong.
        Grandma was right all along. Sometimes the quietest voice has the best answer.
    </div>
    ''', unsafe_allow_html=True)


# ── Default State (no simulation yet) ────────────────────────────────────────

else:
    st.markdown("#### 🎖 Agents")
    render_agent_cards(agents_info)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-val">▶</div>
            <div class="metric-label">Click Run to start</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-val">👀</div>
            <div class="metric-label">Or watch the Demo</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-val">😈</div>
            <div class="metric-label">Try Chaos Mode</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Select a scenario, click Run to watch agents debate in real-time, or click Demo for an instant preview.")
