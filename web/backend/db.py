import asyncio
import json
import os
import psycopg2

SYNC_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "sync_state.json")

# TABLES is a closed hardcoded list — never accept external input for table names.
TABLES = ["appointments", "payments", "invoices", "patients", "professionals"]

def _get_counts() -> dict:
    database_url = os.getenv("DATABASE_URL", "")
    conn = psycopg2.connect(database_url)
    try:
        counts = {}
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
    finally:
        conn.close()
    return counts

async def get_status() -> dict:
    counts = await asyncio.to_thread(_get_counts)

    try:
        with open(SYNC_STATE_FILE) as f:
            state = json.load(f)
        counts["last_sync"] = state.get("last_sync", "N/A")
    except (FileNotFoundError, json.JSONDecodeError):
        counts["last_sync"] = "N/A"

    return counts
