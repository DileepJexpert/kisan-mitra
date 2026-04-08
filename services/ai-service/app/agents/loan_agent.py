"""
Loan Advisory Agent — LangGraph StateGraph
Helps users check loan eligibility, calculate EMIs, find best loan combinations.
"""

from langgraph.graph import StateGraph, END

import structlog

from app.agents.state import AgentState
from app.db.postgres_client import PostgresClient
from app.tools.loan_tools import (
    calculate_emi,
    check_loan_eligibility,
    find_best_loan_combination,
)

logger = structlog.get_logger(__name__)


async def parse_loan_query(state: AgentState) -> AgentState:
    """Parse user intent: eligibility check, EMI calculation, or best combination."""
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    lower = last_msg.lower()

    intent = "eligibility"
    amount_needed = None

    if any(kw in lower for kw in ["emi", "kist", "किस्त", "monthly"]):
        intent = "emi"
    elif any(kw in lower for kw in ["best", "combination", "kitna mil", "कितना मिल", "recommend"]):
        intent = "combination"

    # Try to extract amount
    import re
    amount_match = re.search(r'(\d+)\s*(lakh|lac|लाख)', lower)
    if amount_match:
        amount_needed = float(amount_match.group(1)) * 100000
    else:
        amount_match = re.search(r'rs\.?\s*(\d[\d,]*)', lower)
        if amount_match:
            amount_needed = float(amount_match.group(1).replace(",", ""))

    # Extract specific loan type if mentioned
    loan_type = None
    loan_keywords = {
        "kcc": "KCC", "kisan credit": "KCC",
        "mudra": "MUDRA_SHISHU", "shishu": "MUDRA_SHISHU",
        "kishore": "MUDRA_KISHORE", "tarun": "MUDRA_TARUN",
        "dairy": "NABARD_DEDS", "pmegp": "PMEGP",
        "stand up": "STANDUP_INDIA", "standup": "STANDUP_INDIA",
    }
    for keyword, code in loan_keywords.items():
        if keyword in lower:
            loan_type = code
            break

    state["agent_results"] = state.get("agent_results", {})
    state["agent_results"]["loan_intent"] = intent
    state["agent_results"]["amount_needed"] = amount_needed
    state["agent_results"]["loan_type_filter"] = loan_type
    state["tools_used"] = state.get("tools_used", [])
    return state


async def check_eligibility_node(state: AgentState) -> AgentState:
    """Check loan eligibility for user."""
    db = PostgresClient()
    user_id = state.get("user_id", "")
    loan_type = state.get("agent_results", {}).get("loan_type_filter")

    results = await check_loan_eligibility(db, user_id, loan_type)
    state["agent_results"]["loan_results"] = results
    state["tools_used"].append("check_loan_eligibility")
    return state


async def find_combination_node(state: AgentState) -> AgentState:
    """Find best loan combination for needed amount."""
    db = PostgresClient()
    user_id = state.get("user_id", "")
    amount = state.get("agent_results", {}).get("amount_needed", 500000)

    combination = await find_best_loan_combination(db, user_id, amount)
    state["agent_results"]["combination"] = combination
    state["tools_used"].append("find_best_loan_combination")
    return state


async def calculate_emi_node(state: AgentState) -> AgentState:
    """Calculate EMI for eligible loans."""
    results = state.get("agent_results", {}).get("loan_results", [])
    amount = state.get("agent_results", {}).get("amount_needed")

    emi_details = []
    for loan in results:
        if loan.get("eligible") and loan.get("max_amount"):
            principal = amount if amount and amount <= loan["max_amount"] else loan["max_amount"]
            rate_str = loan.get("interest_rate_range", "9-12%")
            max_rate = float(rate_str.split("-")[1].replace("%", ""))
            tenure = loan.get("tenure_years", 5)
            emi = calculate_emi(principal, max_rate, tenure)
            emi_details.append({
                "loan_code": loan["loan_code"],
                "loan_name": loan["loan_name"],
                "principal": principal,
                "rate": max_rate,
                "tenure_years": tenure,
                **emi,
            })

    state["agent_results"]["emi_details"] = emi_details
    state["tools_used"].append("calculate_emi")
    return state


