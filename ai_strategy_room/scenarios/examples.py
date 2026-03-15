"""
scenarios/examples.py — All scenario definitions with ground truth and events.

Each scenario includes:
  - title: display name with emoji
  - description: the decision question
  - agents_config: optional agent overrides for fun scenarios (None = use defaults)
  - ground_truth: hidden parameters and true outcome
  - black_swan_pool: possible disruptive events
"""

from __future__ import annotations
import random as _random
from simulation.environment import GroundTruth, BlackSwanEvent


# ═══════════════════════════════════════════════════════════════════════════════
# SERIOUS SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════

SCENARIOS = {

    "ai_meal_planning_india": {
        "title": "🍛 AI Meal Planning App — India Launch",
        "description": (
            "Should a startup launch an AI-powered meal-planning app in India? "
            "The app uses ML to recommend personalized weekly meal plans based on "
            "dietary preferences, health goals, local cuisine availability, and "
            "budget. The team has 18 months of runway and $2M in seed funding."
        ),
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.42, "true_safety_score": 0.81, "true_demand_score": 0.55, "true_competition_level": 0.65, "regulatory_threshold": 0.60},
            true_outcome="launch_pilot",
            outcome_explanation="Market is moderate but growing. Regulatory risk is low. Demand is moderate — pilot in 2 cities is correct, not full launch.",
            scoring_rules={"launch": "Premature — demand is only moderate", "launch_pilot": "Correct — validates demand before burning runway", "delay": "Overly cautious — regulatory environment is favorable", "do_not_launch": "Wrong — genuine opportunity exists", "pivot": "Unnecessary — concept is sound"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Competitor Launch", description="A well-funded competitor backed by Swiggy launches a similar feature", impact="First-mover advantage gone. Speed critical.", severity="high", affected_agents=["Founder Agent", "Investor Agent"], parameter_shifts={"true_competition_level": 0.20, "true_market_size": -0.05}),
            BlackSwanEvent(name="FSSAI Regulation Change", description="FSSAI mandates health disclaimers on AI dietary advice", impact="2-month compliance delay required.", severity="medium", affected_agents=["Regulator Agent", "Engineer Agent"], parameter_shifts={"true_safety_score": -0.15, "regulatory_threshold": 0.10}),
            BlackSwanEvent(name="Viral TikTok Moment", description="Food influencer goes viral using prototype — 50K signups overnight", impact="Sudden demand surge. Infrastructure readiness questioned.", severity="medium", affected_agents=["Customer Agent", "Engineer Agent"], parameter_shifts={"true_demand_score": 0.25}),
        ],
    },

    "autonomous_delivery_europe": {
        "title": "🤖 Autonomous Delivery Robots — Europe",
        "description": "Should a logistics company deploy autonomous delivery robots in Berlin, Amsterdam, and Barcelona? Each city costs €5M with a 2-year breakeven target.",
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.68, "true_safety_score": 0.45, "true_demand_score": 0.72, "true_competition_level": 0.40, "regulatory_threshold": 0.70},
            true_outcome="delay",
            outcome_explanation="Strong demand but safety score below regulatory threshold. EU AI Act requires certification that takes 8-12 months.",
            scoring_rules={"launch": "Wrong — safety below threshold, faces EU enforcement", "launch_pilot": "Partial — reduces risk but safety gap remains", "delay": "Correct — wait for certification", "do_not_launch": "Overly cautious — opportunity is real"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Robot Accident in Helsinki", description="Competitor's robot injures pedestrian, making EU headlines", impact="Public backlash. Regulatory scrutiny intensifies.", severity="critical", affected_agents=["Regulator Agent", "Customer Agent"], parameter_shifts={"true_safety_score": -0.20, "regulatory_threshold": 0.15}),
            BlackSwanEvent(name="EU Fast-Track Program", description="EU announces regulatory sandbox with expedited approval for autonomous delivery", impact="Certification drops from 12 months to 4.", severity="high", affected_agents=["Regulator Agent", "Founder Agent"], parameter_shifts={"regulatory_threshold": -0.20}),
        ],
    },

    "enterprise_copilot": {
        "title": "🧠 AI Copilot for Project Management",
        "description": "Should a B2B SaaS company ($80M ARR) build an AI copilot into its PM product? Auto-generates tasks, risk assessments, timelines. 6-month build, team of 8.",
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.75, "true_safety_score": 0.88, "true_demand_score": 0.82, "true_competition_level": 0.70, "regulatory_threshold": 0.30},
            true_outcome="launch",
            outcome_explanation="Strong demand, low risk, but competition is fierce. Ship ASAP or lose differentiation.",
            scoring_rules={"launch": "Correct — market ready, risk low, speed critical", "launch_pilot": "Suboptimal — delays give competitors time", "delay": "Wrong — window closing", "do_not_launch": "Competitive death sentence"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="OpenAI Ships PM Agent", description="OpenAI launches standalone AI project manager integrating with every PM tool", impact="Feature commoditized before launch.", severity="critical", affected_agents=["Founder Agent", "Investor Agent", "Engineer Agent"], parameter_shifts={"true_competition_level": 0.25, "true_demand_score": -0.10}),
        ],
    },

    "healthtech_pivot": {
        "title": "💊 B2C to B2B Healthtech Pivot",
        "description": "Pivot from B2C fitness tracker (50K MAU, flat) to B2B wellness platform? Fortune 500 wants a pilot. Requires 9-month rebuild.",
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.58, "true_safety_score": 0.75, "true_demand_score": 0.40, "true_competition_level": 0.55, "regulatory_threshold": 0.50},
            true_outcome="pivot",
            outcome_explanation="B2C growth is genuinely flat. Fortune 500 pilot validates B2B demand. Pivot is painful but correct.",
            scoring_rules={"launch": "Wrong — more B2C features won't fix flat growth", "pivot": "Correct — B2B demand validated", "delay": "Risky — Fortune 500 won't wait", "do_not_launch": "Partially correct but pivot is better"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Fortune 500 CEO Change", description="Champion at Fortune 500 gets replaced. New leadership reviews all pilots.", impact="B2B pilot at risk.", severity="high", affected_agents=["Founder Agent", "Investor Agent"], parameter_shifts={"true_demand_score": -0.15}),
        ],
    },

    "open_source_model": {
        "title": "🔓 Open Source vs Proprietary AI Model",
        "description": "Release latest LLM as open source (Apache 2.0) or keep proprietary with API access? Scores within 5%% of GPT-4.",
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.85, "true_safety_score": 0.60, "true_demand_score": 0.90, "true_competition_level": 0.80, "regulatory_threshold": 0.55},
            true_outcome="launch",
            outcome_explanation="Open source is correct. API revenue under pressure. Open source builds ecosystem lock-in and enterprise support revenue.",
            scoring_rules={"launch": "Correct — ecosystem effects maximize long-term value", "delay": "Wrong — competitors capture narrative", "do_not_launch": "Wrong — proprietary-only unsustainable"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Model Jailbreak Goes Viral", description="Researchers find harmful content generation exploit, published on social media", impact="Safety concerns dominate. Open sourcing looks irresponsible.", severity="critical", affected_agents=["Regulator Agent", "Founder Agent"], parameter_shifts={"true_safety_score": -0.25}),
        ],
    },

    "geopolitical_crisis": {
        "title": "🌍 Rare Earth Supply Chain Crisis",
        "description": "China announces 90-day rare earth export ban. Your chip company has 45 days of inventory. Stockpile? Alternative suppliers? Redesign chips? Lobby government?",
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.90, "true_safety_score": 0.30, "true_demand_score": 0.95, "true_competition_level": 0.85, "regulatory_threshold": 0.70},
            true_outcome="launch_pilot",
            outcome_explanation="No single strategy works. Correct: stockpile 60 days (buys time) + fast-track Australian supplier + begin chip redesign.",
            scoring_rules={"launch": "Partial — which action?", "launch_pilot": "Correct — multi-pronged parallel approach", "delay": "Dangerous — 45 days means delay = shutdown", "do_not_launch": "Catastrophic — factory shuts in 45 days"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="US Strategic Reserve Release", description="US DoD releases rare earth reserves to allied manufacturers", impact="6-month buffer — but only for defense contractors.", severity="high", affected_agents=["Founder Agent", "Regulator Agent"], parameter_shifts={"true_safety_score": 0.20}),
        ],
    },

    "autonomous_taxi": {
        "title": "🚕 Autonomous Taxi — Mumbai Pilot",
        "description": "Launch autonomous taxis in Mumbai? Tech works in controlled environments. Government offers BKC pilot zone. $50M investment, 18 months.",
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.80, "true_safety_score": 0.38, "true_demand_score": 0.75, "true_competition_level": 0.25, "regulatory_threshold": 0.65},
            true_outcome="launch_pilot",
            outcome_explanation="BKC pilot zone is controlled — perfect for proving tech. Mumbai traffic outside BKC is too chaotic. Accept pilot, prove safety, expand.",
            scoring_rules={"launch": "Reckless outside pilot zone", "launch_pilot": "Correct — BKC proves tech safely", "delay": "Missed opportunity — pilot zone offer expires", "do_not_launch": "Overly cautious — pilot zone reduces risk"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Uber Exits India AV", description="Uber pulls autonomous vehicle program from India citing regulatory uncertainty", impact="Less competition but signals market difficulty.", severity="medium", affected_agents=["Investor Agent", "Founder Agent"], parameter_shifts={"true_competition_level": -0.15}),
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FUN SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════

FUN_SCENARIOS = {

    "family_dinner": {
        "title": "🍕 Family Dinner — Where to Vacation?",
        "description": "The Kumar family needs to decide: Goa (beach), Manali (mountains), Rajasthan (culture), or Bali (international). Budget: ₹3 lakhs, 7 days. Nobody agrees.",
        "agents_config": [
            {"name": "Mom 👩‍🍳", "role_description": "Family organizer. Wants good food, clean hotels, Instagram photos.", "incentives": "Memorable photos. Good restaurants. No complaints.", "biases": "Prefers places from travel reels. Anxious about international logistics.", "evaluation_criteria": "Hotel quality, food, photo ops, family-friendliness."},
            {"name": "Dad 👨‍💼", "role_description": "Budget controller. Secretly wants to relax and not drive.", "incentives": "Under budget. Minimal hassle. Maximum rest per rupee.", "biases": "Defaults to 'we went there last time'. Undervalues new experiences.", "evaluation_criteria": "Cost, travel time, relaxation, value for money."},
            {"name": "Teenager 🎮", "role_description": "17yo wants adventure, WiFi, and social media content.", "incentives": "Instagram content. Adventure. Meeting other young people.", "biases": "Dismisses 'traditional' as boring. Overestimates Bali based on influencers.", "evaluation_criteria": "Adventure activities, social scene, WiFi, cool factor."},
            {"name": "Grandma 👵", "role_description": "68yo, knee problems. Wants comfort, familiar food, temples. Secretly most powerful.", "incentives": "Comfortable travel. Vegetarian food. Temples.", "biases": "Strongly prefers domestic. 'Why go abroad when India has everything?'", "evaluation_criteria": "Accessibility, food familiarity, temples, comfort."},
        ],
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.65, "true_safety_score": 0.80, "true_demand_score": 0.70, "true_competition_level": 0.50, "regulatory_threshold": 0.40},
            true_outcome="launch_pilot",
            outcome_explanation="Rajasthan: temples for Grandma, palaces for Mom's photos, affordable for Dad, camel safari for Teenager. Bali blows budget, Goa too party for Grandma, Manali too strenuous.",
            scoring_rules={"launch_pilot": "Correct — Rajasthan balances everyone", "launch": "If Bali — over budget, Grandma miserable", "delay": "Nobody wants to postpone", "pivot": "If Goa — leaves Grandma out"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Best Friend Going to Bali", description="Teenager's best friend announces family Bali trip. FOMO intensifies.", impact="Emotional pressure from Teenager doubles.", severity="medium", affected_agents=["Teenager 🎮", "Mom 👩‍🍳"], parameter_shifts={"true_demand_score": -0.10}),
            BlackSwanEvent(name="Flash Sale on Heritage Hotels", description="MakeMyTrip: 40%% off heritage hotels in Jaipur and Udaipur", impact="Rajasthan becomes dramatically cheaper. Dad's eyes light up.", severity="medium", affected_agents=["Dad 👨‍💼", "Mom 👩‍🍳"], parameter_shifts={"true_market_size": 0.15}),
            BlackSwanEvent(name="Grandma's Temple Dream", description="Grandma mentions wanting to see Ranakpur Jain Temple 'before her time comes'", impact="Guilt card played. Nobody argues against Grandma's bucket list.", severity="high", affected_agents=["Mom 👩‍🍳", "Dad 👨‍💼", "Teenager 🎮"], parameter_shifts={"true_demand_score": 0.20}),
        ],
    },

    "fantasy_kingdom": {
        "title": "⚔️ Kingdom of Eldermoor — The Famine Crisis",
        "description": "Famine looms. Grain lasts 3 months. Neighbor offers grain for a border province. Rebels smell weakness. Accept, fight, ration, or renegotiate?",
        "agents_config": [
            {"name": "King Aldric 👑", "role_description": "Ruler. Must appear strong while keeping people alive.", "incentives": "Preserve territory. Feed people. Maintain legitimacy.", "biases": "Refuses to give away land. Overestimates military.", "evaluation_criteria": "Territory, popular support, dynasty legacy."},
            {"name": "General Thorne ⚔️", "role_description": "Military commander. Believes army can take grain by force.", "incentives": "Military solution. More army funding.", "biases": "Overconfident. Ignores winter logistics.", "evaluation_criteria": "Military feasibility, army morale."},
            {"name": "Economist Sera 📊", "role_description": "Royal treasurer. Knows exact numbers. Warned months ago.", "incentives": "Economic stability. Preserve trade.", "biases": "Over-relies on numbers. Ignores emotions.", "evaluation_criteria": "Cost-benefit, trade sustainability."},
            {"name": "Spymaster Vale 🕵️", "role_description": "Intelligence chief. Knows the neighbor is also struggling.", "incentives": "Leverage secrets for better deals.", "biases": "Sees conspiracies everywhere.", "evaluation_criteria": "Intelligence reliability, hidden leverage."},
            {"name": "High Priestess Yara 🙏", "role_description": "Religious leader. People trust her more than the King.", "incentives": "Moral authority. Protect the poor.", "biases": "Prioritizes morals over survival.", "evaluation_criteria": "Moral correctness, impact on poor."},
        ],
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.30, "true_safety_score": 0.35, "true_demand_score": 0.85, "true_competition_level": 0.70, "regulatory_threshold": 0.50},
            true_outcome="delay",
            outcome_explanation="Spymaster is right — neighbor is bluffing. They need the province strategically, not because they have grain. Ration 2 months, renegotiate grain-for-trade-rights.",
            scoring_rules={"launch": "Disastrous — gives province for grain that barely exists", "delay": "Correct — rationing + renegotiation exploits weakness", "do_not_launch": "Partial — must also find grain", "pivot": "Correct if changing negotiation terms"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Southern Rebellion", description="Rebels raid a grain storehouse — 2 weeks of reserves stolen", impact="Timeline shortened dramatically.", severity="critical", affected_agents=["King Aldric 👑", "General Thorne ⚔️"], parameter_shifts={"true_demand_score": 0.10, "true_competition_level": 0.15}),
            BlackSwanEvent(name="Spy Confirms Bluff", description="Agent confirms neighbor's grain stores nearly as low as ours", impact="Entire negotiation changes.", severity="high", affected_agents=["King Aldric 👑", "Spymaster Vale 🕵️"], parameter_shifts={"true_market_size": -0.15}),
            BlackSwanEvent(name="Miracle Rainfall", description="Late rains begin. Crops may partially recover in 6 weeks.", impact="Buys time. Rationing more viable.", severity="medium", affected_agents=["Economist Sera 📊", "High Priestess Yara 🙏"], parameter_shifts={"true_demand_score": -0.15, "true_safety_score": 0.10}),
        ],
    },

    "startup_pitch": {
        "title": "🚀 Startup Pitch — AI Pet Translator",
        "description": "AI collar translates dog barks into emotions via app. 73%% accuracy on 5 emotions. Asking $5M Series A. Demo day tomorrow.",
        "agents_config": None,
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.72, "true_safety_score": 0.90, "true_demand_score": 0.80, "true_competition_level": 0.30, "regulatory_threshold": 0.20},
            true_outcome="launch_pilot",
            outcome_explanation="Pet market is huge. 73%% accuracy not enough for launch — wrong translations go viral. Pilot with 1000 beta users, improve to 85%%+.",
            scoring_rules={"launch": "Risky — viral fail videos kill brand", "launch_pilot": "Correct — beta improves accuracy with buzz", "delay": "Cautious — market window open", "do_not_launch": "Wrong — opportunity is real"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Viral Dog Video", description="Beta tester video of translator predicting dog's anxiety attack — 2M views", impact="Pre-orders flood in. Pressure to launch early.", severity="high", affected_agents=["Founder Agent", "Customer Agent"], parameter_shifts={"true_demand_score": 0.15}),
        ],
    },

    "reality_show": {
        "title": "📺 The Board Room — Invest or Split?",
        "description": "Five reality show contestants: invest $100K prize fund in a startup (doubles if success, zero if fail) or split equally. 40%% startup success rate.",
        "agents_config": [
            {"name": "Risk-Taker Rachel 🎰", "role_description": "Wall Street trader. Already rich — here for the thrill.", "incentives": "Maximum drama. Big moves.", "biases": "Addicted to risk. Dismisses caution as weakness.", "evaluation_criteria": "Upside potential, boldness."},
            {"name": "Cautious Carlos 🛡️", "role_description": "Single dad. $20K changes his family's life.", "incentives": "Guaranteed money. No risk.", "biases": "Loss aversion. Every risk = gambling with kids' future.", "evaluation_criteria": "Downside protection, guaranteed outcomes."},
            {"name": "Strategist Sana 🧠", "role_description": "IIM MBA. Makes the math-optimal choice even if unpopular.", "incentives": "Expected value maximization.", "biases": "Over-intellectualizes. Ignores emotions.", "evaluation_criteria": "EV, probability, Nash equilibrium."},
            {"name": "Influencer Isha 📱", "role_description": "2M followers. Cares more about storyline than money.", "incentives": "Camera time. Memorable moment.", "biases": "Optimizes for narrative, not outcome.", "evaluation_criteria": "Story arc, audience reaction, brand."},
            {"name": "Alliance-Builder Alex 🤝", "role_description": "Politician's kid. Has deals with Rachel AND Carlos.", "incentives": "End on winning side. Never be villain.", "biases": "No genuine opinion. Follows crowd.", "evaluation_criteria": "Coalition size, positioning."},
        ],
        "ground_truth": GroundTruth(
            params={"true_market_size": 0.55, "true_safety_score": 0.40, "true_demand_score": 0.60, "true_competition_level": 0.50, "regulatory_threshold": 0.50},
            true_outcome="delay",
            outcome_explanation="40%% success = EV of $80K vs guaranteed $100K split. Splitting is mathematically and emotionally correct.",
            scoring_rules={"launch": "Negative EV — math doesn't support it", "delay": "Correct — $20K each is rational and humane", "pivot": "Clever but rules don't allow partial investment"},
        ),
        "black_swan_pool": [
            BlackSwanEvent(name="Carlos Breaks Down", description="Carlos tears up about daughter's school fees. Audience sympathy floods in.", impact="Emotional pressure to split. Rachel looks heartless.", severity="high", affected_agents=["Risk-Taker Rachel 🎰", "Alliance-Builder Alex 🤝"], parameter_shifts={"true_demand_score": 0.20}),
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# RANDOM STARTUP IDEAS
# ═══════════════════════════════════════════════════════════════════════════════

RANDOM_STARTUP_IDEAS = [
    "An AI toothbrush that diagnoses diseases from saliva while you brush",
    "A smart fridge that auto-orders groceries and judges your eating habits",
    "An AI dog collar that converts barks into passive-aggressive texts",
    "A dating app where your AI avatar goes on dates and reports back",
    "An AI therapist for houseplants monitoring 'emotional wellbeing'",
    "Blockchain karma tracker — good deeds mine crypto",
    "AI that writes out-of-office replies based on how annoyed you are",
    "Smart pants that vibrate to navigate you to the nearest restroom",
    "AI food critic that rates home cooking on a public leaderboard",
    "AI wedding planner that predicts divorce probability and adjusts budget",
    "Fitness app that only tracks speed running TO food, not from it",
    "AI negotiator for auto-rickshaw fares via Bluetooth meter",
    "Smart mirror with motivational speeches that get increasingly disappointed",
    "AI meeting attendant that scores 'was this worth your time'",
    "An AI that watches your Netflix and tells you what you SHOULD have watched",
]


# ═══════════════════════════════════════════════════════════════════════════════
# CHAOS MODE
# ═══════════════════════════════════════════════════════════════════════════════

CHAOS_OVERRIDES = {
    "Founder Agent": {"biases": "EXTREME optimism. Believes they're the next Elon. 'Disruption' every sentence.", "extra_instruction": "WILDLY overconfident. Everything is amazing. Critics are haters. Ship yesterday."},
    "Investor Agent": {"biases": "Obsessed with returns. 100x lens. Mentions IRR unprompted.", "extra_instruction": "Only care about money. TAM, multiples, exits. Drop fund jargon."},
    "Engineer Agent": {"biases": "Everything must be rewritten. Insists on Rust. 80%% time on architecture diagrams.", "extra_instruction": "MASSIVE over-engineer. Simple solutions offend you. Microservices for a todo app."},
    "Customer Agent": {"biases": "Wants everything free, instant, personalized, no ads. 1-star review threats.", "extra_instruction": "Most ENTITLED customer alive. Nothing good enough. Compare to Apple constantly."},
    "Regulator Agent": {"biases": "Regulate EVERYTHING. Existential risk in a calculator app.", "extra_instruction": "ALL technology dangerous. Cite nonexistent regulations. Form committee for everything."},
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

ALL_SCENARIOS = {**SCENARIOS, **FUN_SCENARIOS}


def get_scenario(name: str) -> dict:
    return ALL_SCENARIOS[name]

def list_scenarios() -> list[str]:
    return list(ALL_SCENARIOS.keys())

def list_serious_scenarios() -> list[str]:
    return list(SCENARIOS.keys())

def list_fun_scenarios() -> list[str]:
    return list(FUN_SCENARIOS.keys())

def get_random_startup_idea() -> str:
    return _random.choice(RANDOM_STARTUP_IDEAS)
