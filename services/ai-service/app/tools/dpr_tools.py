"""
DPR (Detailed Project Report) Agent Tools
- get_dpr_template: Load template for business type
- calculate_financials: IRR, DSCR, payback period, revenue projections
- generate_dpr_narrative: Claude Sonnet quality DPR text
- save_dpr_pdf: Generate PDF output
"""

import json
import os
from math import pow

import structlog

from app.db.postgres_client import PostgresClient
from app.models.llm_provider import get_llm_router

logger = structlog.get_logger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "templates")


def get_dpr_template(business_type: str, scale: str | None = None) -> dict | None:
    """Load DPR template JSON for given business type."""
    filename = f"dpr_{business_type}.json"
    path = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(path):
        # Try fallback path
        path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "templates", filename)
    if not os.path.exists(path):
        logger.warning("dpr.template_not_found", business_type=business_type)
        return None

    with open(path, "r", encoding="utf-8") as f:
        template = json.load(f)

    # Select specific scale variant if provided
    if scale and "variants" in template:
        variant = template["variants"].get(scale)
        if variant:
            template["selected_variant"] = variant
            template["selected_scale"] = scale
        else:
            # Default to first variant
            first_key = next(iter(template["variants"]))
            template["selected_variant"] = template["variants"][first_key]
            template["selected_scale"] = first_key
    elif "variants" in template:
        first_key = next(iter(template["variants"]))
        template["selected_variant"] = template["variants"][first_key]
        template["selected_scale"] = first_key

    return template


