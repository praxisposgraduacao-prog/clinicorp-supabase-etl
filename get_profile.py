#!/usr/bin/env python3
"""
Tenta obter informações do perfil do usuário logado
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

print("=" * 80)
print("OBTENDO INFORMAÇÕES DO USUÁRIO LOGADO")
print("=" * 80)

endpoints = [
    "/profile",
    "/me",
    "/user",
    "/user/profile",
    "/auth/profile",
    "/group/profile",
    "/subscriber/info",
    "/account/info",
]

print(f"\nTestando endpoints de profile...\n")

for endpoint in endpoints:
    print(f"[*] GET {endpoint}", end=" ... ")

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )

        print(f"Status {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n>>> ENDPOINT ENCONTRADO: {endpoint}")
            print(f"Response:\n{json.dumps(data, indent=2, default=str)[:500]}")
            break
        elif response.status_code == 400:
            msg = response.json().get('Message', '')[:80]
            if "assinante" in msg or "subscriber" in msg:
                print(f"(Esperado - requer subscriber_id)")

    except Exception as e:
        print(f"Erro")

print("\n" + "=" * 80)
