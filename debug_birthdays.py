#!/usr/bin/env python3
"""
Debug API response structure para patient birthdays
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

print("=" * 80)
print("DEBUG - PATIENT BIRTHDAYS API RESPONSE")
print("=" * 80)

try:
    response = requests.get(
        f"{API_URL}/patient/birthdays",
        params={'subscriber_id': SUBSCRIBER_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Type: {type(response.json())}")

    if response.status_code == 200:
        data = response.json()

        if isinstance(data, list):
            print(f"\nArray com {len(data)} registros\n")
            if len(data) > 0:
                print("Primeiro registro (sample):")
                print(json.dumps(data[0], indent=2, default=str))

                print("\n\nTodas as chaves encontradas:")
                for record in data:
                    for key in record.keys():
                        print(f"  - {key}")
                    break
        else:
            print("\nResposta é um dicionário (não lista):")
            print(json.dumps(data, indent=2, default=str))

except Exception as e:
    print(f"ERROR: {str(e)}")

print("\n" + "=" * 80)
