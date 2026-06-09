#!/usr/bin/env python3
"""
Tenta diferentes nomes de parâmetro para o subscriber_id
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")

print("=" * 80)
print("TESTANDO DIFERENTES NOMES DE PARÂMETRO")
print("=" * 80)

# Testar diferentes nomes de parâmetro com valor "praxis"
param_names = [
    "assinante_id",
    "assinante",
    "subscriber",
    "tenant_id",
    "account_id",
    "org_id",
    "company_id",
    "clinic_id",
    "establishment_id",
]

test_value = "praxis"
endpoint = "/patient/list"

print(f"\nEndpoint: {endpoint}")
print(f"Testando com valor: {test_value}\n")

for param_name in param_names:
    print(f"[*] {param_name} = {test_value}", end=" ... ")

    try:
        params = {param_name: test_value}
        response = requests.get(
            f"{API_URL}{endpoint}",
            params=params,
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else len(data.get('data', []))
            print(f"✓ SUCESSO! {count} registros")
            print(f"\n>>> PARÂMETRO ENCONTRADO: {param_name}")
            break
        elif response.status_code == 400:
            msg = response.json().get('Message', '')[:50]
            print(f"400 - {msg}")
        else:
            print(f"{response.status_code}")

    except Exception as e:
        print(f"Erro: {str(e)[:40]}")

print("\n" + "=" * 80)
