"""
DPR (Detailed Project Report) Agent — LangGraph StateGraph
Generates bank-ready DPRs for agricultural and allied sector projects.
"""

from langgraph.graph import StateGraph, END

import structlog

from app.agents.state import AgentState
from app.db.postgres_client import PostgresClient
from app.tools.dpr_tools import (
    calculate_financials,
    generate_dpr_narrative,
    get_dpr_template,
    save_dpr_record,
)

logger = structlog.get_logger(__name__)

BUSINESS_TYPE_MAP = {
    "dairy": "dairy_farm", "डेयरी": "dairy_farm", "gaay": "dairy_farm", "गाय": "dairy_farm",
    "cattle feed": "cattle_feed", "pashu aahar": "cattle_feed", "पशु आहार": "cattle_feed",
    "food processing": "food_processing", "khadya prasanskaran": "food_processing",
    "खाद्य प्रसंस्करण": "food_processing",
    "poultry": "poultry_farm", "murgi": "poultry_farm", "मुर्गी": "poultry_farm",
    "fishery": "fishery", "machli": "fishery", "मछली": "fishery",
    "goat": "goat_farm", "bakri": "goat_farm", "बकरी": "goat_farm",
}


async def parse_dpr_query(state: AgentState) -> AgentState:
    """Parse DPR request — extract business type, scale, location."""
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    lower = last_msg.lower()
    profile = state.get("user_profile", {})

    # Detect business type
    business_type = None
    for keyword, btype in BUSINESS_TYPE_MAP.items():
        if keyword in lower:
            business_type = btype
            break
    if not business_type:
        business_type = "dairy_farm"  # Default

    # Detect scale
    scale = None
    import re
    cow_match = re.search(r'(\d+)\s*(cow|gaay|गाय|unit)', lower)
    if cow_match:
        num = int(cow_match.group(1))
        scale = f"{num}_cow"

    state["agent_results"] = state.get("agent_results", {})
    state["agent_results"]["business_type"] = business_type
    state["agent_results"]["scale"] = scale
    state["agent_results"]["location"] = profile.get("district", "")
    state["tools_used"] = state.get("tools_used", [])
    return state


async def load_template_node(state: AgentState) -> AgentState:
    """Load DPR template for the business type."""
    results = state["agent_results"]
    template = get_dpr_template(results["business_type"], results.get("scale"))

    if template:
        results["template"] = template
        state["tools_used"].append("get_dpr_template")
    else:
        results["error"] = f"No template found for {results['business_type']}"
    return state


async def calculate_financials_node(state: AgentState) -> AgentState:
    """Calculate financial projections."""
    results = state["agent_results"]
    template = results.get("template")
    if not template:
        return state

    profile = state.get("user_profile", {})
    category = profile.get("category", "general").lower()

    # Determine subsidy based on applicable schemes and user category
    applicable = template.get("applicable_schemes", [])
    best_subsidy = 0
    for scheme in applicable:
        if category in ("sc", "st"):
            sub = scheme.get("subsidy_sc_st", scheme.get("subsidy_general", 0))
        else:
            sub = scheme.get("subsidy_general", 0)
        best_subsidy = max(best_subsidy, sub)

    financials = calculate_financials(
        template,
        subsidy_percent=best_subsidy,
        loan_interest=9.0,
        loan_tenure_years=7,
        user_category=category,
    )

    results["financials"] = financials
    state["tools_used"].append("calculate_financials")
    return state


async def generate_narrative_node(state: AgentState) -> AgentState:
    """Generate DPR narrative using LLM."""
    results = state["agent_results"]
    template = results.get("template")
    financials = results.get("financials")
    profile = state.get("user_profile", {})

    if template and financials:
        narrative = await generate_dpr_narrative(template, financials, profile)
        results["narrative"] = narrative
        state["tools_used"].append("generate_dpr_narrative")
    return state


