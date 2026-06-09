#!/usr/bin/env python3
"""
Script para testar diferentes formas de autenticação na API Clinicorp
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.clinicorp.com/rest/v1"
USER1 = "praxis"
USER2 = "admpraxis@praxis"
PASSWORD = os.getenv("SenhaUsuario", "Cl1nic@Prx@1")
API_KEY = os.getenv("ERP_CLINICORP_API", "e858562a-888f-4135-933d-7e528515b98e")
BUSINESS_ID = 5292365675823104

print("=" * 70)
print("TESTANDO AUTENTICACAO NA API CLINICORP")
print("=" * 70)

# Teste 1: Bearer Token
print("\n[1] Bearer Token com API Key")
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}
try:
    r = requests.get(f"{API_URL}/business/list", headers=headers, timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code != 401:
        print("SUCESSO! Usando Bearer Token")
except Exception as e:
    print(f"Erro: {e}")

# Teste 2: Basic Auth com "praxis"
print("\n[2] Basic Auth com usuario='praxis'")
try:
    r = requests.get(f"{API_URL}/business/list", auth=HTTPBasicAuth(USER1, PASSWORD), timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code != 401:
        print("SUCESSO! Usando Basic Auth com 'praxis'")
except Exception as e:
    print(f"Erro: {e}")

# Teste 3: Basic Auth com "admpraxis@praxis"
print("\n[3] Basic Auth com usuario='admpraxis@praxis'")
try:
    r = requests.get(f"{API_URL}/business/list", auth=HTTPBasicAuth(USER2, PASSWORD), timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code != 401:
        print("SUCESSO! Usando Basic Auth com 'admpraxis@praxis'")
except Exception as e:
    print(f"Erro: {e}")

# Teste 4: Header customizado
print("\n[4] Header X-API-Key")
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
}
try:
    r = requests.get(f"{API_URL}/business/list", headers=headers, timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code != 401:
        print("SUCESSO! Usando X-API-Key header")
except Exception as e:
    print(f"Erro: {e}")

# Teste 5: Query parameter
print("\n[5] API Key como query parameter")
try:
    r = requests.get(f"{API_URL}/business/list?api_key={API_KEY}", timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code != 401:
        print("SUCESSO! Usando API Key como query param")
except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 70)
print("RECOMENDACAO:")
print("Qual teste acima retornou um status diferente de 401?")
print("Se nenhum funcionou, a API pode exigir token OAuth ou outra autenticacao")
print("=" * 70)
