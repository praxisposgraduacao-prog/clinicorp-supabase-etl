#!/usr/bin/env python3
"""
Diagnóstico: Qual é o erro ao inserir um pagamento?
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
print("DIAGNOSTICO: ERRO AO INSERIR PAGAMENTO")
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

        if len(payments) > 0:
            # Pegar primeiro pagamento
            first_payment = payments[0]

            print(f"\n[PRIMEIRO PAGAMENTO DA API]")
            print(f"ID: {first_payment.get('PaymentHeaderId')}")
            print(f"Paciente: {first_payment.get('PatientId')}")
            print(f"Clinica: {first_payment.get('ReceiverBusinessId')}")
            print(f"Valor: {first_payment.get('Amount')}")
            print(f"Data: {first_payment.get('PaymentDate')}\n")

            # Preparar como queremos inserir
            payment_record = {
                'id': first_payment.get('PaymentHeaderId'),
                'clinic_id': first_payment.get('ReceiverBusinessId', BUSINESS_ID),
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

            print(f"[REGISTRO PREPARADO PARA INSERT]")
            for k, v in payment_record.items():
                print(f"  {k}: {v}")

            print(f"\n[TENTANDO INSERT]...")

            try:
                result = client.table('payments').insert([payment_record]).execute()
                print(f"[SUCCESS] Inserido!")
                print(result)

            except Exception as e:
                print(f"[ERROR] {type(e).__name__}")
                print(f"Mensagem: {str(e)}")

except Exception as e:
    print(f"Erro geral: {e}")

print("\n" + "=" * 80)
