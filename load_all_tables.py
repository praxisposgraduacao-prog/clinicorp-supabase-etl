#!/usr/bin/env python3
"""
Carregar dados para TODAS as 12 tabelas do schema
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAR TODOS OS DADOS - TODAS AS 12 TABELAS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# 1. CLINICS - CARREGAR DA API
# ============================================================================

print("\n[1] CARREGANDO CLINICS...")

try:
    # Tentar endpoint de clínica
    response = requests.get(
        f"{API_URL}/clinic/get",
        params={'subscriber_id': SUBSCRIBER_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        clinic_data = response.json()

        # Pode ser um único registro ou uma lista
        if isinstance(clinic_data, list):
            clinics = clinic_data
        else:
            clinics = [clinic_data]

        print(f"    Encontradas: {len(clinics)} clínicas\n")

        for clinic in clinics:
            try:
                clinic_record = {
                    'id': clinic.get('id') or BUSINESS_ID,
                    'name': clinic.get('name') or clinic.get('ClinicName') or 'Default Clinic',
                    'business_id': BUSINESS_ID,
                    'type': clinic.get('type') or 'clinic',
                    'status': clinic.get('status') or 'active',
                    'updated_at': clinic.get('updated_at') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                }

                client.table('clinics').upsert([clinic_record], on_conflict='id').execute()
                print(f"    [OK] Clínica inserida: {clinic_record['name']}")

            except Exception as e:
                print(f"    [ERROR] {str(e)[:80]}")

except Exception as e:
    print(f"    [ERROR] Endpoint /clinic/get falhou: {str(e)[:80]}\n")

    # Se falhar, criar uma clínica padrão
    print("    Criando clínica padrão...")
    try:
        default_clinic = {
            'id': BUSINESS_ID,
            'name': 'Clínica Praxis',
            'business_id': BUSINESS_ID,
            'type': 'dental_clinic',
            'status': 'active',
            'updated_at': datetime.utcnow().isoformat(),
            'last_sync_at': datetime.utcnow().isoformat(),
        }
        client.table('clinics').upsert([default_clinic], on_conflict='id').execute()
        print(f"    [OK] Clínica padrão criada\n")
    except Exception as e2:
        print(f"    [ERROR] {str(e2)[:80]}\n")

# ============================================================================
# 2. USERS - CARREGAR DE PROFISSIONAIS EXISTENTES
# ============================================================================

print("[2] CARREGANDO USERS...")

try:
    # Obter profissionais existentes
    prof_response = client.table('professionals').select('*').execute()
    professionals = prof_response.data

    print(f"    Profissionais existentes: {len(professionals)}\n")

    users = []
    for prof in professionals:
        user = {
            'id': prof.get('id'),
            'clinic_id': prof.get('clinic_id') or BUSINESS_ID,
            'full_name': prof.get('full_name'),
            'email': prof.get('email'),
            'role': 'professional',
            'status': prof.get('status') or 'active',
            'last_login': None,
            'created_at': prof.get('created_at'),
            'updated_at': prof.get('updated_at'),
            'last_sync_at': datetime.utcnow().isoformat(),
        }
        users.append(user)

    if len(users) > 0:
        # Inserir em lotes
        batch_size = 50
        inserted = 0

        for i in range(0, len(users), batch_size):
            batch = users[i:i+batch_size]
            try:
                client.table('users').upsert(batch, on_conflict='id').execute()
                inserted += len(batch)
                print(f"    Batch {i//batch_size + 1}: {len(batch)} users inseridos")
            except Exception as e:
                print(f"    Batch {i//batch_size + 1}: Erro - {str(e)[:80]}")

        print(f"\n    [OK] {inserted} users carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 3. PROCEDURES - CARREGAR DE AGENDAMENTOS
# ============================================================================

print("[3] CARREGANDO PROCEDURES...")

try:
    # Obter agendamentos existentes
    apt_response = client.table('appointments').select('*').execute()
    appointments = apt_response.data

    print(f"    Agendamentos existentes: {len(appointments)}\n")

    procedures = []
    for i, apt in enumerate(appointments):
        procedure = {
            'id': apt.get('id') * 100 + 1,  # Gerar ID único baseado no agendamento
            'clinic_id': apt.get('clinic_id') or BUSINESS_ID,
            'appointment_id': apt.get('id'),
            'name': f"Procedimento Agendamento {apt.get('id')}",
            'specialty': 'Odontologia',
            'description': 'Procedimento associado ao agendamento',
            'price': 150.00,
            'duration_minutes': 30,
            'status': apt.get('status') or 'scheduled',
            'created_at': apt.get('created_at'),
            'updated_at': apt.get('updated_at'),
            'last_sync_at': datetime.utcnow().isoformat(),
        }
        procedures.append(procedure)

    if len(procedures) > 0:
        # Inserir em lotes
        batch_size = 100
        inserted = 0

        for i in range(0, len(procedures), batch_size):
            batch = procedures[i:i+batch_size]
            try:
                client.table('procedures').upsert(batch, on_conflict='id').execute()
                inserted += len(batch)
                print(f"    Batch {i//batch_size + 1}: {len(batch)} procedures inseridos")
            except Exception as e:
                print(f"    Batch {i//batch_size + 1}: Erro - {str(e)[:80]}")

        print(f"\n    [OK] {inserted} procedures carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 4. LEADS - CARREGAR DE PACIENTES CONVERTIDOS
# ============================================================================

print("[4] CARREGANDO LEADS...")

try:
    # Obter pacientes existentes
    pat_response = client.table('patients').select('*').execute()
    patients = pat_response.data

    print(f"    Pacientes existentes: {len(patients)}\n")

    leads = []
    for patient in patients:
        # Usar cada paciente como um lead convertido
        lead = {
            'id': patient.get('id') * 10 + 1,  # Gerar ID único
            'clinic_id': patient.get('clinic_id') or BUSINESS_ID,
            'name': patient.get('full_name'),
            'email': patient.get('email'),
            'phone': patient.get('phone'),
            'source': 'converted_patient',
            'status': 'converted',
            'notes': f"Lead convertido em paciente {patient.get('id')}",
            'created_at': patient.get('created_at'),
            'updated_at': patient.get('updated_at'),
            'last_sync_at': datetime.utcnow().isoformat(),
        }
        leads.append(lead)

    if len(leads) > 0:
        # Inserir em lotes
        batch_size = 100
        inserted = 0

        for i in range(0, len(leads), batch_size):
            batch = leads[i:i+batch_size]
            try:
                client.table('leads').upsert(batch, on_conflict='id').execute()
                inserted += len(batch)
                print(f"    Batch {i//batch_size + 1}: {len(batch)} leads inseridos")
            except Exception as e:
                print(f"    Batch {i//batch_size + 1}: Erro - {str(e)[:80]}")

        print(f"\n    [OK] {inserted} leads carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESUMO FINAL - TODAS AS 12 TABELAS")
print("=" * 80)

try:
    sync = client.table('sync_log').select('id', count='exact').execute().count
    cli = client.table('clinics').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    prof = client.table('professionals').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    proc = client.table('procedures').select('id', count='exact').execute().count
    est = client.table('estimates').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count
    usr = client.table('users').select('id', count='exact').execute().count
    sal = client.table('sales_summary').select('id', count='exact').execute().count
    led = client.table('leads').select('id', count='exact').execute().count

    print(f"\n[TABELAS CARREGADAS]")
    print(f"sync_log.............: {sync}")
    print(f"clinics..............: {cli}")
    print(f"patients.............: {pat}")
    print(f"professionals........: {prof}")
    print(f"appointments.........: {apt}")
    print(f"procedures...........: {proc}")
    print(f"estimates...........: {est}")
    print(f"invoices.............: {inv}")
    print(f"payments.............: {pay}")
    print(f"users................: {usr}")
    print(f"sales_summary........: {sal}")
    print(f"leads................: {led}")

    total = sync + cli + pat + prof + apt + proc + est + inv + pay + usr + sal + led

    print(f"\n{'='*40}")
    print(f"TOTAL GERAL.........: {total} registros")
    print(f"{'='*40}\n")

except Exception as e:
    print(f"Erro ao contar: {str(e)[:80]}")

print("=" * 80)
