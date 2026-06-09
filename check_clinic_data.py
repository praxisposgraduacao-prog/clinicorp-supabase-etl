#!/usr/bin/env python3
"""
Verificar dados da clínica na tabela
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("VERIFICAR DADOS DA CLINICA")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"\nBuscando clinica com ID: {BUSINESS_ID}\n")

try:
    result = client.table('clinics').select('*').eq('id', BUSINESS_ID).execute()

    if len(result.data) > 0:
        clinic = result.data[0]
        print("[DADOS ENCONTRADOS]")
        for key, value in clinic.items():
            print(f"  {key}: {value}")
    else:
        print("[NENHUMA CLINICA ENCONTRADA]")

    # Listar todas as clínicas
    print(f"\n[TODAS AS CLINICAS]")
    all_clinics = client.table('clinics').select('id, name, business_id').execute()
    for clinic in all_clinics.data:
        print(f"  ID: {clinic.get('id')}, Name: {clinic.get('name')}, Business ID: {clinic.get('business_id')}")

except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
