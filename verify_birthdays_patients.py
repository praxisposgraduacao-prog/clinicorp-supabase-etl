#!/usr/bin/env python3
"""
Verificar se patient IDs de birthdays existem na tabela patients
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("VERIFICAR PATIENT IDs DE BIRTHDAYS NA TABELA PATIENTS")
print("=" * 80)

# Get birthdays from API
try:
    response = requests.get(
        f"{API_URL}/patient/birthdays",
        params={'subscriber_id': SUBSCRIBER_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        birthdays = response.json()
        print(f"\nAPI retornou {len(birthdays)} aniversariantes\n")

        patient_ids_from_birthdays = [b.get('PatientId') for b in birthdays]
        print(f"Patient IDs de birthdays: {patient_ids_from_birthdays}\n")

        # Check each one
        for pid in patient_ids_from_birthdays:
            try:
                patient = client.table('patients').select('id, full_name').eq('id', pid).execute()
                if patient.data:
                    print(f"  Patient {pid}: EXISTS ({patient.data[0].get('full_name')})")
                else:
                    print(f"  Patient {pid}: NOT FOUND")
            except Exception as e:
                print(f"  Patient {pid}: ERROR - {str(e)[:50]}")

except Exception as e:
    print(f"ERROR: {str(e)}")

print("\n" + "=" * 80)
