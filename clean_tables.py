#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

tables_to_clean = ['professionals', 'procedures', 'sync_log']

print("Limpando tabelas...\n")

for table in tables_to_clean:
    print(f"[*] Limpando {table}...", end=" ")
    try:
        result = client.table(table).delete().neq('id', 'NULL').execute()
        print(f"OK ({len(result.data) if result.data else 0} registros deletados)")
    except Exception as e:
        # Tenta com gt em vez de neq
        try:
            result = client.table(table).delete().gt('id', 0).execute()
            print(f"OK ({len(result.data) if result.data else 0} registros deletados)")
        except:
            print(f"Erro: {str(e)[:80]}")

print("\nTabelas limpas!")
