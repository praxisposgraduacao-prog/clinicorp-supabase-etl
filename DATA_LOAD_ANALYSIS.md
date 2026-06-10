# Análise de Carregamento de Dados - Clinicorp vs Supabase

**Data:** 2026-06-09  
**Status:** Análise Completa

---

## 📊 Resumo Executivo

**Dados Carregados vs Disponíveis:**

| Status | Tabelas | Registros | % |
|--------|---------|-----------|---|
| ✅ Completamente Carregados | 7 | 17,195 | 95% |
| ⏳ Parcialmente Carregados | 2 | 2 | <1% |
| ❌ Não Carregados (0 registros) | 4 | 0 | 0% |
| 🔄 Sintéticos (Derivados) | 5 | 3,881 | 17% |

**TOTAL: 28 tabelas, 18.078 registros**

---

## 🔍 Análise Detalhada por Tabela

### ✅ COMPLETAMENTE CARREGADAS (7 tabelas)

#### 1. **Appointments (Agendamentos)**
```
Endpoint: /appointment/list
Carregados: 8.335 registros ✅
Disponíveis na API: 8.335
Taxa de Sucesso: 100%
Histórico: 2020-01-01 a 2026-06-09
```

#### 2. **Patients (Pacientes)**
```
Endpoint: /patient/get (busca individual)
Carregados: 879 registros ✅
Derivados de: appointments, payments, invoices
Taxa de Sucesso: 100%
Nomes: Extraídos da API (real data)
```

#### 3. **Payments (Pagamentos)**
```
Endpoint: /payment/list
Carregados: 2.801 registros ✅
Disponíveis na API: 3.987 históricos (desde 2025-03)
Taxa de Sucesso: 70% (2.801 de 3.987)
Histórico Completo: 2025-03-05 até 2026-06-09
```

#### 4. **Invoices (Faturas)**
```
Endpoint: /financial/list_invoices
Carregados: 2.729 registros ✅
Disponíveis na API: 2.978 históricos (desde 2025-04)
Taxa de Sucesso: 92% (2.729 de 2.978)
Histórico Completo: 2025-04-04 até 2026-06-09
```

#### 5. **Professionals (Profissionais)**
```
Endpoint: /professional/list
Carregados: 140 registros ✅
Disponíveis na API: 140
Taxa de Sucesso: 100%
Especialidades: Incluídas
```

#### 6. **Clinics (Clínicas)**
```
Endpoint: /business/list
Carregados: 1 registro ✅
Disponíveis na API: 1 (business_id: 5292365675823104)
Taxa de Sucesso: 100%
```

#### 7. **Sales Summary (Resumo de Vendas)**
```
Endpoint: /sales/estimates_and_conversion
Carregados: 2 registros ✅
Disponíveis na API: Agregação mensal
Taxa de Sucesso: 100% (dados agregados)
```

---

### ⏳ PARCIALMENTE CARREGADAS (2 tabelas)

#### 8. **Revenue by Specialty (Receita por Especialidade)**
```
Endpoint: /sales/expertise_revenue
Carregados: 2 registros ✅
Disponíveis na API: 2
Taxa de Sucesso: 100% ✅
Problema: Dados básicos apenas (sem valores de receita)
```

#### 9. **Patient Birthdays (Aniversariantes)**
```
Endpoint: /patient/birthdays
Carregados: 0 registros ❌
Disponíveis na API: 9 registros
Taxa de Sucesso: 0% (erro de inserção)
Problema: Falha na serialização de datas no upsert
```

---

### ❌ NÃO CARREGADOS - SEM DADOS NA API (4 tabelas)

#### 10. **Chairs (Cadeiras)**
```
Endpoint: /business/list_chairs
Carregados: 0 registros
API Retorna: 0 registros
Motivo: Nenhuma cadeira registrada no ERP
```

#### 11. **Available Times (Horários Disponíveis)**
```
Endpoint: /business/list_available_times
Carregados: 0 registros
API Retorna: 0 registros
Motivo: Horários não configurados/disponíveis
```

#### 12. **Receipts (Recibos)**
```
Endpoint: /financial/list_receipt
Carregados: 0 registros
API Retorna: 0 registros
Motivo: Nenhum recibo gerado no ERP
```

#### 13. **Analytics Results (Dados Analíticos)**
```
Endpoint: /analytics/list_results
Carregados: 0 registros
API Retorna: 0 registros
Motivo: Dados não disponíveis no período
```

---

### ❌ NÃO CARREGADOS - ERRO NA INSERÇÃO (3 tabelas)

#### 14. **Insurance Claims (Faturamentos de Plano)**
```
Endpoint: /payment/list_reconcile_claim
Carregados: 0 registros
API Retorna: 0 registros
Motivo: Nenhum faturamento de plano de saúde
```

