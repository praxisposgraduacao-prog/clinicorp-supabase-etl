#!/usr/bin/env python3
"""
Tenta passar subscriber_id na URL path
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
print("TESTANDO SUBSCRIBER_ID NA URL PATH")
print("=" * 80)

test_values = ["praxis", "clinicorp", "admin", "default"]

print("\nTestando diferentes formatos de URL...\n")

for subscriber in test_values:
    # Formato 1: /patient/list/subscriber
    url1 = f"{API_URL}/patient/list/{subscriber}"
    print(f"[*] {url1}", end=" ... ")

    try:
        response = requests.get(
            url1,
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else len(data.get('data', []))
            print(f"✓ SUCESSO! {count} registros")
            print(f"\n>>> ENCONTRADO! Use: /patient/list/{subscriber}")
            break
        else:
            print(f"{response.status_code}")
    except Exception as e:
        print(f"Erro")

print("\n" + "=" * 80)
print("Se ainda não funcionar, o subscriber_id provavelmente:")
print("  1. É obtido automaticamente da autenticação")
print("  2. Está armazenado em outra interface/dashboard")
print("  3. Precisa ser obtido de um endpoint de 'profile' ou 'me'")
print("=" * 80)
