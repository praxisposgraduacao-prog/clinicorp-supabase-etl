import os
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Set

# Table/column names are caller-controlled — only call from internal ETL scripts, not user input.
def _conn():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return psycopg2.connect(url)

def upsert(table: str, data: List[Dict[str, Any]], conflict_col: str = "id") -> int:
    if not data:
        return 0
    cols = list(data[0].keys())
    update_cols = [c for c in cols if c != conflict_col]
    update_set = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
    sql = (
        f"INSERT INTO {table} ({','.join(cols)}) VALUES %s "
        f"ON CONFLICT ({conflict_col}) DO UPDATE SET {update_set}"
    )
    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                values = [[row.get(c) for c in cols] for row in data]
                psycopg2.extras.execute_values(cur, sql, values)
                return cur.rowcount
    finally:
        conn.close()

def count(table: str) -> int:
    conn = _conn()
    conn.autocommit = True  # read-only, no transaction needed
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            return cur.fetchone()[0]
    finally:
        conn.close()

def select_ids(table: str) -> Set[int]:
    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT id FROM {table}")
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()

def select_col(table: str, col: str) -> Set:
    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL")
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()