async def format_loan_response(state: AgentState) -> AgentState:
    """Format loan advisory response."""
    results = state.get("agent_results", {})
    intent = results.get("loan_intent", "eligibility")
    language = state.get("language", "hi")

    parts = []

    if intent == "combination" and results.get("combination"):
        combo = results["combination"]
        recs = combo.get("recommended_combination", [])
        if language == "hi":
            parts.append(f"💰 *आपके लिए लोन संयोजन* (Rs.{combo.get('total_funding', 0):,.0f}):\n")
        else:
            parts.append(f"💰 *Recommended Loan Combination* (Rs.{combo.get('total_funding', 0):,.0f}):\n")

        for r in recs:
            parts.append(f"  • *{r['loan_name']}*: Rs.{r['amount']:,.0f}")
            if r.get("subsidy"):
                parts.append(f"    Subsidy: Rs.{r['subsidy']:,.0f}")
            if r.get("emi"):
                parts.append(f"    EMI: Rs.{r['emi']:,.0f}/month")

        if combo.get("total_subsidy"):
            parts.append(f"\n✅ Total subsidy: Rs.{combo['total_subsidy']:,.0f}")
        if combo.get("gap", 0) > 0:
            parts.append(f"⚠️ Gap (own contribution needed): Rs.{combo['gap']:,.0f}")

    elif intent == "emi" and results.get("emi_details"):
        emis = results["emi_details"]
        parts.append("📋 *EMI Details*:\n" if language != "hi" else "📋 *EMI विवरण*:\n")
        for e in emis[:5]:
            parts.append(f"  *{e['loan_name']}*")
            parts.append(f"  Loan: Rs.{e['principal']:,.0f} @ {e['rate']}%")
            parts.append(f"  EMI: Rs.{e['emi_monthly']:,.0f}/month × {e['tenure_years']} years")
            parts.append(f"  Total interest: Rs.{e['total_interest']:,.0f}\n")

    else:  # eligibility
        loans = results.get("loan_results", [])
        eligible = [l for l in loans if l.get("eligible")]
        ineligible = [l for l in loans if not l.get("eligible")]

        if eligible:
            header = f"✅ आप {len(eligible)} लोन के लिए पात्र हैं:" if language == "hi" else f"✅ You're eligible for {len(eligible)} loans:"
            parts.append(header + "\n")
            for l in eligible:
                parts.append(f"  • *{l['loan_name']}*")
                parts.append(f"    Max: Rs.{l['max_amount']:,.0f} | Rate: {l['interest_rate_range']}")
                if l.get("subsidy_percentage"):
                    parts.append(f"    Subsidy: {l['subsidy_percentage']}%")
                if l.get("collateral_required"):
                    parts.append(f"    ⚠️ Collateral required")
        else:
            parts.append("❌ No eligible loans found." if language != "hi"
                         else "❌ कोई पात्र लोन नहीं मिला।")

        if ineligible:
            parts.append(f"\n❌ Not eligible ({len(ineligible)}):")
            for l in ineligible[:3]:
                parts.append(f"  • {l['loan_name']}: {l.get('reason_if_ineligible', '')}")

    state["agent_results"]["response"] = "\n".join(parts)
    return state


def route_loan_intent(state: AgentState) -> str:
    intent = state.get("agent_results", {}).get("loan_intent", "eligibility")
    if intent == "combination":
        return "combination"
    return "eligibility"


def route_after_eligibility(state: AgentState) -> str:
    intent = state.get("agent_results", {}).get("loan_intent", "eligibility")
    if intent == "emi":
        return "emi"
    return "format_response"


def build_loan_agent() -> StateGraph:
    """Build the loan advisory agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("parse_query", parse_loan_query)
    graph.add_node("check_eligibility", check_eligibility_node)
    graph.add_node("find_combination", find_combination_node)
    graph.add_node("calculate_emi", calculate_emi_node)
    graph.add_node("format_response", format_loan_response)

    graph.set_entry_point("parse_query")
    graph.add_conditional_edges("parse_query", route_loan_intent, {
        "eligibility": "check_eligibility",
        "combination": "find_combination",
    })
    graph.add_conditional_edges("check_eligibility", route_after_eligibility, {
        "emi": "calculate_emi",
        "format_response": "format_response",
    })
    graph.add_edge("find_combination", "format_response")
    graph.add_edge("calculate_emi", "format_response")
    graph.add_edge("format_response", END)

    return graph
