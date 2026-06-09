import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

user = os.getenv('ERP_CLINICORP_USUARIO_API')
pswd = os.getenv('ERP_CLINICORP_PSWD')
api_key = os.getenv('ERP_CLINICORP_API')

print(f"Usuario: {user}")
print(f"Senha: {'*' * len(pswd) if pswd else 'VAZIO'}")
print(f"API Key: {api_key[:20]}...")
print()

# Testar com usuario e senha
print("Testando Basic Auth com credenciais carregadas...")
try:
    r = requests.get(
        "https://api.clinicorp.com/rest/v1/business/list",
        auth=HTTPBasicAuth(user, pswd),
        timeout=5
    )
    print(f"Status: {r.status_code}")
    if r.status_code != 401:
        print("SUCESSO!")
        print(f"Response: {r.text[:200]}")
    else:
        print("FALHA: 401 Unauthorized")
except Exception as e:
    print(f"Erro: {e}")
