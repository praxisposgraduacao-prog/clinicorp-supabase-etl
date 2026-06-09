#!/usr/bin/env python3
"""
Garantir que a clínica principal existe
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("GARANTIR CLINICA EXISTE")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"\nBusiness ID: {BUSINESS_ID}\n")

# Verificar se clínica existe
print("[1] Verificando se clinica existe...")
try:
    result = client.table('clinics').select('id').eq('id', BUSINESS_ID).execute()

    if len(result.data) > 0:
        print(f"    [OK] Clinica ja existe!")
    else:
        print(f"    [INFO] Clinica nao existe, criando...")

        clinic_data = {
            'id': BUSINESS_ID,
            'business_id': BUSINESS_ID,
            'name': f"Main Clinic",
            'updated_at': datetime.utcnow().isoformat(),
            'last_sync_at': datetime.utcnow().isoformat(),
        }

        try:
            client.table('clinics').insert([clinic_data]).execute()
            print(f"    [OK] Clinica criada!")
        except Exception as e:
            print(f"    [ERROR] {str(e)[:100]}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# Verificar dados
print(f"\n[2] Verificando dados nas tabelas...")

try:
    clinics = client.table('clinics').select('id', count='exact').execute().count
    patients = client.table('patients').select('id', count='exact').execute().count
    payments = client.table('payments').select('id', count='exact').execute().count

    print(f"    Clinicas: {clinics}")
    print(f"    Pacientes: {patients}")
    print(f"    Pagamentos: {payments}")

except Exception as e:
    print(f"    Erro: {e}")

print("\n" + "=" * 80)
