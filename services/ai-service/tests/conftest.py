"""
Shared test fixtures for KisanMitra AI service tests.
"""

import pytest


@pytest.fixture
def farmer_profile_sc():
    """SC farmer with 2 acres land, low income."""
    return {
        "id": "test-user-sc-farmer",
        "phone": "9876543210",
        "name": "Ram Kumar",
        "language": "hi",
        "state": "Uttar Pradesh",
        "district": "Kanpur",
        "category": "sc",
        "gender": "male",
        "income_annual": 180000,
        "land_acres": 2.0,
        "occupation": "farmer",
        "udyam_number": None,
    }


@pytest.fixture
def farmer_profile_general():
    """General category farmer with 5 acres."""
    return {
        "id": "test-user-gen-farmer",
        "phone": "9876543211",
        "name": "Suresh Patel",
        "language": "hi",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "category": "general",
        "gender": "male",
        "income_annual": 300000,
        "land_acres": 5.0,
        "occupation": "farmer",
        "udyam_number": None,
    }


@pytest.fixture
def msme_owner_profile():
    """MSME owner with Udyam registration."""
    return {
        "id": "test-user-msme",
        "phone": "9876543212",
        "name": "Priya Sharma",
        "language": "hi",
        "state": "Rajasthan",
        "district": "Jaipur",
        "category": "general",
        "gender": "female",
        "income_annual": 600000,
        "land_acres": 0,
        "occupation": "msme_owner",
        "udyam_number": "UDYAM-RJ-01-0012345",
    }


@pytest.fixture
def sample_scheme_pmfme():
    """PMFME scheme data for testing."""
    return {
        "scheme_code": "PMFME",
        "name_en": "PM Formalization of Micro Food Processing Enterprises",
        "name_hi": "प्रधानमंत्री सूक्ष्म खाद्य प्रसंस्करण उद्यम योजना",
        "sector": "food_processing",
        "benefit_type": "subsidy",
        "subsidy_percentage": 35,
        "max_subsidy_amount": 1000000,
        "eligibility_criteria": {
            "categories": ["general", "obc", "sc", "st"],
            "gender": ["male", "female"],
            "age_min": 18,
            "occupation": ["farmer", "msme_owner", "shg_member"],
        },
        "documents_required": ["Aadhaar Card", "PAN Card", "DPR", "Bank Passbook"],
    }


@pytest.fixture
def sample_scheme_nabard():
    """NABARD DEDS scheme for testing."""
    return {
        "scheme_code": "NABARD_DEDS",
        "name_en": "NABARD Dairy Entrepreneurship Development Scheme",
        "sector": "dairy",
        "benefit_type": "subsidy",
        "subsidy_percentage": 25,
        "max_subsidy_amount": 1250000,
        "eligibility_criteria": {
            "categories": ["general", "obc", "sc", "st"],
            "gender": ["male", "female"],
            "occupation": ["farmer", "msme_owner"],
        },
    }
