#!/usr/bin/env python3
"""
Carregamento final de pagamentos - Limpar tudo e reinserir
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
import time

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAMENTO FINAL DE PAGAMENTOS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\n[1] OBTENDO PAGAMENTOS DA API...")

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
        print(f"    OK - {len(payments)} pagamentos obtidos\n")

        if len(payments) > 0:
            # Limpar tabela de pagamentos
            print(f"[2] LIMPANDO TABELA DE PAGAMENTOS...")
            try:
                client.table('payments').delete().neq('id', 0).execute()
                print(f"    OK\n")
                time.sleep(1)  # Aguardar um pouco
            except Exception as e:
                print(f"    WARN: {str(e)[:60]}\n")

            # Preparar dados
            print(f"[3] PREPARANDO {len(payments)} PAGAMENTOS...")

            payment_data = []
            clinic_ids = set()
            patient_ids = set()

            for pay in payments:
                clinic_id = pay.get('ReceiverBusinessId', BUSINESS_ID)
                clinic_ids.add(clinic_id)
                patient_id = pay.get('PatientId')
                if patient_id:
                    patient_ids.add(patient_id)

                payment_data.append({
                    'id': pay.get('PaymentHeaderId'),
                    'clinic_id': clinic_id,
                    'invoice_id': None,
                    'patient_id': patient_id,
                    'amount': float(pay.get('Amount', 0)),
                    'payment_method': pay.get('CreditCardType') or 'unknown',
                    'payment_date': pay.get('PaymentDate'),
                    'reference': pay.get('ExternalId') or '',
                    'status': 'completed' if pay.get('PaymentReceived') == 'X' else 'pending',
                    'notes': pay.get('PayerName') or '',
                    'updated_at': pay.get('ConfirmedDate') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            print(f"    OK\n")

            # Garantir clinicas
            print(f"[4] GARANTINDO {len(clinic_ids)} CLINICAS EXISTEM...")
            clinic_data_list = []
            for cid in clinic_ids:
                clinic_data_list.append({
                    'id': cid,
                    'business_id': cid,
                    'name': f"Clinic {cid}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('clinics').upsert(clinic_data_list, on_conflict='id').execute()
                print(f"    OK\n")
            except Exception as e:
                print(f"    WARN: {str(e)[:60]}\n")

            # Garantir pacientes
            print(f"[5] GARANTINDO {len(patient_ids)} PACIENTES EXISTEM...")
            patient_data_list = []
            for pid in patient_ids:
                patient_data_list.append({
                    'id': pid,
                    'clinic_id': BUSINESS_ID,
                    'full_name': f"Patient {pid}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('patients').upsert(patient_data_list, on_conflict='id').execute()
                print(f"    OK\n")
            except Exception as e:
                print(f"    WARN: {str(e)[:60]}\n")

            # Inserir pagamentos em lotes
            print(f"[6] INSERINDO PAGAMENTOS EM LOTES DE 100...")

            batch_size = 100
            inserted = 0
            errors = 0

            for i in range(0, len(payment_data), batch_size):
                batch = payment_data[i:i+batch_size]
                batch_num = i // batch_size + 1

                try:
                    client.table('payments').insert(batch).execute()
                    inserted += len(batch)
                    print(f"    Batch {batch_num}: {len(batch)} inseridos")

                except Exception as e:
                    error_msg = str(e)
                    if 'duplicate' in error_msg:
                        # Se duplicata, tentar fazer update
                        for record in batch:
                            try:
                                # Tentar atualizar
                                existing = client.table('payments').select('id').eq('id', record['id']).execute()
                                if len(existing.data) > 0:
                                    client.table('payments').update(record).eq('id', record['id']).execute()
                                    inserted += 1
                            except:
                                errors += 1
                    else:
                        print(f"    Batch {batch_num}: ERRO - {error_msg[:60]}")
                        errors += len(batch)

            print(f"\n    Total Inserido/Atualizado: {inserted}")
            print(f"    Erros: {errors}\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# RESULTADO
# ============================================================================

print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

try:
    count = client.table('payments').select('id', count='exact').execute().count
    print(f"\nPagamentos no banco: {count}")

    if count > 0:
        print(f"\n[SUCCESS] ✅ {count} pagamentos carregados!")
    else:
        print(f"\n[WARNING] Nenhum pagamento foi inserido - verifique constraints")

except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
