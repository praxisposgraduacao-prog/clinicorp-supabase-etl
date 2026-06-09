#!/usr/bin/env python3
"""
Debug: Verifica exatamente o que a API retorna para profissionais
"""

import os
import json
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))

print("=" * 80)
print("DEBUG: Profissionais da API")
print("=" * 80)

print(f"\nEndpoint: /professional/list_all_professionals")
print(f"Business ID param: {BUSINESS_ID}\n")

try:
    response = requests.get(
        f"{API_URL}/professional/list_all_professionals",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(USER, PASS),
        timeout=10
    )

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}\n")

    data = response.json()

    print(f"Response Type: {type(data).__name__}")

    if isinstance(data, list):
        print(f"Total de registros: {len(data)}")

        if len(data) > 0:
            print(f"\nPrimeiro registro (completo):")
            print(json.dumps(data[0], indent=2, default=str)[:500])

            print(f"\nChaves disponíveis no primeiro registro:")
            print(f"  {list(data[0].keys())}")

    elif isinstance(data, dict):
        print(f"Chaves principales: {list(data.keys())}")
        if 'data' in data:
            print(f"Total em data: {len(data['data'])}")
        else:
            print(json.dumps(data, indent=2, default=str)[:300])

except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
