#!/usr/bin/env python3
"""
ETL Script: Clinicorp API → Supabase
Extração inicial completa + Suporte a sincronizações incrementais

Usage:
    python etl_clinicorp.py --mode initial      # Carga inicial completa
    python etl_clinicorp.py --mode incremental  # Sincronização incremental
    python etl_clinicorp.py --mode all          # Todas as tabelas
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import argparse
from dotenv import load_dotenv

import requests
from supabase import create_client, Client
from requests.auth import HTTPBasicAuth

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

# Clinicorp API Config
CLINICORP_URL = os.getenv("ERP_CLINICORP_API_URL", "https://api.clinicorp.com") + "/rest/v1"
CLINICORP_USER = os.getenv("ERP_CLINICORP_USUARIO_API", "praxis")
CLINICORP_PASS = os.getenv("ERP_CLINICORP_API_SENHA", "")
CLINICORP_BUSINESS_ID = int(os.getenv("ERP_CLINICORP_BUSINESS_ID", "5292365675823104"))

# Supabase Config
SUPABASE_URL = os.getenv("ERP_CLINICORP_URL", "")
SUPABASE_KEY = os.getenv("ERP_SERVICE_ROLE", "")  # Use service_role for ETL

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_clinicorp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CLINICORP API CLIENT
# ============================================================================

class ClinicorpClient:
    """Client para integração com a API do Clinicorp"""

    def __init__(self, base_url: str, user: str, password: str, api_key: str):
        self.base_url = base_url
        self.user = user
        self.password = password
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        # Usar Basic Auth com user/password
        self.session.auth = HTTPBasicAuth(user, password)

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request com tratamento de erros"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar {endpoint}: {str(e)}")
            return {}

    def _post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """POST request com tratamento de erros"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer POST em {endpoint}: {str(e)}")
            return {}

    # ========== BUSINESS & CLINICS ==========
    def list_clinics(self) -> List[Dict]:
        """Retorna lista de clínicas"""
        result = self._get("/business/list", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    def list_available_times(self, clinic_id: int) -> List[Dict]:
        """Retorna horários disponíveis de uma clínica"""
        result = self._get("/business/list_available_times", params={'business_id': clinic_id})
        return result.get('data', []) if result else []

    def list_chairs(self, clinic_id: int) -> List[Dict]:
        """Retorna cadeiras/consultórios de uma clínica"""
        result = self._get("/business/list_chairs", params={'business_id': clinic_id})
        return result.get('data', []) if result else []

    # ========== USERS ==========
    def list_users(self) -> List[Dict]:
        """Retorna lista de usuários"""
        result = self._get("/security/list_users", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    # ========== PATIENTS ==========
    def list_patients(self) -> List[Dict]:
        """Retorna lista de pacientes"""
        result = self._get("/patient/list", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    def get_patient(self, patient_id: int) -> Dict:
        """Retorna detalhes de um paciente"""
        result = self._get(f"/patient/get", params={'id': patient_id, 'business_id': CLINICORP_BUSINESS_ID})
        return result.get('data', {}) if isinstance(result, dict) else {}

    # ========== APPOINTMENTS ==========
    def list_appointments(self) -> List[Dict]:
        """Retorna lista de agendamentos"""
        result = self._get("/appointment/list", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    def list_appointment_categories(self) -> List[Dict]:
        """Retorna categorias de agendamentos"""
        result = self._get("/appointment/list_categories", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    # ========== PROCEDURES ==========
    def list_procedures(self) -> List[Dict]:
        """Retorna lista de procedimentos"""
        result = self._get("/procedures/list", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    def list_specialties(self) -> List[Dict]:
        """Retorna lista de especialidades"""
        result = self._get("/procedures/list_specialties", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    # ========== PROFESSIONALS ==========
    def list_professionals(self) -> List[Dict]:
        """Retorna lista de profissionais"""
        result = self._get("/professional/list_all_professionals", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    # ========== ESTIMATES ==========
    def list_estimates(self) -> List[Dict]:
        """Retorna lista de orçamentos"""
        result = self._get("/estimates/list", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    # ========== FINANCIAL ==========
    def list_invoices(self) -> List[Dict]:
        """Retorna lista de notas fiscais"""
        result = self._get("/financial/list_invoices", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    def list_payments(self) -> List[Dict]:
        """Retorna lista de pagamentos"""
        result = self._get("/financial/list_payments", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    def list_cash_flow(self) -> List[Dict]:
        """Retorna fluxo de caixa"""
        result = self._get("/financial/list_cash_flow", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []

    # ========== CRM ==========
    def list_active_campaigns(self) -> List[Dict]:
        """Retorna campanhas ativas"""
        result = self._get("/crm/list_active_campaigns", params={'business_id': CLINICORP_BUSINESS_ID})
        if isinstance(result, dict):
            return result.get('data', [])
        elif isinstance(result, list):
            return result
        return []


# ============================================================================
# SUPABASE CLIENT WRAPPER
# ============================================================================

class SupabaseETL:
    """Wrapper para operações ETL no Supabase"""

    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
        self.logger = logger

    def upsert_data(self, table: str, data: List[Dict], id_column: str = 'id') -> Dict[str, Any]:
        """Faz upsert de dados (insert or update)"""
        if not data:
            self.logger.warning(f"Nenhum dado para upsert em {table}")
            return {'count': 0}

        try:
            # Adiciona timestamp de sync
            for record in data:
                record['last_sync_at'] = datetime.utcnow().isoformat()

            result = self.client.table(table).upsert(data).execute()
            self.logger.info(f"✓ {table}: {len(data)} registros salvos")
            return {'count': len(data), 'data': result.data}
        except Exception as e:
            self.logger.error(f"✗ Erro ao fazer upsert em {table}: {str(e)}")
            return {'count': 0, 'error': str(e)}

    def get_last_sync_time(self, entity_type: str) -> Optional[datetime]:
        """Retorna o último tempo de sincronização para uma entidade"""
        try:
            result = self.client.table('sync_log') \
                .select('last_sync_time') \
                .eq('entity_type', entity_type) \
                .execute()

            if result.data and len(result.data) > 0:
                return datetime.fromisoformat(result.data[0]['last_sync_time'])
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter último sync de {entity_type}: {str(e)}")
            return None

    def update_sync_log(self, entity_type: str, count: int, status: str = 'completed',
                       error: Optional[str] = None):
        """Atualiza o log de sincronização"""
        try:
            sync_data = {
                'entity_type': entity_type,
                'last_sync_time': datetime.utcnow().isoformat(),
                'last_sync_count': count,
                'status': status,
                'error_message': error,
                'updated_at': datetime.utcnow().isoformat()
            }

            # Tenta atualizar, se não existir, insere
            self.client.table('sync_log').upsert(sync_data).execute()
            self.logger.info(f"✓ Sync log atualizado: {entity_type} ({count} registros)")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar sync_log para {entity_type}: {str(e)}")


# ============================================================================
# ETL PIPELINE
# ============================================================================

class ClinicorpETL:
    """Pipeline ETL: Clinicorp → Supabase"""

    def __init__(self, clinicorp_client: ClinicorpClient, supabase_etl: SupabaseETL):
        self.clinicorp = clinicorp_client
        self.supabase = supabase_etl
        self.logger = logger

    def run_full_extraction(self, mode: str = 'initial'):
        """Executa extração dos dados disponíveis"""
        self.logger.info("=" * 80)
        self.logger.info(f"Iniciando ETL - Modo: {mode}")
        self.logger.info("=" * 80)

        # Apenas endpoints que funcionam sem subscriber_id
        extraction_map = {
            'professionals': (self.extract_professionals, 'professionals'),
            'procedures': (self.extract_procedures, 'procedures'),
        }

        results = {}
        for entity_name, (extractor_func, table_name) in extraction_map.items():
            try:
                self.logger.info(f"\n[*] Extraindo {entity_name}...")
                data = extractor_func()

                if data:
                    result = self.supabase.upsert_data(table_name, data)
                    self.supabase.update_sync_log(entity_name, result.get('count', 0))
                    results[entity_name] = result
                else:
                    self.logger.warning(f"[!] Nenhum dado extraido para {entity_name}")
                    self.supabase.update_sync_log(entity_name, 0, status='completed')

            except Exception as e:
                self.logger.error(f"✗ Erro ao processar {entity_name}: {str(e)}")
                self.supabase.update_sync_log(entity_name, 0, status='failed', error=str(e))
                results[entity_name] = {'error': str(e)}

        self.logger.info("\n" + "=" * 80)
        self.logger.info("RESUMO DA EXTRAÇÃO")
        self.logger.info("=" * 80)
        for entity, result in results.items():
            count = result.get('count', 0)
            status = "✓" if not result.get('error') else "✗"
            self.logger.info(f"{status} {entity}: {count} registros")

        return results

    # ========== EXTRACTORS ==========

    def extract_clinics(self) -> List[Dict]:
        """Extrai clínicas"""
        clinics = self.clinicorp.list_clinics()
        processed = []
        for clinic in clinics:
            processed.append({
                'id': clinic.get('id'),
                'name': clinic.get('name'),
                'business_id': CLINICORP_BUSINESS_ID,
                'type': clinic.get('type'),
                'status': clinic.get('status'),
                'updated_at': datetime.utcnow().isoformat() if clinic.get('updated_at') else None,
            })
        return processed

    def extract_users(self) -> List[Dict]:
        """Extrai usuários"""
        users = self.clinicorp.list_users()
        processed = []
        for user in users:
            processed.append({
                'id': user.get('id'),
                'clinic_id': user.get('clinic_id') or CLINICORP_BUSINESS_ID,
                'full_name': user.get('full_name') or user.get('name'),
                'email': user.get('email'),
                'role': user.get('role'),
                'status': user.get('status'),
                'updated_at': datetime.utcnow().isoformat() if user.get('updated_at') else None,
            })
        return processed

    def extract_patients(self) -> List[Dict]:
        """Extrai pacientes"""
        patients = self.clinicorp.list_patients()
        processed = []
        for patient in patients:
            processed.append({
                'id': patient.get('id'),
                'clinic_id': patient.get('clinic_id') or CLINICORP_BUSINESS_ID,
                'full_name': patient.get('full_name') or patient.get('name'),
                'email': patient.get('email'),
                'phone': patient.get('phone'),
                'cpf': patient.get('cpf'),
                'date_of_birth': patient.get('date_of_birth'),
                'gender': patient.get('gender'),
                'marital_status': patient.get('marital_status'),
                'status': patient.get('status'),
                'updated_at': datetime.utcnow().isoformat() if patient.get('updated_at') else None,
            })
        return processed

    def extract_professionals(self) -> List[Dict]:
        """Extrai profissionais"""
        professionals = self.clinicorp.list_professionals()
        processed = []
        for prof in professionals:
            processed.append({
                'id': prof.get('id'),
                'clinic_id': CLINICORP_BUSINESS_ID,
                'full_name': prof.get('name'),  # API retorna 'name', não 'full_name'
                'email': prof.get('email'),
                'phone': prof.get('phone'),
                'cpf': prof.get('cpf'),
                'license_number': prof.get('license_number'),
                'specialty': prof.get('specialty'),
                'status': prof.get('status'),
                'updated_at': None,  # API não fornece updated_at
            })
        return processed

    def extract_appointments(self) -> List[Dict]:
        """Extrai agendamentos"""
        appointments = self.clinicorp.list_appointments()
        processed = []
        for appt in appointments:
            processed.append({
                'id': appt.get('id'),
                'clinic_id': appt.get('clinic_id') or CLINICORP_BUSINESS_ID,
                'patient_id': appt.get('patient_id'),
                'professional_id': appt.get('professional_id'),
                'scheduled_date': appt.get('scheduled_date'),
                'duration_minutes': appt.get('duration_minutes'),
                'status': appt.get('status'),
                'notes': appt.get('notes'),
                'reason_cancellation': appt.get('reason_cancellation'),
                'updated_at': datetime.utcnow().isoformat() if appt.get('updated_at') else None,
            })
        return processed

    def extract_procedures(self) -> List[Dict]:
        """Extrai procedimentos"""
        procedures = self.clinicorp.list_procedures()
        processed = []
        for proc in procedures:
            processed.append({
                'id': proc.get('id'),
                'clinic_id': proc.get('clinic_id') or CLINICORP_BUSINESS_ID,
                'appointment_id': proc.get('appointment_id'),
                'name': proc.get('name'),
                'specialty': proc.get('specialty'),
                'description': proc.get('description'),
                'price': proc.get('price'),
                'duration_minutes': proc.get('duration_minutes'),
                'status': proc.get('status'),
                'updated_at': datetime.utcnow().isoformat() if proc.get('updated_at') else None,
            })
        return processed

    def extract_estimates(self) -> List[Dict]:
        """Extrai orçamentos"""
        estimates = self.clinicorp.list_estimates()
        processed = []
        for est in estimates:
            processed.append({
                'id': est.get('id'),
                'clinic_id': est.get('clinic_id') or CLINICORP_BUSINESS_ID,
                'patient_id': est.get('patient_id'),
                'professional_id': est.get('professional_id'),
                'total_amount': est.get('total_amount'),
                'discount_amount': est.get('discount_amount', 0),
                'net_amount': est.get('net_amount'),
                'status': est.get('status'),
                'items_count': est.get('items_count'),
                'valid_until': est.get('valid_until'),
                'updated_at': datetime.utcnow().isoformat() if est.get('updated_at') else None,
            })
        return processed

    def extract_invoices(self) -> List[Dict]:
        """Extrai faturas"""
        invoices = self.clinicorp.list_invoices()
        processed = []
        for inv in invoices:
            processed.append({
                'id': inv.get('id'),
                'clinic_id': inv.get('clinic_id') or CLINICORP_BUSINESS_ID,
                'patient_id': inv.get('patient_id'),
                'number': inv.get('number'),
                'total_amount': inv.get('total_amount'),
                'paid_amount': inv.get('paid_amount', 0),
                'due_date': inv.get('due_date'),
                'issue_date': inv.get('issue_date'),
                'status': inv.get('status'),
                'payment_method': inv.get('payment_method'),
                'updated_at': datetime.utcnow().isoformat() if inv.get('updated_at') else None,
            })
        return processed

    def extract_payments(self) -> List[Dict]:
        """Extrai pagamentos"""
        payments = self.clinicorp.list_payments()
        processed = []
        for pay in payments:
            processed.append({
                'id': pay.get('id'),
                'clinic_id': pay.get('clinic_id') or CLINICORP_BUSINESS_ID,
                'invoice_id': pay.get('invoice_id'),
                'patient_id': pay.get('patient_id'),
                'amount': pay.get('amount'),
                'payment_method': pay.get('payment_method'),
                'payment_date': pay.get('payment_date'),
                'reference': pay.get('reference'),
                'status': pay.get('status', 'completed'),
                'notes': pay.get('notes'),
                'updated_at': datetime.utcnow().isoformat() if pay.get('updated_at') else None,
            })
        return processed

    def extract_leads(self) -> List[Dict]:
        """Extrai leads"""
        campaigns = self.clinicorp.list_active_campaigns()
        leads = []

        for campaign in campaigns:
            campaign_leads = campaign.get('leads', [])
            for lead in campaign_leads:
                leads.append({
                    'id': lead.get('id'),
                    'clinic_id': lead.get('clinic_id') or CLINICORP_BUSINESS_ID,
                    'name': lead.get('name'),
                    'email': lead.get('email'),
                    'phone': lead.get('phone'),
                    'source': campaign.get('name'),
                    'status': lead.get('status'),
                    'notes': lead.get('notes'),
                    'updated_at': datetime.utcnow().isoformat() if lead.get('updated_at') else None,
                })

        return leads


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='ETL Clinicorp → Supabase')
    parser.add_argument('--mode', choices=['initial', 'incremental', 'all'],
                       default='initial',
                       help='Modo de extração')
    args = parser.parse_args()

    try:
        # Inicializa clientes
        clinicorp = ClinicorpClient(CLINICORP_URL, CLINICORP_USER, CLINICORP_PASS, "")
        supabase = SupabaseETL(SUPABASE_URL, SUPABASE_KEY)
        etl = ClinicorpETL(clinicorp, supabase)

        # Executa pipeline
        results = etl.run_full_extraction(mode=args.mode)

        logger.info("\n✓ ETL concluído com sucesso!")
        return 0

    except Exception as e:
        logger.error(f"✗ Erro fatal: {str(e)}")
        return 1


if __name__ == '__main__':
    exit(main())
