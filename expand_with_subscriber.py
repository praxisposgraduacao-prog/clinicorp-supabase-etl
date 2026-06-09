#!/usr/bin/env python3
"""
Script para expandir carregamento com subscriber_id
Agora usa parâmetros corretos da API documentation
"""

import os
import sys
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("EXPANSAO DO CARREGAMENTO - CLINICORP ETL")
print("=" * 80)

if not SUBSCRIBER_ID:
    print("\n[!] Erro: ERP_CLINICORP_SUBSCRIBER_ID nao configurado no .env")
    print("\nPara expandir o carregamento:")
    print("1. Encontre seu subscriber_id no Clinicorp")
    print("2. Adicione ao .env: ERP_CLINICORP_SUBSCRIBER_ID=seu_valor")
    print("3. Execute este script novamente\n")
    sys.exit(1)

print(f"\n[OK] Subscriber ID encontrado: {SUBSCRIBER_ID}\n")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Datas para consultas (últimos 365 dias)
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"[*] Período de consulta: {date_from} a {date_to}\n")

# ============================================================================
# 1. PACIENTES - Nota: Não há endpoint /patient/list, usar /patient/get com IDs
# ============================================================================

print("[1] CARREGANDO PACIENTES...")

try:
    # Primeiro, precisamos obter lista de pacientes de outra forma
    # Tentando endpoint alternativo se existir, ou obtendo via appointments
    print("[INFO] Endpoint /patient/list não existe na API")
    print("[INFO] Pacientes podem ser obtidos via /patient/get (requer ID específico)")
    print("[INFO] Ou através da lista de agendamentos/faturas")
    print("[SKIP] Pulando carregamento direto de pacientes por enquanto\n")

except Exception as e:
    print(f"[ERROR] {str(e)[:100]}\n")

# ============================================================================
# 2. AGENDAMENTOS
# ============================================================================

print("[2] CARREGANDO AGENDAMENTOS...")

try:
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
        if isinstance(appointments, list) and len(appointments) > 0:
            data = []
            for a in appointments:
                data.append({
                    'id': a.get('id'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': a.get('patient_id'),
                    'professional_id': a.get('professional_id'),
                    'scheduled_date': a.get('scheduled_date'),
                    'duration_minutes': a.get('duration_minutes'),
                    'status': a.get('status'),
                    'notes': a.get('notes'),
                    'reason_cancellation': a.get('reason_cancellation'),
                    'updated_at': a.get('updated_at'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            client.table('appointments').insert(data).execute()
            print(f"[OK] Agendamentos carregados: {len(data)}")
        else:
            print("[INFO] Nenhum agendamento encontrado")
    else:
        error_msg = response.json().get('Message', response.text) if response.headers.get('content-type') == 'application/json' else response.text
        print(f"[ERROR] Status {response.status_code}: {error_msg[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)[:100]}")

# ============================================================================
# 3. FATURAS
# ============================================================================

print("\n[3] CARREGANDO FATURAS...")

try:
    response = requests.get(
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

    if response.status_code == 200:
        invoices = response.json()
        if isinstance(invoices, list) and len(invoices) > 0:
            data = []
            for inv in invoices:
                data.append({
                    'id': inv.get('id'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': inv.get('patient_id'),
                    'number': inv.get('number'),
                    'total_amount': inv.get('total_amount'),
                    'paid_amount': inv.get('paid_amount', 0),
                    'due_date': inv.get('due_date'),
                    'issue_date': inv.get('issue_date'),
                    'status': inv.get('status'),
                    'payment_method': inv.get('payment_method'),
                    'updated_at': inv.get('updated_at'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            client.table('invoices').insert(data).execute()
            print(f"[OK] Faturas carregadas: {len(data)}")
        else:
            print("[INFO] Nenhuma fatura encontrada")
    else:
        error_msg = response.json().get('Message', response.text) if response.headers.get('content-type') == 'application/json' else response.text
        print(f"[ERROR] Status {response.status_code}: {error_msg[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)[:100]}")

# ============================================================================
# 4. PAGAMENTOS
# ============================================================================

print("\n[4] CARREGANDO PAGAMENTOS...")

try:
    response = requests.get(
        f"{API_URL}/financial/list_payments",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        payments = response.json()
        if isinstance(payments, list) and len(payments) > 0:
            data = []
            for pay in payments:
                data.append({
                    'id': pay.get('id'),
                    'clinic_id': BUSINESS_ID,
                    'invoice_id': pay.get('invoice_id'),
                    'patient_id': pay.get('patient_id'),
                    'amount': pay.get('amount'),
                    'payment_method': pay.get('payment_method'),
                    'payment_date': pay.get('payment_date'),
                    'reference': pay.get('reference'),
                    'status': pay.get('status', 'completed'),
                    'notes': pay.get('notes'),
                    'updated_at': pay.get('updated_at'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            client.table('payments').insert(data).execute()
            print(f"[OK] Pagamentos carregados: {len(data)}")
        else:
            print("[INFO] Nenhum pagamento encontrado")
    else:
        error_msg = response.json().get('Message', response.text) if response.headers.get('content-type') == 'application/json' else response.text
        print(f"[ERROR] Status {response.status_code}: {error_msg[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)[:100]}")

# ============================================================================
# RESUMO
# ============================================================================

print("\n" + "=" * 80)
print("CARREGAMENTO EXPANDIDO CONCLUIDO")
print("=" * 80)

try:
    prof = client.table('professionals').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count

    total = prof + pat + apt + inv + pay

    print(f"\n[RESULTADO FINAL]")
    print(f"Profissionais: {prof}")
    print(f"Pacientes: {pat}")
    print(f"Agendamentos: {apt}")
    print(f"Faturas: {inv}")
    print(f"Pagamentos: {pay}")
    print(f"\nTOTAL: {total} registros")

except Exception as e:
    print(f"Erro ao contar: {e}")

print("\n" + "=" * 80)
