"""
Supervisor Agent — Routes queries to appropriate sub-agents.
Uses LLM to classify intent, manages conversation memory, orchestrates multi-agent flows.
"""

import json
import structlog

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.scheme_agent import build_scheme_agent
from app.agents.mandi_agent import build_mandi_agent
from app.agents.loan_agent import build_loan_agent
from app.agents.dispute_agent import build_dispute_agent
from app.agents.dpr_agent import build_dpr_agent
from app.db.postgres_client import PostgresClient
from app.db.redis_client import RedisClient
from app.models.llm_provider import get_llm_router

logger = structlog.get_logger(__name__)

# Agent registry
AGENT_BUILDERS = {
    "scheme": build_scheme_agent,
    "mandi": build_mandi_agent,
    "loan": build_loan_agent,
    "dispute": build_dispute_agent,
    "dpr": build_dpr_agent,
}

# Intent keywords for fast classification (before LLM fallback)
INTENT_KEYWORDS = {
    "scheme": [
        "yojana", "योजना", "scheme", "subsidy", "anudan", "अनुदान",
        "sarkari", "सरकारी", "government", "pm kisan", "pmfby",
        "eligible", "patra", "पात्र",
    ],
    "mandi": [
        "bhav", "भाव", "price", "mandi", "मंडी", "rate", "dar", "दर",
        "bechu", "बेचू", "sell", "market", "bazaar", "बाजार",
        "tamatar", "टमाटर", "pyaz", "प्याज", "aloo", "आलू",
        "gehun", "गेहूं", "dhan", "धान", "soybean",
    ],
    "loan": [
        "loan", "rin", "ऋण", "karz", "कर्ज", "emi", "kist", "किस्त",
        "kcc", "mudra", "bank", "credit", "udhar", "उधार",
    ],
    "dispute": [
        "dispute", "vivad", "विवाद", "payment", "bhugtan", "भुगतान",
        "invoice", "bill", "challan", "चालान", "notice", "legal",
        "msme", "udyam", "interest", "byaj", "ब्याज",
    ],
    "dpr": [
        "dpr", "project report", "pariyojana", "परियोजना",
        "dairy", "डेयरी", "poultry", "food processing",
        "business plan", "bank proposal",
    ],
}


async def load_user_profile(state: AgentState) -> AgentState:
    """Load user profile from DB and conversation context from Redis."""
    user_id = state.get("user_id", "")

    # Load profile
    db = PostgresClient()
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
    if user:
        state["user_profile"] = dict(user)
    else:
        state["user_profile"] = {}

    # Load conversation context from Redis
    redis = RedisClient()
    context_key = f"conv:{user_id}:context"
    context = await redis.get_json(context_key)
    if context:
        state["agent_results"] = state.get("agent_results", {})
        state["agent_results"]["conversation_context"] = context

    return state


async def classify_intent(state: AgentState) -> AgentState:
    """Classify user intent to route to appropriate sub-agent."""
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    lower = last_msg.lower()

    # Fast keyword-based classification
    scores = {}
    for agent_name, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[agent_name] = score

    if scores:
        best_agent = max(scores, key=scores.get)
        confidence = scores[best_agent] / max(len(INTENT_KEYWORDS[best_agent]), 1)

        if confidence >= 0.1:  # At least one keyword match
            state["current_agent"] = best_agent
            state["agent_results"] = state.get("agent_results", {})
            state["agent_results"]["classification"] = {
                "agent": best_agent,
                "method": "keyword",
                "confidence": round(confidence, 2),
                "scores": scores,
            }
            return state

    # Fallback: LLM classification
    try:
        router = get_llm_router()
        classify_prompt = f"""Classify this user message into exactly one category.

Categories:
- scheme: Government scheme enquiry, subsidy information, eligibility
- mandi: Crop/commodity prices, market rates, selling advice
- loan: Loan enquiry, EMI calculation, credit
- dispute: Payment dispute, MSME invoice, legal notice
- dpr: Project report, business plan, dairy/poultry/food processing setup
- general: Greeting, general question, unrelated

User message: "{last_msg}"

Reply with ONLY the category name, nothing else."""

        result = await router.chat_cheap([{"role": "user", "content": classify_prompt}])
        agent = result.strip().lower().replace('"', "").replace("'", "")

        if agent in AGENT_BUILDERS:
            state["current_agent"] = agent
        else:
            state["current_agent"] = "general"

        state["agent_results"] = state.get("agent_results", {})
        state["agent_results"]["classification"] = {
            "agent": state["current_agent"],
            "method": "llm",
            "confidence": 0.7,
        }
    except Exception as e:
        logger.warning("supervisor.classify_failed", error=str(e))
        state["current_agent"] = "general"

    return state


