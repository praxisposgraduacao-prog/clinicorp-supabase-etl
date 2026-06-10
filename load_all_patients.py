#!/usr/bin/env python3
"""
Carregar TODOS os patients da API
Alguns pacientes têm dados em patient/birthdays mas não aparecem em appointments/payments/invoices
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime
import time

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY = 2

def serialize_value(value):
    """Serializar valores para JSON-compatible"""
    if value is None:
        return None
    elif isinstance(value, (datetime,)):
        return value.isoformat()
    else:
        return value

def safe_upsert(table_name, data, key='id', retry=0):
    """Upsert com retry logic"""
    try:
        if not data or len(data) == 0:
            return 0, 0

        cleaned = []
        seen = {}
        for record in data:
            clean_record = {}
            for k, v in record.items():
                clean_record[k] = serialize_value(v)

            # Avoid duplicates
            record_key = clean_record.get(key)
            if record_key not in seen:
                seen[record_key] = True
                cleaned.append(clean_record)

        if not cleaned:
            return 0, 0

        client.table(table_name).upsert(cleaned, on_conflict=key).execute()
        return len(cleaned), 0

    except Exception as e:
        error_str = str(e)

        if retry < MAX_RETRIES:
            print(f"        [RETRY {retry+1}/{MAX_RETRIES}] Aguardando {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            return safe_upsert(table_name, data, key, retry + 1)
        else:
            print(f"        [ERROR] {error_str[:100]}")
            return 0, len(data)

print("=" * 80)
print("CARREGAR TODOS OS PATIENTS DA API")
print("=" * 80)

# First, get list of patients we already have
print("\n[1] Pacientes já carregados:\n")

try:
    result = client.table('patients').select('id').execute()
    existing_patients = set([p['id'] for p in result.data])
    print(f"    Total: {len(existing_patients)} pacientes já na base\n")
except:
    existing_patients = set()
    print("    Erro ao buscar pacientes existentes\n")

# Now get all patients from API via birthdays endpoint (returns all patients with birthdays)
print("[2] Buscando pacientes da API:\n")

total_new = 0
total_errors = 0

try:
    response = requests.get(
        f"{API_URL}/patient/birthdays",
        params={'subscriber_id': SUBSCRIBER_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        birthdays = response.json()
        print(f"    API retornou: {len(birthdays) if birthdays else 0} aniversariantes\n")

        if birthdays:
            data = []
            for bday in birthdays:
                patient_id = bday.get('PatientId')

                # Skip if already exists
                if patient_id not in existing_patients:
                    data.append({
                        'id': patient_id,
                        'full_name': bday.get('Name', f'Patient {patient_id}'),
                        'date_of_birth': bday.get('BirthDate'),
                        'email': bday.get('Email') or '',
                        'phone': bday.get('MobilePhone') or '',
                        'clinic_id': BUSINESS_ID,
                        'status': 'active',
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })

            print(f"    Pacientes novos para carregar: {len(data)}\n")

            if data:
                for i in range(0, len(data), BATCH_SIZE):
                    batch = data[i:i+BATCH_SIZE]
                    inserted, errors = safe_upsert('patients', batch)
                    total_new += inserted
                    total_errors += errors
                    if inserted > 0:
                        print(f"    [OK] {inserted} pacientes novos carregados")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}")

print("\n" + "=" * 80)
print(f"TOTAL DE PACIENTES NOVOS: {total_new}")
print(f"TOTAL DE ERROS: {total_errors}")
print("=" * 80)
