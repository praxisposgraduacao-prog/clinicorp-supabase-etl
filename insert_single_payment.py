#!/usr/bin/env python3
"""
Inserir um único pagamento e capturar erro completo
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("INSERIR UM PAGAMENTO - DEBUG")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

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
        first_payment = payments[0]

        # Preparar registro
        payment_record = {
            'id': first_payment.get('PaymentHeaderId'),
            'clinic_id': BUSINESS_ID,  # Usar sempre o BUSINESS_ID
            'invoice_id': None,
            'patient_id': first_payment.get('PatientId'),
            'amount': float(first_payment.get('Amount', 0)),
            'payment_method': first_payment.get('CreditCardType') or 'unknown',
            'payment_date': first_payment.get('PaymentDate'),
            'reference': first_payment.get('ExternalId') or '',
            'status': 'completed' if first_payment.get('PaymentReceived') == 'X' else 'pending',
            'notes': first_payment.get('PayerName') or '',
            'updated_at': first_payment.get('ConfirmedDate') or datetime.utcnow().isoformat(),
            'last_sync_at': datetime.utcnow().isoformat(),
        }

        print(f"\n[INSERINDO PAGAMENTO]")
        print(f"ID: {payment_record['id']}")
        print(f"Clinic ID: {payment_record['clinic_id']}")
        print(f"Patient ID: {payment_record['patient_id']}")
        print(f"Amount: {payment_record['amount']}\n")

        try:
            # Verificar se paciente existe
            patient_check = client.table('patients').select('id').eq('id', payment_record['patient_id']).execute()
            if len(patient_check.data) > 0:
                print(f"[OK] Paciente existe na tabela")
            else:
                print(f"[WARN] Paciente nao existe, criando...")
                patient_data = {
                    'id': payment_record['patient_id'],
                    'clinic_id': BUSINESS_ID,
                    'full_name': f"Patient {payment_record['patient_id']}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                }
                client.table('patients').insert([patient_data]).execute()
                print(f"[OK] Paciente criado")

            # Tentar insert
            print(f"\n[TENTANDO INSERT DO PAGAMENTO]...")
            result = client.table('payments').insert([payment_record]).execute()
            print(f"[SUCCESS] Pagamento inserido!")

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}")
            print(f"\nDados do erro:")
            print(f"  Mensagem: {e}")
            print(f"\nDados do pagamento:")
            print(json.dumps(payment_record, indent=2, default=str))

            # Tentar sem invoice_id
            print(f"\n[TENTATIVA 2] Sem campos opcionais...")
            payment_minimal = {
                'id': payment_record['id'],
                'clinic_id': payment_record['clinic_id'],
                'patient_id': payment_record['patient_id'],
                'amount': payment_record['amount'],
                'payment_method': payment_record['payment_method'],
                'payment_date': payment_record['payment_date'],
                'status': payment_record['status'],
                'updated_at': payment_record['updated_at'],
                'last_sync_at': payment_record['last_sync_at'],
            }

            try:
                result = client.table('payments').insert([payment_minimal]).execute()
                print(f"[SUCCESS] Pagamento inserido com registros minimais!")
            except Exception as e2:
                print(f"[ERROR] {str(e2)[:200]}")

except Exception as e:
    print(f"Erro geral: {e}")

print("\n" + "=" * 80)
