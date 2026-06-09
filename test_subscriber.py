#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")

# Testar diferentes formas de passar subscriber_id
test_cases = [
    {"subscriber_id": "clinicorp"},
    {"subscriber_id": "praxis"},
    {"assinante_id": "clinicorp"},
    {"assinante_id": "praxis"},
    {"id_assinante": "clinicorp"},
]

print("Testando diferentes parametros para subscriber_id...\n")

for params in test_cases:
    print(f"Testando com: {params}")
    try:
        r = requests.get(
            f"{API_URL}/patient/list",
            params=params,
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else len(data.get('data', [])) if isinstance(data, dict) else 0
            print(f"  Resultado: {count} registros - SUCESSO!")
        else:
            print(f"  Erro: {r.json().get('Message', 'Erro desconhecido')[:80]}")
    except Exception as e:
        print(f"  Erro: {str(e)[:80]}")
    print()
