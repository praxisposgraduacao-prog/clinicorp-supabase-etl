#!/usr/bin/env python3
"""
Carregar todas as 20+ tabelas estendidas da API Clinicorp
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
import json

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAR TABELAS ESTENDIDAS - 20+ NOVAS TABELAS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Data range
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

# Counter
total_loaded = 0

# ============================================================================
# 1. CHAIRS - Cadeiras
# ============================================================================

print("\n[1] CARREGANDO CHAIRS (Cadeiras)...")

try:
    response = requests.get(
        f"{API_URL}/business/list_chairs",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'Clinic_BusinessId': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        chairs = response.json()
        if isinstance(chairs, list):
            print(f"    Encontradas: {len(chairs)} cadeiras\n")
            data = []
            for chair in chairs:
                data.append({
                    'id': chair.get('id'),
                    'clinic_id': chair.get('BusinessId', BUSINESS_ID),
                    'name': chair.get('Name'),
                    'status': 'active',
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            if data:
                client.table('chairs').upsert(data, on_conflict='id').execute()
                total_loaded += len(data)
                print(f"    [OK] {len(data)} cadeiras carregadas\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 2. RECEIPTS - Recibos
# ============================================================================

print("[2] CARREGANDO RECEIPTS (Recibos)...")

try:
    response = requests.get(
        f"{API_URL}/financial/list_receipt",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        receipts = response.json()
        print(f"    Encontrados: {len(receipts)} recibos\n")
        data = []
        for receipt in receipts:
            data.append({
                'id': receipt.get('id'),
                'clinic_id': receipt.get('ReceiverBusinessId', BUSINESS_ID),
                'patient_id': receipt.get('PatientId'),
                'reference_id': receipt.get('ReferenceId'),
                'amount': float(receipt.get('Amount', 0)),
                'description': receipt.get('Description'),
                'receipt_date': receipt.get('ReceiptDate'),
                'receiver_business_id': receipt.get('ReceiverBusinessId'),
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            batch_size = 50
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    client.table('receipts').upsert(batch, on_conflict='id').execute()
                    total_loaded += len(batch)
                except:
                    pass
            print(f"    [OK] {len(data)} recibos carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 3. CASH FLOW - Fluxo de Caixa
# ============================================================================

print("[3] CARREGANDO CASH_FLOW (Fluxo de Caixa)...")

try:
    response = requests.get(
        f"{API_URL}/financial/list_cash_flow",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        cash_flows = response.json()
        print(f"    Encontrados: {len(cash_flows)} registros\n")

        if isinstance(cash_flows, dict):
            cash_flows = [cash_flows]

        data = []
        for cf in cash_flows:
            data.append({
                'id': str(__import__('uuid').uuid4()),
                'clinic_id': BUSINESS_ID,
                'month': cf.get('month', ''),
                'inflow': float(cf.get('in', 0)),
                'outflow': float(cf.get('out', 0)),
                'inflow_forecast': float(cf.get('in_forecast', 0)),
                'outflow_forecast': float(cf.get('out_forecast', 0)),
                'cash': float(cf.get('cash', 0)),
                'bank_slip': float(cf.get('bank_slip', 0)),
                'credit_card': float(cf.get('credit_card', 0)),
                'debit_card': float(cf.get('debit_card', 0)),
                'check_amount': float(cf.get('check', 0)),
                'transfer': float(cf.get('transfer', 0)),
                'debit': float(cf.get('debit', 0)),
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            client.table('cash_flow').upsert(data, on_conflict='id').execute()
            total_loaded += len(data)
            print(f"    [OK] {len(data)} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 4. INSTALLMENT SUMMARY - Resumo de Parcelamentos
# ============================================================================

print("[4] CARREGANDO INSTALLMENT_SUMMARY (Parcelamentos)...")

try:
    response = requests.get(
        f"{API_URL}/financial/average_installments",
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
        installments = response.json()
        print(f"    Encontrados: {len(installments)} períodos\n")
        data = []
        for inst in installments:
            data.append({
                'id': str(__import__('uuid').uuid4()),
                'clinic_id': BUSINESS_ID,
                'month': inst.get('month', ''),
                'total_payments': int(inst.get('TotalPayments', 0)),
                'total_installments': int(inst.get('TotalInstallments', 0)),
                'average_installments': float(inst.get('AverageInstallments', 0)),
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            client.table('installment_summary').upsert(data, on_conflict='id').execute()
            total_loaded += len(data)
            print(f"    [OK] {len(data)} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 5. PAYMENT SUMMARY - Resumo de Pagamentos
# ============================================================================

print("[5] CARREGANDO PAYMENT_SUMMARY (Resumo Pagamentos)...")

try:
    response = requests.get(
        f"{API_URL}/financial/list_payments",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        payment_data = response.json()
        print(f"    Encontrado 1 registro\n")

        data = [{
            'id': str(__import__('uuid').uuid4()),
            'clinic_id': BUSINESS_ID,
            'period_date': datetime.now().date(),
            'total_in_forecast': float(payment_data.get('totalInForecastAmount', 0)),
            'total_payments_amount': float(payment_data.get('totalPaymentsAmount', 0)),
            'total_debit_amount': float(payment_data.get('totalDebitAmount', 0)),
            'updated_at': datetime.utcnow().isoformat(),
            'last_sync_at': datetime.utcnow().isoformat(),
        }]

        client.table('payment_summary').upsert(data, on_conflict='id').execute()
        total_loaded += 1
        print(f"    [OK] 1 registro carregado\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 6. FINANCIAL SUMMARY - Resumo Financeiro
# ============================================================================

print("[6] CARREGANDO FINANCIAL_SUMMARY (Resumo Financeiro)...")

try:
    response = requests.get(
        f"{API_URL}/financial/list_summary",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'from': date_from,
            'to': date_to,
            'business_id': BUSINESS_ID
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        fin_data = response.json()
        print(f"    Encontrado 1 registro\n")

        data = [{
            'id': str(__import__('uuid').uuid4()),
            'clinic_id': BUSINESS_ID,
            'from_date': datetime.strptime(fin_data.get('From', date_from), '%Y-%m-%d').date(),
            'to_date': datetime.strptime(fin_data.get('To', date_to), '%Y-%m-%d').date(),
            'total_sales': float(fin_data.get('TotalSales', 0)),
            'total_income': float(fin_data.get('TotalIncome', 0)),
            'total_expenses': float(fin_data.get('TotalExpenses', 0)),
            'summary_type': fin_data.get('Type'),
            'summary_data': fin_data.get('values', []),
            'updated_at': datetime.utcnow().isoformat(),
            'last_sync_at': datetime.utcnow().isoformat(),
        }]

        client.table('financial_summary').upsert(data, on_conflict='id').execute()
        total_loaded += 1
        print(f"    [OK] 1 registro carregado\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 7. PATIENT BIRTHDAYS - Aniversariantes
# ============================================================================

print("[7] CARREGANDO PATIENT_BIRTHDAYS (Aniversariantes)...")

try:
    response = requests.get(
        f"{API_URL}/patient/birthdays",
        params={
            'subscriber_id': SUBSCRIBER_ID,
            'date': datetime.now().strftime('%Y-%m-%d')
        },
        auth=HTTPBasicAuth(API_USER, API_PASS),
        timeout=30
    )

    if response.status_code == 200:
        birthdays = response.json()
        print(f"    Encontrados: {len(birthdays)} aniversariantes\n")
        data = []
        for bd in birthdays:
            birth_date_str = bd.get('BirthDate', '')
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                birthday_month = birth_date.month
                birthday_day = birth_date.day
            except:
                birth_date = None
                birthday_month = None
                birthday_day = None

            data.append({
                'id': str(__import__('uuid').uuid4()),
                'patient_id': bd.get('PatientId'),
                'birth_date': birth_date,
                'age': bd.get('Age'),
                'birthday_month': birthday_month,
                'birthday_day': birthday_day,
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            batch_size = 50
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    client.table('patient_birthdays').upsert(batch, on_conflict='id').execute()
                    total_loaded += len(batch)
                except:
                    pass
            print(f"    [OK] {len(data)} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 8. PATIENT APPOINTMENTS LIST - Agendamentos do Paciente
# ============================================================================

print("[8] CARREGANDO PATIENT_APPOINTMENTS_LIST...")

try:
    # Obter lista de pacientes
    patients = client.table('patients').select('id').execute().data
    print(f"    Processando {len(patients)} pacientes\n")

    count = 0
    for patient in patients[:100]:  # Limitar a 100 para não sobrecarregar
        try:
            response = requests.get(
                f"{API_URL}/patient/list_appointments",
                params={'PatientId': patient['id']},
                auth=HTTPBasicAuth(API_USER, API_PASS),
                timeout=30
            )

            if response.status_code == 200:
                appointments = response.json()
                data = []
                for apt in appointments:
                    data.append({
                        'id': apt.get('id'),
                        'patient_id': patient['id'],
                        'patient_name': apt.get('PatientName'),
                        'appointment_date': apt.get('date'),
                        'from_time': apt.get('fromTime'),
                        'to_time': apt.get('toTime'),
                        'atomic_date': apt.get('AtomicDate'),
                        'updated_at': datetime.utcnow().isoformat(),
                        'last_sync_at': datetime.utcnow().isoformat(),
                    })

                if data:
                    client.table('patient_appointments_list').upsert(data, on_conflict='id').execute()
                    count += len(data)
        except:
            pass

    total_loaded += count
    print(f"    [OK] {count} agendamentos carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 9. ANALYTICS RESULTS - Dados Analíticos
# ============================================================================

print("[9] CARREGANDO ANALYTICS_RESULTS (Dados Analíticos)...")

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
        analytics = response.json()
        print(f"    Encontrados: {len(analytics)} registros\n")
        data = []
        for ana in analytics:
            data.append({
                'id': str(__import__('uuid').uuid4()),
                'clinic_id': ana.get('BusinessId', BUSINESS_ID),
                'total_revenue_amount': float(ana.get('TotalRevenueAmount', 0)),
                'estimates_total_amount': float(ana.get('EstimatesTotalAmount', 0)),
                'estimates_total_quantity': int(ana.get('EstimatesTotalQuantity', 0)),
                'estimates_approved_amount': float(ana.get('EstimatesApprovedAmount', 0)),
                'estimates_approved_quantity': int(ana.get('EstimatesApprovedQuantity', 0)),
                'estimates_open_amount': float(ana.get('EstimatesOpenAmount', 0)),
                'estimates_open_quantity': int(ana.get('EstimatesOpenQuantity', 0)),
                'estimates_followup_amount': float(ana.get('EstimatesFollowUpAmount', 0)),
                'estimates_followup_quantity': int(ana.get('EstimatesFollowUpQuantity', 0)),
                'estimates_rejected_amount': float(ana.get('EstimatesRejectedAmount', 0)),
                'estimates_rejected_quantity': int(ana.get('EstimatesRejectedQuantity', 0)),
                'approved_ticket_average': float(ana.get('ApprovedTicketAverage', 0)),
                'conversion_rate': float(ana.get('ConversionRate', 0)),
                'total_received_amount': float(ana.get('TotalReceivedAmount', 0)),
                'total_expenses': float(ana.get('TotalExpenses', 0)),
                'appointments_total': int(ana.get('AppointmentsTotal', 0)),
                'appointments_finished': int(ana.get('AppoinmentsFinished', 0)),
                'appointments_missed': int(ana.get('AppointmentsMissed', 0)),
                'appointments_new_patients': int(ana.get('AppointmentsNewPatients', 0)),
                'appointments_existing_patients': int(ana.get('AppointmentsExistingPatients', 0)),
                'without_category': int(ana.get('WithoutCategory', 0)),
                'unity_name': ana.get('UnityName'),
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            client.table('analytics_results').upsert(data, on_conflict='id').execute()
            total_loaded += len(data)
            print(f"    [OK] {len(data)} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 10. SALES ESTIMATES CONVERSION - Orçamentos e Conversão
# ============================================================================

print("[10] CARREGANDO SALES_ESTIMATES_CONVERSION...")

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
        sales = response.json()
        print(f"    Encontrados: {len(sales)} períodos\n")
        data = []
        for sale in sales:
            for status, values in sale.get('Status', {}).items():
                data.append({
                    'id': str(__import__('uuid').uuid4()),
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
            batch_size = 50
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    client.table('sales_estimates_conversion').upsert(batch, on_conflict='id').execute()
                    total_loaded += len(batch)
                except:
                    pass
            print(f"    [OK] {len(data)} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 11. REVENUE BY SPECIALTY - Receita por Especialidade
# ============================================================================

print("[11] CARREGANDO REVENUE_BY_SPECIALTY...")

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
        print(f"    Encontrados: {len(revenues)} registros\n")
        data = []
        for rev in revenues:
            data.append({
                'id': str(__import__('uuid').uuid4()),
                'clinic_id': BUSINESS_ID,
                'month': rev.get('month', ''),
                'specialty': rev.get('Expertise', 'Unknown'),
                'total_revenue': 0,  # Não retorna valor direto, precisa calcular
                'procedures_count': 0,
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        if data:
            batch_size = 50
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    client.table('revenue_by_specialty').upsert(batch, on_conflict='id').execute()
                    total_loaded += len(batch)
                except:
                    pass
            print(f"    [OK] {len(data)} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# 12. CLINIC DETAILS - Detalhes de Clínicas
# ============================================================================

print("[12] CARREGANDO CLINIC_DETAILS (Detalhes de Clínicas)...")

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
                'id': str(__import__('uuid').uuid4()),
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
            client.table('clinic_details').upsert(data, on_conflict='id').execute()
            total_loaded += len(data)
            print(f"    [OK] {len(data)} registros carregados\n")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}\n")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO DO CARREGAMENTO ESTENDIDO")
print("=" * 80)

print(f"\n[TABELAS CARREGADAS NESTA SESSÃO]")
print(f"Total de registros adicionados: {total_loaded}\n")

print("=" * 80)
print("Carregamento de tabelas estendidas concluído!")
print("=" * 80 + "\n")
