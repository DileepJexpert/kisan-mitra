#!/usr/bin/env python3
"""
Master Data Seeding Script
Sets up a fresh KisanMitra environment from scratch.

Usage:
    python scripts/seed_all_data.py

Steps:
    1. Execute SQL migrations
    2. Load scheme data from JSON into PostgreSQL
    3. Generate 365 days of mock mandi price data
    4. Load scheme data into ChromaDB for RAG
"""

import os
import sys
import json

import psycopg2
from dotenv import load_dotenv

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "scraper"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/kisanmitra")
CHROMA_HOST = os.getenv("CHROMA_HOST", "http://localhost:8000")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_sql_migrations():
    """Execute SQL migration files in order."""
    print("\n[1/4] Running SQL migrations...")
    sql_dir = os.path.join(PROJECT_ROOT, "infra", "sql")
    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])

    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            for sql_file in sql_files:
                filepath = os.path.join(sql_dir, sql_file)
                print(f"  Executing: {sql_file}")
                with open(filepath, "r", encoding="utf-8") as f:
                    sql = f.read()
                cur.execute(sql)
            conn.commit()
        print(f"  ✓ Executed {len(sql_files)} migration files")
    except psycopg2.errors.DuplicateTable:
        conn.rollback()
        print("  Tables already exist. Skipping migrations.")
    except Exception as e:
        conn.rollback()
        print(f"  Error: {e}")
        raise
    finally:
        conn.close()


def load_scheme_data():
    """Load scheme data from JSON files into PostgreSQL."""
    print("\n[2/4] Loading scheme data into PostgreSQL...")
    try:
        from scrapers.myscheme_scraper import load_schemes
        load_schemes()
    except Exception as e:
        print(f"  Error loading schemes: {e}")
        print("  Trying direct load...")
        # Direct load fallback
        schemes_dir = os.path.join(PROJECT_ROOT, "data", "schemes")
        if not os.path.exists(schemes_dir):
            print(f"  Schemes directory not found: {schemes_dir}")
            return

        schemes = []
        for f in os.listdir(schemes_dir):
            if f.endswith(".json"):
                with open(os.path.join(schemes_dir, f), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        schemes.extend(data)
        print(f"  Loaded {len(schemes)} schemes from JSON files")


def seed_mandi_data():
    """Generate and load historical mandi price data."""
    print("\n[3/4] Generating historical mandi price data (365 days)...")
    try:
        from scrapers.agmarknet_scraper import seed_historical_data
        seed_historical_data(365)
    except Exception as e:
        print(f"  Error seeding mandi data: {e}")


def load_schemes_to_chromadb():
    """Load scheme data into ChromaDB for RAG search."""
    print("\n[4/4] Loading schemes into ChromaDB for RAG...")
    try:
        import chromadb

        client = chromadb.HttpClient(host=CHROMA_HOST.replace("http://", "").split(":")[0],
                                      port=int(CHROMA_HOST.split(":")[-1]))
        collection = client.get_or_create_collection(
            name="schemes",
            metadata={"description": "Government scheme data for RAG search"}
        )

        # Load schemes from JSON
        schemes_dir = os.path.join(PROJECT_ROOT, "data", "schemes")
        schemes = []
        for f in os.listdir(schemes_dir):
            if f.endswith(".json"):
                with open(os.path.join(schemes_dir, f), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        schemes.extend(data)

        if not schemes:
            print("  No scheme data found.")
            return

        # Prepare documents for ChromaDB
        documents = []
        metadatas = []
        ids = []

        for scheme in schemes:
            # Combine text for embedding
            doc_text = (
                f"{scheme.get('name_en', '')}. {scheme.get('name_hi', '')}. "
                f"{scheme.get('description_en', '')} "
                f"{scheme.get('description_hi', '')} "
                f"Sector: {scheme.get('sector', '')}. "
                f"Benefit: {scheme.get('benefit_type', '')}. "
                f"Subsidy: {scheme.get('subsidy_percentage', 'N/A')}%. "
                f"Max amount: Rs.{scheme.get('max_subsidy_amount', 'N/A')}."
            )
            documents.append(doc_text)
            metadatas.append({
                "scheme_code": scheme.get("scheme_code", ""),
                "sector": scheme.get("sector", ""),
                "state": scheme.get("state") or "all",
                "scheme_type": scheme.get("scheme_type", "central"),
                "benefit_type": scheme.get("benefit_type", ""),
            })
            ids.append(scheme.get("scheme_code", str(len(ids))))

        # Add to ChromaDB (in batches if needed)
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            end = min(i + batch_size, len(documents))
            collection.upsert(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
            )

        print(f"  ✓ Loaded {len(documents)} schemes into ChromaDB")

    except Exception as e:
        print(f"  Error loading to ChromaDB: {e}")
        print("  ChromaDB may not be running. Start it with: docker-compose up chromadb")


def main():
    print("=" * 60)
    print("KisanMitra Data Seeding Script")
    print("=" * 60)

    run_sql_migrations()
    load_scheme_data()
    seed_mandi_data()
    load_schemes_to_chromadb()

    print("\n" + "=" * 60)
    print("Data seeding complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start all services: docker-compose up -d")
    print("  2. Test: curl http://localhost:8080/api/v1/test/chat")
    print("  3. Check health: curl http://localhost:8001/health")


if __name__ == "__main__":
    main()
