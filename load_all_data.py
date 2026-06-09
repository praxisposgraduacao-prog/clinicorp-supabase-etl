#!/usr/bin/env python3
"""
Script para carregar todos os dados da API Clinicorp com mapeamento correto de campos
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
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAMENTO COMPLETO DE DADOS - CLINICORP ETL (VERSAO 2)")
print("=" * 80)

if not SUBSCRIBER_ID:
    print("\n[!] Erro: ERP_CLINICORP_SUBSCRIBER_ID nao configurado no .env\n")
    sys.exit(1)

print(f"\n[OK] Subscriber ID: {SUBSCRIBER_ID}\n")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Datas para consultas (últimos 30 dias para teste)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"[*] Período de consulta: {date_from} a {date_to}\n")

# ============================================================================
# 1. AGENDAMENTOS
# ============================================================================

print("[1] CARREGANDO AGENDAMENTOS...")

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
                # Mapeamento de campos corretos da API
                data.append({
                    'id': a.get('AppointmentId') or a.get('id'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': a.get('Patient_PersonId'),
                    'professional_id': a.get('Dentist_PersonId') or a.get('ScheduleToId'),
                    'scheduled_date': a.get('date'),
                    'duration_minutes': 30,  # API não retorna duração
                    'status': a.get('Status') or 'scheduled',
                    'notes': a.get('Notes'),
                    'reason_cancellation': a.get('ReasonCancellation'),
                    'updated_at': a.get('Date') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            # Upsert com delete fallback
            try:
                client.table('appointments').upsert(data).execute()
                print(f"[OK] Agendamentos carregados/atualizados: {len(data)}")
            except Exception as upsert_err:
                print(f"[INFO] Upsert falhou, tentando delete+insert...")
                try:
                    client.table('appointments').delete().neq('id', 0).execute()
                    client.table('appointments').insert(data).execute()
                    print(f"[OK] Agendamentos inseridos (delete+insert): {len(data)}")
                except Exception as insert_err:
                    print(f"[ERROR] Insert falhou: {str(insert_err)[:100]}")
        else:
            print("[INFO] Nenhum agendamento encontrado")
    else:
        error_msg = response.json().get('Message', response.text) if response.headers.get('content-type') == 'application/json' else response.text
        print(f"[ERROR] Status {response.status_code}: {error_msg[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)[:100]}")

# ============================================================================
# 2. FATURAS
# ============================================================================

print("\n[2] CARREGANDO FATURAS...")

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
                # Mapeamento de campos corretos da API
                data.append({
                    'id': inv.get('InvoiceId'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': inv.get('PatientId'),
                    'number': inv.get('InvoiceId'),
                    'total_amount': inv.get('Amount', 0),
                    'paid_amount': 0,  # API não retorna valor pago separadamente
                    'due_date': inv.get('Date'),
                    'issue_date': inv.get('Date'),
                    'status': inv.get('Status', 'issued'),
                    'payment_method': None,
                    'updated_at': inv.get('Date'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            # Upsert com delete fallback
            try:
                client.table('invoices').upsert(data).execute()
                print(f"[OK] Faturas carregadas/atualizadas: {len(data)}")
            except Exception as upsert_err:
                print(f"[INFO] Upsert falhou, tentando delete+insert...")
                try:
                    client.table('invoices').delete().neq('id', 0).execute()
                    client.table('invoices').insert(data).execute()
                    print(f"[OK] Faturas inseridas (delete+insert): {len(data)}")
                except Exception as insert_err:
                    print(f"[ERROR] Insert falhou: {str(insert_err)[:100]}")
        else:
            print("[INFO] Nenhuma fatura encontrada")
    else:
        error_msg = response.json().get('Message', response.text) if response.headers.get('content-type') == 'application/json' else response.text
        print(f"[ERROR] Status {response.status_code}: {error_msg[:100]}")

except Exception as e:
    print(f"[ERROR] {str(e)[:100]}")

# ============================================================================
# 3. PAGAMENTOS - NOTA: Retorna agregados por mês, não individual
# ============================================================================

print("\n[3] CARREGANDO PAGAMENTOS...")
print("[INFO] Nota: Endpoint retorna dados agregados por mês, não registros individuais")

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
        payments_summary = response.json()
        if isinstance(payments_summary, list) and len(payments_summary) > 0:
            # Este endpoint retorna sumário, não registros individuais
            print(f"[INFO] Endpoint retorna {len(payments_summary)} períodos")
            for summary in payments_summary:
                print(f"       {summary.get('month')}: R$ {summary.get('totalPaymentsAmount', 0)}")
            print("[SKIP] Dados agregados não inseridos no banco (necessário redesenhar schema)")
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
print("CARREGAMENTO CONCLUIDO")
print("=" * 80)

try:
    prof = client.table('professionals').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count

    total = prof + apt + inv

    print(f"\n[RESULTADO FINAL]")
    print(f"Profissionais: {prof}")
    print(f"Agendamentos: {apt}")
    print(f"Faturas: {inv}")
    print(f"\nTOTAL: {total} registros")

    print(f"\n[OBSERVACOES]")
    print(f"- Pacientes: Não carregados (endpoint /patient/list não existe)")
    print(f"- Pagamentos: Endpoint retorna agregados por mês, não registros individuais")
    print(f"             Para inserir pagamentos individuais, é necessário outro endpoint")

except Exception as e:
    print(f"Erro ao contar: {e}")

print("\n" + "=" * 80)
