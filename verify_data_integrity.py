#!/usr/bin/env python3
"""
Verificação de integridade de dados - identifica registros com problemas
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("VERIFICAÇÃO DE INTEGRIDADE DE DADOS")
print("=" * 80)

# 1. Appointments com referências nulas
print("\n[1] APPOINTMENTS com foreign keys nulas:\n")

try:
    # Patient ID nulo
    result = client.table('appointments').select('count', count='exact').is_('patient_id', 'null').execute()
    print(f"  Sem patient_id: {result.count}")

    # Professional ID nulo
    result = client.table('appointments').select('count', count='exact').is_('professional_id', 'null').execute()
    print(f"  Sem professional_id: {result.count}")

except Exception as e:
    print(f"  ERROR: {str(e)}")

# 2. Payments com referências nulas
print("\n[2] PAYMENTS com foreign keys nulas:\n")

try:
    result = client.table('payments').select('count', count='exact').is_('patient_id', 'null').execute()
    print(f"  Sem patient_id: {result.count}")

except Exception as e:
    print(f"  ERROR: {str(e)}")

# 3. Invoices com referências nulas
print("\n[3] INVOICES com foreign keys nulas:\n")

try:
    result = client.table('invoices').select('count', count='exact').is_('patient_id', 'null').execute()
    print(f"  Sem patient_id: {result.count}")

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
        result = client.table(table).select('count', count='exact').execute()
        count = result.count if result.count else 0
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
            result = client.table(table).select('count', count='exact').execute()
            count = result.count if result.count else 0
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
