#!/usr/bin/env python3
"""
Sincronizacao Incremental - Clinicorp -> PostgreSQL local
Ordem: patients -> professionals -> appointments -> payments -> invoices
"""

import os
import json
import time
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import db_client
from datetime import datetime, timedelta, timezone

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SYNC_STATE_FILE = "sync_state.json"
now_utc = datetime.now(timezone.utc).isoformat()


def upsert_batch(table, data, conflict_col='id'):
    """Upsert em lotes, retorna (inseridos, erros)."""
    if not data:
        return 0, 0
    try:
        n = db_client.upsert(table, data, conflict_col)
        return n, 0
    except Exception as e:
        print(f"    [BATCH ERROR] {e}")
        return 0, len(data)


print("=" * 70)
print("SINCRONIZACAO INCREMENTAL - CLINICORP")
print("=" * 70)

# ── [1] ESTADO ────────────────────────────────────────────────────────────────
print("\n[1] Carregando estado anterior...")

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
        print(f"    Ultima sincronizacao: {sync_state['last_sync']}")
    except Exception:
        print("    Arquivo corrompido, usando padrao")
else:
    print("    Primeira sincronizacao (ultimas 24h)")

try:
    last_sync_dt = datetime.fromisoformat(sync_state['last_sync'])
except Exception:
    last_sync_dt = datetime.now() - timedelta(days=1)

date_from = last_sync_dt.strftime("%Y-%m-%d")
date_to = datetime.now().strftime("%Y-%m-%d")
print(f"    Periodo: {date_from} a {date_to}")

# ── [2] PATIENTS ──────────────────────────────────────────────────────────────
print("\n[2] Sincronizando patients...")

try:
    resp = requests.get(
        f"{API_URL}/patient/birthdays",
        params={'subscriber_id': SUBSCRIBER_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )
    if resp.status_code == 200:
        birthdays = resp.json() or []
        print(f"    API retornou {len(birthdays)} registros")

        existing_ids = db_client.select_ids('patients')

        new_patients = []
        for bday in birthdays:
            pid = bday.get('PatientId')
            if pid and pid not in existing_ids:
                new_patients.append({
                    'id': pid,
                    'clinic_id': BUSINESS_ID,
                    'full_name': bday.get('Name') or f'Patient {pid}',
                    'date_of_birth': bday.get('BirthDate'),
                    'email': bday.get('Email') or '',
                    'phone': bday.get('MobilePhone') or '',
                    'status': 'active',
                    'last_sync_at': now_utc,
                })

        if new_patients:
            ok, err = upsert_batch('patients', new_patients)
            print(f"    [OK] {ok} novos patients inseridos ({err} erros)")
        else:
            print("    Nenhum patient novo")
    else:
        print(f"    API erro: {resp.status_code} - {resp.text[:100]}")
except Exception as e:
    print(f"    [ERROR] {e}")

# ── [3] PROFESSIONALS ─────────────────────────────────────────────────────────
print("\n[3] Sincronizando professionals...")

try:
    resp = requests.get(
        f"{API_URL}/professional/list_all_professionals",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )
    if resp.status_code == 200:
        professionals = resp.json() or []
        print(f"    API retornou {len(professionals)} profissionais")

        existing_prof_ids = db_client.select_ids('professionals')

        new_profs = []
        for prof in professionals:
            pid = prof.get('id')
            if pid and pid not in existing_prof_ids:
                new_profs.append({
                    'id': pid,
                    'clinic_id': BUSINESS_ID,
                    'full_name': prof.get('name') or f'Professional {pid}',
                    'cpf': prof.get('cpf'),
                    'email': None,
                    'phone': None,
                    'license_number': None,
                    'specialty': None,
                    'status': 'active',
                    'last_sync_at': now_utc,
                })

        if new_profs:
            ok, err = upsert_batch('professionals', new_profs)
            print(f"    [OK] {ok} novos professionals inseridos ({err} erros)")
        else:
            print("    Nenhum professional novo")
    else:
        print(f"    API erro: {resp.status_code} - {resp.text[:100]}")
except Exception as e:
    print(f"    [ERROR] {e}")

# ── [4] APPOINTMENTS ──────────────────────────────────────────────────────────
print("\n[4] Sincronizando agendamentos...")

apt_ok = 0

try:
    resp = requests.get(
        f"{API_URL}/appointment/list",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'businessId': BUSINESS_ID,
            'includeCanceled': True,
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )
    if resp.status_code == 200:
        appointments = resp.json() or []
        print(f"    API retornou {len(appointments)} agendamentos")

        valid_patients = db_client.select_ids('patients')
        valid_profs = db_client.select_ids('professionals')

        # Inserir pacientes faltando usando PatientName do agendamento
        fallback_patients = []
        for apt in appointments:
            pid = apt.get('Patient_PersonId')
            if pid and pid not in valid_patients:
                name = apt.get('PatientName') or apt.get('Name') or f'Patient {pid}'
                fallback_patients.append({
                    'id': pid,
                    'clinic_id': BUSINESS_ID,
                    'full_name': name,
                    'status': 'active',
                    'last_sync_at': now_utc,
                })
                valid_patients.add(pid)

        if fallback_patients:
            ok, err = upsert_batch('patients', fallback_patients)
            print(f"    [FALLBACK] {ok} pacientes inseridos via nome do agendamento ({err} erros)")

        data = []
        for apt in appointments:
            pid = apt.get('Patient_PersonId')
            proid = apt.get('Dentist_PersonId') or apt.get('ScheduleToId')

            if not pid or pid not in valid_patients:
                continue

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
                'last_sync_at': now_utc,
            })

        if data:
            ok, err = upsert_batch('appointments', data)
            apt_ok = ok
            sync_state['appointments_count'] += ok
            print(f"    [OK] {ok} agendamentos sincronizados ({err} erros)")
        else:
            print("    Nenhum agendamento para sincronizar")
    else:
        print(f"    API erro: {resp.status_code} - {resp.text[:100]}")
