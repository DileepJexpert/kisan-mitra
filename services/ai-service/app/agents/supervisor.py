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
    """Load user profile from DB, conversation history & context from Redis."""
    user_id = state.get("user_id", "")

    # Load profile
    db = PostgresClient()
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
    if user:
        state["user_profile"] = dict(user)
        state["language"] = state.get("language") or user.get("language", "hi")
    else:
        state["user_profile"] = {}

    # Load conversation history (last 5 messages for context)
    redis = RedisClient()
    history = await redis.get_conversation_history(user_id, last_n=5)
    if history:
        prior_messages = [
            {"role": h["role"], "content": h["content"]}
            for h in history
        ]
        # Prepend history before current message
        current = state.get("messages", [])
        state["messages"] = prior_messages + current

    # Load agent context from previous turn
    context = await redis.get_user_context(user_id)
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
    """Save conversation messages and agent context to Redis."""
    user_id = state.get("user_id", "")
    if not user_id:
        return state

    redis = RedisClient()

    # Save the user's message
    messages = state.get("messages", [])
    if messages:
        last_user = messages[-1]
        await redis.save_message(user_id, "user", last_user.get("content", ""))

    # Save agent reply
    reply = state.get("agent_results", {}).get("final_response") or \
            state.get("agent_results", {}).get("response", "")
    if reply:
        agent_name = state.get("current_agent", "general")
        await redis.save_message(user_id, "assistant", reply, agent_name=agent_name)

    # Save agent context for follow-up queries
    context = {
        "last_agent": state.get("current_agent", ""),
        "last_results_summary": {
            k: v for k, v in state.get("agent_results", {}).items()
            if k in ("classification", "commodity", "market", "scheme_intent",
                      "loan_intent", "mandi_intent", "business_type",
                      "eligible_schemes", "loan_results")
        },
        "tools_used": state.get("tools_used", []),
    }
    await redis.save_user_context(user_id, context)

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
                           language: str = "hi", channel: str = "whatsapp",
                           audio_base64: str | None = None) -> dict:
    """Main entry point: process a user message through the supervisor."""
    import time
    start = time.time()

    # STT: transcribe audio if provided
    if audio_base64 and not message:
        try:
            from app.models.stt_provider import get_stt_router
            import base64
            stt = get_stt_router()
            audio_bytes = base64.b64decode(audio_base64)
            result = await stt.transcribe(audio_bytes, language=language)
            message = result.get("text", "")
            if not message:
                return {
                    "reply_text": "माफ कीजिए, आवाज़ समझ नहीं आई। कृपया दोबारा बोलें।"
                    if language == "hi" else "Sorry, couldn't understand the audio. Please try again.",
                    "agents_used": [],
                    "actions_taken": ["stt_failed"],
                    "follow_up_actions": [],
                }
        except Exception as e:
            logger.error("supervisor.stt_failed", error=str(e))
            message = ""

    if not message:
        return {
            "reply_text": "कृपया अपना सवाल लिखें या बोलें।" if language == "hi"
                          else "Please type or speak your question.",
            "agents_used": [],
            "actions_taken": [],
            "follow_up_actions": [],
        }

    # Handle special commands
    lower = message.strip().lower()
    special = _handle_special_command(lower, language)
    if special:
        return special

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

    latency_ms = int((time.time() - start) * 1000)
    logger.info("supervisor.processed", user_id=user_id,
                agent=result.get("current_agent", ""),
                latency_ms=latency_ms)

    reply_text = result.get("agent_results", {}).get("final_response", "")

    # Generate TTS if channel is whatsapp and reply exists
    reply_audio = None
    if channel == "whatsapp" and reply_text and len(reply_text) < 500:
        try:
            from app.models.tts_provider import get_tts_provider
            import base64 as b64
            tts = get_tts_provider()
            audio_bytes = await tts.speak(reply_text, language=language)
            if audio_bytes:
                reply_audio = b64.b64encode(audio_bytes).decode()
        except Exception:
            pass  # TTS is optional

    return {
        "reply_text": reply_text,
        "reply_audio_base64": reply_audio,
        "agents_used": [result.get("current_agent", "")],
        "actions_taken": result.get("tools_used", []),
        "follow_up_actions": result.get("follow_up_actions", []),
    }


def _handle_special_command(message: str, language: str) -> dict | None:
    """Handle special user commands."""
    help_triggers = {"help", "madad", "मदद", "sahayata", "सहायता"}
    status_triggers = {"status", "meri applications", "मेरी applications", "mera status"}
    lang_en_triggers = {"language english", "english", "angrezi"}
    lang_hi_triggers = {"language hindi", "hindi", "bhasha hindi"}

    if message in help_triggers:
        if language == "hi":
            text = (
                "मैं किसानमित्र हूं! मैं इनमें मदद कर सकता हूं:\n\n"
                "1. *सरकारी योजनाएं* — \"मेरे लिए कौन सी योजना है?\"\n"
                "2. *मंडी भाव* — \"टमाटर का रेट बताओ\"\n"
                "3. *लोन सलाह* — \"डेयरी के लिए लोन चाहिए\"\n"
                "4. *भुगतान विवाद* — \"payment नहीं मिला, notice भेजना है\"\n"
                "5. *प्रोजेक्ट रिपोर्ट* — \"डेयरी फार्म का DPR बनाओ\"\n\n"
                "बस अपना सवाल हिंदी या English में पूछें!"
            )
        else:
            text = (
                "I'm KisanMitra! I can help with:\n\n"
                "1. *Government Schemes* — \"What schemes am I eligible for?\"\n"
                "2. *Mandi Prices* — \"Tomato price in Kanpur\"\n"
                "3. *Loan Advisory* — \"I need a loan for dairy farm\"\n"
                "4. *Payment Disputes* — \"Buyer hasn't paid, send legal notice\"\n"
                "5. *Project Reports* — \"Generate DPR for dairy farm\"\n\n"
                "Just ask your question in Hindi or English!"
            )
        return {"reply_text": text, "agents_used": ["help"], "actions_taken": [], "follow_up_actions": []}

    if message in status_triggers:
        return {"reply_text": "आपकी applications की जानकारी जल्दी आ रही है..." if language == "hi"
                else "Fetching your application status...",
                "agents_used": ["status"], "actions_taken": [], "follow_up_actions": []}

    return None