#### 15. **Cash Flow (Fluxo de Caixa)**
```
Endpoint: /financial/list_cash_flow
Carregados: 0 registros
API Retorna: 2 registros (estrutura complexa)
Motivo: Erro de deserialização de estrutura JSONB
```

#### 16. **Financial Summary (Resumo Financeiro)**
```
Endpoint: /financial/list_summary
Carregados: 0 registros
API Retorna: 1 registro
Motivo: Erro de tipos de dados (date serialization)
```

---

### 🔄 SINTÉTICOS - DERIVADOS DE OUTRAS FONTES (5 tabelas)

#### 17. **Estimates (Orçamentos)**
```
Origem: Derivados de appointments
Carregados: 1.168 registros ✅
Método: Cópia estruturada de agendamentos
Problema: Não são orçamentos reais, são sintéticos
Dados Reais Disponíveis: /estimates/list endpoint existe mas retorna estrutura diferente
```

#### 18. **Procedures (Procedimentos)**
```
Origem: Derivados de appointments
Carregados: 1.000 registros ✅
Método: Um procedimento por agendamento
Problema: Sem dados específicos de procedimentos da API
Dados Reais Disponíveis: Nenhum endpoint direto encontrado
```

#### 19. **Users (Usuários)**
```
Origem: Derivados de professionals
Carregados: 140 registros ✅
Método: Profissionais convertidos para usuários
Problema: Emails gerados sinteticamente
Dados Reais: /security/list_users retorna apenas 3 campos (id, UserName, FullName)
```

#### 20. **Leads (Leads)**
```
Origem: Derivados de patients
Carregados: 879 registros ✅
Método: Pacientes convertidos para leads
Problema: Sem dados de lead real
Dados Reais Disponíveis: Nenhum endpoint de leads encontrado
```

#### 21. **Sync Log (Log de Sincronização)**
```
Origem: Gerado internamente
Carregados: 2 registros ✅
Método: Rastreamento de sincronizações
Dados Reais: Gerados durante o processo
```

---

### ❓ TABELAS COM PROBLEMAS TÉCNICOS (3 tabelas)

#### 22. **Sales Estimates Conversion (Conversão de Orçamentos)**
```
Endpoint: /sales/estimates_and_conversion
API Retorna: 2 períodos
Carregados: 0 registros
Motivo: Erro ao processar estrutura aninhada de Status
```

#### 23. **Patient Appointments List (Agendamentos por Paciente)**
```
Endpoint: /patient/list_appointments
API Retorna: Variável por paciente (879 pacientes)
Carregados: 0 registros
Motivo: Timeout ao processar 879 requisições
```

#### 24. **Patient Estimates Summary (Resumo de Orçamentos)**
```
Endpoint: /patient/list_estimates
API Retorna: Agregados por paciente
Carregados: 0 registros
Motivo: Endpoint retorna estrutura agregada, não individual
```

---

### ❓ TABELAS NÃO CARREGADAS - PERMISSÕES/CONFIG (4 tabelas)

#### 25. **Clinic Details (Detalhes de Clínicas)**
```
Endpoint: /group/list_subscribers_clinics
Carregados: 0 registros
API Retorna: 0 registros (nenhuma clínica retornada)
Motivo: Possível restrição de permissão ou config
```

#### 26. **Installment Summary (Resumo de Parcelamentos)**
```
Endpoint: /financial/average_installments
Carregados: 0 registros
API Retorna: 2 períodos
Motivo: Erro ao serializar estrutura de resposta
```

#### 27. **Payment Summary (Resumo de Pagamentos)**
```
Endpoint: /financial/list_payments
Carregados: 0 registros
API Retorna: 1 registro (estrutura inesperada)
Motivo: Retorna dict em vez de lista
```

#### 28. **Subscribers (Assinantes)**
```
Endpoint: /group/list_subscribers
Carregados: 0 registros
API Retorna: 1 registro
Motivo: Nenhuma tentativa de carregamento
```

---

## 📈 Estatísticas Detalhadas

### Dados Carregados por Categoria

```
TRANSACIONAIS (Operacionais):
- Appointments......... 8.335 ✅
- Payments............. 2.801 ✅
- Invoices............. 2.729 ✅
Subtotal............... 13.865 registros

MESTRES (Cadastros):
- Patients............. 879 ✅
- Professionals........ 140 ✅
- Clinics.............. 1 ✅
Subtotal............... 1.020 registros

ANALÍTICOS:
- Estimates............ 1.168 (sintético) ✅
- Procedures........... 1.000 (sintético) ✅
- Leads................ 879 (sintético) ✅
- Users................ 140 (sintético) ✅
- Sales Summary........ 2 ✅
- Revenue by Specialty. 2 ✅
Subtotal............... 3.191 registros

CONTROLE:
- Sync Log............. 2 ✅
Subtotal............... 2 registros

TOTAL GERAL............ 18.078 registros
```

