#!/usr/bin/env python3
"""
Resumo final de todas as 12 tabelas carregadas
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "=" * 80)
print("RESUMO FINAL - TODAS AS 12 TABELAS CARREGADAS")
print("=" * 80 + "\n")

tables = {
    'sync_log': '[SYNC] Sync Log',
    'clinics': '[CLI] Clinicas',
    'patients': '[PAT] Pacientes',
    'professionals': '[PRO] Profissionais',
    'appointments': '[APT] Agendamentos',
    'procedures': '[PRC] Procedimentos',
    'estimates': '[EST] Orcamentos',
    'invoices': '[INV] Faturas',
    'payments': '[PAY] Pagamentos',
    'users': '[USR] Usuarios',
    'sales_summary': '[SAL] Resumo de Vendas',
    'leads': '[LED] Leads',
}

counts = {}
total = 0

for table_name, display_name in tables.items():
    try:
        result = client.table(table_name).select('id', count='exact').execute()
        count = result.count
        counts[table_name] = count
        total += count
        status = "[OK]" if count > 0 else "[--]"
        print(f"{status} {display_name:.<30} {count:>6} registros")
    except Exception as e:
        print(f"[ERROR] {display_name:.<30} ERRO")

print("\n" + "=" * 80)
print(f"TOTAL GERAL...................... {total:>6} registros")
print("=" * 80 + "\n")

# Estatísticas adicionais
print("ESTATÍSTICAS DETALHADAS:\n")

try:
    # Agendamentos por status
    apt_statuses = client.table('appointments').select('status').execute()
    apt_data = apt_statuses.data
    status_counts = {}
    for apt in apt_data:
        status = apt['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    print("Agendamentos por status:")
    for status, count in sorted(status_counts.items()):
        print(f"  - {status}: {count}")
    print()
except:
    pass

try:
    # Pagamentos por método
    pay_methods = client.table('payments').select('payment_method').execute()
    pay_data = pay_methods.data
    method_counts = {}
    for pay in pay_data:
        method = pay['payment_method']
        method_counts[method] = method_counts.get(method, 0) + 1

    print("Pagamentos por método:")
    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  - {method}: {count}")
    print()
except:
    pass

try:
    # Faturas por status
    inv_statuses = client.table('invoices').select('status').execute()
    inv_data = inv_statuses.data
    inv_status_counts = {}
    for inv in inv_data:
        status = inv['status']
        inv_status_counts[status] = inv_status_counts.get(status, 0) + 1

    print("Faturas por status:")
    for status, count in sorted(inv_status_counts.items()):
        print(f"  - {status}: {count}")
    print()
except:
    pass

print("=" * 80)
print(f"Data de conclusão: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80 + "\n")
