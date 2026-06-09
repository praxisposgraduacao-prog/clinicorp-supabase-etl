#!/usr/bin/env python3
"""
Script de diagnóstico para entender a estrutura dos pagamentos
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

print("=" * 80)
print("DIAGNOSTICO - ESTRUTURA DOS PAGAMENTOS")
print("=" * 80)

end_date = datetime.now()
start_date = end_date - timedelta(days=5)  # Apenas 5 dias para teste
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\nPeriodo: {date_from} a {date_to}\n")

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
        print(f"Total de pagamentos: {len(payments)}\n")

        if len(payments) > 0:
            # Examinar primeiro pagamento
            first_payment = payments[0]
            print("[PRIMEIRO PAGAMENTO]")
            print(json.dumps(first_payment, indent=2, default=str)[:1000])

            # Coletar unique clinic_ids
            clinic_ids = set()
            for pay in payments:
                if pay.get('ClinicId'):
                    clinic_ids.add(pay.get('ClinicId'))

            print(f"\n[CLINIC IDS ENCONTRADOS]")
            print(f"Unique clinic_ids: {clinic_ids}")
            print(f"Total: {len(clinic_ids)}")

            # Verificar campos obrigatórios
            print(f"\n[VALIDACAO DE CAMPOS OBRIGATORIOS]")

            required_fields = ['PaymentId', 'Amount', 'PaymentDate']
            for field in required_fields:
                null_count = sum(1 for p in payments if not p.get(field))
                print(f"  {field}: {len(payments) - null_count}/{len(payments)} preenchidos")

except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
