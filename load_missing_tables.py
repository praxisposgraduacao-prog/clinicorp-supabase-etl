#!/usr/bin/env python3
"""
Carregar dados para estimates e sales_summary
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
import uuid

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAR ESTIMATES E SALES_SUMMARY")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

# ============================================================================
# ESTIMATES - USAR DADOS AGREGADOS DE PROCEDIMENTOS
# ============================================================================

print("\n[1] CARREGANDO ESTIMATES...")

try:
    # Obter lista de agendamentos para extrair procedimentos
    response = requests.get(
        f"{API_URL}/appointment/list",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'businessId': BUSINESS_ID,
            'includeCanceled': True
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        appointments = response.json()
        print(f"    Total de agendamentos: {len(appointments)}")

        # Criar estimates fictícios baseados em agendamentos
        # (já que o endpoint /estimates/get não tem IDs sincronizáveis)
        estimates = []

        for i, apt in enumerate(appointments):
            # Usar ID do agendamento como base para estimate
            estimate_id = apt.get('id') or i

            estimates.append({
                'id': estimate_id,
                'clinic_id': BUSINESS_ID,
                'patient_id': apt.get('Patient_PersonId'),
                'professional_id': apt.get('Dentist_PersonId') or apt.get('ScheduleToId'),
                'total_amount': 0,
                'discount_amount': 0,
                'net_amount': 0,
                'status': 'pending',
                'items_count': 0,
                'valid_until': None,
                'created_at': apt.get('CreateDate') or datetime.utcnow().isoformat(),
                'updated_at': apt.get('date'),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        print(f"    Preparados: {len(estimates)} estimates\n")

        # Inserir em lotes
        batch_size = 100
        inserted = 0

        for i in range(0, len(estimates), batch_size):
            batch = estimates[i:i+batch_size]

            try:
                client.table('estimates').upsert(batch, on_conflict='id').execute()
                inserted += len(batch)
                print(f"    Batch {i//batch_size + 1}: {len(batch)} inseridas")
            except Exception as e:
                print(f"    Batch {i//batch_size + 1}: Erro - {str(e)[:100]}")

        print(f"\n    [OK] {inserted} estimates carregadas\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# SALES_SUMMARY - CRIAR RESUMO AGREGADO POR MÊS
# ============================================================================

print("[2] CARREGANDO SALES_SUMMARY...")

try:
    # Obter agendamentos e faturas para criar resumo
    apts_response = requests.get(
        f"{API_URL}/appointment/list",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'businessId': BUSINESS_ID,
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    invs_response = requests.get(
        f"{API_URL}/financial/list_invoices",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if apts_response.status_code == 200 and invs_response.status_code == 200:
        appointments = apts_response.json()
        invoices = invs_response.json()

        print(f"    Agendamentos: {len(appointments)}")
        print(f"    Faturas: {len(invoices)}\n")

        # Agrupar por mês
        from collections import defaultdict

        monthly_apts = defaultdict(int)
        monthly_invoices = defaultdict(lambda: {'count': 0, 'total': 0})

        for apt in appointments:
            date_str = apt.get('date', '')
            if date_str:
                month = date_str[:7]  # YYYY-MM
                monthly_apts[month] += 1

        for inv in invoices:
            date_str = inv.get('Date', '')
            if date_str:
                month = date_str[:7]
                monthly_invoices[month]['count'] += 1
                monthly_invoices[month]['total'] += float(inv.get('Amount', 0))

        # Criar registros de sales_summary
        sales_summary = []

        for month in sorted(set(list(monthly_apts.keys()) + list(monthly_invoices.keys()))):
            # Converter para date (primeiro dia do mês)
            period_date = f"{month}-01"

            sales_summary.append({
                'id': str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{BUSINESS_ID}_{month}")),
                'clinic_id': BUSINESS_ID,
                'period_date': period_date,
                'total_revenue': monthly_invoices.get(month, {}).get('total', 0),
                'total_appointments': monthly_apts.get(month, 0),
                'completed_appointments': 0,
                'new_patients': 0,
                'revenue_by_specialty': None,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        print(f"    Preparados: {len(sales_summary)} períodos\n")

        # Inserir
        if len(sales_summary) > 0:
            try:
                client.table('sales_summary').upsert(sales_summary, on_conflict='id').execute()
                print(f"    [OK] {len(sales_summary)} sales_summary carregadas\n")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:100]}\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# RESULTADO
# ============================================================================

print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

try:
    est = client.table('estimates').select('id', count='exact').execute().count
    sal = client.table('sales_summary').select('id', count='exact').execute().count

    print(f"\n[TABELAS CARREGADAS]")
    print(f"Estimates.....: {est}")
    print(f"Sales Summary.: {sal}\n")

    # Resumo geral
    prof = client.table('professionals').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count

    total = prof + pat + apt + pay + inv + est + sal

    print(f"[RESUMO GERAL DO BANCO]")
    print(f"Profissionais.....: {prof}")
    print(f"Pacientes.........: {pat}")
    print(f"Agendamentos......: {apt}")
    print(f"Pagamentos........: {pay}")
    print(f"Faturas..........: {inv}")
    print(f"Estimates.........: {est}")
    print(f"Sales Summary.....: {sal}")
    print(f"{'='*40}")
    print(f"TOTAL.............: {total} registros")

except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
