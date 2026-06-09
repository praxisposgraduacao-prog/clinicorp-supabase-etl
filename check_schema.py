#!/usr/bin/env python3
"""
Verificar schema das tabelas estimates e sales_summary no Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")

print("=" * 80)
print("VERIFICAR SCHEMA DAS TABELAS")
print("=" * 80)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tentar obter informações sobre as tabelas
tables_to_check = ['estimates', 'sales_summary']

for table_name in tables_to_check:
    print(f"\n[{table_name}]")

    try:
        # Tentar ler um registro vazio para ver o schema
        response = client.table(table_name).select('*').limit(1).execute()

        if len(response.data) > 0:
            record = response.data[0]
            print(f"  Registros existentes: Sim")
            print(f"  Colunas encontradas:")
            for key in record.keys():
                print(f"    - {key}: {type(record[key]).__name__}")
        else:
            print(f"  Registros existentes: Não")
            print(f"  (Tabela vazia - schema não pode ser inferido)")
            print(f"  Tentando inserção teste para descobrir schema...")

            # Tentar descobrir quais colunas são esperadas
            try:
                test_data = {'id': 'test_id_12345'}
                client.table(table_name).insert([test_data]).execute()
                print(f"    Sucesso com: id")
                # Limpar
                client.table(table_name).delete().eq('id', 'test_id_12345').execute()
            except Exception as e:
                error_msg = str(e)
                print(f"    Erro: {error_msg[:200]}")

                # Extrair quais colunas são obrigatórias
                if 'required' in error_msg.lower() or 'not null' in error_msg.lower():
                    print(f"    Colunas obrigatórias não identificadas no erro")

    except Exception as e:
        print(f"  [ERROR] {str(e)[:200]}")

print("\n" + "=" * 80)
