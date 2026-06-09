#!/usr/bin/env python3
"""
Script para carregar as tabelas faltantes:
- estimates
- payments (pagamentos individuais - não agregados!)
- sales_summary
- procedures (se houver endpoint)
"""

import os
import sys
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
print("CARREGAMENTO DE TABELAS FALTANTES - CLINICORP ETL")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Datas
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

print(f"\n[CONFIG]")
print(f"Subscriber: {SUBSCRIBER_ID}")
print(f"Business ID: {BUSINESS_ID}")
print(f"Periodo: {date_from} a {date_to}\n")

# ============================================================================
# 1. PAGAMENTOS INDIVIDUAIS (novo endpoint!)
# ============================================================================

print("[1] CARREGANDO PAGAMENTOS INDIVIDUAIS...")

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

    print(f"    Status: {response.status_code}")

    if response.status_code == 200:
        payments = response.json()
        if isinstance(payments, list) and len(payments) > 0:
            print(f"    API retornou: {len(payments)} pagamentos")

            data = []
            for pay in payments:
                # Mapeamento de campos
                data.append({
                    'id': pay.get('PaymentId') or pay.get('id'),
                    'clinic_id': BUSINESS_ID,
                    'invoice_id': pay.get('InvoiceId'),
                    'patient_id': pay.get('PatientId'),
                    'amount': pay.get('Amount', 0),
                    'payment_method': pay.get('PaymentMethod') or 'unknown',
                    'payment_date': pay.get('PaymentDate') or pay.get('Date'),
                    'reference': pay.get('Reference') or '',
                    'status': pay.get('Status', 'completed'),
                    'notes': pay.get('Notes') or '',
                    'updated_at': pay.get('UpdatedAt') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('payments').upsert(data, on_conflict='id').execute()
                print(f"    [OK] Pagamentos: {len(data)} inseridos/atualizados")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:100]}")
        else:
            print("    [INFO] Nenhum pagamento encontrado")
    else:
        print(f"    [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# 2. SALES SUMMARY (Orçamentos e Conversão)
# ============================================================================

print("\n[2] CARREGANDO SALES SUMMARY...")

try:
    response = requests.get(
        f"{API_URL}/sales/estimatives_and_conversion",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID,
            'group_by': 'month'
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    print(f"    Status: {response.status_code}")

    if response.status_code == 200:
        summary = response.json()
        if isinstance(summary, list) and len(summary) > 0:
            print(f"    API retornou: {len(summary)} períodos")

            data = []
            for item in summary:
                # Mapeamento de campos
                data.append({
                    'id': f"{BUSINESS_ID}_{item.get('Month', 'unknown')}",
                    'clinic_id': BUSINESS_ID,
                    'period': item.get('Month'),
                    'total_estimates': item.get('TotalEstimates', 0),
                    'completed_estimates': item.get('CompletedEstimates', 0),
                    'cancelled_estimates': item.get('CancelledEstimates', 0),
                    'total_estimate_value': item.get('TotalEstimateValue', 0),
                    'converted_value': item.get('ConvertedValue', 0),
                    'conversion_rate': item.get('ConversionRate', 0),
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            try:
                client.table('sales_summary').upsert(data, on_conflict='id').execute()
                print(f"    [OK] Sales Summary: {len(data)} períodos inseridos/atualizados")
            except Exception as e:
                print(f"    [ERROR] {str(e)[:100]}")
        else:
            print("    [INFO] Nenhum dado de sales encontrado")
    else:
        print(f"    [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# 3. ESTIMATIVAS (Orçamentos)
# ============================================================================

print("\n[3] CARREGANDO ESTIMATIVAS...")
print("    [INFO] Este endpoint requer treatment_id específico")
print("    [INFO] Necessário obter IDs de agendamentos/faturas")
print("    [SKIP] Implementar em versão futura com loop de IDs\n")

# ============================================================================
# 4. PROCEDIMENTOS
# ============================================================================

print("[4] CARREGANDO PROCEDIMENTOS...")

try:
    # Tentando endpoint que já conhecemos
    response = requests.get(
        f"{API_URL}/procedures/list",
        params={
            'business_id': BUSINESS_ID,
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    print(f"    Status: {response.status_code}")

    if response.status_code == 200:
        procedures = response.json()
        if isinstance(procedures, dict):
            print(f"    API retornou: estrutura de procedimentos")
            print(f"    [INFO] Endpoint retorna estrutura de categorias/especialidades")
            print(f"    [SKIP] Necessário redesenhar para armazenar hierarquia\n")
        else:
            print(f"    [INFO] Formato: {type(procedures)}")
    else:
        print(f"    [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# RESUMO FINAL
# ============================================================================

print("=" * 80)
print("RESUMO FINAL")
print("=" * 80)

try:
    est = client.table('estimates').select('id', count='exact').execute().count
    pay = client.table('payments').select('id', count='exact').execute().count
    sal = client.table('sales_summary').select('id', count='exact').execute().count
    proc = client.table('procedures').select('id', count='exact').execute().count

    print(f"\n[DADOS CARREGADOS]")
    print(f"Estimativas.......: {est}")
    print(f"Pagamentos........: {pay} (novo - pagamentos individuais!)")
    print(f"Sales Summary.....: {sal}")
    print(f"Procedimentos.....: {proc}")

    print(f"\n[PROXIMOS PASSOS]")
    print(f"1. Validar dados carregados")
    print(f"2. Extrair IDs de estimativas e carregar detalhes")
    print(f"3. Implementar sincronizacao incremental")

except Exception as e:
    print(f"Erro ao contar: {e}")

print("\n" + "=" * 80)
