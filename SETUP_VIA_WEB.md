# Setup via SQL Editor Web (Alternativa)

Como a conexão PostgreSQL está bloqueada, você pode criar as tabelas via interface web do Supabase.

## 📝 Passo 1: Acessar SQL Editor

Abra no seu navegador:
```
https://app.supabase.com/project/duydqaxviyyzqawqhmgy/sql
```

## 🔧 Passo 2: Executar o Schema em Blocos

Cole **um bloco por vez** e clique em "RUN" (ou Ctrl+Enter):

### Bloco 1: Extensões e Tabela de Sync
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE IF NOT EXISTS public.sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL UNIQUE,
    last_sync_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_sync_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Bloco 2: Clínicas
```sql
CREATE TABLE IF NOT EXISTS public.clinics (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    business_id BIGINT NOT NULL,
    type VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_clinics_business_id ON public.clinics(business_id);
CREATE INDEX idx_clinics_updated_at ON public.clinics(updated_at DESC);

ALTER TABLE public.clinics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.clinics TO service_role USING (true);
```

### Bloco 3: Pacientes
```sql
CREATE TABLE IF NOT EXISTS public.patients (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    cpf VARCHAR(14) UNIQUE,
    date_of_birth DATE,
    gender VARCHAR(10),
    marital_status VARCHAR(50),
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_patients_clinic_id ON public.patients(clinic_id);
CREATE INDEX idx_patients_email ON public.patients(email);
CREATE INDEX idx_patients_cpf ON public.patients(cpf);
CREATE INDEX idx_patients_updated_at ON public.patients(updated_at DESC);

ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.patients TO service_role USING (true);
```

### Bloco 4: Profissionais
```sql
CREATE TABLE IF NOT EXISTS public.professionals (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    cpf VARCHAR(14) UNIQUE,
    license_number VARCHAR(100),
    specialty VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_professionals_clinic_id ON public.professionals(clinic_id);
CREATE INDEX idx_professionals_specialty ON public.professionals(specialty);
CREATE INDEX idx_professionals_updated_at ON public.professionals(updated_at DESC);

ALTER TABLE public.professionals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.professionals TO service_role USING (true);
```

### Bloco 5: Agendamentos
```sql
CREATE TABLE IF NOT EXISTS public.appointments (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    patient_id BIGINT NOT NULL REFERENCES public.patients(id),
    professional_id BIGINT REFERENCES public.professionals(id),
    scheduled_date TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    reason_cancellation VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_appointments_clinic_id ON public.appointments(clinic_id);
CREATE INDEX idx_appointments_patient_id ON public.appointments(patient_id);
CREATE INDEX idx_appointments_professional_id ON public.appointments(professional_id);
CREATE INDEX idx_appointments_scheduled_date ON public.appointments(scheduled_date);
CREATE INDEX idx_appointments_status ON public.appointments(status);
CREATE INDEX idx_appointments_updated_at ON public.appointments(updated_at DESC);

ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.appointments TO service_role USING (true);
```

### Bloco 6: Procedimentos
```sql
CREATE TABLE IF NOT EXISTS public.procedures (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    appointment_id BIGINT REFERENCES public.appointments(id),
    name VARCHAR(255) NOT NULL,
    specialty VARCHAR(255),
    description TEXT,
    price DECIMAL(10, 2),
    duration_minutes INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_procedures_clinic_id ON public.procedures(clinic_id);
CREATE INDEX idx_procedures_appointment_id ON public.procedures(appointment_id);
CREATE INDEX idx_procedures_updated_at ON public.procedures(updated_at DESC);

ALTER TABLE public.procedures ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.procedures TO service_role USING (true);
```

### Bloco 7: Orçamentos
```sql
CREATE TABLE IF NOT EXISTS public.estimates (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    patient_id BIGINT NOT NULL REFERENCES public.patients(id),
    professional_id BIGINT REFERENCES public.professionals(id),
    total_amount DECIMAL(12, 2) NOT NULL,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    net_amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    items_count INTEGER,
    valid_until DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_estimates_clinic_id ON public.estimates(clinic_id);
CREATE INDEX idx_estimates_patient_id ON public.estimates(patient_id);
CREATE INDEX idx_estimates_status ON public.estimates(status);
CREATE INDEX idx_estimates_updated_at ON public.estimates(updated_at DESC);

ALTER TABLE public.estimates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.estimates TO service_role USING (true);
```

