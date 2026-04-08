"""
Tests for Loan Agent tools.
"""

import pytest

from app.tools.loan_tools import calculate_emi


class TestCalculateEMI:
    """Test EMI calculation formula."""

    def test_emi_standard_case(self):
        """Rs.5L at 10% for 5 years → EMI ≈ Rs.10,624."""
        result = calculate_emi(500000, 10.0, 5)
        assert 10600 <= result["emi_monthly"] <= 10650
        assert result["total_interest"] > 0
        assert result["total_payment"] == pytest.approx(
            result["emi_monthly"] * 60, rel=0.01
        )

    def test_emi_zero_interest(self):
        """Zero interest should give simple division."""
        result = calculate_emi(120000, 0, 2)
        assert result["emi_monthly"] == 5000.0
        assert result["total_interest"] == 0
        assert result["total_payment"] == 120000.0

    def test_emi_kcc_rate(self):
        """KCC at 4% for 1 year on Rs.3L."""
        result = calculate_emi(300000, 4.0, 1)
        assert 25000 <= result["emi_monthly"] <= 26000
        assert result["total_interest"] < 300000 * 0.05  # Interest < 5% of principal

    def test_emi_large_amount(self):
        """Rs.10L at 12% for 7 years."""
        result = calculate_emi(1000000, 12.0, 7)
        assert result["emi_monthly"] > 0
        assert result["total_payment"] > 1000000  # Must pay more than principal

    def test_emi_small_mudra_shishu(self):
        """MUDRA Shishu: Rs.50K at 12% for 3 years."""
        result = calculate_emi(50000, 12.0, 3)
        assert 1600 <= result["emi_monthly"] <= 1700

    def test_emi_nabard_sc_st(self):
        """NABARD DEDS after 33% subsidy: Rs.6.7L at 9% for 5 years."""
        # 10L project, 33% subsidy = 3.3L subsidy, 10% own = 1L, loan = 5.7L
        result = calculate_emi(570000, 9.0, 5)
        assert result["emi_monthly"] > 0
        assert result["total_interest"] > 0


class TestEMIEdgeCases:

    def test_emi_one_month_tenure(self):
        """Very short tenure."""
        result = calculate_emi(100000, 12.0, 1)
        # ~12 monthly payments
        assert result["emi_monthly"] > 8000

    def test_emi_high_interest(self):
        """High interest rate (credit card level)."""
        result = calculate_emi(100000, 36.0, 1)
        assert result["total_interest"] > 15000
