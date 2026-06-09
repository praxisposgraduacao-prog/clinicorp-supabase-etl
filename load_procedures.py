#!/usr/bin/env python3
"""
Carregar procedures (procedimentos/tabelas de preço) da API
Já que estimates individuais não estão disponíveis de forma sincronizável
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAR PROCEDURES (TABELAS DE PROCEDIMENTOS)")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n[1] OBTENDO PROCEDURES DA API...")

try:
    response = requests.get(
        f"{API_URL}/procedures/list",
        params={'business_id': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        procedures_dict = response.json()

        if isinstance(procedures_dict, dict):
            print(f"    Encontradas: {len(procedures_dict)} tabelas de procedimentos\n")

            # Converter estrutura para lista
            procedures = []
            for table_name, items in procedures_dict.items():
                if isinstance(items, list):
                    for item in items:
                        procedures.append({
                            'id': f"{BUSINESS_ID}_{table_name}_{item.get('id', '')}",
                            'clinic_id': BUSINESS_ID,
                            'name': item.get('name', table_name),
                            'description': table_name,
                            'category': table_name,
                            'price': float(item.get('price', 0)) if item.get('price') else None,
                            'status': 'active',
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat(),
                            'last_sync_at': datetime.utcnow().isoformat(),
                        })

            print(f"[2] PREPARANDO {len(procedures)} PROCEDURES...")

            if len(procedures) > 0:
                # Limpar dados antigos
                print("    Limpando procedures antigas...")
                try:
                    client.table('procedures').delete().neq('id', 0).execute()
                except:
                    pass

                # Inserir em lotes
                print(f"    Inserindo em lotes...\n")

                batch_size = 100
                inserted = 0
                failed = 0

                for i in range(0, len(procedures), batch_size):
                    batch = procedures[i:i+batch_size]
                    batch_num = i // batch_size + 1

                    try:
                        client.table('procedures').insert(batch).execute()
                        inserted += len(batch)
                        print(f"    Batch {batch_num}: {len(batch)} inseridas")

                    except Exception as e:
                        error_msg = str(e)
                        if 'duplicate' in error_msg:
                            # Tentar update
                            for record in batch:
                                try:
                                    client.table('procedures').update(record).eq('id', record['id']).execute()
                                    inserted += 1
                                except:
                                    failed += 1
                        else:
                            print(f"    Batch {batch_num}: ERRO - {error_msg[:60]}")
                            failed += len(batch)

                print(f"\n    Total inserido: {inserted}")
                if failed > 0:
                    print(f"    Falhas: {failed}\n")
                else:
                    print()

            else:
                print("    [INFO] Nenhuma procedure encontrada\n")

        else:
            print(f"    [INFO] Estrutura retornada: {type(procedures_dict).__name__}\n")

    else:
        print(f"    [ERROR] HTTP {response.status_code}\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# NOTA SOBRE ESTIMATES
# ============================================================================

print("[3] NOTA SOBRE ESTIMATES")
print("-" * 80)
print("""
Análise realizada:
- Endpoint /estimates/get requer treatment_id específico
- Agendamentos não contêm treatment_id sincronizável
- Endpoint /estimates/list retorna 400 Bad Request
- Estrutura de procedures carregada como alternativa

Recomendação:
Contacte suporte Clinicorp para:
1. Confirmar se estimates individuais estão disponíveis para sincronização
2. Qual é o identificador correto para treatment_id
3. Se existe endpoint /estimates/list funcional com parâmetros diferentes
4. Ou se estimates devem ser obtidos por paciente via /patient/list_estimates

Por enquanto, as tabelas de procedimentos foram carregadas como referência.
""")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

try:
    proc_count = client.table('procedures').select('id', count='exact').execute().count
    est_count = client.table('estimates').select('id', count='exact').execute().count

    prof = client.table('professionals').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count

    total = prof + pat + apt + pay + inv + proc_count + est_count

    print(f"\n[TABELAS]")
    print(f"Procedures.....: {proc_count}")
    print(f"Estimates......: {est_count}\n")

    print(f"[RESUMO GERAL]")
    print(f"Profissionais.....: {prof}")
    print(f"Pacientes.........: {pat}")
    print(f"Agendamentos......: {apt}")
    print(f"Pagamentos........: {pay}")
    print(f"Faturas..........: {inv}")
    print(f"Procedures........: {proc_count}")
    print(f"Estimates.........: {est_count}")
    print(f"{'='*40}")
    print(f"TOTAL.............: {total} registros")

except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
