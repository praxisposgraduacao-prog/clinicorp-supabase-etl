#!/usr/bin/env python3
"""
Aplicar SQL fix e recarregar pagamentos
"""

import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client
from datetime import datetime, timedelta
import time

load_dotenv()

API_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
API_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
API_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUBSCRIBER_ID = os.getenv("ERP_CLINICORP_SUBSCRIBER_ID", "praxis")

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("APLICAR FIX SQL E RECARREGAR PAGAMENTOS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# PASSO 1: APLICAR FIX SQL
# ============================================================================

print("\n[1] APLICANDO FIX SQL...")
print("    Alterando constraint em payments.clinic_id\n")

try:
    # Tentar método 1: via rpc
    result = client.rpc('exec_sql', {
        'sql': 'ALTER TABLE payments ALTER COLUMN clinic_id DROP NOT NULL;'
    }).execute()
    print("    [OK] SQL executado via RPC")

except Exception as e:
    print(f"    [INFO] RPC não disponível, tentando alternativa...")
    print(f"    (Erro: {str(e)[:60]})\n")

    # Método alternativo: usar query builder para verificar
    try:
        # Tentar inserir um pagamento sem clinic_id para testar
        test_record = {
            'id': 9999999999999999,
            'clinic_id': None,
            'invoice_id': None,
            'patient_id': None,
            'amount': 0,
            'payment_method': 'test',
            'payment_date': datetime.utcnow().isoformat(),
            'reference': 'test',
            'status': 'test',
            'updated_at': datetime.utcnow().isoformat(),
            'last_sync_at': datetime.utcnow().isoformat(),
        }

        client.table('payments').insert([test_record]).execute()
        print("    [OK] Constraint já removido (teste passou)\n")

        # Limpar teste
        try:
            client.table('payments').delete().eq('id', 9999999999999999).execute()
        except:
            pass

    except Exception as e2:
        if 'NOT NULL' in str(e2):
            print(f"    [WARN] Constraint ainda está ativo")
            print(f"    Erro: {str(e2)[:80]}\n")
        else:
            print(f"    [INFO] Outro erro: {str(e2)[:80]}\n")

# ============================================================================
# PASSO 2: OBTER PAGAMENTOS DA API
# ============================================================================

print("[2] OBTENDO PAGAMENTOS DA API...")

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
        print(f"    OK - {len(payments)} pagamentos obtidos\n")

        # ============================================================================
        # PASSO 3: PREPARAR DADOS
        # ============================================================================

        print(f"[3] PREPARANDO DADOS...")

        payment_data = []
        clinic_ids = set()
        patient_ids = set()

        for pay in payments:
            clinic_id = pay.get('ReceiverBusinessId', BUSINESS_ID)
            clinic_ids.add(clinic_id)
            patient_id = pay.get('PatientId')
            if patient_id:
                patient_ids.add(patient_id)

            payment_data.append({
                'id': pay.get('PaymentHeaderId'),
                'clinic_id': clinic_id,
                'invoice_id': None,
                'patient_id': patient_id,
                'amount': float(pay.get('Amount', 0)),
                'payment_method': pay.get('CreditCardType') or 'unknown',
                'payment_date': pay.get('PaymentDate'),
                'reference': pay.get('ExternalId') or '',
                'status': 'completed' if pay.get('PaymentReceived') == 'X' else 'pending',
                'notes': pay.get('PayerName') or '',
                'updated_at': pay.get('ConfirmedDate') or datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            })

        print(f"    OK\n")

        # ============================================================================
        # PASSO 4: GARANTIR CLINICAS E PACIENTES
        # ============================================================================

        print(f"[4] GARANTINDO CLINICAS E PACIENTES...")

        clinic_data_list = [
            {
                'id': cid,
                'business_id': cid,
                'name': f"Clinic {cid}",
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            }
            for cid in clinic_ids
        ]

        try:
            client.table('clinics').upsert(clinic_data_list, on_conflict='id').execute()
            print(f"    Clinicas: OK")
        except Exception as e:
            print(f"    Clinicas: {str(e)[:60]}")

        patient_data_list = [
            {
                'id': pid,
                'clinic_id': BUSINESS_ID,
                'full_name': f"Patient {pid}",
                'updated_at': datetime.utcnow().isoformat(),
                'last_sync_at': datetime.utcnow().isoformat(),
            }
            for pid in patient_ids
        ]

        try:
            client.table('patients').upsert(patient_data_list, on_conflict='id').execute()
            print(f"    Pacientes: OK\n")
        except Exception as e:
            print(f"    Pacientes: {str(e)[:60]}\n")

        # ============================================================================
        # PASSO 5: LIMPAR E CARREGAR PAGAMENTOS
        # ============================================================================

        print(f"[5] CARREGANDO {len(payment_data)} PAGAMENTOS...")

        try:
            # Limpar
            print(f"    Limpando pagamentos antigos...")
            client.table('payments').delete().neq('id', 0).execute()
            time.sleep(0.5)
        except:
            pass

        # Inserir em lotes
        batch_size = 100
        inserted = 0
        failed = 0

        for i in range(0, len(payment_data), batch_size):
            batch = payment_data[i:i+batch_size]
            batch_num = i // batch_size + 1

            try:
                client.table('payments').insert(batch).execute()
                inserted += len(batch)
                print(f"    Batch {batch_num}: {len(batch)} ✓")

            except Exception as e:
                error_msg = str(e)
                if 'duplicate' in error_msg:
                    print(f"    Batch {batch_num}: Duplicatas encontradas")
                    # Tentar update
                    for record in batch:
                        try:
                            client.table('payments').update(record).eq('id', record['id']).execute()
                            inserted += 1
                        except:
                            failed += 1
                else:
                    print(f"    Batch {batch_num}: ERRO - {error_msg[:60]}")
                    failed += len(batch)

        print(f"\n    Total: {inserted} inseridos")
        if failed > 0:
            print(f"    Falhas: {failed}\n")
        else:
            print()

except Exception as e:
    print(f"    [ERROR] {str(e)[:100]}")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

try:
    payments_count = client.table('payments').select('id', count='exact').execute().count

    print(f"\n[PAGAMENTOS NO BANCO]")
    print(f"Total: {payments_count}")

    if payments_count > 0:
        print(f"\n[SUCCESS] ✅ {payments_count} pagamentos carregados com sucesso!")

        # Resumo geral
        prof = client.table('professionals').select('id', count='exact').execute().count
        pat = client.table('patients').select('id', count='exact').execute().count
        apt = client.table('appointments').select('id', count='exact').execute().count
        inv = client.table('invoices').select('id', count='exact').execute().count

        total = prof + pat + apt + inv + payments_count

        print(f"\n[RESUMO GERAL DO BANCO]")
        print(f"Profissionais.....: {prof}")
        print(f"Pacientes.........: {pat}")
        print(f"Agendamentos......: {apt}")
        print(f"Faturas..........: {inv}")
        print(f"Pagamentos........: {payments_count}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"TOTAL.............: {total} registros")

    else:
        print(f"\n[WARNING] Nenhum pagamento foi inserido")
        print(f"Possíveis causas:")
        print(f"  1. Constraint ainda ativo (NOT NULL)")
        print(f"  2. Foreign key ainda com problema")
        print(f"  3. RLS policy bloqueando insert")

except Exception as e:
    print(f"Erro ao contar: {e}")

print("\n" + "=" * 80)
