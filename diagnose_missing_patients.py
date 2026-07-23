#!/usr/bin/env python3
"""
Investiga pacientes sem data de nascimento que estao sendo ignorados no sync.
Testa /patient/get por ID e fallback via PatientName dos agendamentos/pagamentos.
"""

import os
import time
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta

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
print("DIAGNOSTICO: PACIENTES SEM DATA DE NASCIMENTO")
print(f"Periodo: {date_from} a {date_to}")
print("=" * 70)

# ── Pacientes existentes no banco ─────────────────────────────────────────────
existing = {r['id'] for r in client.table('patients').select('id').execute().data}
print(f"\nPacientes no banco: {len(existing)}")

# ── Coletar IDs e nomes faltando dos agendamentos e pagamentos ────────────────
missing = {}  # {patient_id: {'name': ..., 'source': ...}}

print("\n[1] Buscando IDs faltando nos agendamentos...")
resp = requests.get(
    f"{API_URL}/appointment/list",
    params={'subscriber_id': SUBSCRIBER_ID, 'from': date_from, 'to': date_to,
            'businessId': BUSINESS_ID, 'includeCanceled': True},
    auth=HTTPBasicAuth(API_USER, API_PASS), timeout=30
)
if resp.status_code == 200:
    for apt in resp.json() or []:
        pid = apt.get('Patient_PersonId')
        if pid and pid not in existing:
            name = apt.get('PatientName') or apt.get('Name') or ''
            if pid not in missing:
                missing[pid] = {'name': name, 'source': 'appointment'}
            elif not missing[pid]['name'] and name:
                missing[pid]['name'] = name
    print(f"    {len(missing)} pacientes faltando em agendamentos")
else:
    print(f"    Erro API: {resp.status_code}")

print("\n[2] Buscando IDs faltando nos pagamentos...")
resp = requests.get(
    f"{API_URL}/payment/list",
    params={'subscriber_id': SUBSCRIBER_ID, 'from': date_from, 'to': date_to},
    auth=HTTPBasicAuth(API_USER, API_PASS), timeout=30
)
if resp.status_code == 200:
    pay_missing_before = len(missing)
    for pay in resp.json() or []:
        pid = pay.get('PatientId')
        if pid and pid not in existing:
            name = pay.get('PatientName') or pay.get('OwnerName') or pay.get('PayerName') or ''
            if pid not in missing:
                missing[pid] = {'name': name, 'source': 'payment'}
            elif not missing[pid]['name'] and name:
                missing[pid]['name'] = name
    print(f"    {len(missing) - pay_missing_before} IDs adicionais via pagamentos")
else:
    print(f"    Erro API: {resp.status_code}")

print(f"\nTotal de pacientes faltando: {len(missing)}")

# Separar os que tem nome dos que nao tem
with_name = {pid: info for pid, info in missing.items() if info['name']}
without_name = {pid: info for pid, info in missing.items() if not info['name']}

print(f"  Com nome nos dados da API:  {len(with_name)}")
print(f"  Sem nome nos dados da API:  {len(without_name)}")

# ── Testar /patient/get para os sem nome (amostra de ate 5) ──────────────────
sample_ids = list(without_name.keys())[:5]

if sample_ids:
    print(f"\n[3] Testando /patient/get para {len(sample_ids)} IDs sem nome (amostra)...")
    get_ok = 0
    get_fail = 0
    for pid in sample_ids:
        try:
            r = requests.get(
                f"{API_URL}/patient/get",
                params={'id': pid, 'business_id': BUSINESS_ID},
                auth=HTTPBasicAuth(API_USER, API_PASS),
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                name = None
                if isinstance(data, dict):
                    name = data.get('full_name') or data.get('name') or data.get('Name')
                elif isinstance(data, list) and data:
                    name = data[0].get('full_name') or data[0].get('name') or data[0].get('Name')
                if name:
                    missing[pid]['name'] = name
                    get_ok += 1
                    print(f"    [OK] {pid} -> {name}")
                else:
                    print(f"    [SEM NOME] {pid} -> resposta: {str(data)[:80]}")
                    get_fail += 1
            else:
                print(f"    [HTTP {r.status_code}] {pid} -> {r.text[:80]}")
                get_fail += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"    [ERROR] {pid} -> {e}")
            get_fail += 1

    print(f"\n    /patient/get: {get_ok} com nome, {get_fail} sem nome/erro")
else:
    print("\n[3] Todos os IDs faltando ja tem nome nos dados da API - /patient/get nao necessario")

# ── Resumo final ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("RESUMO")
print("=" * 70)

can_recover = {pid: info for pid, info in missing.items() if info['name']}
cannot_recover = {pid: info for pid, info in missing.items() if not info['name']}

print(f"\nPacientes que PODEM ser inseridos (tem nome): {len(can_recover)}")
if can_recover:
    for pid, info in list(can_recover.items())[:5]:
        print(f"  {pid} -> '{info['name']}' (via {info['source']})")
    if len(can_recover) > 5:
        print(f"  ... e mais {len(can_recover) - 5}")

print(f"\nPacientes que NAO podem ser recuperados (sem nome): {len(cannot_recover)}")
if cannot_recover:
    for pid in list(cannot_recover.keys())[:5]:
        print(f"  {pid}")
    if len(cannot_recover) > 5:
        print(f"  ... e mais {len(cannot_recover) - 5}")

print(f"""
CONCLUSAO:
- {len(can_recover)} pacientes podem ser inseridos agora usando o nome
  extraido dos agendamentos/pagamentos
- {len(cannot_recover)} pacientes nao tem nome disponivel em nenhuma fonte
- O sync incremental pode usar PatientName do agendamento/pagamento como
  fallback quando o paciente nao esta no banco
""")
