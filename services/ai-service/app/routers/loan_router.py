from fastapi import APIRouter

from app.schemas import LoanCheckRequest, LoanCheckResponse
from app.db.postgres_client import PostgresClient
from app.tools.loan_tools import (
    calculate_emi,
    check_loan_eligibility,
    find_best_loan_combination,
)

router = APIRouter()


@router.post("/loan/check", response_model=LoanCheckResponse)
async def check_loan(request: LoanCheckRequest):
    """Check loan eligibility for a user."""
    db = PostgresClient()
    results = await check_loan_eligibility(db, request.user_id, request.loan_type)
    eligible = [r for r in results if r.get("eligible")]

    combination = None
    if request.amount_needed and eligible:
        combination = await find_best_loan_combination(db, request.user_id, request.amount_needed)

    return LoanCheckResponse(
        eligible_loans=results,
        recommended_combination=combination,
    )


@router.post("/loan/emi")
async def calculate_emi_endpoint(
    principal: float, annual_rate: float, tenure_years: int,
):
    """Calculate EMI for a loan."""
    return calculate_emi(principal, annual_rate, tenure_years)


@router.post("/loan/best-combination")
async def find_best_combination(request: LoanCheckRequest):
    """Find the best combination of loans for needed amount."""
    db = PostgresClient()
    amount = request.amount_needed or 500000
    result = await find_best_loan_combination(db, request.user_id, amount)
    return result
