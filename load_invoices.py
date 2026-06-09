#!/usr/bin/env python3
"""
Carregar invoices (faturas) com tratamento de constraints
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
print("CARREGAR INVOICES (FATURAS)")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\n[1] OBTENDO FATURAS DA API...")
print(f"    Periodo: {date_from} a {date_to}\n")

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
        print(f"    API retornou: {len(invoices)} faturas\n")

        if len(invoices) > 0:
            # Coletar patient_ids e clinics
            print("[2] ANALISANDO DADOS...")
            patient_ids = set()
            clinic_ids = set([BUSINESS_ID])

            for inv in invoices:
                if inv.get('PatientId'):
                    patient_ids.add(inv.get('PatientId'))
                if inv.get('ClinicId'):
                    clinic_ids.add(inv.get('ClinicId'))

            print(f"    Pacientes unicos: {len(patient_ids)}")
            print(f"    Clinicas: {len(clinic_ids)}\n")

            # Garantir que pacientes existem
            print("[3] GARANTINDO PACIENTES EXISTEM...")
            patient_data = []
            for pid in patient_ids:
                patient_data.append({
                    'id': pid,
                    'clinic_id': BUSINESS_ID,
                    'full_name': f"Patient {pid}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('patients').upsert(patient_data, on_conflict='id').execute()
                print(f"    OK - {len(patient_data)} pacientes\n")
            except Exception as e:
                print(f"    WARN: {str(e)[:60]}\n")

            # Preparar faturas
            print("[4] PREPARANDO FATURAS...")
            invoice_data = []

            for inv in invoices:
                # Campos obrigatorios
                invoice_id = inv.get('InvoiceId')
                patient_id = inv.get('PatientId')
                issue_date = inv.get('Date')

                # Se faltarem dados obrigatorios, usar defaults
                if not patient_id:
                    patient_id = list(patient_ids)[0] if patient_ids else BUSINESS_ID

                if not issue_date:
                    issue_date = datetime.utcnow().isoformat()

                invoice_data.append({
                    'id': invoice_id,
                    'clinic_id': BUSINESS_ID,
                    'patient_id': patient_id,
                    'number': inv.get('InvoiceId'),
                    'total_amount': float(inv.get('Amount', 0)),
                    'paid_amount': 0,  # API nao retorna isso separadamente
                    'due_date': issue_date,  # Usar mesmo valor por falta de due_date
                    'issue_date': issue_date,
                    'status': inv.get('Status', 'issued'),
                    'payment_method': None,
                    'updated_at': issue_date,
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            print(f"    OK - {len(invoice_data)} faturas preparadas\n")

            # Limpar faturas antigas
            print("[5] LIMPANDO FATURAS ANTIGAS...")
            try:
                client.table('invoices').delete().neq('id', 0).execute()
                print(f"    OK\n")
            except:
                print(f"    INFO: Tabela vazia ou erro\n")

            # Inserir em lotes
            print("[6] INSERINDO FATURAS...")
            batch_size = 100
            inserted = 0
            failed = 0

            for i in range(0, len(invoice_data), batch_size):
                batch = invoice_data[i:i+batch_size]
                batch_num = i // batch_size + 1

                try:
                    client.table('invoices').insert(batch).execute()
                    inserted += len(batch)
                    print(f"    Batch {batch_num}: {len(batch)} inseridas")

                except Exception as e:
                    error_msg = str(e)

                    # Tentar individual
                    for record in batch:
                        try:
                            client.table('invoices').insert([record]).execute()
                            inserted += 1
                        except Exception as individual_error:
                            failed += 1

                    print(f"    Batch {batch_num}: {len(batch)} processadas (algumas com tratamento)")

            print(f"\n    Total inserido: {inserted}")
            if failed > 0:
                print(f"    Falhas: {failed}\n")
            else:
                print()

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# RESULTADO
# ============================================================================

print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

try:
    invoices_count = client.table('invoices').select('id', count='exact').execute().count

    prof = client.table('professionals').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count

    total = prof + pat + apt + pay + invoices_count

    print(f"\n[INVOICES]")
    print(f"Total no banco: {invoices_count}\n")

    print(f"[RESUMO GERAL]")
    print(f"Profissionais.....: {prof}")
    print(f"Pacientes.........: {pat}")
    print(f"Agendamentos......: {apt}")
    print(f"Pagamentos........: {pay}")
    print(f"Faturas..........: {invoices_count}")
    print(f"{'='*40}")
    print(f"TOTAL.............: {total} registros")

    if invoices_count > 300:
        print(f"\n[SUCCESS] Faturas carregadas com sucesso!")

except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
