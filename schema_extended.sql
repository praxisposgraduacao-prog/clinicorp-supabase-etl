-- ============================================================================
-- CLINICORP EXTENDED SCHEMA - NOVAS TABELAS
-- Adiciona 20+ tabelas para cobertura completa da API
-- ============================================================================

-- ============================================================================
-- OPERACIONAL - CADEIRAS E DISPONIBILIDADE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.chairs (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_chairs_clinic_id ON public.chairs(clinic_id);

-- ============================================================================
-- DISPONIBILIDADE DE HORÁRIOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.available_times (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professional_id BIGINT NOT NULL REFERENCES public.professionals(id),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    available_date DATE NOT NULL,
    slot_time TIME,
    from_time TIME,
    to_time TIME,
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_available_times_professional_id ON public.available_times(professional_id);
CREATE INDEX idx_available_times_clinic_id ON public.available_times(clinic_id);
CREATE INDEX idx_available_times_date ON public.available_times(available_date);

-- ============================================================================
-- RECIBOS E RECEITAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.receipts (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    patient_id BIGINT NOT NULL REFERENCES public.patients(id),
    reference_id BIGINT,
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    receipt_date DATE,
    receiver_business_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_receipts_clinic_id ON public.receipts(clinic_id);
CREATE INDEX idx_receipts_patient_id ON public.receipts(patient_id);
CREATE INDEX idx_receipts_receipt_date ON public.receipts(receipt_date);

-- ============================================================================
-- FLUXO DE CAIXA
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.cash_flow (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    month VARCHAR(7) NOT NULL,
    inflow DECIMAL(12, 2) DEFAULT 0,
    outflow DECIMAL(12, 2) DEFAULT 0,
    inflow_forecast DECIMAL(12, 2) DEFAULT 0,
    outflow_forecast DECIMAL(12, 2) DEFAULT 0,
    cash DECIMAL(12, 2) DEFAULT 0,
    bank_slip DECIMAL(12, 2) DEFAULT 0,
    credit_card DECIMAL(12, 2) DEFAULT 0,
    debit_card DECIMAL(12, 2) DEFAULT 0,
    check_amount DECIMAL(12, 2) DEFAULT 0,
    transfer DECIMAL(12, 2) DEFAULT 0,
    debit DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_cash_flow_clinic_id ON public.cash_flow(clinic_id);
CREATE INDEX idx_cash_flow_month ON public.cash_flow(month);

-- ============================================================================
-- RESUMO DE PARCELAMENTOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.installment_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    month VARCHAR(7) NOT NULL,
    total_payments INTEGER DEFAULT 0,
    total_installments INTEGER DEFAULT 0,
    average_installments DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_installment_summary_clinic_id ON public.installment_summary(clinic_id);
CREATE INDEX idx_installment_summary_month ON public.installment_summary(month);

-- ============================================================================
-- RESUMO DE PAGAMENTOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.payment_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    period_date DATE NOT NULL,
    total_in_forecast DECIMAL(12, 2) DEFAULT 0,
    total_payments_amount DECIMAL(12, 2) DEFAULT 0,
    total_debit_amount DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_payment_summary_clinic_id ON public.payment_summary(clinic_id);
CREATE INDEX idx_payment_summary_period_date ON public.payment_summary(period_date);

-- ============================================================================
-- RESUMO FINANCEIRO
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.financial_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    total_sales DECIMAL(12, 2) DEFAULT 0,
    total_income DECIMAL(12, 2) DEFAULT 0,
    total_expenses DECIMAL(12, 2) DEFAULT 0,
    summary_type VARCHAR(100),
    summary_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_financial_summary_clinic_id ON public.financial_summary(clinic_id);
CREATE INDEX idx_financial_summary_from_date ON public.financial_summary(from_date);

-- ============================================================================
-- ANIVERSARIANTES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.patient_birthdays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id BIGINT NOT NULL REFERENCES public.patients(id),
    birth_date DATE NOT NULL,
    age INTEGER,
    birthday_month INTEGER,
    birthday_day INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_patient_birthdays_patient_id ON public.patient_birthdays(patient_id);
CREATE INDEX idx_patient_birthdays_birthday_month ON public.patient_birthdays(birthday_month);
CREATE INDEX idx_patient_birthdays_birth_date ON public.patient_birthdays(birth_date);

-- ============================================================================
-- AGENDAMENTOS DO PACIENTE (RESUMO)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.patient_appointments_list (
    id BIGINT PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES public.patients(id),
    patient_name VARCHAR(255),
    appointment_date TIMESTAMPTZ,
    from_time VARCHAR(10),
    to_time VARCHAR(10),
    atomic_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_patient_appointments_list_patient_id ON public.patient_appointments_list(patient_id);
CREATE INDEX idx_patient_appointments_list_date ON public.patient_appointments_list(appointment_date);

-- ============================================================================
-- RESUMO DE ORÇAMENTOS DO PACIENTE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.patient_estimates_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    from_date DATE,
    to_date DATE,
    approved_quantity INTEGER DEFAULT 0,
    approved_total_amount DECIMAL(12, 2) DEFAULT 0,
    followup_quantity INTEGER DEFAULT 0,
    followup_total_amount DECIMAL(12, 2) DEFAULT 0,
    open_quantity INTEGER DEFAULT 0,
    open_total_amount DECIMAL(12, 2) DEFAULT 0,
    rejected_quantity INTEGER DEFAULT 0,
    rejected_total_amount DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_patient_estimates_summary_clinic_id ON public.patient_estimates_summary(clinic_id);

-- ============================================================================
-- FATURAMENTOS POR PLANO DE SAÚDE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.insurance_claims (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    patient_id BIGINT REFERENCES public.patients(id),
    amount DECIMAL(12, 2),
    claim_number BIGINT,
    person_id BIGINT,
    patient_name VARCHAR(255),
    treatment_id BIGINT,
    procedure_name VARCHAR(255),
    price_list_name VARCHAR(255),
    atomic_date INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_insurance_claims_clinic_id ON public.insurance_claims(clinic_id);
CREATE INDEX idx_insurance_claims_patient_id ON public.insurance_claims(patient_id);
CREATE INDEX idx_insurance_claims_claim_number ON public.insurance_claims(claim_number);

-- ============================================================================
-- DADOS ANALÍTICOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.analytics_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    total_revenue_amount DECIMAL(12, 2) DEFAULT 0,
    estimates_total_amount DECIMAL(12, 2) DEFAULT 0,
    estimates_total_quantity INTEGER DEFAULT 0,
    estimates_approved_amount DECIMAL(12, 2) DEFAULT 0,
    estimates_approved_quantity INTEGER DEFAULT 0,
    estimates_open_amount DECIMAL(12, 2) DEFAULT 0,
    estimates_open_quantity INTEGER DEFAULT 0,
    estimates_followup_amount DECIMAL(12, 2) DEFAULT 0,
    estimates_followup_quantity INTEGER DEFAULT 0,
    estimates_rejected_amount DECIMAL(12, 2) DEFAULT 0,
    estimates_rejected_quantity INTEGER DEFAULT 0,
    approved_ticket_average DECIMAL(10, 2) DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    total_received_amount DECIMAL(12, 2) DEFAULT 0,
    total_expenses DECIMAL(12, 2) DEFAULT 0,
    appointments_total INTEGER DEFAULT 0,
    appointments_finished INTEGER DEFAULT 0,
    appointments_missed INTEGER DEFAULT 0,
    appointments_new_patients INTEGER DEFAULT 0,
    appointments_existing_patients INTEGER DEFAULT 0,
    without_category INTEGER DEFAULT 0,
    unity_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_analytics_results_clinic_id ON public.analytics_results(clinic_id);

-- ============================================================================
-- RESUMO DE ORÇAMENTOS E CONVERSÃO
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.sales_estimates_conversion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    month VARCHAR(7) NOT NULL,
    status VARCHAR(50),
    total_estimates INTEGER DEFAULT 0,
    total_estimates_amount DECIMAL(12, 2) DEFAULT 0,
    average_ticket DECIMAL(10, 2) DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_sales_estimates_conversion_clinic_id ON public.sales_estimates_conversion(clinic_id);
CREATE INDEX idx_sales_estimates_conversion_month ON public.sales_estimates_conversion(month);

-- ============================================================================
-- RECEITA POR ESPECIALIDADE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.revenue_by_specialty (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    month VARCHAR(7) NOT NULL,
    specialty VARCHAR(255),
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    procedures_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_revenue_by_specialty_clinic_id ON public.revenue_by_specialty(clinic_id);
CREATE INDEX idx_revenue_by_specialty_month ON public.revenue_by_specialty(month);
CREATE INDEX idx_revenue_by_specialty_specialty ON public.revenue_by_specialty(specialty);

-- ============================================================================
-- DETALHES DE CLÍNICAS (EXPANDIDO)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.clinic_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    name VARCHAR(255),
    email VARCHAR(255),
    landline VARCHAR(20),
    other_landline VARCHAR(20),
    no_limit_apt_same_time BOOLEAN,
    address VARCHAR(500),
    active BOOLEAN DEFAULT true,
    slot_time INTEGER,
    working_days_hours JSONB,
    subscriber_business_uid VARCHAR(255),
    company_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_clinic_details_clinic_id ON public.clinic_details(clinic_id);

-- ============================================================================
-- INFORMAÇÕES DE ASSINANTE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.subscribers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_business_uid VARCHAR(255) UNIQUE,
    namespace VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

-- ============================================================================
-- ENABLE RLS
-- ============================================================================

ALTER TABLE public.chairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.available_times ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cash_flow ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.installment_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_birthdays ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_appointments_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_estimates_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insurance_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales_estimates_conversion ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.revenue_by_specialty ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.clinic_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscribers ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES
-- ============================================================================

CREATE POLICY "Service role can access all" ON public.chairs TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.available_times TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.receipts TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.cash_flow TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.installment_summary TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.payment_summary TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.financial_summary TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.patient_birthdays TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.patient_appointments_list TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.patient_estimates_summary TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.insurance_claims TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.analytics_results TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.sales_estimates_conversion TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.revenue_by_specialty TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.clinic_details TO service_role USING (true);
CREATE POLICY "Service role can access all" ON public.subscribers TO service_role USING (true);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
