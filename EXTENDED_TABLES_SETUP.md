# Setup de Tabelas Estendidas - Guia Completo

**Data:** 2026-06-09  
**Status:** Pronto para implementação  

---

## 📋 O Que São Tabelas Estendidas

Expandem a integração de 12 para 32+ tabelas, cobrindo:
- Operacional (cadeiras, horários)
- Financeiro (recibos, fluxo de caixa, parcelamentos)
- Analítico (dados de vendas, especialidades)
- Pacientes (aniversariantes, agendamentos)

---

## 🚀 Como Aplicar o Schema

### Opção 1: Via Dashboard Supabase (Recomendado)

1. **Acesse o Supabase Dashboard:**
   - URL: https://supabase.com/dashboard
   - Projeto: Seu projeto Clinicorp

2. **Vá para SQL Editor:**
   - Clique em "SQL Editor"
   - Clique em "New Query"

3. **Copie e Cole o Schema:**
   - Abra o arquivo: `schema_extended.sql`
   - Copie TODO o conteúdo
   - Cole no editor SQL do Supabase

4. **Execute:**
   - Clique em "Run" (Cmd+Enter)
   - Aguarde a conclusão

5. **Verifique:**
   - Vá para "Table Editor"
   - Deve haver 16 novas tabelas

---

### Opção 2: Via CLI (se instalado)

```bash
supabase db execute < schema_extended.sql
```

---

## 📊 Tabelas Criadas

| # | Tabela | Registros Esperados | Fonte |
|---|--------|-------------------|-------|
| 1 | chairs | 2-5 | /business/list_chairs |
| 2 | available_times | 10-100 | /business/list_available_times |
| 3 | receipts | 50-200 | /financial/list_receipt |
| 4 | cash_flow | 1-12 | /financial/list_cash_flow |
| 5 | installment_summary | 1-12 | /financial/average_installments |
| 6 | payment_summary | 1 | /financial/list_payments |
| 7 | financial_summary | 1-12 | /financial/list_summary |
| 8 | patient_birthdays | 5-50 | /patient/birthdays |
| 9 | patient_appointments_list | 100-1000 | /patient/list_appointments |
| 10 | patient_estimates_summary | 1-12 | /patient/list_estimates |
| 11 | insurance_claims | 10-100 | /payment/list_reconcile_claim |
| 12 | analytics_results | 1-5 | /analytics/list_results |
| 13 | sales_estimates_conversion | 5-50 | /sales/estimates_and_conversion |
| 14 | revenue_by_specialty | 5-50 | /sales/expertise_revenue |
| 15 | clinic_details | 1-5 | /group/list_subscribers_clinics |
| 16 | subscribers | 1 | /group/list_subscribers |

**Total: +500 registros adicionais esperados**

---

## 🔄 Carregar Dados

### Passo 1: Aplicar Schema

```bash
# Copiar schema_extended.sql para Supabase SQL Editor
# Executar conforme instruções acima
```

### Passo 2: Carregar Dados

```bash
python load_extended_tables.py
```

### Resultado Esperado

```
[1] CARREGANDO CHAIRS... [OK] X cadeiras
[2] CARREGANDO RECEIPTS... [OK] X recibos
[3] CARREGANDO CASH_FLOW... [OK] X registros
... (mais 9 tabelas)

Total de registros adicionados: 500+
```

---

## ⚠️ Notas Importantes

1. **Ordem de Execução:**
   - Sempre aplicar schema ANTES de carregar dados
   - Sem schema, os loaders falharam com "table not found"

2. **Chaves Estrangeiras:**
   - Tabelas referenciam clinics, patients, professionals
   - Certifique-se que estas tabelas base estão carregadas ✅

3. **IDs Sintéticos:**
   - Algumas tabelas usam UUID (gerado localmente)
   - Outras usam IDs da API (garantem unicidade)

4. **Dados Vazios:**
   - Se alguma tabela retornar 0 registros, é porque:
     - O endpoint não tem dados (chairs, analytics, etc)
     - Precisa ser buscado com parâmetros diferentes
     - É agregado e precisa de cálculo

---

## 🔍 Verificar Resultado

### Via SQL

```sql
-- Contar todas as tabelas estendidas
SELECT 
  'chairs' as tabela, COUNT(*) as registros FROM public.chairs
UNION ALL
SELECT 'receipts', COUNT(*) FROM public.receipts
UNION ALL
SELECT 'cash_flow', COUNT(*) FROM public.cash_flow
-- ... etc para todas as 16 tabelas
```

### Via Python

```bash
python final_summary.py
```

---

## 🛠️ Troubleshooting

### Erro: "table ... not found"

**Solução:** O schema não foi aplicado. Execute `schema_extended.sql` no Supabase SQL Editor.

### Erro: "permission denied"

**Solução:** Use `ERP_SERVICE_ROLE` em .env, não anon key.

### Erro: "foreign key violation"

**Solução:** Garanta que clinics, patients, professionals existem primeiro.

### Tabela vazia depois de carregar

**Solução:** O endpoint API retornou 0 resultados. Verifique parâmetros ou permissões.

---

## 📈 Próximas Etapas

1. ✅ Aplicar schema estendido
2. ✅ Executar load_extended_tables.py
3. ⏳ Configurar sync incremental para novas tabelas
4. ⏳ Criar dashboards analíticos

---

## 📞 Referência Rápida

**Arquivo Principal:** `load_extended_tables.py`  
**Schema:** `schema_extended.sql`  
**Testes:** `final_summary.py`  
**Status:** Pronto para deploy  

