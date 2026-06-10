#!/usr/bin/env python3
"""
Carregar tabelas estendidas com tratamento robusto de erros
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
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
print("CARREGAR TABELAS ESTENDIDAS - MODO ROBUSTO")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

total_loaded = 0

def safe_upsert(table_name, data):
    """Upsert com tratamento seguro de dados"""
    try:
        if not data:
            return 0

        # Limpar dados de datas para JSON
        cleaned = []
        for record in data:
            clean_record = {}
            for key, value in record.items():
                if isinstance(value, (datetime, date)):
                    clean_record[key] = value.isoformat()
                elif isinstance(value, dict) or isinstance(value, list):
                    clean_record[key] = value
                else:
                    clean_record[key] = value
            cleaned.append(clean_record)

        client.table(table_name).upsert(cleaned, on_conflict='id').execute()
        return len(cleaned)
    except Exception as e:
        print(f"        [WARN] Erro no upsert: {str(e)[:80]}")
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
        print(f"    Encontrados: {len(birthdays)} aniversariantes\n")

        data = []
        for bd in birthdays:
            try:
                birth_date = datetime.strptime(bd.get('BirthDate', ''), '%Y-%m-%d').date() if bd.get('BirthDate') else None
                data.append({
                    'id': str(uuid_lib.uuid4()),
                    'patient_id': bd.get('PatientId'),
                    'birth_date': birth_date,
                    'age': bd.get('Age'),
                    'birthday_month': birth_date.month if birth_date else None,
                    'birthday_day': birth_date.day if birth_date else None,
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })
            except:
                pass

        if data:
            inserted = safe_upsert('patient_birthdays', data)
            total_loaded += inserted
            print(f"    [OK] {inserted} aniversariantes carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 2. REVENUE BY SPECIALTY
# ============================================================================

print("[2] CARREGANDO REVENUE_BY_SPECIALTY (Receita por Especialidade)...")

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
        revenues = response.json()
        print(f"    Encontrados: {len(revenues)} especialidades\n")

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
            print(f"    [OK] {inserted} especialidades carregadas\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 3. CLINIC DETAILS
# ============================================================================

print("[3] CARREGANDO CLINIC_DETAILS (Detalhes de Clínicas)...")

try:
    response = requests.get(
        f"{API_URL}/group/list_subscribers_clinics",
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        clinics = response.json()
        print(f"    Encontradas: {len(clinics)} clínicas\n")

        data = []
        for clinic in clinics:
            data.append({
                'id': str(uuid_lib.uuid4()),
                'clinic_id': BUSINESS_ID,
                'name': clinic.get('Name'),
                'email': clinic.get('Email'),
                'landline': clinic.get('Landline'),
                'other_landline': clinic.get('OtherLandline'),
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
            print(f"    [OK] {inserted} clínicas carregadas\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 4. ANALYTICS RESULTS
# ============================================================================

print("[4] CARREGANDO ANALYTICS_RESULTS (Dados Analíticos)...")

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
        analytics_list = response.json()
        if not isinstance(analytics_list, list):
            analytics_list = [analytics_list]

        print(f"    Encontrados: {len(analytics_list)} registros\n")

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
            print(f"    [OK] {inserted} registros analíticos carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# 5. SALES ESTIMATES CONVERSION
# ============================================================================

print("[5] CARREGANDO SALES_ESTIMATES_CONVERSION (Orçamentos e Conversão)...")

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
        sales_list = response.json()
        if not isinstance(sales_list, list):
            sales_list = [sales_list]

        print(f"    Encontrados: {len(sales_list)} períodos\n")

        data = []
        for sale in sales_list:
            status_dict = sale.get('Status', {})
            if isinstance(status_dict, dict):
                for status, values in status_dict.items():
                    data.append({
                        'id': str(uuid_lib.uuid4()),
                        'clinic_id': BUSINESS_ID,
                        'month': sale.get('month', ''),
                        'status': status,
                        'total_estimates': int(values.get('TotalEstimates', 0)) if isinstance(values, dict) else 0,
                        'total_estimates_amount': float(values.get('TotalEstimatesAmount', 0)) if isinstance(values, dict) else 0,
                        'average_ticket': float(values.get('AverageTicket', 0)) if isinstance(values, dict) else 0,
                        'conversion_rate': float(sale.get('Conversion', 0)),
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })

        if data:
            inserted = safe_upsert('sales_estimates_conversion', data)
            total_loaded += inserted
            print(f"    [OK] {inserted} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO DO CARREGAMENTO ROBUSTO")
print("=" * 80)

try:
    bd = client.table('patient_birthdays').select('id', count='exact').execute().count
    spec = client.table('revenue_by_specialty').select('id', count='exact').execute().count
    cd = client.table('clinic_details').select('id', count='exact').execute().count
    ana = client.table('analytics_results').select('id', count='exact').execute().count
    sec = client.table('sales_estimates_conversion').select('id', count='exact').execute().count

    print(f"\n[TABELAS CARREGADAS]")
    print(f"Patient Birthdays.........: {bd}")
    print(f"Revenue by Specialty......: {spec}")
    print(f"Clinic Details............: {cd}")
    print(f"Analytics Results.........: {ana}")
    print(f"Sales Estimates Conv......: {sec}")
    print(f"{'='*40}")
    print(f"TOTAL ADICIONADO..........: {total_loaded} registros\n")

except Exception as e:
    print(f"Erro ao contar: {str(e)[:80]}")

print("=" * 80)
print("Carregamento robusto concluído!")
print("=" * 80 + "\n")
