#!/usr/bin/env python3
"""
Carregar estimates (orçamentos) via endpoint /estimates/get
Requer treatment_id específico para cada orçamento
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
print("CARREGAR ESTIMATES (ORCAMENTOS)")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

# ============================================================================
# PASSO 1: EXTRAIR TREATMENT IDS DOS AGENDAMENTOS
# ============================================================================

print("\n[1] EXTRAINDO TREATMENT IDs DOS AGENDAMENTOS...")

treatment_ids = set()

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
        timeout=30
    )

    if response.status_code == 200:
        appointments = response.json()

        for apt in appointments:
            # Procurar por diferentes nomes de ID de tratamento
            treatment_id = (apt.get('TreatmentId') or
                          apt.get('treatment_id') or
                          apt.get('EstimateId') or
                          apt.get('estimate_id') or
                          apt.get('ProcedureId') or
                          apt.get('AppointmentId'))

            if treatment_id:
                treatment_ids.add(treatment_id)

        print(f"    Encontrados: {len(treatment_ids)} treatment IDs\n")

except Exception as e:
    print(f"    [WARN] Erro ao extrair IDs: {str(e)[:80]}\n")

if len(treatment_ids) == 0:
    print("[INFO] Nenhum treatment ID encontrado nos agendamentos")
    print("[INFO] Tentando obter lista via endpoint de lista...\n")

    # Tentar endpoint alternativo se houver
    try:
        # Alguns endpoints retornam estrutura em vez de lista
        response = requests.get(
            f"{API_URL}/estimates/list",
            params={'subscriber_id': SUBSCRIBER_ID},
            auth=HTTPBasicAuth(API_USER, API_PASS),
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"    Endpoint retornou: {type(data).__name__}")
            if isinstance(data, list):
                treatment_ids = set(e.get('id') for e in data if e.get('id'))
                print(f"    Extraidos: {len(treatment_ids)} IDs\n")

    except:
        pass

# ============================================================================
# PASSO 2: OBTER DETALHES DE CADA ESTIMATE
# ============================================================================

if len(treatment_ids) > 0:
    print(f"[2] OBTENDO DETALHES DE {len(treatment_ids)} ESTIMATES...")
    print(f"    Isto pode levar alguns minutos...\n")

    estimates_data = []
    success = 0
    failed = 0

    for i, treatment_id in enumerate(treatment_ids):
        if (i + 1) % 50 == 0:
            print(f"    Progresso: {i + 1}/{len(treatment_ids)}")

        try:
            response = requests.get(
                f"{API_URL}/estimates/get",
                params={
                    'subscriber_id': SUBSCRIBER_ID,
                    'treatment_id': treatment_id
                },
                auth=HTTPBasicAuth(API_USER, API_PASS),
                timeout=10
            )

            if response.status_code == 200:
                estimate = response.json()

                if isinstance(estimate, dict):
                    estimates_data.append({
                        'id': estimate.get('id') or treatment_id,
                        'clinic_id': BUSINESS_ID,
                        'patient_id': estimate.get('patient_id'),
                        'professional_id': estimate.get('professional_id'),
                        'title': estimate.get('title') or estimate.get('name') or f"Estimate {treatment_id}",
                        'description': estimate.get('description'),
                        'total_amount': float(estimate.get('total_amount', 0)) or float(estimate.get('amount', 0)),
                        'discount_amount': float(estimate.get('discount_amount', 0)),
                        'final_amount': float(estimate.get('final_amount', 0)),
                        'status': estimate.get('status', 'pending'),
                        'created_at': estimate.get('created_at'),
                        'updated_at': estimate.get('updated_at') or datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })
                    success += 1

        except Exception as e:
            failed += 1

    print(f"\n    Obtidos: {success}")
    print(f"    Falhados: {failed}\n")

    # ============================================================================
    # PASSO 3: INSERIR NO BANCO
    # ============================================================================

    if len(estimates_data) > 0:
        print(f"[3] INSERINDO {len(estimates_data)} ESTIMATES NO BANCO...")

        try:
            # Limpar dados antigos
            client.table('estimates').delete().neq('id', 0).execute()
        except:
            pass

        batch_size = 50
        inserted = 0
        failed = 0

        for i in range(0, len(estimates_data), batch_size):
            batch = estimates_data[i:i+batch_size]
            batch_num = i // batch_size + 1

            try:
                client.table('estimates').insert(batch).execute()
                inserted += len(batch)
                print(f"    Batch {batch_num}: {len(batch)} inseridas")

            except Exception as e:
                # Tentar individual
                for record in batch:
                    try:
                        client.table('estimates').insert([record]).execute()
                        inserted += 1
                    except:
                        failed += 1

                print(f"    Batch {batch_num}: {len(batch)} processadas")

        print(f"\n    Total inserido: {inserted}")
        if failed > 0:
            print(f"    Falhas: {failed}\n")

else:
    print("[INFO] Nenhum estimate para carregar")
    print("[SKIP] Pulando carregamento de estimates\n")

# ============================================================================
# RESULTADO
# ============================================================================

print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

try:
    estimates_count = client.table('estimates').select('id', count='exact').execute().count

    prof = client.table('professionals').select('id', count='exact').execute().count
    pat = client.table('patients').select('id', count='exact').execute().count
    apt = client.table('appointments').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count
    inv = client.table('invoices').select('id', count='exact').execute().count

    total = prof + pat + apt + pay + inv + estimates_count

    print(f"\n[ESTIMATES]")
    print(f"Total no banco: {estimates_count}\n")

    print(f"[RESUMO GERAL]")
    print(f"Profissionais.....: {prof}")
    print(f"Pacientes.........: {pat}")
    print(f"Agendamentos......: {apt}")
    print(f"Pagamentos........: {pay}")
    print(f"Faturas..........: {inv}")
    print(f"Estimates.........: {estimates_count}")
    print(f"{'='*40}")
    print(f"TOTAL.............: {total} registros")

except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
