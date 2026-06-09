#!/usr/bin/env python3
"""
Verifica profissionais carregados no Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("VERIFICANDO PROFISSIONAIS NO SUPABASE")
print("=" * 80)

# Contar total
print("\n[1] Total de Profissionais...")
try:
    result = client.table('professionals').select('id', count='exact').execute()
    total = result.count if hasattr(result, 'count') else len(result.data)
    print(f"    Total: {total} profissionais")
except Exception as e:
    print(f"    Erro: {e}")

# Listar algumas amostras
print("\n[2] Amostra dos Profissionais...")
try:
    result = client.table('professionals').select('*').limit(5).execute()
    if result.data:
        for i, prof in enumerate(result.data, 1):
            print(f"\n    [{i}] {prof.get('full_name', 'N/A')}")
            print(f"        ID: {prof.get('id')}")
            print(f"        Email: {prof.get('email', 'N/A')}")
            print(f"        Specialty: {prof.get('specialty', 'N/A')}")
            print(f"        CPF: {prof.get('cpf', 'N/A')}")
            print(f"        Status: {prof.get('status', 'N/A')}")
    else:
        print("    Nenhum profissional encontrado")
except Exception as e:
    print(f"    Erro: {e}")

# Contar por specialty
print("\n[3] Profissionais por Especialidade...")
try:
    result = client.table('professionals').select('specialty').execute()
    if result.data:
        specialties = {}
        for prof in result.data:
            spec = prof.get('specialty', 'Não informado')
            specialties[spec] = specialties.get(spec, 0) + 1

        for spec, count in sorted(specialties.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {spec}: {count}")
    else:
        print("    Nenhum profissional encontrado")
except Exception as e:
    print(f"    Erro: {e}")

# Sync log
print("\n[4] Sync Log...")
try:
    result = client.table('sync_log').select('*').execute()
    if result.data:
        for log in result.data:
            print(f"\n    Entity: {log.get('entity_type')}")
            print(f"    Count: {log.get('last_sync_count')}")
            print(f"    Status: {log.get('status')}")
            print(f"    Last Sync: {log.get('last_sync_time')}")
    else:
        print("    Nenhum log encontrado")
except Exception as e:
    print(f"    Erro: {e}")

print("\n" + "=" * 80)
