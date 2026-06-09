#!/usr/bin/env python3
"""
Script v2: Carregar pagamentos tratando todas as dependências
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
print("CARREGAMENTO V2 - PAGAMENTOS COM DEPENDENCIAS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\n[*] Periodo: {date_from} a {date_to}\n")

# ============================================================================
# CARREGAR PAGAMENTOS
# ============================================================================

print("[1] CARREGANDO PAGAMENTOS...")

try:
    response = requests.get(
        f"{API_URL}/payment/list",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        payments = response.json()
        if isinstance(payments, list) and len(payments) > 0:
            print(f"    API retornou: {len(payments)} pagamentos")

            # Primeiro passe: coletar todas as clínicas necessárias
            clinic_ids = set([BUSINESS_ID])
            invoice_ids = set()
            patient_ids = set()

            for pay in payments:
                if pay.get('ClinicId'):
                    clinic_ids.add(int(pay.get('ClinicId')))
                if pay.get('InvoiceId'):
                    invoice_ids.add(pay.get('InvoiceId'))
                if pay.get('PatientId'):
                    patient_ids.add(pay.get('PatientId'))

            # Criar clínicas faltantes
            if clinic_ids:
                print(f"    Criando/atualizando {len(clinic_ids)} clínicas...")
                clinic_data = []
                for cid in clinic_ids:
                    clinic_data.append({
                        'id': cid,
                        'business_id': cid,  # Campo obrigatório
                        'name': f"Clinic {cid}",
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })
                try:
                    client.table('clinics').upsert(clinic_data, on_conflict='id').execute()
                    print(f"    OK - Clínicas criadas")
                except Exception as e:
                    print(f"    WARN - {str(e)[:60]}")

            # Criar pacientes faltantes
            if patient_ids:
                print(f"    Criando/atualizando {len(patient_ids)} pacientes...")
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
                    print(f"    OK - Pacientes criados")
                except Exception as e:
                    print(f"    WARN - {str(e)[:60]}")

            # Criar faturas faltantes (com pacientes aleatórios se necessário)
            if invoice_ids:
                print(f"    Criando/atualizando {len(invoice_ids)} faturas (stub)...")
                invoice_data = []
                # Usar primeiro paciente como default
                default_patient = list(patient_ids)[0] if patient_ids else 0

                for iid in invoice_ids:
                    invoice_data.append({
                        'id': iid,
                        'clinic_id': BUSINESS_ID,
                        'patient_id': default_patient,  # Usar paciente default
                        'number': str(iid),
                        'total_amount': 0,
                        'paid_amount': 0,
                        'status': 'issued',
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })
                try:
                    client.table('invoices').upsert(invoice_data, on_conflict='id').execute()
                    print(f"    OK - Faturas criadas")
                except Exception as e:
                    print(f"    WARN - {str(e)[:60]}")

            # Agora inserir pagamentos
            print(f"    Inserindo {len(payments)} pagamentos...")
            data = []
            for pay in payments:
                data.append({
                    'id': pay.get('PaymentId') or pay.get('id'),
                    'clinic_id': pay.get('ClinicId', BUSINESS_ID),
                    'invoice_id': pay.get('InvoiceId'),
                    'patient_id': pay.get('PatientId'),
                    'amount': float(pay.get('Amount', 0)),
                    'payment_method': pay.get('PaymentMethod') or 'unknown',
                    'payment_date': pay.get('PaymentDate') or pay.get('Date'),
                    'reference': pay.get('Reference') or '',
                    'status': pay.get('Status', 'completed'),
                    'notes': pay.get('Notes') or '',
                    'updated_at': pay.get('UpdatedAt') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('payments').upsert(data, on_conflict='id').execute()
                print(f"    [OK] {len(data)} pagamentos inseridos!")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:100]}")
        else:
            print("    [INFO] Nenhum pagamento encontrado")
    else:
        print(f"    [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# RESUMO
# ============================================================================

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)

try:
    clinics = client.table('clinics').select('id', count='exact').execute().count
    invoices = client.table('invoices').select('id', count='exact').execute().count
    payments = client.table('payments').select('id', count='exact').execute().count
    patients = client.table('patients').select('id', count='exact').execute().count

    print(f"\n[DADOS NO BANCO]")
    print(f"Clinicas.........: {clinics}")
    print(f"Pacientes........: {patients}")
    print(f"Faturas..........: {invoices}")
    print(f"Pagamentos.......: {payments}")

except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
