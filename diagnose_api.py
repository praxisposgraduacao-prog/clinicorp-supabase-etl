#!/usr/bin/env python3
"""
Script de diagnóstico para testar todos os endpoints da API Clinicorp
"""

import os
import json
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

# Credenciais
API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))

print("=" * 80)
print("DIAGNOSTICO DA API CLINICORP")
print("=" * 80)
print(f"URL: {API_URL}")
print(f"User: {USER}")
print(f"Business ID: {BUSINESS_ID}\n")

# Lista de endpoints para testar
endpoints = [
    ("/business/list", "Clínicas"),
    ("/security/list_users", "Usuários"),
    ("/patient/list", "Pacientes"),
    ("/professional/list_all_professionals", "Profissionais"),
    ("/appointment/list", "Agendamentos"),
    ("/procedures/list", "Procedimentos"),
    ("/estimates/list", "Orçamentos"),
    ("/financial/list_invoices", "Faturas"),
    ("/financial/list_payments", "Pagamentos"),
    ("/crm/list_active_campaigns", "Campanhas CRM"),
]

results = []

for endpoint, name in endpoints:
    print(f"\n[*] Testando: {name}")
    print(f"    Endpoint: {endpoint}")

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            params={'business_id': BUSINESS_ID},
            auth=HTTPBasicAuth(USER, PASS),
            timeout=10
        )

        print(f"    Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()

                # Verifica se é dict ou list
                if isinstance(data, dict):
                    if 'data' in data:
                        count = len(data['data']) if isinstance(data['data'], list) else 1
                        print(f"    Resultado: {count} registro(s) em data")
                        results.append((name, count, "OK"))
                    else:
                        print(f"    Resultado: Dict vazio ou sem 'data'")
                        print(f"    Chaves: {list(data.keys())[:5]}")
                        results.append((name, 0, "Sem dados"))
                elif isinstance(data, list):
                    count = len(data)
                    print(f"    Resultado: {count} registro(s) (array direto)")
                    results.append((name, count, "OK"))
                else:
                    print(f"    Resultado: Tipo desconhecido: {type(data)}")
                    results.append((name, 0, "Erro"))

            except json.JSONDecodeError:
                print(f"    Erro: Response não é JSON válido")
                print(f"    Response text: {response.text[:100]}")
                results.append((name, 0, "JSON inválido"))

        elif response.status_code == 400:
            print(f"    Erro: Bad Request (400)")
            try:
                print(f"    Detalhes: {response.json()}")
            except:
                print(f"    Response: {response.text[:200]}")
            results.append((name, 0, "Bad Request"))

        elif response.status_code == 401:
            print(f"    Erro: Unauthorized (401)")
            results.append((name, 0, "Unauthorized"))

        else:
            print(f"    Erro: Status {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            results.append((name, 0, f"Erro {response.status_code}"))

    except requests.exceptions.Timeout:
        print(f"    Erro: Timeout (10s)")
        results.append((name, 0, "Timeout"))
    except Exception as e:
        print(f"    Erro: {str(e)}")
        results.append((name, 0, "Exceção"))

# Resumo
print("\n" + "=" * 80)
print("RESUMO DOS TESTES")
print("=" * 80)
print(f"\n{'Endpoint':<30} {'Registros':<15} {'Status':<20}")
print("-" * 65)

total_records = 0
for name, count, status in results:
    print(f"{name:<30} {count:<15} {status:<20}")
    total_records += count

print("-" * 65)
print(f"{'TOTAL':<30} {total_records:<15}")
print()

# Recomendações
print("=" * 80)
print("RECOMENDACOES")
print("=" * 80)

endpoints_com_dados = [r for r in results if r[1] > 0]
endpoints_sem_dados = [r for r in results if r[1] == 0]
endpoints_com_erro = [r for r in results if r[2] not in ["OK", "Sem dados"]]

if endpoints_com_dados:
    print(f"\n✓ Endpoints com dados ({len(endpoints_com_dados)}):")
    for name, count, _ in endpoints_com_dados:
        print(f"  • {name}: {count} registros")
else:
    print(f"\n! Nenhum endpoint retornou dados")

if endpoints_sem_dados:
    print(f"\n⚠ Endpoints sem dados ({len(endpoints_sem_dados)}):")
    for name, _, _ in endpoints_sem_dados:
        print(f"  • {name}")

if endpoints_com_erro:
    print(f"\n✗ Endpoints com erro ({len(endpoints_com_erro)}):")
    for name, _, status in endpoints_com_erro:
        print(f"  • {name}: {status}")

print()
