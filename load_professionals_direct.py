#!/usr/bin/env python3
"""
Carrega profissionais diretamente com INSERT (ignorando duplicatas)
"""

import os
from dotenv import load_dotenv
import db_client
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

# Credenciais
API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))

print("=" * 80)
print("CARREGANDO PROFISSIONAIS DO CLINICORP PARA SUPABASE")
print("=" * 80)

# 1. Buscar profissionais da API
print("\n[1] Buscando profissionais da API...")
try:
    response = requests.get(
        f"{API_URL}/professional/list_all_professionals",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=10
    )

    if response.status_code != 200:
        print(f"    Erro: Status {response.status_code}")
        exit(1)

    professionals = response.json()
    print(f"    Total obtido: {len(professionals)} profissionais")

except Exception as e:
    print(f"    Erro: {e}")
    exit(1)

# 2. Preparar dados
print("\n[2] Preparando dados...")
data_to_insert = []
for prof in professionals:
    data_to_insert.append({
        'id': prof.get('id'),
        'clinic_id': BUSINESS_ID,
        'full_name': prof.get('name'),
        'cpf': prof.get('cpf'),
        'email': None,
        'phone': None,
        'license_number': None,
        'specialty': None,
        'status': None,
        'updated_at': None,
        'last_sync_at': None,
        '_sync_id': None,
    })

print(f"    Dados preparados: {len(data_to_insert)} registros")

# 3. Inserir no banco local
print("\n[3] Inserindo no banco local...")
try:
    n = db_client.upsert('professionals', data_to_insert, conflict_col='id')
    print(f"    Sucesso! {n} inseridos")

except Exception as e:
    print(f"    Erro: {str(e)[:200]}")
    exit(1)

# 4. Verificar
print("\n[4] Verificando carga...")
try:
    total = db_client.count('professionals')
    print(f"    Total no banco: {total} profissionais")

    if total > 0:
        print("\nSUCESSO! Profissionais carregados com sucesso!")
    else:
        print("\nNenhum profissional foi carregado")

except Exception as e:
    print(f"    Erro na verificação: {e}")

print("\n" + "=" * 80)
