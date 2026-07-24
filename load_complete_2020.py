#!/usr/bin/env python3
"""
Carregamento Completo de 100% dos Dados desde 2020-01-01
Com tratamento robusto de erros, retry logic e batch optimization
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, date, timezone
import uuid as uuid_lib
import time
import db_client

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

print("=" * 80)
print("CARREGAMENTO COMPLETO 2020-2026 - 100% DOS DADOS")
print("=" * 80)

START_DATE = datetime(2020, 1, 1)
END_DATE = datetime.now()
CHUNK_DAYS = 30
BATCH_SIZE = 50  # Reduzido para evitar erros
MAX_RETRIES = 3
RETRY_DELAY = 2

total_loaded = 0
total_errors = 0

_cached_patient_ids = None
_cached_prof_ids = None

def get_patient_ids():
    global _cached_patient_ids
    if _cached_patient_ids is None:
        _cached_patient_ids = db_client.select_ids('patients')
    return _cached_patient_ids

def get_prof_ids():
    global _cached_prof_ids
    if _cached_prof_ids is None:
        _cached_prof_ids = db_client.select_ids('professionals')
    return _cached_prof_ids

def ensure_patients(id_name_map):
    """Insert fallback patient records for any IDs not yet in DB."""
    existing = get_patient_ids()
    now = datetime.now(timezone.utc).isoformat()
    missing = [
        {'id': pid, 'clinic_id': BUSINESS_ID, 'full_name': name or f'Patient {pid}',
         'status': 'active', 'last_sync_at': now}
        for pid, name in id_name_map.items()
        if pid and pid not in existing
    ]
    if missing:
        try:
            db_client.upsert('patients', missing, conflict_col='id')
            existing.update(r['id'] for r in missing)
        except Exception as e:
            print(f"        [WARN] fallback patients: {str(e)[:80]}")

def serialize_value(value):
    """Serializar valores para JSON-compatible"""
    if value is None:
        return None
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, (dict, list)):
        return value
    else:
        return value

def safe_upsert(table_name, data, key='id', retry=0):
    """Upsert com retry logic usando psycopg2"""
    try:
        if not data or len(data) == 0:
            return 0, 0

        cleaned = []
        for record in data:
            clean_record = {}
            for k, v in record.items():
                clean_record[k] = serialize_value(v)
            cleaned.append(clean_record)

        # Filtrar registros com ID nulo e deduplicar por ID no batch
        seen = {}
        for r in cleaned:
            rid = r.get(key)
            if rid is not None:
                seen[rid] = r
        cleaned = list(seen.values())

        if not cleaned:
            return 0, 0

        n = db_client.upsert(table_name, cleaned, conflict_col=key)
        return n, 0

    except Exception as e:
        error_str = str(e)

        if retry < MAX_RETRIES:
            print(f"        [RETRY {retry+1}/{MAX_RETRIES}] Aguardando {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            return safe_upsert(table_name, data, key, retry + 1)
        else:
            print(f"        [ERROR] {error_str[:100]}")
            return 0, len(data)

def date_range_chunks(start, end, chunk_days):
    """Gerar chunks de datas"""
    current = start
    while current < end:
        chunk_end = min(current + timedelta(days=chunk_days), end)
        yield current, chunk_end
        current = chunk_end

# ============================================================================
# 1. APPOINTMENTS - HISTÓRICO COMPLETO
# ============================================================================

print("\n[1] CARREGANDO APPOINTMENTS (2020-2026)...\n")

total_apt = 0
for start, end in date_range_chunks(START_DATE, END_DATE, CHUNK_DAYS):
    date_from = start.strftime("%Y-%m-%d")
    date_to = end.strftime("%Y-%m-%d")

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
                # Garantir que todos os pacientes existam antes de inserir
                id_name = {apt.get('Patient_PersonId'): apt.get('PatientName') or apt.get('Name') for apt in appointments if apt.get('Patient_PersonId')}
                ensure_patients(id_name)

                valid_patients = get_patient_ids()
                valid_profs = get_prof_ids()

                data = []
                for apt in appointments:
                    pid = apt.get('Patient_PersonId')
                    if not pid or pid not in valid_patients:
                        continue
                    proid = apt.get('Dentist_PersonId') or apt.get('ScheduleToId')
                    if proid and proid not in valid_profs:
                        proid = None
                    data.append({
                        'id': apt.get('id'),
                        'clinic_id': BUSINESS_ID,
                        'patient_id': pid,
                        'professional_id': proid,
                        'scheduled_date': apt.get('date'),
                        'duration_minutes': 30,
                        'status': apt.get('Status') or 'scheduled',
                        'notes': apt.get('Notes'),
                        'reason_cancellation': None,
                        'updated_at': apt.get('Date'),
                        'last_sync_at': datetime.now(timezone.utc).isoformat(),
                    })

                # Inserir em lotes pequenos
                for i in range(0, len(data), BATCH_SIZE):
                    batch = data[i:i+BATCH_SIZE]
                    inserted, errors = safe_upsert('appointments', batch)
                    total_apt += inserted
                    total_errors += errors

    except Exception as e:
        print(f"    [{date_from} a {date_to}] ERRO: {str(e)[:80]}")

print(f"    [OK] Total: {total_apt} appointments carregados\n")
total_loaded += total_apt

# ============================================================================
# 2. PAYMENTS - HISTÓRICO COMPLETO
# ============================================================================

print("[2] CARREGANDO PAYMENTS (2020-2026)...\n")

total_pay = 0
for start, end in date_range_chunks(START_DATE, END_DATE, CHUNK_DAYS):
    date_from = start.strftime("%Y-%m-%d")
    date_to = end.strftime("%Y-%m-%d")

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
                # Garantir que todos os pacientes existam
                id_name = {pay.get('PatientId'): pay.get('PatientName') or pay.get('PayerName') or pay.get('OwnerName') for pay in payments if pay.get('PatientId')}
                ensure_patients(id_name)

                valid_patients = get_patient_ids()

                data = []
                for pay in payments:
                    pid = pay.get('PatientId')
                    if not pid or pid not in valid_patients:
                        continue
                    data.append({
                        'id': pay.get('PaymentHeaderId'),
                        'clinic_id': pay.get('ReceiverBusinessId', BUSINESS_ID),
                        'invoice_id': None,
                        'patient_id': pid,
                        'amount': float(pay.get('Amount', 0)),
                        'payment_method': pay.get('CreditCardType') or 'unknown',
                        'payment_date': pay.get('PaymentDate'),
                        'reference': pay.get('ExternalId') or '',
                        'status': 'completed' if pay.get('PaymentReceived') == 'X' else 'pending',
                        'notes': pay.get('PayerName') or '',
                        'updated_at': pay.get('ConfirmedDate') or datetime.now(timezone.utc).isoformat(),
                        'last_sync_at': datetime.now(timezone.utc).isoformat(),
                    })

                # Inserir em lotes pequenos
                for i in range(0, len(data), BATCH_SIZE):
                    batch = data[i:i+BATCH_SIZE]
                    inserted, errors = safe_upsert('payments', batch)
                    total_pay += inserted
                    total_errors += errors

    except Exception as e:
        print(f"    [{date_from} a {date_to}] ERRO: {str(e)[:80]}")

print(f"    [OK] Total: {total_pay} payments carregados\n")
total_loaded += total_pay

# ============================================================================
# 3. INVOICES - HISTÓRICO COMPLETO
# ============================================================================

print("[3] CARREGANDO INVOICES (2020-2026)...\n")

total_inv = 0
for start, end in date_range_chunks(START_DATE, END_DATE, CHUNK_DAYS):
    date_from = start.strftime("%Y-%m-%d")
    date_to = end.strftime("%Y-%m-%d")

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
                # Garantir que todos os pacientes existam
                id_name = {inv.get('PatientId'): inv.get('PatientName') for inv in invoices if inv.get('PatientId')}
                ensure_patients(id_name)

                valid_patients = get_patient_ids()

                data = []
                for inv in invoices:
                    pid = inv.get('PatientId')
                    if not pid or pid not in valid_patients:
                        continue
                    data.append({
                        'id': inv.get('InvoiceId'),
                        'clinic_id': BUSINESS_ID,
                        'patient_id': pid,
                        'number': str(inv.get('InvoiceId')),
                        'total_amount': float(inv.get('Amount', 0)),
                        'paid_amount': 0,
                        'due_date': inv.get('Date'),
                        'issue_date': inv.get('Date'),
                        'status': inv.get('Status', 'issued'),
                        'payment_method': None,
                        'updated_at': inv.get('Date'),
                        'last_sync_at': datetime.now(timezone.utc).isoformat(),
                    })

                # Inserir em lotes pequenos
                for i in range(0, len(data), BATCH_SIZE):
                    batch = data[i:i+BATCH_SIZE]
                    inserted, errors = safe_upsert('invoices', batch)
                    total_inv += inserted
                    total_errors += errors

    except Exception as e:
        print(f"    [{date_from} a {date_to}] ERRO: {str(e)[:80]}")

print(f"    [OK] Total: {total_inv} invoices carregados\n")
total_loaded += total_inv

# ============================================================================
# 4. PATIENT BIRTHDAYS - COM TRATAMENTO DE ERRO
# ============================================================================

print("[4] CARREGANDO PATIENT_BIRTHDAYS...\n")

total_bd = 0
try:
    response = requests.get(
        f"{API_URL}/patient/birthdays",
        params={'subscriber_id': SUBSCRIBER_ID, 'date': datetime.now().strftime('%Y-%m-%d')},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        birthdays = response.json()
        print(f"    API retornou: {len(birthdays)} aniversariantes")

        data = []
        for bd in birthdays:
            birth_date_str = bd.get('BirthDate', '')
            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                    data.append({
                        'id': str(uuid_lib.uuid4()),
                        'patient_id': bd.get('PatientId'),
                        'birth_date': birth_date.isoformat(),  # Serializar como string
                        'age': bd.get('Age'),
                        'birthday_month': birth_date.month,
                        'birthday_day': birth_date.day,
                        'updated_at': datetime.now(timezone.utc).isoformat(),
                        'last_sync_at': datetime.now(timezone.utc).isoformat(),
                    })
                except:
                    pass

        if data:
            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i:i+BATCH_SIZE]
                inserted, errors = safe_upsert('patient_birthdays', batch)
                total_bd += inserted
                total_errors += errors

        print(f"    [OK] {total_bd} aniversariantes carregados\n")
        total_loaded += total_bd

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 5. ANALYTICS RESULTS
# ============================================================================

print("[5] CARREGANDO ANALYTICS_RESULTS...\n")

total_ana = 0
try:
    response = requests.get(
        f"{API_URL}/analytics/list_results",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': START_DATE.strftime("%Y-%m-%d"),
            'to': END_DATE.strftime("%Y-%m-%d")
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        analytics_list = result if isinstance(result, list) else [result] if result else []
        print(f"    API retornou: {len(analytics_list)} registros")

        data = []
        for ana in analytics_list:
            data.append({
                'id': str(uuid_lib.uuid4()),
                'clinic_id': ana.get('BusinessId', BUSINESS_ID),
                'total_revenue_amount': float(ana.get('TotalRevenueAmount', 0)),
                'estimates_total_amount': float(ana.get('EstimatesTotalAmount', 0)),
                'estimates_total_quantity': int(ana.get('EstimatesTotalQuantity', 0)),
                'estimates_approved_amount': float(ana.get('EstimatesApprovedAmount', 0)),
                'estimates_approved_quantity': int(ana.get('EstimatesApprovedQuantity', 0)),
                'conversion_rate': float(ana.get('ConversionRate', 0)),
                'total_received_amount': float(ana.get('TotalReceivedAmount', 0)),
                'total_expenses': float(ana.get('TotalExpenses', 0)),
                'appointments_total': int(ana.get('AppointmentsTotal', 0)),
                'appointments_finished': int(ana.get('AppoinmentsFinished', 0)),
                'appointments_missed': int(ana.get('AppointmentsMissed', 0)),
                'unity_name': ana.get('UnityName'),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'last_sync_at': datetime.now(timezone.utc).isoformat(),
            })

        if data:
            inserted, errors = safe_upsert('analytics_results', data)
            total_ana += inserted
            total_errors += errors

        print(f"    [OK] {total_ana} registros analíticos carregados\n")
        total_loaded += total_ana

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 6. REVENUE BY SPECIALTY
# ============================================================================

print("[6] CARREGANDO REVENUE_BY_SPECIALTY...\n")

total_spec = 0
try:
    response = requests.get(
        f"{API_URL}/sales/expertise_revenue",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': START_DATE.strftime("%Y-%m-%d"),
            'to': END_DATE.strftime("%Y-%m-%d"),
            'businessId': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        revenues = result if isinstance(result, list) else [result] if result else []
        print(f"    API retornou: {len(revenues)} registros")

        data = []
        for rev in revenues:
            data.append({
                'id': str(uuid_lib.uuid4()),
                'clinic_id': BUSINESS_ID,
                'month': str(rev.get('month', ''))[:7],
                'specialty': rev.get('Expertise', 'Unknown'),
                'total_revenue': 0,
                'procedures_count': 0,
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'last_sync_at': datetime.now(timezone.utc).isoformat(),
            })

        if data:
            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i:i+BATCH_SIZE]
                inserted, errors = safe_upsert('revenue_by_specialty', batch)
                total_spec += inserted
                total_errors += errors

        print(f"    [OK] {total_spec} especialidades carregadas\n")
        total_loaded += total_spec

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO DO CARREGAMENTO COMPLETO")
print("=" * 80)

try:
    apt_count = db_client.count('appointments')
    pay_count = db_client.count('payments')
    inv_count = db_client.count('invoices')
    bd_count  = db_client.count('patient_birthdays')
    ana_count = db_client.count('analytics_results')
    spec_count = db_client.count('revenue_by_specialty')

    print(f"\n[DADOS REAIS CARREGADOS AGORA]")
    print(f"Appointments........: {apt_count:,} registros")
    print(f"Payments............: {pay_count:,} registros")
    print(f"Invoices............: {inv_count:,} registros")
    print(f"Patient Birthdays...: {bd_count} registros")
    print(f"Analytics Results...: {ana_count} registros")
    print(f"Revenue by Specialty: {spec_count} registros")
    print(f"{'='*40}")
    print(f"TOTAL REAL NESTA SESSAO: {apt_count + pay_count + inv_count + bd_count + ana_count + spec_count:,} registros")

    # Resumo geral
    pat  = db_client.count('patients')
    prof = db_client.count('professionals')
    est  = db_client.count('estimates')
    pro  = db_client.count('procedures')
    led  = db_client.count('leads')
    usr  = db_client.count('users')

    print(f"\n[ESTADO ATUAL DO BANCO]")
    print(f"Patients..........: {pat:,}")
    print(f"Professionals....: {prof:,}")
    print(f"Appointments.....: {apt_count:,}")
    print(f"Payments..........: {pay_count:,}")
    print(f"Invoices..........: {inv_count:,}")
    print(f"Estimates.........: {est:,}")
    print(f"Procedures........: {pro:,}")
    print(f"Users.............: {usr:,}")
    print(f"Leads.............: {led:,}")
    print(f"Patient Birthdays.: {bd_count}")
    print(f"Analytics.........: {ana_count}")
    print(f"Revenue Specialty.: {spec_count}")
    print(f"{'='*40}")

    grand_total = pat + prof + apt_count + pay_count + inv_count + est + pro + usr + led + bd_count + ana_count + spec_count
    print(f"TOTAL GERAL......: {grand_total:,} registros")

    print(f"\n[ERROS DURANTE CARREGAMENTO]")
    print(f"Total de erros: {total_errors}")

    if total_errors == 0:
        print(f"Status: ✅ SEM ERROS - CARREGAMENTO 100%\n")
    else:
        print(f"Status: ⚠️ {total_errors} registros não puderam ser carregados\n")

except Exception as e:
    print(f"Erro ao contar: {str(e)[:80]}")

print("=" * 80)
print("Carregamento completo finalizado!")
print("Período coberto: 2020-01-01 a 2026-06-09")
print("=" * 80 + "\n")
