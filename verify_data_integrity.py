#!/usr/bin/env python3
"""
Verificação de integridade de dados - identifica registros com problemas
"""

import os
import psycopg2
from dotenv import load_dotenv
import db_client

load_dotenv()

def _conn():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return psycopg2.connect(url)

def count_where_null(table, col):
    """Count rows where col IS NULL."""
    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
            return cur.fetchone()[0]
    finally:
        conn.close()

print("=" * 80)
print("VERIFICAÇÃO DE INTEGRIDADE DE DADOS")
print("=" * 80)

# 1. Appointments com referências nulas
print("\n[1] APPOINTMENTS com foreign keys nulas:\n")

try:
    print(f"  Sem patient_id: {count_where_null('appointments', 'patient_id')}")
    print(f"  Sem professional_id: {count_where_null('appointments', 'professional_id')}")
except Exception as e:
    print(f"  ERROR: {str(e)}")

# 2. Payments com referências nulas
print("\n[2] PAYMENTS com foreign keys nulas:\n")

try:
    print(f"  Sem patient_id: {count_where_null('payments', 'patient_id')}")
except Exception as e:
    print(f"  ERROR: {str(e)}")

# 3. Invoices com referências nulas
print("\n[3] INVOICES com foreign keys nulas:\n")

try:
    print(f"  Sem patient_id: {count_where_null('invoices', 'patient_id')}")
except Exception as e:
    print(f"  ERROR: {str(e)}")

# 4. Status das tabelas estendidas
print("\n[4] TABELAS ESTENDIDAS - STATUS DE CARREGAMENTO:\n")

extended_tables = [
    'chairs',
    'available_times',
    'receipts',
    'cash_flow',
    'installment_summary',
    'payment_summary',
    'financial_summary',
    'patient_birthdays',
    'patient_appointments_list',
    'patient_estimates_summary',
    'insurance_claims',
    'analytics_results',
    'sales_estimates_conversion',
    'revenue_by_specialty',
    'clinic_details',
    'subscribers'
]

for table in extended_tables:
    try:
        count = db_client.count(table)
        status = "OK" if count > 0 else "VAZIO"
        print(f"  {table:30s}: {count:5d} registros [{status}]")
    except Exception as e:
        print(f"  {table:30s}: ERROR - {str(e)[:50]}")

# 5. Relatório geral
print("\n[5] RELATÓRIO GERAL DE CARREGAMENTO:\n")

try:
    tables = [
        'clinics', 'patients', 'professionals', 'appointments', 'procedures',
        'estimates', 'invoices', 'payments', 'users', 'sales_summary', 'leads',
        'sync_log'
    ]

    total = 0
    for table in tables:
        try:
            count = db_client.count(table)
            total += count
            print(f"  {table:20s}: {count:8d}")
        except:
            pass

    print(f"\n  {'TOTAL':20s}: {total:8d}")

except Exception as e:
    print(f"  ERROR: {str(e)}")

print("\n" + "=" * 80)
print("VERIFICAÇÃO CONCLUÍDA")
print("=" * 80)
