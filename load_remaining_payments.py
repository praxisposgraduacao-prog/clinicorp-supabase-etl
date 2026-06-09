#!/usr/bin/env python3
"""
Carregar os pagamentos restantes com tratamento robusto
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
print("CARREGAR PAGAMENTOS RESTANTES")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print("\n[1] OBTENDO PAGAMENTOS DA API...")

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
        print(f"    Total: {len(payments)} pagamentos da API\n")

        # Verificar quantos ja existem
        print("[2] VERIFICANDO DADOS EXISTENTES...")
        try:
            existing = client.table('payments').select('id').execute()
            existing_ids = set(p['id'] for p in existing.data)
            print(f"    Ja existem: {len(existing_ids)} pagamentos\n")
        except:
            existing_ids = set()
            print(f"    Nao foi possivel verificar\n")

        # Preparar lista de novos pagamentos
        print("[3] PREPARANDO NOVOS PAGAMENTOS...")
        new_payments = []
        skipped = 0

        for pay in payments:
            pay_id = pay.get('PaymentHeaderId')

            if pay_id not in existing_ids:
                # Verificar campos obrigatorios
                if pay.get('PatientId') is None:
                    # Usar um paciente default se nao houver
                    patient_id = BUSINESS_ID
                    skipped += 1
                else:
                    patient_id = pay.get('PatientId')

                new_payments.append({
                    'id': pay_id,
                    'clinic_id': pay.get('ReceiverBusinessId', BUSINESS_ID),
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

        print(f"    Novos pagamentos: {len(new_payments)}")
        if skipped > 0:
            print(f"    Precisaram de default patient: {skipped}\n")
        else:
            print()

        # Inserir em lotes, com tratamento individual
        print("[4] INSERINDO PAGAMENTOS EM LOTES...")

        batch_size = 50
        inserted = 0
        failed = 0

        for i in range(0, len(new_payments), batch_size):
            batch = new_payments[i:i+batch_size]
            batch_num = i // batch_size + 1

            try:
                result = client.table('payments').insert(batch).execute()
                inserted += len(batch)
                print(f"    Batch {batch_num}: {len(batch)} inseridos")

            except Exception as e:
                error_msg = str(e)

                # Tentar individual
                for record in batch:
                    try:
                        client.table('payments').insert([record]).execute()
                        inserted += 1
                    except Exception as individual_error:
                        # Se mesmo assim falhar, pode ser falta de patient
                        if 'patient_id' in str(individual_error) and record['patient_id'] == BUSINESS_ID:
                            # Tentar com NULL
                            record['patient_id'] = None
                            try:
                                client.table('payments').insert([record]).execute()
                                inserted += 1
                            except:
                                failed += 1
                        else:
                            failed += 1

                print(f"    Batch {batch_num}: {len(batch)} processados (alguns com tratamento especial)")

        print(f"\n    Total inserido: {inserted}")
        print(f"    Falhas: {failed}\n")

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

    prof = client.table('professionals').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count

    total = prof + pat + apt + count

    print(f"\n[PAGAMENTOS]")
    print(f"Total no banco: {count}\n")

    print(f"[RESUMO GERAL]")
    print(f"Profissionais.....: {prof}")
    print(f"Pacientes.........: {pat}")
    print(f"Agendamentos......: {apt}")
    print(f"Pagamentos........: {count}")
    print(f"{'='*40}")
    print(f"TOTAL.............: {total} registros")

    if count >= 400:
        print(f"\n[SUCCESS] Pagamentos carregados com sucesso!")

except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
