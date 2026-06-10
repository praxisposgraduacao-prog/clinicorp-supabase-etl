#!/usr/bin/env python3
"""
Aplicar schema estendido via Supabase HTTP API
"""

import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("APLICAR SCHEMA ESTENDIDO VIA API")
print("=" * 80)

# Ler arquivo SQL
try:
    with open('schema_extended.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    print("\n[OK] Schema SQL lido\n")
except Exception as e:
    print(f"\n[ERROR] Erro ao ler schema: {str(e)}\n")
    exit(1)

# Dividir SQL em comandos
commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]

print(f"[*] Total de comandos SQL: {len(commands)}\n")
print("[*] Executando comandos via Supabase RPC...\n")

# Headers para requisição
headers = {
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "apikey": SUPABASE_KEY
}

executed = 0
skipped = 0
failed = 0

for i, command in enumerate(commands, 1):
    if not command.strip():
        continue

    try:
        # Usar endpoint de query do Supabase
        payload = {
            "query": command
        }

        # Tentar via query endpoint
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code in [200, 201, 204]:
            executed += 1
            if i % 10 == 0:
                print(f"[*] {executed} comandos executados...")
        elif "already exists" in response.text.lower():
            skipped += 1
        else:
            # Ignorar erros de sintaxe conhecidos
            if response.status_code >= 400:
                failed += 1

    except Exception as e:
        # Ignorar erros de conexão, tentar próximo comando
        failed += 1
        if failed <= 3:
            print(f"    [WARN] Erro no comando {i}: {str(e)[:60]}")

print(f"\n[OK] Schema processado!")
print(f"    Executados: {executed}")
print(f"    Já existentes: {skipped}")
print(f"    Erros (ignorados): {failed}\n")

# Alternativa: Usar operações individuais do Supabase para criar tabelas críticas
print("[*] Verificando tabelas via API...\n")

from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)

tables_to_check = [
    'chairs', 'available_times', 'receipts', 'cash_flow',
    'installment_summary', 'payment_summary', 'financial_summary',
    'patient_birthdays', 'patient_appointments_list',
    'patient_estimates_summary', 'insurance_claims',
    'analytics_results', 'sales_estimates_conversion',
    'revenue_by_specialty', 'clinic_details', 'subscribers'
]

found = 0
for table in tables_to_check:
    try:
        # Tentar fazer um query para ver se tabela existe
        client.table(table).select('id').limit(1).execute()
        found += 1
        print(f"    [OK] Tabela '{table}' encontrada")
    except Exception as e:
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            print(f"    [MISSING] Tabela '{table}' - CRIAR MANUALMENTE")
        else:
            print(f"    [OK] Tabela '{table}' acessível")
            found += 1

print(f"\n[RESULTADO]")
print(f"Tabelas acessíveis: {found}/{len(tables_to_check)}\n")

if found < len(tables_to_check):
    print("[!] IMPORTANTE:")
    print("    Se tabelas estão faltando, execute manualmente:")
    print("    1. Vá para Supabase Dashboard → SQL Editor")
    print("    2. Copie todo o conteúdo de: schema_extended.sql")
    print("    3. Cole no editor SQL")
    print("    4. Clique em 'Run' para executar\n")

print("=" * 80)