except Exception as e:
    print(f"    [ERROR] {e}")

# ── [5] PAYMENTS ──────────────────────────────────────────────────────────────
print("\n[5] Sincronizando pagamentos...")

try:
    resp = requests.get(
        f"{API_URL}/payment/list",
        params={'subscriber_id': SUBSCRIBER_ID, 'from': date_from, 'to': date_to},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )
    if resp.status_code == 200:
        payments = resp.json() or []
        print(f"    API retornou {len(payments)} pagamentos")

        valid_patients = db_client.select_ids('patients')

        # Inserir pacientes faltando usando nome do pagamento
        fallback_patients = []
        for pay in payments:
            pid = pay.get('PatientId')
            if pid and pid not in valid_patients:
                name = pay.get('PatientName') or pay.get('OwnerName') or pay.get('PayerName') or f'Patient {pid}'
                fallback_patients.append({
                    'id': pid,
                    'clinic_id': pay.get('ReceiverBusinessId', BUSINESS_ID),
                    'full_name': name,
                    'status': 'active',
                    'last_sync_at': now_utc,
                })
                valid_patients.add(pid)

        if fallback_patients:
            ok, err = upsert_batch('patients', fallback_patients)
            print(f"    [FALLBACK] {ok} pacientes inseridos via nome do pagamento ({err} erros)")

        data = []
        for pay in payments:
            pid = pay.get('PatientId')
            cid = pay.get('ReceiverBusinessId', BUSINESS_ID)

            if not pid or pid not in valid_patients:
                continue

            data.append({
                'id': pay.get('PaymentHeaderId'),
                'clinic_id': cid,
                'invoice_id': None,
                'patient_id': pid,
                'amount': float(pay.get('Amount', 0)),
                'payment_method': pay.get('CreditCardType') or 'unknown',
                'payment_date': pay.get('PaymentDate'),
                'reference': pay.get('ExternalId') or '',
                'status': 'completed' if pay.get('PaymentReceived') == 'X' else 'pending',
                'notes': pay.get('PayerName') or '',
                'updated_at': pay.get('ConfirmedDate') or now_utc,
                'last_sync_at': now_utc,
            })

        if data:
            ok, err = upsert_batch('payments', data)
            sync_state['payments_count'] += ok
            print(f"    [OK] {ok} pagamentos sincronizados ({err} erros)")
        else:
            print(f"    Nenhum pagamento valido ({pay_skipped} ignorados por FK)")
    else:
        print(f"    API erro: {resp.status_code} - {resp.text[:100]}")
except Exception as e:
    print(f"    [ERROR] {e}")

# ── [6] INVOICES ──────────────────────────────────────────────────────────────
print("\n[6] Sincronizando faturas...")

try:
    resp = requests.get(
        f"{API_URL}/financial/list_invoices",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID,
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )
    if resp.status_code == 200:
        invoices = resp.json() or []
        print(f"    API retornou {len(invoices)} faturas")

        if invoices:
            valid_patients = db_client.select_ids('patients')

            data = []
            inv_skipped = 0
            for inv in invoices:
                pid = inv.get('PatientId')
                if not pid or pid not in valid_patients:
                    inv_skipped += 1
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
                    'last_sync_at': now_utc,
                })

            if data:
                ok, err = upsert_batch('invoices', data)
                sync_state['invoices_count'] += ok
                print(f"    [OK] {ok} faturas sincronizadas ({err} erros, {inv_skipped} ignoradas por FK)")
            else:
                print(f"    Nenhuma fatura valida ({inv_skipped} ignoradas por FK)")
    else:
        print(f"    API erro: {resp.status_code} - {resp.text[:100]}")
except Exception as e:
    print(f"    [ERROR] {e}")

# ── [7] SALVAR ESTADO ─────────────────────────────────────────────────────────
print("\n[7] Salvando estado...")

sync_state['last_sync'] = datetime.now().isoformat()
with open(SYNC_STATE_FILE, 'w') as f:
    json.dump(sync_state, f, indent=2)
print("    [OK] Estado salvo")

# ── RESULTADO ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("RESULTADO")
print("=" * 70)

try:
    apt_total = db_client.count('appointments')
    pay_total = db_client.count('payments')
    inv_total = db_client.count('invoices')

    print(f"\nSincronizados nesta execucao:")
    print(f"  Agendamentos: +{sync_state['appointments_count']}")
    print(f"  Pagamentos:   +{sync_state['payments_count']}")
    print(f"  Faturas:      +{sync_state['invoices_count']}")

    print(f"\nTotal no banco:")
    print(f"  Agendamentos: {apt_total}")
    print(f"  Pagamentos:   {pay_total}")
    print(f"  Faturas:      {inv_total}")
except Exception as e:
    print(f"Erro ao contar: {e}")

print("\n" + "=" * 70)
print("Sincronizacao concluida!")
print("=" * 70)