async def save_dpr_node(state: AgentState) -> AgentState:
    """Save DPR to database."""
    db = PostgresClient()
    user_id = state.get("user_id", "")
    results = state["agent_results"]

    dpr_data = {
        "project_cost": results.get("financials", {}).get("project_cost", {}),
        "funding_pattern": results.get("financials", {}).get("funding_pattern", {}),
        "yearly_projections": results.get("financials", {}).get("yearly_projections", []),
        "financial_ratios": results.get("financials", {}).get("financial_ratios", {}),
        "viable": results.get("financials", {}).get("viable", False),
    }

    record = await save_dpr_record(db, user_id, results.get("business_type", ""), dpr_data)
    results["dpr_record"] = record
    state["tools_used"].append("save_dpr_record")

    state["follow_up_actions"] = state.get("follow_up_actions", [])
    state["follow_up_actions"].append({
        "type": "dpr_generated",
        "dpr_id": record.get("id"),
        "next_step": "Download PDF or apply to bank",
    })
    return state


async def format_dpr_response(state: AgentState) -> AgentState:
    """Format DPR summary response."""
    results = state.get("agent_results", {})
    language = state.get("language", "hi")

    if results.get("error"):
        state["agent_results"]["response"] = f"⚠️ {results['error']}"
        return state

    template = results.get("template", {})
    financials = results.get("financials", {})
    parts = []

    biz_name = template.get("business_name_hi" if language == "hi" else "business_name_en", "")
    variant = template.get("selected_variant", {})
    scale = variant.get("scale", "")

    parts.append(f"📊 *DPR: {biz_name}* ({scale})\n")

    # Project cost summary
    pc = financials.get("project_cost", {})
    parts.append(f"💰 *{'परियोजना लागत' if language == 'hi' else 'Project Cost'}*: Rs.{pc.get('total', 0):,.0f}")

    # Funding pattern
    fp = financials.get("funding_pattern", {})
    parts.append(f"  Subsidy: Rs.{fp.get('subsidy', 0):,.0f} ({fp.get('subsidy_percent', 0)}%)")
    parts.append(f"  Loan: Rs.{fp.get('loan_amount', 0):,.0f}")
    parts.append(f"  Own contribution: Rs.{fp.get('margin_money', 0):,.0f}")
    parts.append(f"  EMI: Rs.{fp.get('emi_monthly', 0):,.0f}/month")

    # Financial ratios
    fr = financials.get("financial_ratios", {})
    parts.append(f"\n📈 *{'वित्तीय अनुपात' if language == 'hi' else 'Financial Ratios'}*:")
    parts.append(f"  DSCR: {fr.get('dscr', 0)}")
    parts.append(f"  IRR: {fr.get('irr_percent', 0)}%")
    parts.append(f"  Payback: {fr.get('payback_period_years', 'N/A')} years")

    # Viability
    viable = financials.get("viable", False)
    if viable:
        parts.append(f"\n✅ *{'परियोजना व्यवहार्य है' if language == 'hi' else 'Project is VIABLE'}*")
    else:
        parts.append(f"\n⚠️ *{'कुछ अनुपात न्यूनतम से कम हैं' if language == 'hi' else 'Some ratios below minimum'}*")

    if results.get("dpr_record", {}).get("id"):
        parts.append(f"\n📁 DPR #{results['dpr_record']['id']} saved. PDF generation available.")

    state["agent_results"]["response"] = "\n".join(parts)
    return state


def route_template_loaded(state: AgentState) -> str:
    if state.get("agent_results", {}).get("error"):
        return "format_response"
    return "calculate_financials"


def build_dpr_agent() -> StateGraph:
    """Build the DPR generation agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("parse_query", parse_dpr_query)
    graph.add_node("load_template", load_template_node)
    graph.add_node("calculate_financials", calculate_financials_node)
    graph.add_node("generate_narrative", generate_narrative_node)
    graph.add_node("save_dpr", save_dpr_node)
    graph.add_node("format_response", format_dpr_response)

    graph.set_entry_point("parse_query")
    graph.add_edge("parse_query", "load_template")
    graph.add_conditional_edges("load_template", route_template_loaded, {
        "calculate_financials": "calculate_financials",
        "format_response": "format_response",
    })
    graph.add_edge("calculate_financials", "generate_narrative")
    graph.add_edge("generate_narrative", "save_dpr")
    graph.add_edge("save_dpr", "format_response")
    graph.add_edge("format_response", END)

    return graph
