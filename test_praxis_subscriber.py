#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
SUBSCRIBER = "praxis"

print("=" * 80)
print("TESTANDO SUBSCRIBER_ID: praxis")
print("=" * 80)

endpoints = [
    "/patient/list",
    "/appointment/list",
    "/financial/list_invoices",
]

for endpoint in endpoints:
    print(f"\n[*] {endpoint}")
    try:
        r = requests.get(
            f"{API_URL}{endpoint}",
            params={"subscriber_id": SUBSCRIBER},
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )

        print(f"    Status: {r.status_code}")

        if r.status_code != 200:
            try:
                error = r.json()
                print(f"    Erro: {json.dumps(error, indent=6)[:200]}")
            except:
                print(f"    Response: {r.text[:200]}")
        else:
            data = r.json()
            count = len(data) if isinstance(data, list) else len(data.get('data', []))
            print(f"    OK! {count} registros")

    except Exception as e:
        print(f"    Exception: {str(e)[:100]}")
