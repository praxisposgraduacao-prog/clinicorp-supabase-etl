#!/usr/bin/env python3
"""
Aplicar schema estendido no Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import psycopg2
from psycopg2 import sql

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("APLICAR SCHEMA ESTENDIDO")
print("=" * 80)

# Ler arquivo SQL
try:
    with open('schema_extended.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    print("\n[OK] Schema SQL lido\n")
except Exception as e:
    print(f"\n[ERROR] Erro ao ler schema: {str(e)}\n")
    exit(1)

# Conectar ao Supabase via psycopg2 para executar SQL puro
try:
    # Extrair credenciais da URL do Supabase
    # URL format: https://[project-id].supabase.co
    project_id = SUPABASE_URL.replace('https://', '').split('.')[0]

    # Conectar usando psycopg2
    conn = psycopg2.connect(
        host=f"{project_id}.supabase.co",
        database="postgres",
        user="postgres",
        password=SUPABASE_KEY,
        port=5432
    )

    cur = conn.cursor()
    print("[*] Conectado ao Supabase PostgreSQL\n")

    # Dividir SQL em comandos individuais e executar
    commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]

    executed = 0
    for i, command in enumerate(commands, 1):
        if command.strip():
            try:
                cur.execute(command)
                executed += 1
                if i % 10 == 0:
                    print(f"[*] Executados {executed} comandos SQL...")
            except Exception as e:
                # Ignorar erros de tabelas já existentes
                if "already exists" in str(e) or "already created" in str(e).lower():
                    executed += 1
                    if i % 10 == 0:
                        print(f"[*] Executados {executed} comandos SQL (alguns já existem)...")
                else:
                    print(f"    [WARN] Erro no comando {i}: {str(e)[:80]}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n[OK] Schema estendido aplicado com sucesso!")
    print(f"    Total de comandos: {executed}\n")

except Exception as e:
    print(f"\n[ERROR] Erro ao aplicar schema: {str(e)}\n")
    exit(1)

print("=" * 80)
print("Schema estendido está pronto para uso!")
print("=" * 80 + "\n")
