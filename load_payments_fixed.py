#!/usr/bin/env python3
"""
Script corrigido: Carregar pagamentos com campos corretos da API
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
print("CARREGAMENTO PAGAMENTOS - CAMPOS CORRETOS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\n[*] Periodo: {date_from} a {date_to}\n")

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
        print(f"[1] API retornou: {len(payments)} pagamentos")

        if len(payments) > 0:
            # Coletar clinics, invoices, patients
            clinic_ids = set()
            invoice_ids = set()
            patient_ids = set()

            for pay in payments:
                clinic_id = pay.get('ReceiverBusinessId', BUSINESS_ID)
                clinic_ids.add(clinic_id)
                patient_id = pay.get('PatientId')
                if patient_id:
                    patient_ids.add(patient_id)
                # Pagamentos não têm invoice_id direto, vamos pular

            # Criar clínicas
            if clinic_ids:
                print(f"[2] Criando {len(clinic_ids)} clínicas...")
                clinic_data = []
                for cid in clinic_ids:
                    clinic_data.append({
                        'id': cid,
                        'business_id': cid,
                        'name': f"Clinic {cid}",
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })
                try:
                    client.table('clinics').upsert(clinic_data, on_conflict='id').execute()
                    print(f"    OK")
                except Exception as e:
                    print(f"    WARN: {str(e)[:60]}")

            # Criar pacientes
            if patient_ids:
                print(f"[3] Criando {len(patient_ids)} pacientes...")
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
                    print(f"    OK")
                except Exception as e:
                    print(f"    WARN: {str(e)[:60]}")

            # Inserir pagamentos com campos corretos
            print(f"[4] Inserindo {len(payments)} pagamentos...")
            data = []
            for pay in payments:
                data.append({
                    'id': pay.get('PaymentHeaderId'),  # Campo correto!
                    'clinic_id': pay.get('ReceiverBusinessId', BUSINESS_ID),  # Campo correto!
                    'invoice_id': None,  # Não disponível na API
                    'patient_id': pay.get('PatientId'),
                    'amount': float(pay.get('Amount', 0)),
                    'payment_method': pay.get('CreditCardType') or 'unknown',
                    'payment_date': pay.get('PaymentDate'),
                    'reference': pay.get('ExternalId') or '',
                    'status': 'completed' if pay.get('PaymentReceived') == 'X' else 'pending',
                    'notes': pay.get('PayerName') or '',
                    'updated_at': pay.get('ConfirmedDate') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            # Tentar em lotes para melhorar robustez
            batch_size = 50
            inserted_count = 0

            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    client.table('payments').insert(batch).execute()
                    inserted_count += len(batch)
                except Exception as e:
                    error_msg = str(e)
                    if 'duplicate key' in error_msg or 'already exists' in error_msg:
                        # Se é erro de duplicata, tentar fazer upsert individual
                        print(f"    [INFO] Batch {i//batch_size + 1}: Erro de duplicata, tentando updates")
                        for record in batch:
                            try:
                                client.table('payments').update(record).eq('id', record['id']).execute()
                                inserted_count += 1
                            except:
                                pass
                    else:
                        print(f"    [ERROR] Batch {i//batch_size + 1}: {error_msg[:80]}")

            print(f"    [OK] {inserted_count} pagamentos processados!")
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
    payments = client.table('payments').select('id', count='exact').execute().count
    print(f"\n[RESULTADO]")
    print(f"Pagamentos no banco: {payments}")

except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
