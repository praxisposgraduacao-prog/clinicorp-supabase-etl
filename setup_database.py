#!/usr/bin/env python3
"""
Script para criar as tabelas no Supabase em partes menores
Executa o schema.sql dividido em blocos SQL
"""

import os
import logging
from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Erro: psycopg2 não instalado")
    print("Execute: pip install psycopg2-binary")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Credenciais Supabase
SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "").replace("https://", "").replace(".supabase.co", "")
SUPABASE_PASSWORD = os.getenv("ERP_CLINICORP_PSWD", "")

# Connection string para Postgres
DB_HOST = f"{SUPABASE_URL}.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = SUPABASE_PASSWORD
DB_PORT = 5432

def split_sql_statements(sql_content: str) -> list:
    """Divide o SQL em statements individuais"""
    statements = []
    current = ""

    for line in sql_content.split('\n'):
        # Ignora comentários e linhas vazias
        stripped = line.strip()
        if stripped.startswith('--') or not stripped:
            continue

        current += line + "\n"

        # Statement completo termina com ;
        if stripped.endswith(';'):
            statements.append(current.strip())
            current = ""

    return [s for s in statements if s]  # Remove vazios


def execute_schema():
    """Executa o schema.sql no banco de dados em partes menores"""

    try:
        # Conecta ao banco de dados
        logger.info(f"Conectando ao Supabase: {DB_HOST}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode='require',
            connect_timeout=10
        )

        cursor = conn.cursor()
        logger.info("✓ Conectado com sucesso\n")

        # Lê o arquivo schema.sql
        logger.info("Lendo schema.sql...")
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Divide em statements menores
        statements = split_sql_statements(schema_sql)
        logger.info(f"✓ {len(statements)} statements identificados\n")

        # Executa cada statement
        success_count = 0
        error_count = 0

        for i, statement in enumerate(statements, 1):
            try:
                # Mostra o tipo de statement
                stmt_type = statement.split()[0].upper()

                logger.info(f"[{i}/{len(statements)}] {stmt_type}...", end=' ')
                cursor.execute(statement)
                conn.commit()
                logger.info("✓")
                success_count += 1

            except Exception as e:
                logger.error(f"✗")
                logger.error(f"   Erro: {str(e)}\n")
                error_count += 1
                # Continua mesmo com erro
                conn.rollback()

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"✓ {success_count} statements executados")
        logger.info(f"✗ {error_count} erros")
        logger.info("=" * 60 + "\n")

        # Verifica as tabelas criadas
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        logger.info(f"✓ {len(tables)} tabelas criadas no banco:")
        for table in tables:
            logger.info(f"  • {table[0]}")

        cursor.close()
        conn.close()

        logger.info("\n✓ Setup concluído com sucesso!")
        return error_count == 0

    except psycopg2.OperationalError as e:
        logger.error(f"✗ Erro de conexão: {str(e)}")
        logger.error("Verifique as credenciais no .env")
        return False
    except Exception as e:
        logger.error(f"✗ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = execute_schema()
    exit(0 if success else 1)
