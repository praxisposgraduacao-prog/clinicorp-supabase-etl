#!/usr/bin/env python3
"""
Script final: Carrega todos os dados disponíveis do Clinicorp para Supabase
- Profissionais: 140 registros
- Procedures: Estrutura especial (tabelas por especialidade)
- Qualquer outro dado acessível sem subscriber_id
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

load_dotenv()

# Credenciais
API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAMENTO COMPLETO - TODOS OS DADOS DISPONÍVEIS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# 1. PROFISSIONAIS (140 registros)
# ============================================================================

print("\n[1] PROFISSIONAIS")
print("-" * 80)

try:
    response = requests.get(
        f"{API_URL}/professional/list_all_professionals",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=10
    )

    if response.status_code == 200:
        professionals = response.json()
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
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        # Deletar existentes e inserir novos
        try:
            client.table('professionals').delete().gte('id', 0).execute()
        except:
            pass

        result = client.table('professionals').insert(data_to_insert).execute()
        count = len(result.data) if result.data else len(data_to_insert)
        print(f"[OK] Profissionais carregados: {count}")

except Exception as e:
    print(f"[ERROR] Erro ao carregar profissionais: {str(e)[:100]}")

# ============================================================================
# 2. PROCEDURES (Estrutura especial: dict com tabelas por especialidade)
# ============================================================================

print("\n[2] PROCEDIMENTOS")
print("-" * 80)

try:
    response = requests.get(
        f"{API_URL}/procedures/list",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()

        # A API retorna um dict com as tabelas de procedimentos por especialidade
        # Ex: {"DRA ANDREZZA RABELO": [...], "ENDO": [...], ...}

        if isinstance(data, dict):
            all_procedures = []
            procedure_id = 1

            for specialty, procedures_list in data.items():
                if isinstance(procedures_list, list):
                    for proc in procedures_list:
                        all_procedures.append({
                            'id': procedure_id,
                            'clinic_id': BUSINESS_ID,
                            'appointment_id': None,
                            'name': proc.get('name') or proc.get('descricao') if isinstance(proc, dict) else str(proc),
                            'specialty': specialty,
                            'description': None,
                            'price': proc.get('price') or proc.get('valor') if isinstance(proc, dict) else None,
                            'duration_minutes': None,
                            'status': 'active',
                            'updated_at': None,
                            'last_sync_at': datetime.utcnow().isoformat(),
                        })
                        procedure_id += 1

            if all_procedures:
                # Deletar existentes e inserir novos
                try:
                    client.table('procedures').delete().gte('id', 0).execute()
                except:
                    pass

                result = client.table('procedures').insert(all_procedures).execute()
                count = len(result.data) if result.data else len(all_procedures)
                print(f"[OK] Procedimentos carregados: {count}")
            else:
                print("[INFO] Nenhum procedimento encontrado na resposta")

except Exception as e:
    print(f"[ERROR] Erro ao carregar procedimentos: {str(e)[:100]}")

# ============================================================================
# 3. ESPECIALIDADES
# ============================================================================

print("\n[3] ESPECIALIDADES")
print("-" * 80)

try:
    response = requests.get(
        f"{API_URL}/procedures/list_specialties",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=10
    )

    if response.status_code == 200:
        specialties = response.json()
        print(f"[OK] Especialidades obtidas: {len(specialties) if isinstance(specialties, list) else 'Info disponivel'}")

except Exception as e:
    print(f"[ERROR] Erro ao obter especialidades: {str(e)[:100]}")

# ============================================================================
# 4. CATEGORIAS DE AGENDAMENTO
# ============================================================================

print("\n[4] CATEGORIAS DE AGENDAMENTO")
print("-" * 80)

try:
    response = requests.get(
        f"{API_URL}/appointment/list_categories",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=10
    )

    if response.status_code == 200:
        categories = response.json()
        print(f"[OK] Categorias obtidas: {len(categories) if isinstance(categories, list) else 'Info disponivel'}")

except Exception as e:
    print(f"[ERROR] Erro ao obter categorias: {str(e)[:100]}")

# ============================================================================
# RESUMO FINAL
# ============================================================================

print("\n" + "=" * 80)
print("RESUMO DO CARREGAMENTO")
print("=" * 80)

try:
    prof_count = client.table('professionals').select('id', count='exact').execute().count
    proc_count = client.table('procedures').select('id', count='exact').execute().count

    print(f"\n[RESULTADO] Profissionais: {prof_count}")
    print(f"[RESULTADO] Procedimentos: {proc_count}")
    print(f"\nTotal de registros carregados: {prof_count + proc_count}")

except Exception as e:
    print(f"Erro ao contar registros: {e}")

print("\n" + "=" * 80)
print("Para carregar outros dados (pacientes, agendamentos, financeiro),")
print("você precisará do subscriber_id correto da sua conta no Clinicorp.")
print("=" * 80)
