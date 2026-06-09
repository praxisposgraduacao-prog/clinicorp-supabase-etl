#!/usr/bin/env python3
"""
Remover constraint NOT NULL via API REST do Supabase
"""

import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("REMOVER CONSTRAINT NOT NULL - VIA SQL REST")
print("=" * 80)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] Faltam credenciais do Supabase no .env")
    exit(1)

# Extrair project ID e host
# URL é tipo: https://duydqaxviyyzqawqhmgy.supabase.co
supabase_host = SUPABASE_URL.replace("https://", "").replace("http://", "")
project_id = supabase_host.split(".")[0]

print(f"\nSUPABASE_HOST: {supabase_host}")
print(f"PROJECT_ID: {project_id}\n")

# SQL que queremos executar
sql_commands = [
    "ALTER TABLE payments ALTER COLUMN clinic_id DROP NOT NULL;",
    "ALTER TABLE payments ALTER COLUMN invoice_id DROP NOT NULL;",
    "ALTER TABLE payments ALTER COLUMN payment_method DROP NOT NULL;"
]

print("[1] TENTANDO EXECUTAR SQL VIA API REST\n")

for i, sql in enumerate(sql_commands, 1):
    print(f"    [{i}] {sql[:60]}...")

    # Tentar via POST para /rest/v1/rpc/exec_sql
    try:
        # Formato 1: RPC call
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            },
            json={"sql": sql},
            timeout=10
        )

        print(f"        Status: {response.status_code}")

        if response.status_code in [200, 201]:
            print(f"        [OK] Executado!")
        else:
            print(f"        Response: {response.text[:100]}")

    except Exception as e:
        print(f"        Error: {str(e)[:80]}")

print("\n" + "=" * 80)
print("MANUAL FIX - EXECUTE NO SUPABASE SQL EDITOR")
print("=" * 80)

print("""
Se a execução via API não funcionou, execute manualmente no Supabase:

1. Abra: https://app.supabase.com/project/{project_id}/sql/new
2. Cole os comandos abaixo:
""".format(project_id=project_id))

print("""
-- Remove NOT NULL constraints para permitir nulls
ALTER TABLE payments ALTER COLUMN clinic_id DROP NOT NULL;
ALTER TABLE payments ALTER COLUMN invoice_id DROP NOT NULL;
ALTER TABLE payments ALTER COLUMN payment_method DROP NOT NULL;

-- Verifique se funcionou
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_name = 'payments'
AND column_name IN ('clinic_id', 'invoice_id', 'payment_method');

3. Depois execute: python apply_fix_and_reload.py
""")

print("=" * 80)
