import asyncpg
import json
import os

SYNC_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "sync_state.json")

# TABLES is a closed hardcoded list — never accept external input for table names.
TABLES = ["appointments", "payments", "invoices", "patients", "professionals"]

async def get_status() -> dict:
    database_url = os.getenv("DATABASE_URL", "")
    async with await asyncpg.connect(database_url) as conn:
        counts = {}
        for table in TABLES:
            row = await conn.fetchrow(f"SELECT COUNT(*) FROM {table}")
            counts[table] = row[0]

    try:
        with open(SYNC_STATE_FILE) as f:
            state = json.load(f)
        counts["last_sync"] = state.get("last_sync", "N/A")
    except (FileNotFoundError, json.JSONDecodeError):
        counts["last_sync"] = "N/A"

    return counts
