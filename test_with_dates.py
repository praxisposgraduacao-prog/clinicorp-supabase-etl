#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
SUBSCRIBER = "praxis"

# Datas para consulta
today = datetime.now()
start_date = (today - timedelta(days=365)).strftime("%Y-%m-%d")  # 1 ano atrás
end_date = today.strftime("%Y-%m-%d")

print("=" * 80)
print("TESTANDO COM DATAS")
print("=" * 80)
print(f"\nData Início: {start_date}")
print(f"Data Fim: {end_date}\n")

# Teste 1: Agendamentos com datas
print("[1] /appointment/list com datas")
try:
    r = requests.get(
        f"{API_URL}/appointment/list",
        params={
            "subscriber_id": SUBSCRIBER,
            "data_inicial": start_date,
            "data_final": end_date,
        },
        auth=HTTPBasicAuth(USER, PASS),
        timeout=5
    )

    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data) if isinstance(data, list) else len(data.get('data', []))
        print(f"    [OK] {count} agendamentos encontrados!")
    else:
        print(f"    Erro: {r.json().get('Message', r.text)[:100]}")

except Exception as e:
    print(f"    Exception: {str(e)[:100]}")

# Teste 2: Faturas com datas
print("\n[2] /financial/list_invoices com datas")
try:
    r = requests.get(
        f"{API_URL}/financial/list_invoices",
        params={
            "subscriber_id": SUBSCRIBER,
            "data_inicial": start_date,
            "data_final": end_date,
        },
        auth=HTTPBasicAuth(USER, PASS),
        timeout=5
    )

    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data) if isinstance(data, list) else len(data.get('data', []))
        print(f"    [OK] {count} faturas encontradas!")
    else:
        print(f"    Erro: {r.json().get('Message', r.text)[:100]}")

except Exception as e:
    print(f"    Exception: {str(e)[:100]}")

# Teste 3: Pagamentos com datas
print("\n[3] /financial/list_payments com datas")
try:
    r = requests.get(
        f"{API_URL}/financial/list_payments",
        params={
            "subscriber_id": SUBSCRIBER,
            "data_inicial": start_date,
            "data_final": end_date,
        },
        auth=HTTPBasicAuth(USER, PASS),
        timeout=5
    )

    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data) if isinstance(data, list) else len(data.get('data', []))
        print(f"    [OK] {count} pagamentos encontrados!")
    else:
        print(f"    Erro: {r.json().get('Message', r.text)[:100]}")

except Exception as e:
    print(f"    Exception: {str(e)[:100]}")

print("\n" + "=" * 80)
