#!/usr/bin/env python3
"""
Script de diagnóstico para testar cada endpoint individualmente
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
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

print("=" * 80)
print("DIAGNOSTICO DE ENDPOINTS - CLINICORP API")
print("=" * 80)

# Datas
end_date = datetime.now()
start_date = end_date - timedelta(days=30)  # Reduzido para 30 dias para teste
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\n[CONFIG]")
print(f"  API: {API_URL}")
print(f"  Subscriber: {SUBSCRIBER_ID}")
print(f"  Business ID: {BUSINESS_ID}")
print(f"  Periodo: {date_from} a {date_to}\n")

# ============================================================================
# TEST 1: /appointment/list - Diagnóstico Detalhado
# ============================================================================

print("[TEST 1] GET /appointment/list")
print("-" * 80)

url = f"{API_URL}/appointment/list"
params = {
    'subscriber_id': SUBSCRIBER_ID,
    'from': date_from,
    'to': date_to,
    'businessId': BUSINESS_ID,
    'includeCanceled': True
}

print(f"URL: {url}")
print(f"Parametros: {json.dumps(params, indent=2)}\n")

try:
    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}\n")

    try:
        data = response.json()
        print(f"Response Body:")
        print(json.dumps(data, indent=2)[:500])
    except:
        print(f"Response Body (raw):")
        print(response.text[:500])

except Exception as e:
    print(f"[EXCEPTION] {str(e)}")

# ============================================================================
# TEST 2: /financial/list_invoices
# ============================================================================

print("\n[TEST 2] GET /financial/list_invoices")
print("-" * 80)

url = f"{API_URL}/financial/list_invoices"
params = {
    'subscriber_id': SUBSCRIBER_ID,
    'from': date_from,
    'to': date_to,
    'business_id': BUSINESS_ID
}

print(f"URL: {url}")
print(f"Parametros: {json.dumps(params, indent=2)}\n")

try:
    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print(f"Response Body:")
        print(json.dumps(data, indent=2)[:500])
    except:
        print(f"Response Body (raw):")
        print(response.text[:500])

except Exception as e:
    print(f"[EXCEPTION] {str(e)}")

# ============================================================================
# TEST 3: /financial/list_payments
# ============================================================================

print("\n[TEST 3] GET /financial/list_payments")
print("-" * 80)

url = f"{API_URL}/financial/list_payments"
params = {
    'subscriber_id': SUBSCRIBER_ID,
    'from': date_from,
    'to': date_to,
    'business_id': BUSINESS_ID
}

print(f"URL: {url}")
print(f"Parametros: {json.dumps(params, indent=2)}\n")

try:
    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print(f"Response Body:")
        print(json.dumps(data, indent=2)[:500])
    except:
        print(f"Response Body (raw):")
        print(response.text[:500])

except Exception as e:
    print(f"[EXCEPTION] {str(e)}")

# ============================================================================
# TEST 4: Teste com period menor (últimos 7 dias)
# ============================================================================

print("\n[TEST 4] /appointment/list - Últimos 7 dias")
print("-" * 80)

start_date_7d = end_date - timedelta(days=7)
date_from_7d = start_date_7d.strftime("%Y-%m-%d")
date_to_7d = end_date.strftime("%Y-%m-%d")

params = {
    'subscriber_id': SUBSCRIBER_ID,
    'from': date_from_7d,
    'to': date_to_7d,
    'businessId': BUSINESS_ID
}

print(f"Periodo: {date_from_7d} a {date_to_7d}\n")

try:
    response = requests.get(
        f"{API_URL}/appointment/list",
        params=params,
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        count = len(data) if isinstance(data, list) else 0
        print(f"[OK] Retornou {count} registros")
    else:
        try:
            data = response.json()
            print(json.dumps(data, indent=2)[:300])
        except:
            print(response.text[:300])

except Exception as e:
    print(f"[EXCEPTION] {str(e)}")

print("\n" + "=" * 80)
print("FIM DO DIAGNOSTICO")
print("=" * 80)
