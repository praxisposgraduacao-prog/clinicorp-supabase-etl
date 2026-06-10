#!/usr/bin/env python3
"""
Carregar tabelas estendidas - Versão Final Otimizada
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta, date
import json
import uuid as uuid_lib

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAR TABELAS ESTENDIDAS - VERSAO FINAL")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

total_loaded = 0

def serialize_value(value):
    """Serializar valores para JSON-compatible"""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, (dict, list)):
        return value
    else:
        return value

def safe_upsert(table_name, data, key='id'):
    """Upsert com tratamento completo"""
    try:
        if not data or len(data) == 0:
            return 0

        # Limpar dados
        cleaned = []
        for record in data:
            clean_record = {}
            for k, v in record.items():
                if v is None:
                    clean_record[k] = None
                else:
                    clean_record[k] = serialize_value(v)
            cleaned.append(clean_record)

        client.table(table_name).upsert(cleaned, on_conflict=key).execute()
        return len(cleaned)
    except Exception as e:
        error_str = str(e)
        if "already exists" not in error_str.lower():
            print(f"        [WARN] {table_name}: {error_str[:70]}")
        return 0

# ============================================================================
# 1. PATIENT BIRTHDAYS
# ============================================================================

print("\n[1] CARREGANDO PATIENT_BIRTHDAYS (Aniversariantes)...")

try:
    response = requests.get(
        f"{API_URL}/patient/birthdays",
        params={'subscriber_id': SUBSCRIBER_ID, 'date': datetime.now().strftime('%Y-%m-%d')},
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        birthdays = response.json()
        print(f"    API retornou: {len(birthdays)} aniversariantes")

        data = []
        for bd in birthdays:
            birth_date_str = bd.get('BirthDate', '')
            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                    data.append({
                        'id': str(uuid_lib.uuid4()),
                        'patient_id': bd.get('PatientId'),
                        'birth_date': birth_date,
                        'age': bd.get('Age'),
                        'birthday_month': birth_date.month,
                        'birthday_day': birth_date.day,
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })
                except:
                    pass

        if data:
            inserted = safe_upsert('patient_birthdays', data)
            total_loaded += inserted
            print(f"    [OK] {inserted} inseridos\n")
        else:
            print(f"    [OK] 0 inseridos\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 2. ANALYTICS RESULTS
# ============================================================================

print("[2] CARREGANDO ANALYTICS_RESULTS (Dados Analíticos)...")

try:
    response = requests.get(
        f"{API_URL}/analytics/list_results",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        analytics_list = result if isinstance(result, list) else [result] if result else []
        print(f"    API retornou: {len(analytics_list)} registros")

        data = []
        for ana in analytics_list:
            data.append({
                'id': str(uuid_lib.uuid4()),
                'clinic_id': ana.get('BusinessId', BUSINESS_ID),
                'total_revenue_amount': float(ana.get('TotalRevenueAmount', 0)),
                'estimates_total_amount': float(ana.get('EstimatesTotalAmount', 0)),
                'estimates_total_quantity': int(ana.get('EstimatesTotalQuantity', 0)),
                'estimates_approved_amount': float(ana.get('EstimatesApprovedAmount', 0)),
                'estimates_approved_quantity': int(ana.get('EstimatesApprovedQuantity', 0)),
                'conversion_rate': float(ana.get('ConversionRate', 0)),
                'total_received_amount': float(ana.get('TotalReceivedAmount', 0)),
                'total_expenses': float(ana.get('TotalExpenses', 0)),
                'appointments_total': int(ana.get('AppointmentsTotal', 0)),
                'appointments_finished': int(ana.get('AppoinmentsFinished', 0)),
                'appointments_missed': int(ana.get('AppointmentsMissed', 0)),
                'unity_name': ana.get('UnityName'),
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            inserted = safe_upsert('analytics_results', data)
            total_loaded += inserted
            print(f"    [OK] {inserted} inseridos\n")
        else:
            print(f"    [OK] 0 inseridos\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 3. SALES ESTIMATES CONVERSION
# ============================================================================

print("[3] CARREGANDO SALES_ESTIMATES_CONVERSION (Orçamentos e Conversão)...")

try:
    response = requests.get(
        f"{API_URL}/sales/estimates_and_conversion",
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

    if response.status_code == 200:
        result = response.json()
        sales_list = result if isinstance(result, list) else [result] if result else []
        print(f"    API retornou: {len(sales_list)} períodos")

        data = []
        for sale in sales_list:
            status_dict = sale.get('Status', {})
            if isinstance(status_dict, dict):
                for status, values in status_dict.items():
                    if isinstance(values, dict):
                        data.append({
                            'id': str(uuid_lib.uuid4()),
                            'clinic_id': BUSINESS_ID,
                            'month': sale.get('month', ''),
                            'status': status,
                            'total_estimates': int(values.get('TotalEstimates', 0)),
                            'total_estimates_amount': float(values.get('TotalEstimatesAmount', 0)),
                            'average_ticket': float(values.get('AverageTicket', 0)),
                            'conversion_rate': float(sale.get('Conversion', 0)),
                            'updated_at': datetime.utcnow().isoformat(),
                            'last_sync_at': datetime.utcnow().isoformat(),
                        })

        if data:
            inserted = safe_upsert('sales_estimates_conversion', data)
            total_loaded += inserted
            print(f"    [OK] {inserted} inseridos\n")
        else:
            print(f"    [OK] 0 inseridos\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 4. REVENUE BY SPECIALTY
# ============================================================================

print("[4] CARREGANDO REVENUE_BY_SPECIALTY (Receita por Especialidade)...")

try:
    response = requests.get(
        f"{API_URL}/sales/expertise_revenue",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'businessId': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        revenues = result if isinstance(result, list) else [result] if result else []
        print(f"    API retornou: {len(revenues)} registros")

        data = []
        for rev in revenues:
            data.append({
                'id': str(uuid_lib.uuid4()),
                'clinic_id': BUSINESS_ID,
                'month': rev.get('month', ''),
                'specialty': rev.get('Expertise', 'Unknown'),
                'total_revenue': 0,
                'procedures_count': 0,
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            inserted = safe_upsert('revenue_by_specialty', data)
            total_loaded += inserted
            print(f"    [OK] {inserted} inseridos\n")
        else:
            print(f"    [OK] 0 inseridos\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 5. CLINIC DETAILS
# ============================================================================

print("[5] CARREGANDO CLINIC_DETAILS (Detalhes de Clínicas)...")

try:
    response = requests.get(
        f"{API_URL}/group/list_subscribers_clinics",
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        clinics = result if isinstance(result, list) else [result] if result else []
        print(f"    API retornou: {len(clinics)} registros")

        data = []
        for clinic in clinics:
            data.append({
                'id': str(uuid_lib.uuid4()),
                'clinic_id': BUSINESS_ID,
                'name': clinic.get('Name'),
                'email': clinic.get('Email'),
                'landline': str(clinic.get('Landline', '')) if clinic.get('Landline') else None,
                'other_landline': str(clinic.get('OtherLandline', '')) if clinic.get('OtherLandline') else None,
                'no_limit_apt_same_time': clinic.get('NoLimitAptSameTime') == 'true',
                'address': clinic.get('Address'),
                'active': clinic.get('Active') == 'true',
                'slot_time': clinic.get('SlotTime'),
                'working_days_hours': clinic.get('WorkingDaysHours'),
                'subscriber_business_uid': clinic.get('SubscriberBussinessUID'),
                'company_id': clinic.get('CompanyId'),
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            inserted = safe_upsert('clinic_details', data)
            total_loaded += inserted
            print(f"    [OK] {inserted} inseridos\n")
        else:
            print(f"    [OK] 0 inseridos\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO DO CARREGAMENTO")
print("=" * 80)

try:
    bd_count = client.table('patient_birthdays').select('id', count='exact').execute().count or 0
    ana_count = client.table('analytics_results').select('id', count='exact').execute().count or 0
    sec_count = client.table('sales_estimates_conversion').select('id', count='exact').execute().count or 0
    spec_count = client.table('revenue_by_specialty').select('id', count='exact').execute().count or 0
    cd_count = client.table('clinic_details').select('id', count='exact').execute().count or 0

    print(f"\n[TABELAS CARREGADAS]")
    print(f"Patient Birthdays.........: {bd_count} registros")
    print(f"Analytics Results.........: {ana_count} registros")
    print(f"Sales Estimates Conv......: {sec_count} registros")
    print(f"Revenue by Specialty......: {spec_count} registros")
    print(f"Clinic Details............: {cd_count} registros")
    print(f"{'='*40}")
    print(f"TOTAL ADICIONADO..........: {bd_count + ana_count + sec_count + spec_count + cd_count} registros\n")

    # Resumo geral
    print("[RESUMO GERAL DE TODAS AS TABELAS]")
    pat = client.table('patients').select('id', count='exact').execute().count or 0
    prof = client.table('professionals').select('id', count='exact').execute().count or 0
    apt = client.table('appointments').select('id', count='exact').execute().count or 0
    pay = client.table('payments').select('id', count='exact').execute().count or 0
    inv = client.table('invoices').select('id', count='exact').execute().count or 0
    est = client.table('estimates').select('id', count='exact').execute().count or 0
    pro = client.table('procedures').select('id', count='exact').execute().count or 0
    led = client.table('leads').select('id', count='exact').execute().count or 0
    usr = client.table('users').select('id', count='exact').execute().count or 0

    tabelas_base = pat + prof + apt + pay + inv + est + pro + led + usr
    tabelas_ext = bd_count + ana_count + sec_count + spec_count + cd_count

    print(f"Tabelas Base (9).........: {tabelas_base} registros")
    print(f"Tabelas Estendidas (5)...: {tabelas_ext} registros")
    print(f"{'='*40}")
    print(f"TOTAL GERAL..............: {tabelas_base + tabelas_ext} registros\n")

except Exception as e:
    print(f"Erro ao contar: {str(e)[:80]}")

print("=" * 80)
print("Carregamento concluído com sucesso!")
print("=" * 80 + "\n")
