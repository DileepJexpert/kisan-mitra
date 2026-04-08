"""
Government Scheme Data Loader
Loads scheme data from curated JSON files into PostgreSQL and ChromaDB.
In future: scrape from myscheme.gov.in
"""

import os
import json
import uuid

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/kisanmitra")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes")


def load_schemes_from_json() -> list[dict]:
    """Load all scheme JSON files from data directory."""
    schemes = []
    json_files = [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.endswith(".json")
    ]

    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                schemes.extend(data)
            else:
                schemes.append(data)

    print(f"Loaded {len(schemes)} schemes from {len(json_files)} files")
    return schemes


def save_schemes_to_db(schemes: list[dict]):
    """Insert schemes into PostgreSQL."""
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            for scheme in schemes:
                cur.execute("""
                    INSERT INTO schemes (
                        id, scheme_code, name_en, name_hi, ministry, department,
                        scheme_type, state, sector, subsector, eligibility_criteria,
                        benefit_type, subsidy_percentage, max_subsidy_amount,
                        loan_amount_max, interest_subsidy, application_url,
                        documents_required, application_process, description_en,
                        description_hi, is_active, last_verified_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    )
                    ON CONFLICT (scheme_code) DO UPDATE SET
                        name_en = EXCLUDED.name_en,
                        name_hi = EXCLUDED.name_hi,
                        eligibility_criteria = EXCLUDED.eligibility_criteria,
                        subsidy_percentage = EXCLUDED.subsidy_percentage,
                        max_subsidy_amount = EXCLUDED.max_subsidy_amount,
                        description_en = EXCLUDED.description_en,
                        description_hi = EXCLUDED.description_hi,
                        last_verified_at = NOW(),
                        updated_at = NOW()
                """, (
                    str(uuid.uuid4()),
                    scheme.get("scheme_code"),
                    scheme.get("name_en"),
                    scheme.get("name_hi"),
                    scheme.get("ministry"),
                    scheme.get("department"),
                    scheme.get("scheme_type", "central"),
                    scheme.get("state"),
                    scheme.get("sector"),
                    scheme.get("subsector"),
                    json.dumps(scheme.get("eligibility_criteria", {})),
                    scheme.get("benefit_type"),
                    scheme.get("subsidy_percentage"),
                    scheme.get("max_subsidy_amount"),
                    scheme.get("loan_amount_max"),
                    scheme.get("interest_subsidy"),
                    scheme.get("application_url"),
                    json.dumps(scheme.get("documents_required", [])),
                    scheme.get("application_process"),
                    scheme.get("description_en"),
                    scheme.get("description_hi"),
                    scheme.get("is_active", True),
                ))

            conn.commit()
            print(f"Saved {len(schemes)} schemes to database")
    except Exception as e:
        conn.rollback()
        print(f"Error saving schemes: {e}")
        raise
    finally:
        conn.close()


def load_schemes():
    """Main function: load from JSON and save to DB."""
    schemes = load_schemes_from_json()
    if schemes:
        save_schemes_to_db(schemes)
    else:
        print("No scheme data found. Check data/schemes/ directory.")


if __name__ == "__main__":
    load_schemes()
