#!/usr/bin/env python3
"""
Diagnosticar o problema com estimates
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

print("=" * 80)
print("DIAGNOSTICO DE ESTIMATES")
print("=" * 80)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

# Verificar estrutura de agendamentos
print("\n[1] ANALISANDO AGENDAMENTOS PARA EXTRAIR IDs...")

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
        print(f"    Total: {len(appointments)} agendamentos\n")

        if len(appointments) > 0:
            apt = appointments[0]
            print("[PRIMEIRO AGENDAMENTO - CAMPOS DISPONVEIS]")
            for key in sorted(apt.keys()):
                value = apt[key]
                print(f"  {key}: {str(value)[:60]}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# Tentar endpoints diferentes
print("\n[2] TESTANDO DIFERENTES ENDPOINTS DE ESTIMATES...")

endpoints_to_test = [
    ('/estimates/list', {'subscriber_id': SUBSCRIBER_ID}),
    ('/procedures/list', {'business_id': BUSINESS_ID}),
    ('/patient/list_estimates', {'subscriber_id': SUBSCRIBER_ID}),
]

for endpoint, params in endpoints_to_test:
    print(f"\n    [{endpoint}]")

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            params=params,
            auth=HTTPBasicAuth(API_USER, API_PASS),
            timeout=10
        )

        print(f"    Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"    Tipo: {type(data).__name__}")

            if isinstance(data, list):
                print(f"    Itens: {len(data)}")
                if len(data) > 0:
                    print(f"    Primeiro item: {json.dumps(data[0], indent=2, default=str)[:200]}")
            elif isinstance(data, dict):
                print(f"    Chaves: {list(data.keys())[:10]}")

    except Exception as e:
        print(f"    [ERROR] {str(e)[:80]}")

# Tentar um estimate específico com IDs diferentes
print("\n[3] TESTANDO /estimates/get COM IDs DIFERENTES...")

test_ids = [
    "5292365675823104",
    "1",
    "123456",
]

for test_id in test_ids:
    print(f"\n    [treatment_id={test_id}]")

    try:
        response = requests.get(
            f"{API_URL}/estimates/get",
            params={
                'subscriber_id': SUBSCRIBER_ID,
                'treatment_id': test_id
            },
            auth=HTTPBasicAuth(API_USER, API_PASS),
            timeout=10
        )

        print(f"    Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"    Resposta: {json.dumps(data, indent=2, default=str)[:300]}")

    except Exception as e:
        print(f"    Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
print("CONCLUSAO")
print("=" * 80)

print("""
Se nenhum endpoint retornar dados úteis:
1. O endpoint /estimates/get pode requerir IDs que não estão nos agendamentos
2. Ou pode ser que estimates não estejam disponíveis para sincronização
3. Contate suporte Clinicorp para confirmar disponibilidade de estimates

Alternativamente, estimates podem estar nos agendamentos com outro nome de campo.
""")

print("=" * 80)
