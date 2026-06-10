#!/usr/bin/env python3
"""
Carregamento de Tabelas Estendidas - Versão Otimizada
Com tratamento de duplicatas, serialização robusta e retry logic
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, date
import json
import time
import uuid as uuid_lib

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

BATCH_SIZE = 50
MAX_RETRIES = 3
RETRY_DELAY = 2

def serialize_value(value):
    """Serializar valores para JSON-compatible"""
    if value is None:
        return None
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, (dict, list)):
        return value
    else:
        return value

def safe_upsert(table_name, data, key='id', retry=0):
    """Upsert com tratamento de duplicatas e retry logic"""
    try:
        if not data or len(data) == 0:
            return 0, 0

        # Remover duplicatas baseado na chave primary
        seen = {}
        cleaned = []
        for record in data:
            clean_record = {}
            for k, v in record.items():
                clean_record[k] = serialize_value(v)

            # Evitar duplicatas na mesma requisição
            record_key = clean_record.get(key)
            if record_key not in seen:
                seen[record_key] = True
                cleaned.append(clean_record)

        if not cleaned:
            return 0, 0

        client.table(table_name).upsert(cleaned, on_conflict=key).execute()
        return len(cleaned), 0

    except Exception as e:
        error_str = str(e)

        if retry < MAX_RETRIES:
            print(f"        [RETRY {retry+1}/{MAX_RETRIES}] Aguardando {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            return safe_upsert(table_name, data, key, retry + 1)
        else:
            print(f"        [ERROR] {error_str[:100]}")
            return 0, len(data)

print("=" * 80)
print("CARREGAMENTO DE TABELAS ESTENDIDAS - VERSÃO OTIMIZADA")
print("=" * 80)

total_loaded = 0
total_errors = 0

# ============================================================================
# 1. PATIENT BIRTHDAYS (9 registros)
# ============================================================================

print("\n[1] CARREGANDO PATIENT BIRTHDAYS...\n")

try:
    response = requests.get(
        f"{API_URL}/patient/birthdays",
        params={'subscriber_id': SUBSCRIBER_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        birthdays = response.json()
        print(f"    API retornou: {len(birthdays) if birthdays else 0} aniversariantes")

        if birthdays:
            data = []
            for bday in birthdays:
                patient_id = bday.get('PatientId')
                birth_date_str = bday.get('BirthDate')
                birthday_month = None
                birthday_day = None

                if patient_id and birth_date_str:
                    try:
                        bd = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00'))
                        birthday_month = bd.month
                        birthday_day = bd.day
                    except:
                        pass

                    # Generate consistent UUID based on patient_id
                    record_id = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, f"patient_birthday_{patient_id}"))

                    data.append({
                        'id': record_id,
                        'patient_id': patient_id,
                        'birth_date': birth_date_str,
                        'age': bday.get('Age'),
                        'birthday_month': birthday_month,
                        'birthday_day': birthday_day,
                    })

            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i:i+BATCH_SIZE]
                inserted, errors = safe_upsert('patient_birthdays', batch, key='id')
                total_loaded += inserted
                total_errors += errors
                if inserted > 0:
                    print(f"    [OK] {inserted} aniversariantes carregados")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}")

# ============================================================================
# 2. ANALYTICS RESULTS
# ============================================================================

print("\n[2] CARREGANDO ANALYTICS RESULTS...\n")

try:
    response = requests.get(
        f"{API_URL}/analytics/list_results",
        params={'subscriber_id': SUBSCRIBER_ID, 'businessId': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        results = response.json()
        print(f"    API retornou: {len(results) if results else 0} registros")

        if results:
            data = []
            for result in results:
                data.append({
                    'id': result.get('id', str(datetime.utcnow().timestamp())),
                    'metric_name': result.get('name'),
                    'metric_value': result.get('value'),
                    'period_start': result.get('start_date'),
                    'period_end': result.get('end_date'),
                    'category': result.get('category'),
                    'data': json.dumps(result) if isinstance(result, dict) else None,
                })

            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i:i+BATCH_SIZE]
                inserted, errors = safe_upsert('analytics_results', batch, key='id')
                total_loaded += inserted
                total_errors += errors
                if inserted > 0:
                    print(f"    [OK] {inserted} resultados analíticos carregados")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}")

# ============================================================================
# 3. REVENUE BY SPECIALTY (já carregado, apenas verificar)
# ============================================================================

print("\n[3] VERIFICANDO REVENUE BY SPECIALTY...\n")

try:
    result = client.table('revenue_by_specialty').select('count', count='exact').execute()
    count = result.count if result.count else 0
    print(f"    Status: {count} registros carregados")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}")

# ============================================================================
# 4. CASH FLOW
# ============================================================================

print("\n[4] CARREGANDO CASH FLOW...\n")

try:
    response = requests.get(
        f"{API_URL}/financial/list_cash_flow",
        params={'subscriber_id': SUBSCRIBER_ID, 'businessId': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        cash_flows = response.json()
        print(f"    API retornou: {len(cash_flows) if isinstance(cash_flows, list) else 1} registros")

        if cash_flows:
            # cash_flows pode ser lista ou dict
            if not isinstance(cash_flows, list):
                cash_flows = [cash_flows]

            data = []
            for cf in cash_flows:
                # Generate UUID v4 for each cash flow record
                cf_id = cf.get('id')
                if not cf_id:
                    # Try to generate from month/date
                    month = cf.get('month') or cf.get('date', '')
                    cf_id = str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, f"cash_flow_{month}"))

                data.append({
                    'id': cf_id,
                    'clinic_id': BUSINESS_ID,
                    'month': cf.get('month') or cf.get('date', '')[:7] if cf.get('date') else '',
                    'inflow': float(cf.get('inflow', cf.get('amount_in', 0))) if cf.get('inflow') or cf.get('amount_in') else 0,
                    'outflow': float(cf.get('outflow', cf.get('amount_out', 0))) if cf.get('outflow') or cf.get('amount_out') else 0,
                    'cash': float(cf.get('cash', cf.get('balance', 0))) if cf.get('cash') or cf.get('balance') else 0,
                })

            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i:i+BATCH_SIZE]
                inserted, errors = safe_upsert('cash_flow', batch, key='id')
                total_loaded += inserted
                total_errors += errors
                if inserted > 0:
                    print(f"    [OK] {inserted} registros de fluxo de caixa carregados")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}")

# ============================================================================
# 5. FINANCIAL SUMMARY
# ============================================================================

print("\n[5] CARREGANDO FINANCIAL SUMMARY...\n")

try:
    response = requests.get(
        f"{API_URL}/financial/list_summary",
        params={'subscriber_id': SUBSCRIBER_ID, 'businessId': BUSINESS_ID},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        summary = response.json()
        print(f"    API retornou: dados de resumo financeiro")

        if summary:
            # summary é geralmente um dict, não uma lista
            if isinstance(summary, dict):
                data = [{
                    'id': summary.get('id', str(datetime.utcnow().timestamp())),
                    'period': summary.get('period') or summary.get('date'),
                    'total_revenue': float(summary.get('total_revenue', 0)),
                    'total_expenses': float(summary.get('total_expenses', 0)),
                    'net_profit': float(summary.get('net_profit', 0)),
                    'data': json.dumps(summary) if isinstance(summary, dict) else None,
                }]

                inserted, errors = safe_upsert('financial_summary', data, key='id')
                total_loaded += inserted
                total_errors += errors
                if inserted > 0:
                    print(f"    [OK] {inserted} resumo financeiro carregado")
            elif isinstance(summary, list) and len(summary) > 0:
                data = []
                for s in summary:
                    data.append({
                        'id': s.get('id', str(datetime.utcnow().timestamp())),
                        'period': s.get('period') or s.get('date'),
                        'total_revenue': float(s.get('total_revenue', 0)),
                        'total_expenses': float(s.get('total_expenses', 0)),
                        'net_profit': float(s.get('net_profit', 0)),
                        'data': json.dumps(s) if isinstance(s, dict) else None,
                    })

                for i in range(0, len(data), BATCH_SIZE):
                    batch = data[i:i+BATCH_SIZE]
                    inserted, errors = safe_upsert('financial_summary', batch, key='id')
                    total_loaded += inserted
                    total_errors += errors

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("CARREGAMENTO DE TABELAS ESTENDIDAS CONCLUÍDO")
print("=" * 80)
print(f"\nTotal de registros carregados: {total_loaded}")
print(f"Total de erros: {total_errors}")
print(f"Taxa de sucesso: {100 * total_loaded / (total_loaded + total_errors) if total_loaded + total_errors > 0 else 0:.1f}%")
print("\n" + "=" * 80)
