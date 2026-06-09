# Plano de Expansão - Clinicorp ETL

## 🎯 Objetivo
Carregar todos os dados disponíveis do Clinicorp para Supabase assim que o `subscriber_id` correto for identificado.

---

## 📋 Dados a Carregar (Por Prioridade)

### **FASE 1: Dados Operacionais (Alta Prioridade)**
- [ ] **Pacientes** → `patients` (GET `/patient/list`)
- [ ] **Agendamentos** → `appointments` (GET `/appointment/list`)
- [ ] **Clínicas/Unidades** → `clinics` (GET `/business/list`)

**Impacto:** Core do sistema, necessário para análises e relatórios

---

### **FASE 2: Dados Financeiros (Alta Prioridade)**
- [ ] **Faturas** → `invoices` (GET `/financial/list_invoices`)
- [ ] **Pagamentos** → `payments` (GET `/financial/list_payments`)
- [ ] **Orçamentos** → `estimates` (GET `/estimates/list`)

**Impacto:** Análise financeira, fluxo de caixa, receita

---

### **FASE 3: Dados de Usuários e Operacional**
- [ ] **Usuários** → `users` (GET `/security/list_users`)
- [ ] **Profissionais** → `professionals` (JÁ CARREGADO ✓)
- [ ] **Procedimentos** → `procedures` (PARCIAL - precisa estruturação)

**Impacto:** Gestão de recursos, relatórios de desempenho

---

### **FASE 4: Dados de CRM e Análise**
- [ ] **Leads/Campanhas** → `leads` (GET `/crm/list_active_campaigns`)
- [ ] **Resumo de Vendas** → `sales_summary` (GET `/analytics/list_results`)

**Impacto:** Análise de vendas, pipeline de CRM

---

## 🔑 Passo 1: Encontrar o Subscriber ID

**Onde procurar:**

1. **Dashboard do Clinicorp**
   - Acesse: https://clinicorp.com/dashboard
   - Procure por: "ID", "Subscriber", "Código", "Código da Clínica"

2. **URL do Sistema**
   - Exemplo: `https://clinicorp.com/dashboard/PRAXIS/pacientes`
   - O `PRAXIS` seria o subscriber_id

3. **Email de Configuração**
   - Verifique emails da Clinicorp
   - Procure por "ID" ou "Código" da sua conta

4. **Contato com Suporte**
   - Clinicorp: suporte@clinicorp.com
   - Solicite: "Qual é o subscriber_id para API?"

---

## ⚙️ Passo 2: Configurar no .env

Uma vez encontrado, adicione ao `.env`:

```env
ERP_CLINICORP_SUBSCRIBER_ID=seu_subscriber_id_aqui
```

**Exemplo:**
```env
ERP_CLINICORP_SUBSCRIBER_ID=praxis
```

---

## 🚀 Passo 3: Executar Carregamento Expandido

### Script para Uso:

```bash
# Atualizar o script com o novo subscriber_id
python update_etl_subscriber.py

# Executar carga completa
python load_all_available_data.py --mode full --include-all
```

---

## 📊 Estrutura de Dados Esperada

### Pacientes (100-10,000 registros esperados)
```sql
SELECT COUNT(*) FROM patients;
-- Análise esperada:
-- - Distribuição por data de cadastro
-- - Pacientes por clínica
-- - Status ativo/inativo
```

### Agendamentos (500-50,000 registros)
```sql
SELECT COUNT(*) FROM appointments;
-- Análise esperada:
-- - Taxa de ocupação (confirmados/total)
-- - Distribuição por profissional
-- - Taxa de cancelamento
```

### Financeiro (200-20,000 registros)
```sql
SELECT SUM(total_amount) FROM invoices;
-- Análise esperada:
-- - Receita total
-- - Faturamento por período
-- - Taxa de inadimplência
```

---

## 🔄 Sincronização Incremental

Após a carga inicial, configure sincronizações incrementais:

```bash
# Diário - sincronizar dados novos
0 2 * * * python etl_clinicorp.py --mode incremental

# Semanal - relatório completo
0 3 * * 0 python etl_clinicorp.py --mode full
```

---

## ✅ Checklist de Expansão

- [ ] Subscriber ID identificado
- [ ] `.env` atualizado com subscriber_id
- [ ] Script de carregamento expandido testado
- [ ] Primeira carga de pacientes executada
- [ ] Primeira carga de agendamentos executada
- [ ] Primeira carga de financeiro executada
- [ ] Sincronizações incrementais configuradas
- [ ] Testes de integridade de dados
- [ ] Documentação atualizada
- [ ] Backup automático configurado

---

## 🎯 Resultados Esperados

Após expansão completa:

| Tabela | Registros Esperados | Atualização |
|--------|-------------------|-------------|
| professionals | 140 | ✓ Completo |
| clinics | 1-10 | Pendente |
| patients | 100-10,000 | Pendente |
| appointments | 500-50,000 | Pendente |
| procedures | 50-500 | Pendente |
| invoices | 200-10,000 | Pendente |
| payments | 200-20,000 | Pendente |
| estimates | 50-5,000 | Pendente |
| users | 5-50 | Pendente |
| leads | 10-1,000 | Pendente |

**TOTAL ESPERADO:** 1,000 - 100,000+ registros

---

## 📞 Suporte

Para problemas durante a expansão:

1. **Validar subscriber_id:**
   ```bash
   python test_subscriber.py --id seu_subscriber_id
   ```

2. **Verificar dados carregados:**
   ```bash
   python check_professionals.py  # Modelo para outras tabelas
   ```

3. **Ver logs detalhados:**
   ```bash
   tail -f etl_clinicorp.log
   ```

---

## 📅 Próximas Etapas

1. **Semana 1:** Identificar subscriber_id
2. **Semana 2:** Expandir para pacientes e agendamentos
3. **Semana 3:** Adicionar dados financeiros
4. **Semana 4:** Configurar sincronizações automáticas
5. **Semana 5:** Criar dashboards e relatórios

---

**Status:** Pronto para expansão ✓  
**Última Atualização:** 2026-06-09  
**Sistema:** Clinicorp ↔ Supabase ETL
