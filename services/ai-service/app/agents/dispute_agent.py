"""
Dispute Resolution Agent — LangGraph StateGraph
Helps MSMEs with payment dispute resolution under MSMED Act.
OCR invoice → calculate interest → generate legal notice → create dispute record.
"""

import base64
from datetime import date, datetime

from langgraph.graph import StateGraph, END

import structlog

from app.agents.state import AgentState
from app.db.postgres_client import PostgresClient
from app.tools.dispute_tools import (
    calculate_msmed_interest,
    create_dispute_record,
    extract_invoice_data,
    generate_legal_notice,
)

logger = structlog.get_logger(__name__)


async def parse_dispute_input(state: AgentState) -> AgentState:
    """Parse dispute query — check for invoice image or manual data."""
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else {}
    content = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)

    state["agent_results"] = state.get("agent_results", {})
    state["tools_used"] = state.get("tools_used", [])

    # Check if there's an image attachment (base64)
    has_image = False
    if isinstance(last_msg, dict) and last_msg.get("image_base64"):
        has_image = True
        state["agent_results"]["image_base64"] = last_msg["image_base64"]
    elif isinstance(last_msg, dict) and last_msg.get("invoice_data"):
        state["agent_results"]["invoice_data"] = last_msg["invoice_data"]

    state["agent_results"]["has_image"] = has_image
    state["agent_results"]["dispute_stage"] = "new"
    return state


async def extract_invoice_node(state: AgentState) -> AgentState:
    """OCR extract invoice data from image."""
    results = state["agent_results"]

    if results.get("has_image") and results.get("image_base64"):
        image_bytes = base64.b64decode(results["image_base64"])
        invoice_data = await extract_invoice_data(image_bytes)
        results["invoice_data"] = invoice_data
        state["tools_used"].append("extract_invoice_data")
    return state


async def calculate_interest_node(state: AgentState) -> AgentState:
    """Calculate MSMED interest on overdue amount."""
    results = state["agent_results"]
    invoice = results.get("invoice_data", {})

    # Parse dates
    due_date_str = invoice.get("due_date") or invoice.get("payment_due_date")
    invoice_date_str = invoice.get("invoice_date")
    amount = float(invoice.get("total_amount", 0))

    if not due_date_str and invoice_date_str:
        # Default: payment due within 45 days of invoice (MSMED Act Section 15)
        try:
            inv_date = _parse_date(invoice_date_str)
            from datetime import timedelta
            due_date = inv_date + timedelta(days=45)
            due_date_str = str(due_date)
        except (ValueError, TypeError):
            pass

    if due_date_str and amount > 0:
        due_date = _parse_date(due_date_str)
        interest = calculate_msmed_interest(amount, due_date)
        results["interest_calculation"] = interest
        state["tools_used"].append("calculate_msmed_interest")
    else:
        results["interest_calculation"] = {"error": "Missing due date or amount"}

    return state


async def generate_notice_node(state: AgentState) -> AgentState:
    """Generate legal notice draft."""
    results = state["agent_results"]
    invoice = results.get("invoice_data", {})
    interest = results.get("interest_calculation", {})
    profile = state.get("user_profile", {})

    dispute_data = {
        "sender_name": profile.get("name", "MSME Owner"),
        "udyam_number": profile.get("udyam_number", ""),
        "buyer_name": invoice.get("buyer_name", ""),
        "buyer_gstin": invoice.get("buyer_gstin", ""),
        "invoice_number": invoice.get("invoice_number", ""),
        "invoice_date": invoice.get("invoice_date", ""),
        "invoice_amount": invoice.get("total_amount", 0),
        "due_date": interest.get("due_date", ""),
        "days_overdue": interest.get("days_overdue", 0),
        "interest_amount": interest.get("interest_amount", 0),
        "total_claim": interest.get("total_claim", 0),
    }

    notice = await generate_legal_notice(dispute_data)
    results["legal_notice"] = notice
    results["dispute_data"] = dispute_data
    state["tools_used"].append("generate_legal_notice")
    return state


