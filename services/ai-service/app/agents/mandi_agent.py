"""
Mandi Price Agent — LangGraph StateGraph
Helps users check mandi prices, compare markets, get price predictions.
"""

from langgraph.graph import StateGraph, END

import structlog

from app.agents.state import AgentState
from app.db.postgres_client import PostgresClient
from app.tools.mandi_tools import (
    compare_nearby_markets,
    get_current_price,
    get_price_history,
    normalize_commodity,
    set_price_alert,
)
from app.tools.price_predictor import predict_price

logger = structlog.get_logger(__name__)


async def parse_mandi_query(state: AgentState) -> AgentState:
    """Extract commodity, market, and intent from user message."""
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    lower = last_msg.lower()
    profile = state.get("user_profile", {})

    # Detect intent
    intent = "current_price"
    if any(kw in lower for kw in ["predict", "forecast", "agla", "अगला", "kal", "कल", "bhav kya hoga"]):
        intent = "predict"
    elif any(kw in lower for kw in ["compare", "tulna", "तुलना", "best market", "kahan bechu"]):
        intent = "compare"
    elif any(kw in lower for kw in ["history", "itihas", "इतिहास", "trend", "pichle"]):
        intent = "history"
    elif any(kw in lower for kw in ["alert", "suchna", "सूचना", "batana", "बताना jab"]):
        intent = "alert"

    # Extract commodity (simple keyword matching)
    from app.tools.mandi_tools import HINDI_COMMODITY_MAP
    commodity = None
    for hindi, english in HINDI_COMMODITY_MAP.items():
        if hindi in lower:
            commodity = english
            break
    # Check English names too
    if not commodity:
        for english in set(HINDI_COMMODITY_MAP.values()):
            if english.lower() in lower:
                commodity = english
                break
    if not commodity:
        commodity = profile.get("primary_crop", "Wheat")

    # Market defaults to user's nearest market
    market = profile.get("nearest_market", profile.get("district", "Indore"))

    state["agent_results"] = state.get("agent_results", {})
    state["agent_results"]["mandi_intent"] = intent
    state["agent_results"]["commodity"] = commodity
    state["agent_results"]["market"] = market
    state["tools_used"] = state.get("tools_used", [])
    return state


async def fetch_current_price(state: AgentState) -> AgentState:
    """Get current price for commodity in market."""
    db = PostgresClient()
    results = state["agent_results"]
    commodity = results["commodity"]
    market = results["market"]

    price = await get_current_price(db, commodity, market)
    results["current_price"] = price
    state["tools_used"].append("get_current_price")
    return state


async def fetch_price_history(state: AgentState) -> AgentState:
    """Get price history for trend analysis."""
    db = PostgresClient()
    results = state["agent_results"]

    history = await get_price_history(db, results["commodity"], results["market"], days=30)
    results["price_history"] = history
    state["tools_used"].append("get_price_history")
    return state


async def fetch_prediction(state: AgentState) -> AgentState:
    """Run price prediction model."""
    db = PostgresClient()
    results = state["agent_results"]

    prediction = await predict_price(db, results["commodity"], results["market"])
    results["prediction"] = prediction
    state["tools_used"].append("predict_price")
    return state


async def fetch_comparison(state: AgentState) -> AgentState:
    """Compare prices across nearby markets."""
    db = PostgresClient()
    results = state["agent_results"]
    profile = state.get("user_profile", {})
    user_state = profile.get("state", "Madhya Pradesh")

    comparison = await compare_nearby_markets(db, results["commodity"], user_state)
    results["market_comparison"] = comparison
    state["tools_used"].append("compare_nearby_markets")
    return state


async def create_alert(state: AgentState) -> AgentState:
    """Create a price alert for the user."""
    db = PostgresClient()
    results = state["agent_results"]
    user_id = state.get("user_id", "")

    current = results.get("current_price", {})
    modal = float(current.get("modal_price", 0)) if current else 0
    # Default alert: notify when price goes 10% above current
    threshold = modal * 1.10 if modal > 0 else 0

    alert = await set_price_alert(
        db, user_id, results["commodity"], results["market"],
        "above", threshold
    )
    results["alert_created"] = alert
    state["tools_used"].append("set_price_alert")

    state["follow_up_actions"] = state.get("follow_up_actions", [])
    state["follow_up_actions"].append({
        "type": "price_alert",
        "commodity": results["commodity"],
        "threshold": threshold,
    })
    return state


