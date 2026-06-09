#!/usr/bin/env python3
"""
Sincronização Incremental - Carrega apenas dados novos/modificados
Executa apenas deltas desde a última sincronização
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

# Arquivo para rastrear última sincronização
SYNC_STATE_FILE = "sync_state.json"

print("=" * 80)
print("SINCRONIZACAO INCREMENTAL - CLINICORP")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# CARREGAR ESTADO ANTERIOR
# ============================================================================

print("\n[1] CARREGANDO ESTADO ANTERIOR...")

sync_state = {
    'last_sync': (datetime.now() - timedelta(days=1)).isoformat(),
    'appointments_count': 0,
    'payments_count': 0,
    'invoices_count': 0,
}

if os.path.exists(SYNC_STATE_FILE):
    try:
        with open(SYNC_STATE_FILE, 'r') as f:
            sync_state = json.load(f)
        print(f"    Última sincronização: {sync_state['last_sync']}\n")
    except:
        print(f"    Arquivo corrompido, usando padrão\n")
else:
    print(f"    Primeira sincronização (padrão: últimas 24 horas)\n")

# Converter para datetime
try:
    last_sync_dt = datetime.fromisoformat(sync_state['last_sync'])
except:
    last_sync_dt = datetime.now() - timedelta(days=1)

# Data para consulta
date_from = last_sync_dt.strftime("%Y-%m-%d")
date_to = datetime.now().strftime("%Y-%m-%d")

print(f"[2] PERIODO DE SINCRONIZACAO: {date_from} a {date_to}\n")

# ============================================================================
# SINCRONIZAR AGENDAMENTOS
# ============================================================================

print("[3] SINCRONIZANDO AGENDAMENTOS...")

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
        print(f"    API retornou: {len(appointments)} agendamentos\n")

        if len(appointments) > 0:
            # Preparar dados
            data = []
            for apt in appointments:
                data.append({
                    'id': apt.get('id'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': apt.get('Patient_PersonId'),
                    'professional_id': apt.get('Dentist_PersonId') or apt.get('ScheduleToId'),
                    'scheduled_date': apt.get('date'),
                    'duration_minutes': 30,
                    'status': apt.get('Status') or 'scheduled',
                    'notes': apt.get('Notes'),
                    'reason_cancellation': None,
                    'updated_at': apt.get('Date'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            # Upsert
            try:
                client.table('appointments').upsert(data, on_conflict='id').execute()
                sync_state['appointments_count'] += len(data)
                print(f"    [OK] {len(data)} agendamentos sincronizados")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:80]}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# SINCRONIZAR PAGAMENTOS
# ============================================================================

print("\n[4] SINCRONIZANDO PAGAMENTOS...")

try:
    response = requests.get(
        f"{API_URL}/payment/list",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        payments = response.json()
        print(f"    API retornou: {len(payments)} pagamentos\n")

        if len(payments) > 0:
            # Preparar dados
            data = []
            for pay in payments:
                data.append({
                    'id': pay.get('PaymentHeaderId'),
                    'clinic_id': pay.get('ReceiverBusinessId', BUSINESS_ID),
                    'invoice_id': None,
                    'patient_id': pay.get('PatientId'),
                    'amount': float(pay.get('Amount', 0)),
                    'payment_method': pay.get('CreditCardType') or 'unknown',
                    'payment_date': pay.get('PaymentDate'),
                    'reference': pay.get('ExternalId') or '',
                    'status': 'completed' if pay.get('PaymentReceived') == 'X' else 'pending',
                    'notes': pay.get('PayerName') or '',
                    'updated_at': pay.get('ConfirmedDate') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            # Upsert
            try:
                client.table('payments').upsert(data, on_conflict='id').execute()
                sync_state['payments_count'] += len(data)
                print(f"    [OK] {len(data)} pagamentos sincronizados")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:80]}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# SINCRONIZAR FATURAS
# ============================================================================

print("\n[5] SINCRONIZANDO FATURAS...")

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
        print(f"    API retornou: {len(invoices)} faturas\n")

        if len(invoices) > 0:
            # Preparar dados
            data = []
            for inv in invoices:
                data.append({
                    'id': inv.get('InvoiceId'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': inv.get('PatientId'),
                    'number': inv.get('InvoiceId'),
                    'total_amount': float(inv.get('Amount', 0)),
                    'paid_amount': 0,
                    'due_date': inv.get('Date'),
                    'issue_date': inv.get('Date'),
                    'status': inv.get('Status', 'issued'),
                    'payment_method': None,
                    'updated_at': inv.get('Date'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            # Upsert
            try:
                client.table('invoices').upsert(data, on_conflict='id').execute()
                sync_state['invoices_count'] += len(data)
                print(f"    [OK] {len(data)} faturas sincronizadas")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:80]}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# SALVAR ESTADO
# ============================================================================

print("\n[6] SALVANDO ESTADO...")

sync_state['last_sync'] = datetime.now().isoformat()

with open(SYNC_STATE_FILE, 'w') as f:
    json.dump(sync_state, f, indent=2)

print(f"    [OK] Estado salvo\n")

# ============================================================================
# RESULTADO
# ============================================================================

print("=" * 80)
print("RESULTADO DA SINCRONIZACAO")
print("=" * 80)

try:
    apt = client.table('appointments').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count

    print(f"\n[DADOS SINCRONIZADOS NESTA EXECUCAO]")
    print(f"Agendamentos: +{sync_state['appointments_count']}")
    print(f"Pagamentos: +{sync_state['payments_count']}")
    print(f"Faturas: +{sync_state['invoices_count']}")

    total_sync = (sync_state['appointments_count'] +
                  sync_state['payments_count'] +
                  sync_state['invoices_count'])

    print(f"\n[TOTAL ADICIONADO]: {total_sync} registros\n")

    print(f"[ESTADO ATUAL DO BANCO]")
    print(f"Agendamentos: {apt}")
    print(f"Pagamentos: {pay}")
    print(f"Faturas: {inv}")

    print(f"\n[PROXIMA SINCRONIZACAO]")
    print(f"Última sincronização: {sync_state['last_sync']}")
    print(f"Período próximo: {sync_state['last_sync']} a [data próxima sincronização]")

except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
print("Sincronização incremental concluída com sucesso!")
print("=" * 80 + "\n")
