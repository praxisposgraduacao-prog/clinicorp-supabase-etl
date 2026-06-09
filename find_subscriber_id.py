#!/usr/bin/env python3
"""
Script para descobrir o subscriber_id correto testando diferentes valores
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
BUSINESS_ID = os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104")

print("=" * 80)
print("DESCOBRINDO O SUBSCRIBER_ID CORRETO")
print("=" * 80)

# Testar diferentes valores de subscriber_id
test_values = [
    "praxis",
    "clinicorp",
    "admin",
    "default",
    "main",
    BUSINESS_ID,
    str(int(BUSINESS_ID) // 1000000000),  # Primeiros dígitos
    "5292365675823104",
]

endpoint = "/patient/list"  # Usar patient/list que é simples

print(f"\nTestando endpoint: {endpoint}")
print(f"Testando diferentes valores de subscriber_id...\n")

for subscriber_id in test_values:
    print(f"[*] Testando: subscriber_id = {subscriber_id}")

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            params={'subscriber_id': subscriber_id},
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )

        print(f"    Status: {response.status_code}", end="")

        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else len(data.get('data', []))
            print(f" - SUCESSO! {count} registros")
            print(f"\n    >>> SUBSCRIBER_ID ENCONTRADO: {subscriber_id}")
            print(f"    >>> Use isso no .env: ERP_CLINICORP_SUBSCRIBER_ID={subscriber_id}\n")
            break
        else:
            msg = response.json().get('Message', 'Erro desconhecido')[:60] if response.status_code == 400 else f"Status {response.status_code}"
            print(f" - {msg}")

    except Exception as e:
        print(f"    Erro: {str(e)[:60]}")

print("\n" + "=" * 80)
print("Se nenhum valor funcionou, verifique:")
print("  1. A documentação do Clinicorp")
print("  2. O dashboard/admin do Clinicorp para encontrar o subscriber_id")
print("  3. Contactar suporte do Clinicorp")
print("=" * 80)
