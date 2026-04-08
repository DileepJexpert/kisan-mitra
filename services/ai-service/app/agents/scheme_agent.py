"""
Scheme Advisory Agent — LangGraph StateGraph
Helps users discover government schemes, check eligibility, get document checklists.
"""

from langgraph.graph import StateGraph, END

import structlog

from app.agents.state import AgentState
from app.db.chroma_client import ChromaClient
from app.db.postgres_client import PostgresClient
from app.tools.scheme_tools import (
    check_eligibility,
    get_document_checklist,
    get_eligible_schemes_for_user,
    search_schemes,
)

logger = structlog.get_logger(__name__)


async def understand_query(state: AgentState) -> AgentState:
    """Parse user intent: search, eligibility check, or document checklist."""
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    lower = last_msg.lower()

    intent = "search"
    if any(kw in lower for kw in ["eligible", "eligib", "patra", "पात्र", "योग्य", "qualify"]):
        intent = "eligibility"
    elif any(kw in lower for kw in ["document", "dastavez", "दस्तावेज", "kagaz", "कागज", "papers"]):
        intent = "documents"
    elif any(kw in lower for kw in ["all scheme", "sab yojana", "सब योजना", "list"]):
        intent = "list_all"

    state["agent_results"] = state.get("agent_results", {})
    state["agent_results"]["scheme_intent"] = intent
    state["tools_used"] = state.get("tools_used", [])
    return state


async def search_schemes_node(state: AgentState) -> AgentState:
    """Search for relevant schemes using RAG."""
    messages = state.get("messages", [])
    query = messages[-1]["content"] if messages else ""
    profile = state.get("user_profile", {})

    chroma = ChromaClient()
    results = await search_schemes(
        chroma, query,
        sector=profile.get("sector"),
        state=profile.get("state"),
    )

    state["agent_results"]["schemes_found"] = results
    state["tools_used"].append("search_schemes")
    return state


async def check_eligibility_node(state: AgentState) -> AgentState:
    """Check eligibility for found schemes or all active schemes."""
    db = PostgresClient()
    chroma = ChromaClient()
    user_id = state.get("user_id", "")
    profile = state.get("user_profile", {})

    eligible = await get_eligible_schemes_for_user(
        db, chroma, user_id, sector=profile.get("sector")
    )

    state["agent_results"]["eligible_schemes"] = eligible
    state["tools_used"].append("check_eligibility")
    return state


async def get_documents_node(state: AgentState) -> AgentState:
    """Get document checklists for eligible schemes."""
    db = PostgresClient()
    schemes = state.get("agent_results", {}).get("eligible_schemes", [])

    doc_lists = {}
    for scheme in schemes[:5]:  # Limit to top 5
        code = scheme.get("scheme_code", "")
        docs = await get_document_checklist(db, code)
        if docs:
            doc_lists[code] = {
                "scheme_name": scheme.get("scheme_name", ""),
                "documents": docs,
            }

    state["agent_results"]["document_checklists"] = doc_lists
    state["tools_used"].append("get_document_checklist")
    return state


async def format_response(state: AgentState) -> AgentState:
    """Format final response for user."""
    results = state.get("agent_results", {})
    intent = results.get("scheme_intent", "search")
    language = state.get("language", "hi")

    response_parts = []

    if intent == "eligibility" or intent == "list_all":
        schemes = results.get("eligible_schemes", [])
        if schemes:
            if language == "hi":
                response_parts.append(f"आपके लिए {len(schemes)} योजनाएं उपलब्ध हैं:\n")
            else:
                response_parts.append(f"You are eligible for {len(schemes)} schemes:\n")

            for i, s in enumerate(schemes[:5], 1):
                name = s.get("scheme_name", "")
                subsidy = s.get("subsidy_percentage")
                max_amt = s.get("max_subsidy_amount")
                line = f"{i}. *{name}*"
                if subsidy:
                    line += f" — {subsidy}% subsidy"
                if max_amt:
                    line += f" (max Rs.{max_amt:,.0f})"
                response_parts.append(line)
        else:
            response_parts.append("कोई योजना नहीं मिली।" if language == "hi"
                                  else "No matching schemes found.")

    elif intent == "documents":
        doc_lists = results.get("document_checklists", {})
        if doc_lists:
            for code, info in doc_lists.items():
                response_parts.append(f"\n📋 *{info['scheme_name']}*:")
                for doc in info["documents"]:
                    response_parts.append(f"  • {doc}")
        else:
            response_parts.append("कृपया पहले योजना बताएं।" if language == "hi"
                                  else "Please specify which scheme.")

    else:  # search
        schemes = results.get("schemes_found", [])
        if schemes:
            if language == "hi":
                response_parts.append(f"{len(schemes)} योजनाएं मिलीं:\n")
            else:
                response_parts.append(f"Found {len(schemes)} schemes:\n")
            for i, s in enumerate(schemes[:5], 1):
                name = s.get("name_en", s.get("scheme_name", ""))
                response_parts.append(f"{i}. *{name}*")
                desc = s.get("description_en", "")
                if desc:
                    response_parts.append(f"   {desc[:100]}...")
        else:
            response_parts.append("कोई योजना नहीं मिली।" if language == "hi"
                                  else "No schemes found.")

    state["agent_results"]["response"] = "\n".join(response_parts)
    return state


def route_by_intent(state: AgentState) -> str:
    """Route based on parsed intent."""
    intent = state.get("agent_results", {}).get("scheme_intent", "search")
    if intent == "eligibility" or intent == "list_all":
        return "check_eligibility"
    elif intent == "documents":
        return "check_eligibility"  # Need eligible schemes first
    else:
        return "search"


def route_after_eligibility(state: AgentState) -> str:
    """After eligibility, check if documents were requested."""
    intent = state.get("agent_results", {}).get("scheme_intent", "")
    if intent == "documents":
        return "get_documents"
    return "format_response"


def build_scheme_agent() -> StateGraph:
    """Build the scheme advisory agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("understand", understand_query)
    graph.add_node("search", search_schemes_node)
    graph.add_node("check_eligibility", check_eligibility_node)
    graph.add_node("get_documents", get_documents_node)
    graph.add_node("format_response", format_response)

    graph.set_entry_point("understand")
    graph.add_conditional_edges("understand", route_by_intent, {
        "check_eligibility": "check_eligibility",
        "search": "search",
    })
    graph.add_edge("search", "format_response")
    graph.add_conditional_edges("check_eligibility", route_after_eligibility, {
        "get_documents": "get_documents",
        "format_response": "format_response",
    })
    graph.add_edge("get_documents", "format_response")
    graph.add_edge("format_response", END)

    return graph
