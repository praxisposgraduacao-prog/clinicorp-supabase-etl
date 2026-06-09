#!/usr/bin/env python3
"""
Script para carregar todos os dados da API Clinicorp - Versão 3
Com tratamento correto de integridade referencial
"""

import os
import sys
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
print("CARREGAMENTO COMPLETO V3 - CLINICORP ETL")
print("=" * 80)

if not SUBSCRIBER_ID:
    print("\n[!] Erro: ERP_CLINICORP_SUBSCRIBER_ID nao configurado no .env\n")
    sys.exit(1)

print(f"\n[OK] Subscriber ID: {SUBSCRIBER_ID}\n")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Datas para consultas (últimos 30 dias)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"[*] Periodo: {date_from} a {date_to}\n")

# ============================================================================
# 0. VERIFICAR DADOS EXISTENTES
# ============================================================================

print("[0] VERIFICANDO DADOS EXISTENTES...")
try:
    patients_count = client.table('patients').select('id', count='exact').execute().count
    professionals_count = client.table('professionals').select('id', count='exact').execute().count
    print(f"    Pacientes no BD: {patients_count}")
    print(f"    Profissionais no BD: {professionals_count}\n")
except Exception as e:
    print(f"    [WARN] Nao consegui verificar: {str(e)[:50]}\n")

# ============================================================================
# 1. AGENDAMENTOS
# ============================================================================

print("[1] CARREGANDO AGENDAMENTOS...")

try:
    response = requests.get(
        f"{API_URL}/appointment/list",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'businessId': BUSINESS_ID,
            'includeCanceled': True
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        appointments = response.json()
        if isinstance(appointments, list) and len(appointments) > 0:
            print(f"    API retornou: {len(appointments)} agendamentos")

            # Primeiro, vamos inserir pacientes faltantes
            patient_ids = set()
            for a in appointments:
                pid = a.get('Patient_PersonId')
                if pid:
                    patient_ids.add(pid)

            if patient_ids:
                print(f"    Criando registros de pacientes faltantes...")
                patient_data = []
                for pid in patient_ids:
                    patient_data.append({
                        'id': pid,
                        'clinic_id': BUSINESS_ID,
                        'full_name': f"Paciente {pid}",
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })

                try:
                    client.table('patients').upsert(patient_data, on_conflict='id').execute()
                    print(f"    Criados/atualizados {len(patient_data)} pacientes")
                except Exception as e:
                    print(f"    [WARN] Erro ao inserir pacientes: {str(e)[:80]}")

            # Agora inserir agendamentos
            data = []
            for a in appointments:
                data.append({
                    'id': a.get('AppointmentId') or a.get('id'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': a.get('Patient_PersonId'),
                    'professional_id': a.get('Dentist_PersonId') or a.get('ScheduleToId') or a.get('CreateUserId'),
                    'scheduled_date': a.get('date'),
                    'duration_minutes': 30,
                    'status': a.get('Status') or 'scheduled',
                    'notes': a.get('Notes'),
                    'reason_cancellation': None,
                    'updated_at': a.get('Date'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('appointments').upsert(data, on_conflict='id').execute()
                print(f"    [OK] Agendamentos: {len(data)} inseridos/atualizados")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:100]}")
        else:
            print("    [INFO] Nenhum agendamento encontrado")
    else:
        print(f"    [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# 2. FATURAS
# ============================================================================

print("\n[2] CARREGANDO FATURAS...")

try:
    response = requests.get(
        f"{API_URL}/financial/list_invoices",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        invoices = response.json()
        if isinstance(invoices, list) and len(invoices) > 0:
            print(f"    API retornou: {len(invoices)} faturas")

            # Inserir pacientes faltantes se necessário
            patient_ids = set()
            for inv in invoices:
                pid = inv.get('PatientId')
                if pid:
                    patient_ids.add(pid)

            if patient_ids:
                print(f"    Criando registros de pacientes faltantes...")
                patient_data = []
                for pid in patient_ids:
                    patient_data.append({
                        'id': pid,
                        'clinic_id': BUSINESS_ID,
                        'full_name': f"Paciente {pid}",
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })

                try:
                    client.table('patients').upsert(patient_data, on_conflict='id').execute()
                    print(f"    Criados/atualizados {len(patient_data)} pacientes")
                except Exception as e:
                    print(f"    [WARN] Erro ao inserir pacientes: {str(e)[:80]}")

            # Inserir faturas
            data = []
            for inv in invoices:
                data.append({
                    'id': inv.get('InvoiceId'),
                    'clinic_id': BUSINESS_ID,
                    'patient_id': inv.get('PatientId'),
                    'number': inv.get('InvoiceId'),
                    'total_amount': inv.get('Amount', 0),
                    'paid_amount': 0,
                    'due_date': inv.get('Date'),
                    'issue_date': inv.get('Date'),
                    'status': inv.get('Status', 'issued'),
                    'payment_method': None,
                    'updated_at': inv.get('Date'),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('invoices').upsert(data, on_conflict='id').execute()
                print(f"    [OK] Faturas: {len(data)} inseridas/atualizadas")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:100]}")
        else:
            print("    [INFO] Nenhuma fatura encontrada")
    else:
        print(f"    [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# 3. RESUMO FINAL
# ============================================================================

print("\n" + "=" * 80)
print("RESUMO FINAL")
print("=" * 80)

try:
    prof = client.table('professionals').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count

    total = prof + pat + apt + inv

    print(f"\n[DADOS CARREGADOS]")
    print(f"Profissionais: {prof}")
    print(f"Pacientes: {pat}")
    print(f"Agendamentos: {apt}")
    print(f"Faturas: {inv}")
    print(f"\nTOTAL: {total} registros")

    print(f"\n[PROXIMOS PASSOS]")
    print(f"1. Validar dados no Supabase")
    print(f"2. Se necessario, implementar sincronizacao incremental")
    print(f"3. Para pagamentos individuais, solicitar endpoint diferente ao suporte")

except Exception as e:
    print(f"Erro ao contar: {e}")

print("\n" + "=" * 80)
