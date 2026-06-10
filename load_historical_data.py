#!/usr/bin/env python3
"""
Carregar dados históricos completos desde data inicial
Suporta chunking de datas para respeitar limites da API
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

# Data inicial para carregamento histórico
START_DATE = datetime(2020, 1, 1)  # Modificar conforme necessário
END_DATE = datetime.now()

# Tamanho do chunk de datas (em dias)
CHUNK_DAYS = 30

print("=" * 80)
print("CARREGAR DADOS HISTÓRICOS COMPLETOS")
print("=" * 80)
print(f"\nPeríodo: {START_DATE.date()} a {END_DATE.date()}")
print(f"Tamanho de chunk: {CHUNK_DAYS} dias\n")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def date_range_chunks(start, end, chunk_days):
    """Gerar chunks de datas"""
    current = start
    while current < end:
        chunk_end = min(current + timedelta(days=chunk_days), end)
        yield current, chunk_end
        current = chunk_end

def safe_insert_batch(table_name, data, conflict_key='id'):
    """Inserir batch com tratamento de erro"""
    if not data:
        return 0

    try:
        client.table(table_name).upsert(data, on_conflict=conflict_key).execute()
        return len(data)
    except Exception as e:
        # Se falhar em batch, tentar um por um
        inserted = 0
        for record in data:
            try:
                client.table(table_name).upsert([record], on_conflict=conflict_key).execute()
                inserted += 1
            except:
                pass
        return inserted

# ============================================================================
# 1. AGENDAMENTOS HISTÓRICOS
# ============================================================================

print("[1] CARREGANDO AGENDAMENTOS HISTÓRICOS...\n")

total_appointments = 0

for start_date, end_date in date_range_chunks(START_DATE, END_DATE, CHUNK_DAYS):
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

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

            if appointments:
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

                inserted = safe_insert_batch('appointments', data)
                total_appointments += inserted
                print(f"    {date_from} a {date_to}: {len(appointments)} obtidos, {inserted} inseridos")

    except Exception as e:
        print(f"    {date_from} a {date_to}: [ERROR] {str(e)[:60]}")

print(f"\n[OK] Total de agendamentos: {total_appointments}\n")

# ============================================================================
# 2. PAGAMENTOS HISTÓRICOS
# ============================================================================

print("[2] CARREGANDO PAGAMENTOS HISTÓRICOS...\n")

total_payments = 0

for start_date, end_date in date_range_chunks(START_DATE, END_DATE, CHUNK_DAYS):
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

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

            if payments:
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

                inserted = safe_insert_batch('payments', data)
                total_payments += inserted
                print(f"    {date_from} a {date_to}: {len(payments)} obtidos, {inserted} inseridos")

    except Exception as e:
        print(f"    {date_from} a {date_to}: [ERROR] {str(e)[:60]}")

print(f"\n[OK] Total de pagamentos: {total_payments}\n")

# ============================================================================
# 3. FATURAS HISTÓRICOS
# ============================================================================

print("[3] CARREGANDO FATURAS HISTÓRICOS...\n")

total_invoices = 0

for start_date, end_date in date_range_chunks(START_DATE, END_DATE, CHUNK_DAYS):
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")

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

            if invoices:
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

                inserted = safe_insert_batch('invoices', data)
                total_invoices += inserted
                print(f"    {date_from} a {date_to}: {len(invoices)} obtidos, {inserted} inseridos")

    except Exception as e:
        print(f"    {date_from} a {date_to}: [ERROR] {str(e)[:60]}")

print(f"\n[OK] Total de faturas: {total_invoices}\n")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO DO CARREGAMENTO HISTÓRICO")
print("=" * 80)

try:
    apt = client.table('appointments').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    prof = client.table('professionals').select('id', count='exact').execute().count
    est = client.table('estimates').select('id', count='exact').execute().count
    proc = client.table('procedures').select('id', count='exact').execute().count
    usr = client.table('users').select('id', count='exact').execute().count
    sal = client.table('sales_summary').select('id', count='exact').execute().count
    led = client.table('leads').select('id', count='exact').execute().count
    cli = client.table('clinics').select('id', count='exact').execute().count

    print(f"\n[NESTA EXECUÇÃO]")
    print(f"Agendamentos adicionados: +{total_appointments}")
    print(f"Pagamentos adicionados: +{total_payments}")
    print(f"Faturas adicionadas: +{total_invoices}")
    print(f"{'='*40}")
    print(f"TOTAL ADICIONADO: {total_appointments + total_payments + total_invoices}")

    print(f"\n[ESTADO ATUAL DO BANCO]")
    print(f"Clínicas............: {cli}")
    print(f"Pacientes..........: {pat}")
    print(f"Profissionais......: {prof}")
    print(f"Agendamentos.......: {apt}")
    print(f"Procedures.........: {proc}")
    print(f"Estimates..........: {est}")
    print(f"Faturas............: {inv}")
    print(f"Pagamentos.........: {pay}")
    print(f"Users..............: {usr}")
    print(f"Sales Summary......: {sal}")
    print(f"Leads..............: {led}")
    print(f"{'='*40}")

    total = cli + pat + prof + apt + proc + est + inv + pay + usr + sal + led
    print(f"TOTAL GERAL.......: {total} registros\n")

except Exception as e:
    print(f"Erro ao contar: {str(e)[:80]}")

print("=" * 80)
print("Carregamento histórico concluído!")
print("=" * 80 + "\n")