async def format_mandi_response(state: AgentState) -> AgentState:
    """Format response with prices, predictions, recommendations."""
    results = state.get("agent_results", {})
    intent = results.get("mandi_intent", "current_price")
    language = state.get("language", "hi")
    commodity = results.get("commodity", "")

    parts = []

    # Current price (always shown)
    price = results.get("current_price")
    if price:
        modal = price.get("modal_price", 0)
        min_p = price.get("min_price", 0)
        max_p = price.get("max_price", 0)
        market = price.get("market", results.get("market", ""))
        if language == "hi":
            parts.append(f"📊 *{commodity}* — {market}")
            parts.append(f"आज का भाव: Rs.{modal:.0f}/क्विंटल")
            parts.append(f"(न्यूनतम: Rs.{min_p:.0f}, अधिकतम: Rs.{max_p:.0f})")
        else:
            parts.append(f"📊 *{commodity}* — {market}")
            parts.append(f"Today's price: Rs.{modal:.0f}/quintal")
            parts.append(f"(Min: Rs.{min_p:.0f}, Max: Rs.{max_p:.0f})")
    elif not results.get("error"):
        parts.append(f"भाव उपलब्ध नहीं है।" if language == "hi"
                     else f"Price data not available for {commodity}.")

    # Prediction
    if intent == "predict" and results.get("prediction"):
        pred = results["prediction"]
        if pred.get("forecast"):
            rec = pred.get("recommendation", "")
            reason = pred.get("reason", "")
            parts.append(f"\n🔮 *{'पूर्वानुमान' if language == 'hi' else 'Forecast'}*:")
            for f in pred["forecast"][:3]:
                parts.append(f"  {f['date']}: Rs.{f['predicted_price']:.0f}")
            parts.append(f"\n💡 *{'सलाह' if language == 'hi' else 'Recommendation'}*: {rec}")
            parts.append(reason)

    # Comparison
    if intent == "compare" and results.get("market_comparison"):
        comp = results["market_comparison"]
        parts.append(f"\n🏪 *{'मंडी तुलना' if language == 'hi' else 'Market Comparison'}*:")
        for m in comp:
            parts.append(f"  {m['market']}: Rs.{m.get('modal_price', 0):.0f}/quintal")

    # History
    if intent == "history" and results.get("price_history"):
        hist = results["price_history"]
        if len(hist) >= 2:
            first = hist[0].get("modal_price", 0)
            last = hist[-1].get("modal_price", 0)
            change = ((last - first) / first * 100) if first > 0 else 0
            trend = "📈" if change > 0 else "📉"
            parts.append(f"\n{trend} *30-day trend*: {change:+.1f}%")
            parts.append(f"  30 days ago: Rs.{first:.0f} → Today: Rs.{last:.0f}")

    # Alert
    if results.get("alert_created"):
        alert = results["alert_created"]
        parts.append(f"\n🔔 Alert set: Will notify when {commodity} crosses Rs.{alert.get('threshold', 0):.0f}")

    state["agent_results"]["response"] = "\n".join(parts)
    return state


def route_mandi_intent(state: AgentState) -> str:
    intent = state.get("agent_results", {}).get("mandi_intent", "current_price")
    return intent


def build_mandi_agent() -> StateGraph:
    """Build the mandi price agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("parse_query", parse_mandi_query)
    graph.add_node("current_price", fetch_current_price)
    graph.add_node("history", fetch_price_history)
    graph.add_node("predict", fetch_prediction)
    graph.add_node("compare", fetch_comparison)
    graph.add_node("alert", create_alert)
    graph.add_node("format_response", format_mandi_response)

    graph.set_entry_point("parse_query")

    # All intents fetch current price first
    graph.add_edge("parse_query", "current_price")

    graph.add_conditional_edges("current_price", route_mandi_intent, {
        "current_price": "format_response",
        "predict": "predict",
        "compare": "compare",
        "history": "history",
        "alert": "alert",
    })

    graph.add_edge("predict", "format_response")
    graph.add_edge("compare", "format_response")
    graph.add_edge("history", "format_response")
    graph.add_edge("alert", "format_response")
    graph.add_edge("format_response", END)

    return graph
