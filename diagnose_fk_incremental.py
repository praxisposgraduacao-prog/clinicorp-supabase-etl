#!/usr/bin/env python3
"""
Diagnóstico de erros de Foreign Key no sync incremental.
Verifica quais patient_ids, professional_ids e clinic_ids estão faltando no banco.
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID")
SUPABASE_URL = os.getenv("ERP_CLINICORP_URL")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
date_to = datetime.now().strftime("%Y-%m-%d")

print("=" * 70)
print("DIAGNÓSTICO DE FOREIGN KEY - SYNC INCREMENTAL")
print(f"Período: {date_from} a {date_to}")
print("=" * 70)

# IDs existentes no banco
print("\n[1] Carregando IDs existentes no banco...")

existing_clinics = {r['id'] for r in client.table('clinics').select('id').execute().data}
existing_patients = {r['id'] for r in client.table('patients').select('id').execute().data}
existing_professionals = {r['id'] for r in client.table('professionals').select('id').execute().data}

print(f"    Clínicas:      {len(existing_clinics)}")
print(f"    Pacientes:     {len(existing_patients)}")
print(f"    Profissionais: {len(existing_professionals)}")

# ── AGENDAMENTOS ──────────────────────────────────────────────────────────────
print("\n[2] Verificando agendamentos...")

resp = requests.get(
    f"{API_URL}/appointment/list",
    params={'subscriber_id': SUBSCRIBER_ID, 'from': date_from, 'to': date_to,
            'businessId': BUSINESS_ID, 'includeCanceled': True},
    auth=HTTPBasicAuth(API_USER, API_PASS), timeout=30
)

if resp.status_code == 200:
    appointments = resp.json()
    print(f"    API retornou {len(appointments)} agendamentos")

    missing_clinics_apt    = set()
    missing_patients_apt   = set()
    missing_professionals  = set()

    for apt in appointments:
        cid = BUSINESS_ID
        pid = apt.get('Patient_PersonId')
        proid = apt.get('Dentist_PersonId') or apt.get('ScheduleToId')

        if cid not in existing_clinics:
            missing_clinics_apt.add(cid)
        if pid and pid not in existing_patients:
            missing_patients_apt.add(pid)
        if proid and proid not in existing_professionals:
            missing_professionals.add(proid)

    print(f"\n    Clinicas faltando:      {len(missing_clinics_apt)} -> {sorted(missing_clinics_apt)}")
    print(f"    Pacientes faltando:     {len(missing_patients_apt)}")
    if missing_patients_apt:
        sample = sorted(missing_patients_apt)[:10]
        print(f"      Exemplos: {sample}{'...' if len(missing_patients_apt) > 10 else ''}")
    print(f"    Profissionais faltando: {len(missing_professionals)}")
    if missing_professionals:
        sample = sorted(missing_professionals)[:10]
        print(f"      Exemplos: {sample}{'...' if len(missing_professionals) > 10 else ''}")
else:
    print(f"    Erro na API: {resp.status_code}")
    appointments = []

# ── PAGAMENTOS ────────────────────────────────────────────────────────────────
print("\n[3] Verificando pagamentos...")

resp = requests.get(
    f"{API_URL}/payment/list",
    params={'subscriber_id': SUBSCRIBER_ID, 'from': date_from, 'to': date_to},
    auth=HTTPBasicAuth(API_USER, API_PASS), timeout=30
)

if resp.status_code == 200:
    payments = resp.json()
    print(f"    API retornou {len(payments)} pagamentos")

    missing_clinics_pay  = set()
    missing_patients_pay = set()

    for pay in payments:
        cid = pay.get('ReceiverBusinessId', BUSINESS_ID)
        pid = pay.get('PatientId')

        if cid and cid not in existing_clinics:
            missing_clinics_pay.add(cid)
        if pid and pid not in existing_patients:
            missing_patients_pay.add(pid)

    print(f"\n    Clinicas faltando:  {len(missing_clinics_pay)} -> {sorted(missing_clinics_pay)}")
    print(f"    Pacientes faltando: {len(missing_patients_pay)}")
    if missing_patients_pay:
        sample = sorted(missing_patients_pay)[:10]
        print(f"      Exemplos: {sample}{'...' if len(missing_patients_pay) > 10 else ''}")
else:
    print(f"    Erro na API: {resp.status_code}")

# ── RESUMO E RECOMENDAÇÃO ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("RESUMO E CAUSA RAIZ")
print("=" * 70)

all_missing_patients = missing_patients_apt | missing_patients_pay
all_missing_clinics  = missing_clinics_apt | missing_clinics_pay

if all_missing_clinics:
    print(f"\n[!] {len(all_missing_clinics)} clinic_id(s) nao existem na tabela clinics:")
    print(f"    {sorted(all_missing_clinics)}")
    print("    -> Rodar ETL de clinics antes do sync incremental")

if all_missing_patients:
    print(f"\n[!] {len(all_missing_patients)} patient_id(s) nao existem na tabela patients")
    print("    -> Rodar ETL de patients para o periodo recente antes de sync")

if missing_professionals:
    print(f"\n[!] {len(missing_professionals)} professional_id(s) nao existem na tabela professionals")
    print("    -> Rodar ETL de professionals antes do sync incremental")

if not all_missing_clinics and not all_missing_patients and not missing_professionals:
    print("\n[OK] Nenhuma FK faltando detectada para o período atual")

print()
