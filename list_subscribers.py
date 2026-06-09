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

print("Testando endpoints de grupo/assinante...\n")

endpoints = [
    "/group/list_subscribers",
    "/group/list_subscribers_clinics",
]

for endpoint in endpoints:
    print(f"[*] Testando: {endpoint}")
    try:
        r = requests.get(
            f"{API_URL}{endpoint}",
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )
        print(f"    Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"    Response type: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"    Keys: {list(data.keys())}")
                if 'data' in data:
                    print(f"    Data count: {len(data['data']) if isinstance(data['data'], list) else 'N/A'}")
                    if len(data['data']) > 0:
                        print(f"    First record: {json.dumps(data['data'][0], indent=2)[:200]}")
            elif isinstance(data, list):
                print(f"    Records: {len(data)}")
                if len(data) > 0:
                    print(f"    First record: {json.dumps(data[0], indent=2)[:200]}")
        else:
            print(f"    Error: {r.json()}")
    except Exception as e:
        print(f"    Exception: {str(e)}")
    print()
