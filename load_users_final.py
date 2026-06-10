#!/usr/bin/env python3
"""
Carregar USERS com emails gerados para profissionais
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))
SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("CARREGAR USERS - PROFISSIONAIS COM EMAILS GERADOS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Obter profissionais
prof_response = client.table('professionals').select('*').execute()
professionals = prof_response.data

print(f"\nProfissionais encontrados: {len(professionals)}\n")

users = []
count_with_email = 0
count_without_email = 0

for i, prof in enumerate(professionals):
    email = prof.get('email')

    # Se não tiver email, gerar um
    if not email:
        # Usar nome para gerar email
        name = prof.get('full_name', f'prof_{prof.get("id")}')
        # Remover espaços e caracteres especiais
        name_clean = name.lower().replace(' ', '.').replace('ç', 'c').replace('ã', 'a').replace('á', 'a').replace('é', 'e')
        email = f"{name_clean}@praxis.local"
        count_without_email += 1
    else:
        count_with_email += 1

    user = {
        'id': prof.get('id'),
        'clinic_id': prof.get('clinic_id') or BUSINESS_ID,
        'full_name': prof.get('full_name'),
        'email': email,
        'role': 'professional',
        'status': prof.get('status') or 'active',
        'last_login': None,
        'created_at': prof.get('created_at'),
        'updated_at': prof.get('updated_at'),
        'last_sync_at': datetime.utcnow().isoformat(),
    }
    users.append(user)

print(f"Emails existentes: {count_with_email}")
print(f"Emails gerados: {count_without_email}\n")

if len(users) > 0:
    # Inserir em lotes
    batch_size = 50
    inserted = 0

    for i in range(0, len(users), batch_size):
        batch = users[i:i+batch_size]
        try:
            client.table('users').upsert(batch, on_conflict='id').execute()
            inserted += len(batch)
            print(f"Batch {i//batch_size + 1}: {len(batch)} users inseridos")
        except Exception as e:
            print(f"Batch {i//batch_size + 1}: Erro - {str(e)[:100]}")

    print(f"\n[OK] {inserted} users carregados\n")

# Contar registros finais
try:
    usr = client.table('users').select('id', count='exact').execute().count
    print(f"Total de users no banco: {usr}")
except Exception as e:
    print(f"Erro: {str(e)[:80]}")

print("\n" + "=" * 80)
