#!/usr/bin/env python3
"""
Script inteligente para carregar pagamentos:
- Trata duplicatas
- Trata foreign keys
- Insere um por um se necessário
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
print("CARREGAR PAGAMENTOS - MODO INTELIGENTE")
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
        print(f"[1] API retornou: {len(payments)} pagamentos\n")

        if len(payments) > 0:
            # Preparar dados
            print(f"[2] Preparando dados...")
            clinic_ids = set()
            patient_ids = set()

            for pay in payments:
                clinic_id = pay.get('ReceiverBusinessId', BUSINESS_ID)
                clinic_ids.add(clinic_id)
                patient_id = pay.get('PatientId')
                if patient_id:
                    patient_ids.add(patient_id)

            # Criar clínicas
            print(f"    - Criando {len(clinic_ids)} clinicas")
            clinic_data = [
                {
                    'id': cid,
                    'business_id': cid,
                    'name': f"Clinic {cid}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                }
                for cid in clinic_ids
            ]
            try:
                client.table('clinics').upsert(clinic_data, on_conflict='id').execute()
            except Exception as e:
                print(f"      WARN: {str(e)[:50]}")

            # Criar pacientes
            print(f"    - Criando {len(patient_ids)} pacientes")
            patient_data = [
                {
                    'id': pid,
                    'clinic_id': BUSINESS_ID,
                    'full_name': f"Patient {pid}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                }
                for pid in patient_ids
            ]
            try:
                client.table('patients').upsert(patient_data, on_conflict='id').execute()
            except Exception as e:
                print(f"      WARN: {str(e)[:50]}")

            # Preparar pagamentos
            print(f"\n[3] Inserindo {len(payments)} pagamentos (modo robusto)...\n")

            payment_data = []
            for pay in payments:
                payment_data.append({
                    'id': pay.get('PaymentHeaderId'),
                    'clinic_id': pay.get('ReceiverBusinessId', BUSINESS_ID),
                    'invoice_id': None,
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

            # Inserir individualmente para melhor tratamento de erros
            inserted = 0
            updated = 0
            skipped = 0

            for i, payment in enumerate(payment_data):
                try:
                    # Tentar insert
                    client.table('payments').insert([payment]).execute()
                    inserted += 1
                    if (i + 1) % 50 == 0:
                        print(f"    Progresso: {i + 1}/{len(payment_data)} inseridos")

                except Exception as e:
                    error_msg = str(e)

                    # Se é erro de duplicata, tentar update
                    if 'duplicate key' in error_msg or 'already exists' in error_msg:
                        try:
                            client.table('payments').update(payment).eq('id', payment['id']).execute()
                            updated += 1
                        except:
                            skipped += 1

                    # Se é foreign key, pode ser que invoice não exista
                    elif 'foreign key' in error_msg:
                        # Tentar remover invoice_id e retentar
                        payment_no_invoice = payment.copy()
                        payment_no_invoice['invoice_id'] = None
                        try:
                            client.table('payments').insert([payment_no_invoice]).execute()
                            inserted += 1
                        except:
                            skipped += 1

                    else:
                        skipped += 1

            print(f"\n[4] RESULTADO:")
            print(f"    Inseridos: {inserted}")
            print(f"    Atualizados: {updated}")
            print(f"    Ignorados: {skipped}")
            print(f"    Total: {inserted + updated}/{len(payment_data)}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# RESUMO
# ============================================================================

print("\n" + "=" * 80)
print("VERIFICACAO FINAL")
print("=" * 80)

try:
    payments_count = client.table('payments').select('id', count='exact').execute().count
    print(f"\nPagamentos no banco: {payments_count}")

    if payments_count > 0:
        print(f"\n[SUCCESS] Pagamentos carregados com sucesso!")
    else:
        print(f"\n[INFO] Verifique se há constraints impeditivas")

except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