async def run_sub_agent(state: AgentState) -> AgentState:
    """Execute the selected sub-agent."""
    agent_name = state.get("current_agent", "general")

    if agent_name == "general":
        # Handle general queries with LLM
        state = await handle_general_query(state)
        return state

    builder = AGENT_BUILDERS.get(agent_name)
    if not builder:
        state["error"] = f"Unknown agent: {agent_name}"
        return state

    try:
        graph = builder()
        compiled = graph.compile()
        result = await compiled.ainvoke(state)

        # Merge results back
        if isinstance(result, dict):
            state["agent_results"] = result.get("agent_results", state.get("agent_results", {}))
            state["tools_used"] = result.get("tools_used", state.get("tools_used", []))
            state["follow_up_actions"] = result.get("follow_up_actions", state.get("follow_up_actions", []))
    except Exception as e:
        logger.error("supervisor.agent_failed", agent=agent_name, error=str(e))
        state["error"] = str(e)

    return state


async def handle_general_query(state: AgentState) -> AgentState:
    """Handle general/greeting queries with LLM."""
    messages = state.get("messages", [])
    language = state.get("language", "hi")
    profile = state.get("user_profile", {})
    name = profile.get("name", "")

    router = get_llm_router()

    system_msg = f"""You are KisanMitra, a helpful AI assistant for Indian farmers and small business owners.
You speak {'Hindi' if language == 'hi' else 'English'}.
User's name: {name}
You help with: government schemes, mandi prices, loans, MSME dispute resolution, and project reports.
Be warm, helpful, and concise. If the user's question is about one of your specialties, guide them to ask specifically."""

    try:
        response = await router.chat_cheap([
            {"role": "system", "content": system_msg},
            *messages[-5:],  # Last 5 messages for context
        ])
        state["agent_results"] = state.get("agent_results", {})
        state["agent_results"]["response"] = response
    except Exception as e:
        fallback = "नमस्ते! मैं किसानमित्र हूं। मैं आपकी कैसे मदद कर सकता हूं?" if language == "hi" else "Hello! I'm KisanMitra. How can I help you?"
        state["agent_results"] = state.get("agent_results", {})
        state["agent_results"]["response"] = fallback
        logger.warning("supervisor.general_failed", error=str(e))

    return state


async def save_conversation_context(state: AgentState) -> AgentState:
    """Save conversation context to Redis for continuity."""
    user_id = state.get("user_id", "")
    if not user_id:
        return state

    redis = RedisClient()
    context = {
        "last_agent": state.get("current_agent", ""),
        "last_results_summary": {
            k: v for k, v in state.get("agent_results", {}).items()
            if k in ("classification", "commodity", "market", "scheme_intent", "loan_intent")
        },
        "tools_used": state.get("tools_used", []),
    }
    await redis.set_json(f"conv:{user_id}:context", context, ttl=3600)  # 1 hour
    return state


async def build_final_response(state: AgentState) -> AgentState:
    """Assemble final response from agent results."""
    results = state.get("agent_results", {})

    if state.get("error"):
        language = state.get("language", "hi")
        if language == "hi":
            state["agent_results"]["final_response"] = "माफ कीजिए, कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।"
        else:
            state["agent_results"]["final_response"] = "Sorry, something went wrong. Please try again."
    else:
        state["agent_results"]["final_response"] = results.get("response", "")

    return state


def build_supervisor() -> StateGraph:
    """Build the supervisor orchestration graph."""
    graph = StateGraph(AgentState)

    graph.add_node("load_profile", load_user_profile)
    graph.add_node("classify", classify_intent)
    graph.add_node("run_agent", run_sub_agent)
    graph.add_node("save_context", save_conversation_context)
    graph.add_node("build_response", build_final_response)

    graph.set_entry_point("load_profile")
    graph.add_edge("load_profile", "classify")
    graph.add_edge("classify", "run_agent")
    graph.add_edge("run_agent", "save_context")
    graph.add_edge("save_context", "build_response")
    graph.add_edge("build_response", END)

    return graph


async def process_message(user_id: str, message: str,
                           language: str = "hi", channel: str = "whatsapp") -> dict:
    """Main entry point: process a user message through the supervisor."""
    state: AgentState = {
        "user_id": user_id,
        "messages": [{"role": "user", "content": message}],
        "language": language,
        "tools_used": [],
        "agent_results": {},
        "follow_up_actions": [],
    }

    graph = build_supervisor()
    compiled = graph.compile()
    result = await compiled.ainvoke(state)

    return {
        "reply_text": result.get("agent_results", {}).get("final_response", ""),
        "agents_used": [result.get("current_agent", "")],
        "actions_taken": result.get("tools_used", []),
        "follow_up_actions": result.get("follow_up_actions", []),
    }
