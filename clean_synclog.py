#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Limpando tabela sync_log...")
try:
    result = client.table('sync_log').delete().neq('id', '').execute()
    print(f"Sucesso! Registros deletados: {len(result.data) if result.data else 0}")
except Exception as e:
    print(f"Erro: {e}")