def calculate_financials(template: dict, subsidy_percent: float = 0,
                         loan_interest: float = 9.0, loan_tenure_years: int = 7,
                         user_category: str = "general") -> dict:
    """
    Calculate complete financial projections for DPR.
    Returns: project cost, funding pattern, revenue/expense projections,
    IRR, DSCR, payback period.
    """
    variant = template.get("selected_variant", {})
    total_cost = variant.get("total_project_cost", 0)
    components = variant.get("components", [])

    # Funding pattern
    subsidy = total_cost * subsidy_percent / 100
    margin_money = total_cost * 0.10  # 10% promoter contribution
    loan_amount = total_cost - subsidy - margin_money

    # EMI calculation
    if loan_amount > 0 and loan_interest > 0:
        r = loan_interest / 100 / 12
        n = loan_tenure_years * 12
        emi = loan_amount * r * pow(1 + r, n) / (pow(1 + r, n) - 1)
        annual_debt_service = emi * 12
    else:
        emi = 0
        annual_debt_service = 0

    # Revenue projections (5 years)
    revenue_assumptions = variant.get("revenue_assumptions", {})
    expense_assumptions = variant.get("annual_expenses", {})

    yearly_projections = []
    cumulative_cash = -margin_money  # Initial investment
    payback_year = None

    for year in range(1, 6):
        # Revenue calculation (example for dairy)
        price_growth = pow(1 + revenue_assumptions.get("price_growth_annual_percent", 5) / 100, year - 1)

        if revenue_assumptions.get("milk_yield_per_cow_per_day_litres"):
            # Dairy-specific revenue
            cows = components[0].get("quantity", 10) if components else 10
            mortality = revenue_assumptions.get("mortality_rate_percent", 2) / 100
            active_cows = cows * (1 - mortality * (year - 1))
            active_cows = max(active_cows, cows * 0.8)

            milk_yield = revenue_assumptions.get("milk_yield_per_cow_per_day_litres", 12)
            lactation_days = revenue_assumptions.get("lactation_period_days", 300)
            milk_price = revenue_assumptions.get("milk_price_per_litre", 45) * price_growth

            milk_income = active_cows * milk_yield * lactation_days * milk_price
            calf_income = active_cows * revenue_assumptions.get("calf_sale_income_per_cow", 15000)
            dung_income = revenue_assumptions.get("dung_sale_annual", 20000)
            gross_revenue = milk_income + calf_income + dung_income
        else:
            # Generic revenue estimation
            gross_revenue = total_cost * 0.6 * price_growth

        # Expenses
        if expense_assumptions:
            num_units = components[0].get("quantity", 10) if components else 10
            feed_cost = (
                expense_assumptions.get("green_fodder_per_cow_per_day_kg", 0)
                * expense_assumptions.get("green_fodder_cost_per_kg", 0)
                + expense_assumptions.get("dry_fodder_per_cow_per_day_kg", 0)
                * expense_assumptions.get("dry_fodder_cost_per_kg", 0)
                + expense_assumptions.get("concentrate_per_cow_per_day_kg", 0)
                * expense_assumptions.get("concentrate_cost_per_kg", 0)
            ) * 365 * num_units

            vet_cost = expense_assumptions.get("veterinary_per_cow_annual", 0) * num_units
            labour = expense_assumptions.get("labour_monthly", 0) * 12
            electricity = expense_assumptions.get("electricity_monthly", 0) * 12
            maintenance = expense_assumptions.get("maintenance_annual", 0)
            insurance = expense_assumptions.get("insurance_annual", 0)
            misc = expense_assumptions.get("miscellaneous_annual", 0)

            total_expenses = feed_cost + vet_cost + labour + electricity + maintenance + insurance + misc
        else:
            total_expenses = gross_revenue * 0.6

        # Inflation on expenses (5% per year)
        total_expenses *= pow(1.05, year - 1)

        net_income = gross_revenue - total_expenses
        cash_after_debt = net_income - annual_debt_service
        cumulative_cash += cash_after_debt

        # Depreciation (straight line, 10 years on fixed assets)
        fixed_assets = sum(c["total_cost"] for c in components if "shed" in c.get("name", "").lower()
                          or "machine" in c.get("name", "").lower()
                          or "cooler" in c.get("name", "").lower()
                          or "vehicle" in c.get("name", "").lower())
        depreciation = fixed_assets / 10

        if payback_year is None and cumulative_cash >= 0:
            payback_year = year

        yearly_projections.append({
            "year": year,
            "gross_revenue": round(gross_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "net_income": round(net_income, 2),
            "debt_service": round(annual_debt_service, 2),
            "cash_after_debt": round(cash_after_debt, 2),
            "cumulative_cash": round(cumulative_cash, 2),
            "depreciation": round(depreciation, 2),
        })

    # Calculate DSCR (average over loan tenure)
    avg_net_income = sum(p["net_income"] for p in yearly_projections) / len(yearly_projections)
    dscr = avg_net_income / annual_debt_service if annual_debt_service > 0 else float("inf")

    # Calculate IRR (simplified using cash flows)
    cash_flows = [-margin_money] + [p["cash_after_debt"] for p in yearly_projections]
    irr = _calculate_irr(cash_flows)

    # Check against minimum ratios
    ratios = template.get("financial_ratios", {})
    viability = {
        "dscr_ok": dscr >= ratios.get("dscr_min", 1.5),
        "irr_ok": (irr or 0) >= ratios.get("irr_min_percent", 15) / 100,
        "payback_ok": (payback_year or 99) <= ratios.get("payback_period_max_years", 5),
        "debt_equity_ok": (loan_amount / margin_money if margin_money > 0 else 0) <= ratios.get("debt_equity_ratio_max", 3.0),
    }

    return {
        "project_cost": {
            "total": round(total_cost, 2),
            "components": components,
        },
        "funding_pattern": {
            "subsidy": round(subsidy, 2),
            "subsidy_percent": subsidy_percent,
            "margin_money": round(margin_money, 2),
            "loan_amount": round(loan_amount, 2),
            "loan_interest": loan_interest,
            "loan_tenure_years": loan_tenure_years,
            "emi_monthly": round(emi, 2),
        },
        "yearly_projections": yearly_projections,
        "financial_ratios": {
            "dscr": round(dscr, 2),
            "irr_percent": round(irr * 100, 2) if irr else None,
            "payback_period_years": payback_year,
            "debt_equity_ratio": round(loan_amount / margin_money, 2) if margin_money > 0 else None,
        },
        "viability": viability,
        "viable": all(viability.values()),
    }


def _calculate_irr(cash_flows: list[float], tolerance: float = 0.0001,
                    max_iterations: int = 100) -> float | None:
    """Calculate IRR using Newton's method."""
    if not cash_flows or all(cf == 0 for cf in cash_flows):
        return None

    rate = 0.1  # Initial guess
    for _ in range(max_iterations):
        npv = sum(cf / pow(1 + rate, i) for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / pow(1 + rate, i + 1) for i, cf in enumerate(cash_flows))
        if abs(dnpv) < 1e-12:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < tolerance:
            return new_rate
        rate = new_rate
        # Guard against divergence
        if rate < -0.99 or rate > 10:
            return None
    return rate if -1 < rate < 10 else None


async def generate_dpr_narrative(template: dict, financials: dict,
                                  user_profile: dict) -> str:
    """Generate professional DPR narrative using Claude Sonnet."""
    router = get_llm_router()

    variant = template.get("selected_variant", {})
    prompt = f"""Generate a professional Detailed Project Report (DPR) narrative for a bank loan application.

Business: {template.get('business_name_en', '')} ({template.get('business_name_hi', '')})
Scale: {variant.get('scale', '')}
Location: {user_profile.get('district', '')}, {user_profile.get('state', '')}
Applicant: {user_profile.get('name', 'Applicant')}
Category: {user_profile.get('category', 'General')}

Project Cost: Rs.{financials['project_cost']['total']:,.0f}
Subsidy: Rs.{financials['funding_pattern']['subsidy']:,.0f} ({financials['funding_pattern']['subsidy_percent']}%)
Loan Required: Rs.{financials['funding_pattern']['loan_amount']:,.0f}
EMI: Rs.{financials['funding_pattern']['emi_monthly']:,.0f}/month

Financial Ratios:
- DSCR: {financials['financial_ratios']['dscr']}
- IRR: {financials['financial_ratios']['irr_percent']}%
- Payback: {financials['financial_ratios']['payback_period_years']} years

Year-wise projections:
{json.dumps(financials['yearly_projections'], indent=2)}

Generate sections:
1. Executive Summary
2. Project Description & Technical Details
3. Market Analysis
4. Project Cost & Means of Finance
5. Revenue & Expense Projections
6. Financial Analysis (DSCR, IRR, Payback)
7. Risk Analysis & Mitigation
8. Conclusion & Recommendation

Use formal business English suitable for bank submission."""

    narrative = await router.chat_quality([
        {"role": "system", "content": "You are a professional DPR writer for agricultural and allied sector projects in India. Write formal, bank-ready project reports."},
        {"role": "user", "content": prompt},
    ], max_tokens=4000)

    return narrative


async def save_dpr_record(db: PostgresClient, user_id: str,
                           business_type: str, dpr_data: dict) -> dict:
    """Save DPR record to database."""
    row = await db.fetch_one(
        """INSERT INTO dpr_reports (user_id, business_type, project_cost,
                  subsidy_amount, loan_amount, dpr_json, status)
           VALUES ($1, $2, $3, $4, $5, $6::jsonb, 'draft')
           RETURNING id, status""",
        user_id, business_type,
        dpr_data.get("project_cost", {}).get("total", 0),
        dpr_data.get("funding_pattern", {}).get("subsidy", 0),
        dpr_data.get("funding_pattern", {}).get("loan_amount", 0),
        json.dumps(dpr_data))
    return dict(row) if row else {"error": "Failed to save DPR"}
