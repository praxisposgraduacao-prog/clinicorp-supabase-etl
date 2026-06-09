#!/usr/bin/env python3
"""
Corrigir nomes dos pacientes carregando dados reais da API
"""

import os
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
print("CORRIGIR NOMES DOS PACIENTES")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Obter lista de pacientes atuais no banco
print("\n[1] OBTENDO IDS DE PACIENTES DO BANCO...")

try:
    result = client.table('patients').select('id').execute()
    patient_ids = [p['id'] for p in result.data]
    print(f"    Total: {len(patient_ids)} pacientes\n")
except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")
    exit(1)

# Tentar obter nomes dos pacientes via API
print("[2] OBTENDO NOMES REAIS DOS PACIENTES DA API...")

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

patient_names = {}
total_found = 0

# Tentar via agendamentos
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

        for apt in appointments:
            patient_id = apt.get('Patient_PersonId')
            patient_name = apt.get('PatientName') or apt.get('Name')

            if patient_id and patient_name and patient_id not in patient_names:
                patient_names[patient_id] = patient_name
                total_found += 1

        print(f"    Via agendamentos: {total_found} pacientes com nomes\n")

except Exception as e:
    print(f"    [WARN] Erro ao obter via agendamentos: {str(e)[:60]}\n")

# Tentar via pagamentos
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

        for pay in payments:
            patient_id = pay.get('PatientId')
            patient_name = pay.get('PatientName') or pay.get('OwnerName')

            if patient_id and patient_name and patient_id not in patient_names:
                patient_names[patient_id] = patient_name

        print(f"    Via pagamentos: {len(patient_names)} pacientes com nomes\n")

except Exception as e:
    print(f"    [WARN] Erro ao obter via pagamentos: {str(e)[:60]}\n")

# Tentar via faturas
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

        for inv in invoices:
            patient_id = inv.get('PatientId')
            patient_name = inv.get('PatientName')

            if patient_id and patient_name and patient_id not in patient_names:
                patient_names[patient_id] = patient_name

        print(f"    Via faturas: {len(patient_names)} pacientes com nomes\n")

except Exception as e:
    print(f"    [WARN] Erro ao obter via faturas: {str(e)[:60]}\n")

# Atualizar nomes no banco
print(f"[3] ATUALIZANDO NOMES NO BANCO...")
print(f"    Nomes encontrados: {len(patient_names)}")
print(f"    Nomes faltando: {len(patient_ids) - len(patient_names)}\n")

updated = 0
failed = 0

for patient_id, patient_name in patient_names.items():
    try:
        client.table('patients').update({
            'full_name': patient_name,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', patient_id).execute()
        updated += 1

        if updated % 100 == 0:
            print(f"    Progresso: {updated}/{len(patient_names)}")

    except Exception as e:
        failed += 1

print(f"\n    Atualizados: {updated}")
print(f"    Falhas: {failed}\n")

# Verificar resultado
print("[4] VERIFICANDO RESULTADO...")

try:
    result = client.table('patients').select('id, full_name').limit(5).execute()

    print("\n    [Amostra de pacientes atualizados]")
    for p in result.data:
        name = p['full_name']
        is_default = name.startswith('Patient ') or name.startswith('patient ')
        status = "❌" if is_default else "✅"
        print(f"    {status} ID: {p['id']}, Nome: {name[:50]}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)

print(f"""
Total de pacientes: {len(patient_ids)}
Nomes corrigidos: {updated}
Ainda com nomes genéricos: {len(patient_ids) - updated}

Proximos passos:
1. Se houver pacientes com nomes genéricos, contate o suporte Clinicorp
2. para obter endpoint de busca por ID de paciente
3. Ou considere usar apenas o ID como identificador

Status: Correcao parcial concluida ({updated}/{len(patient_ids)})
""")

print("=" * 80)
