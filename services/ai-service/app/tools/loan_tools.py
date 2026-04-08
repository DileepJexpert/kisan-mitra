"""
Loan Agent Tools
- check_loan_eligibility, calculate_emi, find_best_loan_combination
"""

import json
import os
import structlog

from app.db.postgres_client import PostgresClient

logger = structlog.get_logger(__name__)

_loan_rules: list[dict] | None = None


def _load_loan_rules() -> list[dict]:
    global _loan_rules
    if _loan_rules is not None:
        return _loan_rules

    rules_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "loan_rules", "all_loans.json")
    # Fallback to project data directory
    if not os.path.exists(rules_path):
        rules_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "loan_rules", "all_loans.json")

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            _loan_rules = json.load(f)
    except FileNotFoundError:
        logger.warning("loan_rules.file_not_found", path=rules_path)
        _loan_rules = []
    return _loan_rules


def calculate_emi(principal: float, annual_rate: float, tenure_years: int) -> dict:
    """Standard EMI calculation: EMI = P × r × (1+r)^n / ((1+r)^n - 1)"""
    if annual_rate == 0:
        monthly = principal / (tenure_years * 12)
        return {"emi_monthly": round(monthly, 2), "total_interest": 0, "total_payment": round(principal, 2)}

    r = annual_rate / 100 / 12  # monthly rate
    n = tenure_years * 12  # total months
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    total_payment = emi * n
    total_interest = total_payment - principal

    return {
        "emi_monthly": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
    }


async def check_loan_eligibility(db: PostgresClient, user_id: str,
                                   loan_type: str | None = None) -> list[dict]:
    """Check eligibility for all or specific loan types."""
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        return []

    rules = _load_loan_rules()
    results = []

    for loan in rules:
        if loan_type and loan["loan_code"] != loan_type:
            continue

        elig = loan.get("eligibility_rules", {})
        eligible = True
        reasons = []

        # Occupation check
        occupations = [o.lower() for o in elig.get("occupation", ["any"])]
        if "any" not in occupations and user.get("occupation"):
            if user["occupation"].lower() not in occupations:
                eligible = False
                reasons.append(f"Occupation '{user['occupation']}' not eligible")

        # Category check
        if elig.get("categories") and user.get("category"):
            if user["category"].lower() not in [c.lower() for c in elig["categories"]]:
                eligible = False
                reasons.append(f"Category '{user['category']}' not eligible")

        # Gender check
        if elig.get("gender") and user.get("gender"):
            if user["gender"].lower() not in [g.lower() for g in elig["gender"]]:
                eligible = False
                reasons.append(f"Gender restriction")

        # Land requirement
        if elig.get("land_required") and not user.get("land_acres"):
            eligible = False
            reasons.append("Land ownership required")

        # Udyam requirement
        if elig.get("udyam_required") and not user.get("udyam_number"):
            eligible = False
            reasons.append("Udyam registration required")

        # Calculate EMI
        max_amt = loan.get("max_amount", 0)
        rate = loan.get("interest_rate_max", 10)
        tenure = loan.get("tenure_years_max", 5)
        emi_info = calculate_emi(max_amt, rate, tenure) if max_amt > 0 else {}

        results.append({
            "loan_code": loan["loan_code"],
            "loan_name": loan.get("loan_name_en", ""),
            "loan_name_hi": loan.get("loan_name_hi", ""),
            "eligible": eligible,
            "max_amount": max_amt,
            "interest_rate_range": f"{loan.get('interest_rate_min', 0)}-{loan.get('interest_rate_max', 0)}%",
            "subsidy_percentage": loan.get("subsidy_percentage", 0),
            "collateral_required": loan.get("collateral_required", False),
            "emi_monthly": emi_info.get("emi_monthly"),
            "tenure_years": tenure,
            "documents_required": loan.get("documents_required", []),
            "reason_if_ineligible": "; ".join(reasons) if not eligible else None,
        })

    return results


async def find_best_loan_combination(db: PostgresClient, user_id: str,
                                      amount_needed: float) -> dict:
    """Recommend best loan combination to cover needed amount."""
    eligible = [l for l in await check_loan_eligibility(db, user_id) if l["eligible"]]

    # Sort by: highest subsidy first, then lowest interest
    eligible.sort(key=lambda x: (-(x.get("subsidy_percentage") or 0), x.get("interest_rate_range", "99")))

    combination = []
    remaining = amount_needed
    total_subsidy = 0

    for loan in eligible:
        if remaining <= 0:
            break
        amount = min(remaining, loan["max_amount"])
        subsidy = amount * (loan.get("subsidy_percentage") or 0) / 100
        loan_amount = amount - subsidy

        combination.append({
            "loan_code": loan["loan_code"],
            "loan_name": loan["loan_name"],
            "amount": amount,
            "subsidy": subsidy,
            "loan_after_subsidy": loan_amount,
            "emi": calculate_emi(loan_amount, float(loan["interest_rate_range"].split("-")[1].replace("%", "")),
                                  loan["tenure_years"])["emi_monthly"] if loan_amount > 0 else 0,
        })
        remaining -= amount
        total_subsidy += subsidy

    return {
        "recommended_combination": combination,
        "total_funding": amount_needed,
        "total_subsidy": round(total_subsidy, 2),
        "own_contribution": round(max(0, remaining), 2),
        "gap": round(max(0, remaining), 2),
    }
