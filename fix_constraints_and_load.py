#!/usr/bin/env python3
"""
Script para:
1. Alterar constraints na tabela payments
2. Recarregar os 474 pagamentos
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
print("CORRIGIR CONSTRAINTS E CARREGAR PAGAMENTOS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# PASSO 1: REMOVER CONSTRAINT DE NOT NULL EM invoice_id
# ============================================================================

print("\n[1] REMOVENDO CONSTRAINT NOT NULL de payments.invoice_id...")

try:
    # Executar SQL para alterar a constraint
    client.postgrest.execute_sql("""
        ALTER TABLE payments
        ALTER COLUMN invoice_id DROP NOT NULL;
    """).execute()
    print("    [OK] Constraint removido!")
except Exception as e:
    # Se usar supabase-py, talvez use outro método
    try:
        # Tentar via rpc se disponível
        client.rpc("execute_sql", {
            "sql": "ALTER TABLE payments ALTER COLUMN invoice_id DROP NOT NULL;"
        }).execute()
        print("    [OK] Constraint removido!")
    except:
        print(f"    [INFO] Constraint pode já estar removido ou erro: {str(e)[:80]}")

# ============================================================================
# PASSO 2: CARREGAR PAGAMENTOS
# ============================================================================

print("\n[2] CARREGANDO PAGAMENTOS...")

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
date_from = start_date.strftime("%Y-%m-%d")
date_to = end_date.strftime("%Y-%m-%d")

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

    if response.status_code == 200:
        payments = response.json()
        print(f"    API retornou: {len(payments)} pagamentos")

        if len(payments) > 0:
            # Coletar clinics e patients
            clinic_ids = set()
            patient_ids = set()

            for pay in payments:
                clinic_id = pay.get('ReceiverBusinessId', BUSINESS_ID)
                clinic_ids.add(clinic_id)
                patient_id = pay.get('PatientId')
                if patient_id:
                    patient_ids.add(patient_id)

            # Criar clínicas
            print(f"    Criando {len(clinic_ids)} clínicas...")
            clinic_data = []
            for cid in clinic_ids:
                clinic_data.append({
                    'id': cid,
                    'business_id': cid,
                    'name': f"Clinic {cid}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })
            try:
                client.table('clinics').upsert(clinic_data, on_conflict='id').execute()
                print(f"    OK")
            except Exception as e:
                print(f"    WARN: {str(e)[:60]}")

            # Criar pacientes
            print(f"    Criando {len(patient_ids)} pacientes...")
            patient_data = []
            for pid in patient_ids:
                patient_data.append({
                    'id': pid,
                    'clinic_id': BUSINESS_ID,
                    'full_name': f"Patient {pid}",
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })
            try:
                client.table('patients').upsert(patient_data, on_conflict='id').execute()
                print(f"    OK")
            except Exception as e:
                print(f"    WARN: {str(e)[:60]}")

            # Limpar pagamentos antigos
            print(f"    Limpando pagamentos antigos...")
            try:
                client.table('payments').delete().neq('id', 0).execute()
                print(f"    OK")
            except:
                print(f"    INFO: Tabela já vazia ou erro")

            # Inserir pagamentos com fields corretos
            print(f"    Inserindo {len(payments)} pagamentos...")
            data = []
            for pay in payments:
                data.append({
                    'id': pay.get('PaymentHeaderId'),
                    'clinic_id': pay.get('ReceiverBusinessId', BUSINESS_ID),
                    'invoice_id': None,  # Agora pode ser NULL
                    'patient_id': pay.get('PatientId'),
                    'amount': float(pay.get('Amount', 0)),
                    'payment_method': pay.get('CreditCardType') or 'unknown',
                    'payment_date': pay.get('PaymentDate'),
                    'reference': pay.get('ExternalId') or '',
                    'status': 'completed' if pay.get('PaymentReceived') == 'X' else 'pending',
                    'notes': pay.get('PayerName') or '',
                    'updated_at': pay.get('ConfirmedDate') or datetime.utcnow().isoformat(),
                    'last_sync_at': datetime.utcnow().isoformat(),
                })

            # Inserir em lotes
            batch_size = 100
            inserted_count = 0

            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    client.table('payments').insert(batch).execute()
                    inserted_count += len(batch)
                    print(f"    Batch {i//batch_size + 1}: {len(batch)} inseridos")
                except Exception as e:
                    print(f"    [ERROR] Batch {i//batch_size + 1}: {str(e)[:80]}")

            print(f"\n    [OK] Total: {inserted_count} pagamentos inseridos!")

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# RESUMO FINAL
# ============================================================================

print("\n" + "=" * 80)
print("RESUMO FINAL")
print("=" * 80)

try:
    payments_count = client.table('payments').select('id', count='exact').execute().count
    print(f"\n[RESULTADO]")
    print(f"Pagamentos no banco: {payments_count}")

    if payments_count > 0:
        print(f"\n[SUCCESS] ✅ Carregamento de pagamentos concluído!")
    else:
        print(f"\n[WARNING] ⚠️ Nenhum pagamento foi inserido")

except Exception as e:
    print(f"Erro ao contar: {e}")

print("\n" + "=" * 80)
