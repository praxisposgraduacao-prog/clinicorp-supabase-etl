#!/usr/bin/env python3
"""
Script para testar os parâmetros corrigidos da API
Não grava nada no Supabase, apenas testa a conectividade
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

print("=" * 80)
print("TESTE DOS PARAMETROS CORRIGIDOS DA API CLINICORP")
print("=" * 80)

# Datas para consulta
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\n[CONFIG]")
print(f"  API URL: {API_URL}")
print(f"  Usuario: {API_USER}")
print(f"  Subscriber: {SUBSCRIBER_ID}")
print(f"  Business ID: {BUSINESS_ID}")
print(f"  Periodo: {date_from} a {date_to}\n")

# ============================================================================
# 1. TESTE: /appointment/list
# ============================================================================

print("[TEST 1] GET /appointment/list")
print("-" * 80)

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
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        count = len(data) if isinstance(data, list) else len(data.get('data', []))
        print(f"[OK] Retornou {count} agendamentos")
        if count > 0 and isinstance(data, list):
            print(f"     Primeiro agendamento:")
            print(f"       ID: {data[0].get('id')}")
            print(f"       Patient ID: {data[0].get('patient_id')}")
            print(f"       Data: {data[0].get('scheduled_date')}")
    else:
        try:
            error = response.json()
            print(f"[ERROR] {error.get('Message', str(error)[:100])}")
        except:
            print(f"[ERROR] {response.text[:100]}")

except Exception as e:
    print(f"[EXCEPTION] {str(e)}")

# ============================================================================
# 2. TESTE: /financial/list_invoices
# ============================================================================

print("\n[TEST 2] GET /financial/list_invoices")
print("-" * 80)

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
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        count = len(data) if isinstance(data, list) else len(data.get('data', []))
        print(f"[OK] Retornou {count} faturas")
        if count > 0 and isinstance(data, list):
            print(f"     Primeira fatura:")
            print(f"       ID: {data[0].get('id')}")
            print(f"       Numero: {data[0].get('number')}")
            print(f"       Valor: {data[0].get('total_amount')}")
    else:
        try:
            error = response.json()
            print(f"[ERROR] {error.get('Message', str(error)[:100])}")
        except:
            print(f"[ERROR] {response.text[:100]}")

except Exception as e:
    print(f"[EXCEPTION] {str(e)}")

# ============================================================================
# 3. TESTE: /financial/list_payments
# ============================================================================

print("\n[TEST 3] GET /financial/list_payments")
print("-" * 80)

try:
    response = requests.get(
        f"{API_URL}/financial/list_payments",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        count = len(data) if isinstance(data, list) else len(data.get('data', []))
        print(f"[OK] Retornou {count} pagamentos")
        if count > 0 and isinstance(data, list):
            print(f"     Primeiro pagamento:")
            print(f"       ID: {data[0].get('id')}")
            print(f"       Valor: {data[0].get('amount')}")
            print(f"       Data: {data[0].get('payment_date')}")
    else:
        try:
            error = response.json()
            print(f"[ERROR] {error.get('Message', str(error)[:100])}")
        except:
            print(f"[ERROR] {response.text[:100]}")

except Exception as e:
    print(f"[EXCEPTION] {str(e)}")

# ============================================================================
# RESUMO
# ============================================================================

print("\n" + "=" * 80)
print("RESUMO DOS TESTES")
print("=" * 80)
print("""
Se todos os testes retornaram status 200:
  [OK] Os parametros estao corretos!
  [PROXIMO] Execute: python expand_with_subscriber.py

Se algum teste retornou status diferente:
  [CHECK] Verifique a mensagem de erro acima
  [CHECK] Consulte API_PARAMETERS_ANALYSIS.md para detalhes
  [HELP] Entre em contato com suporte Clinicorp se necessario
""")
print("=" * 80)