### Bloco 8: Faturas
```sql
CREATE TABLE IF NOT EXISTS public.invoices (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    patient_id BIGINT NOT NULL REFERENCES public.patients(id),
    number VARCHAR(50) NOT NULL UNIQUE,
    total_amount DECIMAL(12, 2) NOT NULL,
    paid_amount DECIMAL(12, 2) DEFAULT 0,
    due_date DATE NOT NULL,
    issue_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    payment_method VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_invoices_clinic_id ON public.invoices(clinic_id);
CREATE INDEX idx_invoices_patient_id ON public.invoices(patient_id);
CREATE INDEX idx_invoices_status ON public.invoices(status);
CREATE INDEX idx_invoices_due_date ON public.invoices(due_date);
CREATE INDEX idx_invoices_updated_at ON public.invoices(updated_at DESC);

ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.invoices TO service_role USING (true);
```

### Bloco 9: Pagamentos
```sql
CREATE TABLE IF NOT EXISTS public.payments (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.payments(id),
    invoice_id BIGINT REFERENCES public.invoices(id),
    patient_id BIGINT NOT NULL REFERENCES public.patients(id),
    amount DECIMAL(12, 2) NOT NULL,
    payment_method VARCHAR(100) NOT NULL,
    payment_date TIMESTAMPTZ NOT NULL,
    reference VARCHAR(255),
    status VARCHAR(50) DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_payments_clinic_id ON public.payments(clinic_id);
CREATE INDEX idx_payments_invoice_id ON public.payments(invoice_id);
CREATE INDEX idx_payments_patient_id ON public.payments(patient_id);
CREATE INDEX idx_payments_payment_date ON public.payments(payment_date DESC);
CREATE INDEX idx_payments_updated_at ON public.payments(updated_at DESC);

ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.payments TO service_role USING (true);
```

### Bloco 10: Usuários, Resumos e Leads
```sql
CREATE TABLE IF NOT EXISTS public.users (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(100),
    status VARCHAR(50),
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_users_clinic_id ON public.users(clinic_id);
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_role ON public.users(role);
CREATE INDEX idx_users_updated_at ON public.users(updated_at DESC);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.users TO service_role USING (true);

CREATE TABLE IF NOT EXISTS public.sales_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    period_date DATE NOT NULL,
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    total_appointments INTEGER DEFAULT 0,
    completed_appointments INTEGER DEFAULT 0,
    new_patients INTEGER DEFAULT 0,
    revenue_by_specialty JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_sales_summary_clinic_id ON public.sales_summary(clinic_id);
CREATE INDEX idx_sales_summary_period_date ON public.sales_summary(period_date DESC);

ALTER TABLE public.sales_summary ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.sales_summary TO service_role USING (true);

CREATE TABLE IF NOT EXISTS public.leads (
    id BIGINT PRIMARY KEY,
    clinic_id BIGINT NOT NULL REFERENCES public.clinics(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    source VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    _sync_id UUID REFERENCES public.sync_log(id)
);

CREATE INDEX idx_leads_clinic_id ON public.leads(clinic_id);
CREATE INDEX idx_leads_status ON public.leads(status);
CREATE INDEX idx_leads_updated_at ON public.leads(updated_at DESC);

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role can access all" ON public.leads TO service_role USING (true);
```

### Bloco 11: Permissões Finais
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Verificar que tudo foi criado
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

## ✅ Pronto!

Depois de executar todos os blocos, você verá uma lista com 12 tabelas criadas.

Próximo passo: Execute no terminal
```bash
cd C:\projetos_praxis\Clinicorp
uv run setup_database.py  # ou: python etl_clinicorp.py
```

Aprox. tempo: **5-10 minutos**
