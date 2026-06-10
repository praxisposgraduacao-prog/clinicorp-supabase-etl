#!/usr/bin/env python3
"""
Diagnóstico de erros de Foreign Key - verificar integridade referencial
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("DIAGNÓSTICO DE FOREIGN KEY ERRORS")
print("=" * 80)

# 1. Verificar tabelas pai
print("\n[1] TABELAS PAI (devem existir antes de inserir dados filhos):\n")

tables_pai = ['clinics', 'patients', 'professionals']
for table in tables_pai:
    try:
        result = client.table(table).select('count', count='exact').execute()
        count = result.count if result.count else 0
        print(f"  {table:20s}: {count:5d} registros")
    except Exception as e:
        print(f"  {table:20s}: ERROR - {str(e)[:60]}")

# 2. Verificar tabelas filhas
print("\n[2] TABELAS FILHAS (dependem de referências das tabelas pai):\n")

tables_filhas = ['appointments', 'payments', 'invoices']
for table in tables_filhas:
    try:
        result = client.table(table).select('count', count='exact').execute()
        count = result.count if result.count else 0
        print(f"  {table:20s}: {count:5d} registros")
    except Exception as e:
        print(f"  {table:20s}: ERROR - {str(e)[:60]}")

# 3. Verificar referências - appointments vs patients e professionals
print("\n[3] VALIDAÇÃO DE REFERÊNCIAS - APPOINTMENTS:\n")

try:
    # Buscar alguns appointments
    apts = client.table('appointments').select('id, patient_id, professional_id').limit(10).execute()

    if apts.data:
        patient_ids = set([apt.get('patient_id') for apt in apts.data if apt.get('patient_id')])
        prof_ids = set([apt.get('professional_id') for apt in apts.data if apt.get('professional_id')])

        print(f"  Sample patients em appointments: {patient_ids}")
        print(f"  Sample professionals em appointments: {prof_ids}")

        # Verificar se existem
        if patient_ids:
            for pid in list(patient_ids)[:3]:
                try:
                    patient = client.table('patients').select('id').eq('id', pid).execute()
                    status = "EXISTS" if patient.data else "MISSING"
                    print(f"    Patient {pid}: {status}")
                except:
                    print(f"    Patient {pid}: ERROR")

        if prof_ids:
            for prof_id in list(prof_ids)[:3]:
                try:
                    prof = client.table('professionals').select('id').eq('id', prof_id).execute()
                    status = "EXISTS" if prof.data else "MISSING"
                    print(f"    Professional {prof_id}: {status}")
                except:
                    print(f"    Professional {prof_id}: ERROR")
    else:
        print("  Sem dados em appointments")

except Exception as e:
    print(f"  ERROR: {str(e)}")

# 4. Verificar referências - payments vs patients
print("\n[4] VALIDAÇÃO DE REFERÊNCIAS - PAYMENTS:\n")

try:
    pays = client.table('payments').select('id, patient_id').limit(10).execute()

    if pays.data:
        patient_ids = set([pay.get('patient_id') for pay in pays.data if pay.get('patient_id')])
        print(f"  Sample patients em payments: {patient_ids}")

        if patient_ids:
            for pid in list(patient_ids)[:3]:
                try:
                    patient = client.table('patients').select('id').eq('id', pid).execute()
                    status = "EXISTS" if patient.data else "MISSING"
                    print(f"    Patient {pid}: {status}")
                except:
                    print(f"    Patient {pid}: ERROR")
    else:
        print("  Sem dados em payments")

except Exception as e:
    print(f"  ERROR: {str(e)}")

# 5. Verificar referências - invoices vs patients
print("\n[5] VALIDAÇÃO DE REFERÊNCIAS - INVOICES:\n")

try:
    invs = client.table('invoices').select('id, patient_id').limit(10).execute()

    if invs.data:
        patient_ids = set([inv.get('patient_id') for inv in invs.data if inv.get('patient_id')])
        print(f"  Sample patients em invoices: {patient_ids}")

        if patient_ids:
            for pid in list(patient_ids)[:3]:
                try:
                    patient = client.table('patients').select('id').eq('id', pid).execute()
                    status = "EXISTS" if patient.data else "MISSING"
                    print(f"    Patient {pid}: {status}")
                except:
                    print(f"    Patient {pid}: ERROR")
    else:
        print("  Sem dados em invoices")

except Exception as e:
    print(f"  ERROR: {str(e)}")

print("\n" + "=" * 80)
print("DIAGNÓSTICO CONCLUÍDO")
print("=" * 80)
