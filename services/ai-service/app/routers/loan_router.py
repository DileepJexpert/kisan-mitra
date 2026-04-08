from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas import LoanCheckRequest, LoanCheckResponse

router = APIRouter()


@router.post("/loan/check", response_model=LoanCheckResponse)
async def check_loan_eligibility(request: LoanCheckRequest):
    """Check loan eligibility for a farmer."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Loan eligibility check endpoint not yet implemented"},
    )


@router.post("/loan/emi")
async def calculate_emi(request: LoanCheckRequest):
    """Calculate EMI for different loan options."""
    return JSONResponse(
        status_code=501,
        content={"detail": "EMI calculation endpoint not yet implemented"},
    )


@router.post("/loan/best-combination")
async def find_best_loan_combination(request: LoanCheckRequest):
    """Find the best combination of loans for a farmer."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Best loan combination endpoint not yet implemented"},
    )