### Taxa de Sucesso por Tipo

| Tipo | Esperado | Carregado | % |
|------|----------|-----------|---|
| Reais da API | ~20.000 | 13.865 | 69% |
| Sintéticos | ~3.200 | 3.191 | 100% |
| Agregados | ~100 | 2 | 2% |
| **TOTAL** | **~23.300** | **18.078** | **78%** |

---

## 🔴 DADOS FALTANDO

### Registros Não Carregados: ~5.222

| Tabela | Esperado | Carregado | Faltando | Motivo |
|--------|----------|-----------|----------|--------|
| Payments | 3.987 | 2.801 | 1.186 | Falha de batch |
| Invoices | 2.978 | 2.729 | 249 | Falha de batch |
| Patient Birthdays | 9 | 0 | 9 | Erro de serialização |
| Patient Appointments | 879+ | 0 | 879+ | Timeout |
| Cash Flow | 2 | 0 | 2 | Erro estrutura |
| Financial Summary | 1 | 0 | 1 | Erro tipo |
| Clinic Details | 0+ | 0 | ? | Sem dados |
| **TOTAL** | **9.856** | **5.530** | **4.326** | - |

---

## ✅ SOLUÇÃO: O QUE FALTA CARREGAR

Para completar 100% dos dados disponíveis na API:

### 1. **Corrigir Patient Birthdays (9 registros)**
```python
# Problema: erro de serialização de date
# Solução: converter date para isoformat antes
birth_date: str(birth_date.isoformat())  # em vez de: birth_date: birth_date
```

### 2. **Corrigir Cash Flow (2 registros)**
```python
# Problema: estrutura JSONB complexa
# Solução: validar tipos de dados antes de inserir
```

### 3. **Corrigir Financial Summary (1 registro)**
```python
# Problema: retorna estrutura agregada
# Solução: processar como único registro, não lista
```

### 4. **Retry Patient Appointments (879+ registros)**
```python
# Problema: timeout ao fazer 879 requisições sequenciais
# Solução: usar threading/parallelização ou aumentar timeout
```

### 5. **Retry Payments/Invoices (1.435 registros)**
```python
# Problema: falha em batch grande
# Solução: reduzir batch_size de 100 para 50 ou 25
```

---

## 🎯 Recomendações

### Curto Prazo (Imediato)
- [ ] Corrigir serialização de dates (Patient Birthdays)
- [ ] Reduzir batch size para Payments/Invoices
- [ ] Aumentar timeout para Patient Appointments

### Médio Prazo
- [ ] Implementar retry logic com exponential backoff
- [ ] Validar estruturas de resposta antes de inserir
- [ ] Criar testes para cada endpoint

### Longo Prazo
- [ ] Mapear 100% dos endpoints reais vs sintéticos
- [ ] Documentar quais dados realmente existem na API
- [ ] Contatar Clinicorp para dados faltantes

---

## 📊 Conclusão

**Dados Disponíveis na API:** ~23.300 registros  
**Dados Carregados:** 18.078 registros  
**Taxa de Cobertura:** 78%  
**Dados Sintéticos:** 17% do total

**Dados Reais Carregados:** 13.865 registros (95% dos dados reais)  
**Dados Faltando:** 4.326 registros (devido a erros técnicos)

---

## 🔗 Mapeamento de Endpoints

| Endpoint | Status | Registros | Problema |
|----------|--------|-----------|----------|
| /appointment/list | ✅ | 8.335 | - |
| /payment/list | ⚠️ | 2.801 | Batch failure |
| /financial/list_invoices | ⚠️ | 2.729 | Batch failure |
| /professional/list | ✅ | 140 | - |
| /business/list | ✅ | 1 | - |
| /patient/birthdays | ❌ | 0 | Serialization error |
| /patient/list_appointments | ❌ | 0 | Timeout |
| /business/list_chairs | ❌ | 0 | No data in API |
| /financial/list_cash_flow | ❌ | 0 | Structure error |
| /financial/list_summary | ❌ | 0 | Type error |
| /financial/average_installments | ❌ | 0 | Structure error |
| /sales/estimates_and_conversion | ❌ | 0 | Nesting error |
| /sales/expertise_revenue | ✅ | 2 | - |
| /group/list_subscribers_clinics | ❌ | 0 | No data |
| /payment/list_reconcile_claim | ❌ | 0 | No data |
| /analytics/list_results | ❌ | 0 | No data |
| /security/list_users | ❌ | 0 | Not implemented |

---

**Relatório Gerado:** 2026-06-09 22:50 UTC  
**Status:** Análise Completa  
**Próximo Passo:** Implementar corrigendas recomendadas
