#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")

print("Testando endpoints SEM parametros...\n")

endpoints = [
    ("/patient/list", "Pacientes"),
    ("/appointment/list", "Agendamentos"),
    ("/business/list", "Clinicas"),
    ("/security/list_users", "Usuarios"),
]

for endpoint, name in endpoints:
    print(f"[*] {name} - Sem parametros")
    try:
        r = requests.get(
            f"{API_URL}{endpoint}",
            auth=HTTPBasicAuth(USER, PASS),
            timeout=5
        )
        print(f"    Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                print(f"    Resultado: {len(data)} registros")
            elif isinstance(data, dict) and 'data' in data:
                print(f"    Resultado: {len(data['data'])} registros")
            else:
                print(f"    Resultado: {str(data)[:100]}")
        else:
            error_msg = r.json().get('Message', 'Erro desconhecido') if r.status_code == 400 else f"Status {r.status_code}"
            print(f"    Erro: {error_msg[:80]}")
    except Exception as e:
        print(f"    Exception: {str(e)[:80]}")
    print()