async def save_dispute_node(state: AgentState) -> AgentState:
    """Save dispute record to database."""
    db = PostgresClient()
    user_id = state.get("user_id", "")
    results = state["agent_results"]
    dispute_data = results.get("dispute_data", {})
    interest = results.get("interest_calculation", {})

    record_data = {
        "buyer_name": dispute_data.get("buyer_name"),
        "buyer_gstin": dispute_data.get("buyer_gstin"),
        "invoice_number": dispute_data.get("invoice_number"),
        "invoice_date": dispute_data.get("invoice_date"),
        "invoice_amount": dispute_data.get("invoice_amount"),
        "due_date": interest.get("due_date"),
        "days_overdue": interest.get("days_overdue"),
        "interest_amount": interest.get("interest_amount"),
        "total_claim": interest.get("total_claim"),
    }

    record = await create_dispute_record(db, user_id, record_data)
    results["dispute_record"] = record
    state["tools_used"].append("create_dispute_record")

    # Add follow-up action
    state["follow_up_actions"] = state.get("follow_up_actions", [])
    state["follow_up_actions"].append({
        "type": "dispute_created",
        "dispute_id": record.get("id"),
        "next_step": "Review and send legal notice",
    })
    return state


async def format_dispute_response(state: AgentState) -> AgentState:
    """Format dispute resolution response."""
    results = state.get("agent_results", {})
    language = state.get("language", "hi")
    invoice = results.get("invoice_data", {})
    interest = results.get("interest_calculation", {})

    parts = []

    if invoice.get("error"):
        parts.append(f"⚠️ {invoice['error']}")
        state["agent_results"]["response"] = "\n".join(parts)
        return state

    # Invoice summary
    if language == "hi":
        parts.append("📄 *चालान विवरण*:")
    else:
        parts.append("📄 *Invoice Details*:")

    if invoice.get("invoice_number"):
        parts.append(f"  Invoice: {invoice['invoice_number']}")
    if invoice.get("buyer_name"):
        parts.append(f"  Buyer: {invoice['buyer_name']}")
    if invoice.get("total_amount"):
        parts.append(f"  Amount: Rs.{float(invoice['total_amount']):,.0f}")

    # Interest calculation
    if interest and not interest.get("error"):
        parts.append(f"\n💰 *{'ब्याज गणना (MSMED Act)' if language == 'hi' else 'Interest Calculation (MSMED Act)'}*:")
        parts.append(f"  Days overdue: {interest.get('days_overdue', 0)}")
        parts.append(f"  Interest rate: {interest.get('interest_rate_annual', 0)}% p.a.")
        parts.append(f"  Interest amount: Rs.{interest.get('interest_amount', 0):,.0f}")
        parts.append(f"  *Total claim: Rs.{interest.get('total_claim', 0):,.0f}*")
        parts.append(f"  Legal basis: {interest.get('legal_basis', '')}")

    # Legal notice
    if results.get("legal_notice"):
        parts.append(f"\n📝 *{'कानूनी नोटिस तैयार' if language == 'hi' else 'Legal Notice Prepared'}*")
        parts.append("Notice has been generated and saved. You can download or send it.")

    # Dispute record
    if results.get("dispute_record", {}).get("id"):
        parts.append(f"\n✅ Dispute #{results['dispute_record']['id']} created.")

    state["agent_results"]["response"] = "\n".join(parts)
    return state


def _parse_date(date_str: str) -> date:
    """Parse date from various formats."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def route_has_image(state: AgentState) -> str:
    if state.get("agent_results", {}).get("has_image"):
        return "extract_invoice"
    return "calculate_interest"


def build_dispute_agent() -> StateGraph:
    """Build the dispute resolution agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("parse_input", parse_dispute_input)
    graph.add_node("extract_invoice", extract_invoice_node)
    graph.add_node("calculate_interest", calculate_interest_node)
    graph.add_node("generate_notice", generate_notice_node)
    graph.add_node("save_dispute", save_dispute_node)
    graph.add_node("format_response", format_dispute_response)

    graph.set_entry_point("parse_input")
    graph.add_conditional_edges("parse_input", route_has_image, {
        "extract_invoice": "extract_invoice",
        "calculate_interest": "calculate_interest",
    })
    graph.add_edge("extract_invoice", "calculate_interest")
    graph.add_edge("calculate_interest", "generate_notice")
    graph.add_edge("generate_notice", "save_dispute")
    graph.add_edge("save_dispute", "format_response")
    graph.add_edge("format_response", END)

    return graph
