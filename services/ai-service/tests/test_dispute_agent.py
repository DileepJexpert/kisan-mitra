"""
Tests for Dispute Agent tools — MSMED Act interest calculation.
"""

import pytest
from datetime import date

from app.tools.dispute_tools import calculate_msmed_interest, MSMED_INTEREST_RATE


class TestMSMEDInterestCalculation:
    """Test compound interest under MSMED Act Section 16."""

    def test_interest_45_days_overdue(self):
        """Rs.3.5L overdue 45 days."""
        result = calculate_msmed_interest(
            350000, date(2026, 2, 1), date(2026, 3, 18)
        )
        assert result["principal"] == 350000
        assert result["days_overdue"] == 45
        assert result["interest_rate_annual"] == MSMED_INTEREST_RATE  # 19.5%
        assert result["interest_amount"] > 0
        assert result["total_claim"] > 350000
        assert result["legal_basis"] == "Section 15 & 16 of MSMED Act, 2006"

    def test_interest_90_days_overdue(self):
        """Rs.5L overdue 90 days — should be more than 45 days."""
        result_90 = calculate_msmed_interest(
            500000, date(2026, 1, 1), date(2026, 4, 1)
        )
        result_45 = calculate_msmed_interest(
            500000, date(2026, 1, 1), date(2026, 2, 15)
        )
        assert result_90["interest_amount"] > result_45["interest_amount"]
        assert result_90["months_overdue"] == 3.0

    def test_not_yet_overdue(self):
        """Not overdue — should return zero interest."""
        result = calculate_msmed_interest(
            100000, date(2026, 6, 1), date(2026, 5, 1)
        )
        assert result["days_overdue"] == 0
        assert result["interest_amount"] == 0
        assert result["total_claim"] == 100000

    def test_one_year_overdue(self):
        """Rs.10L overdue 365 days — significant compound interest."""
        result = calculate_msmed_interest(
            1000000, date(2025, 4, 1), date(2026, 4, 1)
        )
        assert result["days_overdue"] == 365
        # At 19.5% compound monthly for 1 year, interest should be ~21% of principal
        assert result["interest_amount"] > 190000  # At least ~19% simple
        assert result["interest_amount"] < 250000  # Not unreasonably high
        assert result["total_claim"] == result["principal"] + result["interest_amount"]

    def test_compound_vs_simple(self):
        """Compound interest should be higher than simple interest."""
        result = calculate_msmed_interest(
            1000000, date(2025, 1, 1), date(2026, 1, 1)
        )
        simple_interest = 1000000 * MSMED_INTEREST_RATE / 100  # Simple for 1 year
        assert result["interest_amount"] > simple_interest  # Compound > Simple

    def test_small_amount(self):
        """Small invoice amount."""
        result = calculate_msmed_interest(
            5000, date(2026, 1, 1), date(2026, 4, 1)
        )
        assert result["interest_amount"] > 0
        assert result["total_claim"] > 5000

    def test_default_calculation_date(self):
        """Uses today if no calculation_date provided."""
        result = calculate_msmed_interest(100000, date(2025, 1, 1))
        assert result["days_overdue"] > 0
        assert result["calculation_date"] == str(date.today())
