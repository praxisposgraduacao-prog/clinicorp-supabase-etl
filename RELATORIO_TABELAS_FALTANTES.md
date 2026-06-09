# Relatório: Carregamento de Tabelas Faltantes

**Data:** 2026-06-09  
**Status:** ✅ Parcialmente Completo

---

## 📊 Tabelas Faltantes - Status

| Tabela | Registros | Status | Observação |
|--------|-----------|--------|-----------|
| **invoices** | 0 → ??? | ⚠️ Erro na inserção | Unique constraint |
| **estimates** | 0 | ❌ Não carregado | Requer IDs específicos |
| **procedures** | 0 | ⚠️ Estrutura diferente | Retorna hierarquia |
| **payments** | 0 | ⚠️ Foreign key issues | Constraint de invoice_id |
| **sales_summary** | 0 | ❌ Endpoint não encontrado | HTTP 404 |

---

## 🔍 O Que Foi Descoberto

### 1. Pagamentos ✅ (Endpoint existe!)

**Endpoint:** `GET /payment/list`

**Parâmetros:**
- `subscriber_id` (obrigatório)
- `from` (obrigatório) - Data YYYY-MM-DD
- `to` (obrigatório) - Data YYYY-MM-DD

**Campos Importantes:**
```
PaymentHeaderId      → id
ReceiverBusinessId   → clinic_id  
PatientId            → patient_id
Amount               → amount
PaymentDate          → payment_date
CreditCardType       → payment_method
PaymentReceived      → status (X = completed)
PayerName            → notes
```

**Dados Disponíveis:** 474 pagamentos em 30 dias!

---

### 2. Estimativas (Orçamentos) ✅ (Endpoint existe!)

**Endpoint:** `GET /estimates/get`

**Parâmetros:**
- `subscriber_id` (obrigatório)
- `treatment_id` (obrigatório) - ID do orçamento específico

**Observação:** Este é um endpoint de detalhes, não de lista. Precisa de IDs específicos.

---

### 3. Sales Summary ❌ (Endpoint não encontrado)

**Endpoint Esperado:** `GET /sales/estimatives_and_conversion`

**Parâmetros Tentados:**
- `subscriber_id`
- `from` / `to`
- `business_id`
- `group_by` = month

**Resultado:** HTTP 404 - Endpoint não existe ou path está errado

---

### 4. Procedimentos ✅ (Endpoint existe!)

**Endpoint:** `GET /procedures/list` (já conhecido)

**Observação:** Retorna estrutura hierárquica (especialidades/categorias), não lista de procedimentos individuais

---

## 🚧 Problemas Encontrados

### Problema 1: Foreign Key em Payments
**Causa:** Column `invoice_id` não pode ser NULL  
**Impacto:** Impossível inserir pagamentos sem fatura associada  
**Solução:** 
- Option A: Extrair invoice_id dos dados de pagamento
- Option B: Remover constraint de FK ou tornå-lo opcional
- Option C: Criar stub de faturas primeiro

### Problema 2: Invoices com Constraints
**Causa:** Multiplas constraints (patient_id NOT NULL, due_date NOT NULL)  
**Impacto:** Não consegue inserir faturas stub  
**Solução:** Mapear corretamente cada fatura com paciente e datas

### Problema 3: Estimativas Requer IDs
**Causa:** Endpoint `/estimates/get` requer `treatment_id` específico  
**Impacto:** Precisa fazer loop de IDs de tratamentos  
**Solução:**
1. Extrair todos os `treatment_id` de appointments/agendamentos
2. Fazer chamada `/estimates/get` para cada ID
3. Inserir no banco

---

## 📋 Recomendações

### Imediato (Crítico)
1. **Fixar constraints em payments**
   - Alterar `invoice_id` para NULL se não tiver fatura
   - Ou remover constraint de FK temporariamente

2. **Mapear corretamente fieldsde invoices**
   - Usar dados do `/financial/list_invoices`
   - Preencher `patient_id` e `due_date` corretamente

### Próximo Passo
3. **Implementar loop para estimativas**
   - Extrair IDs de appointments
   - Chamar `/estimates/get` para cada ID
   - Inserir estrutura de estimativas

### Futuro
4. **Investigar sales_summary**
   - Verificar path correto do endpoint
   - Considerar usar dados de `/financial/list_summary`

---

## 💾 Scripts Criados

| Script | Propósito | Status |
|--------|-----------|--------|
| `load_remaining_tables.py` | Primeira tentativa | ❌ Falhou |
| `load_remaining_v2.py` | Com dependências | ⚠️ Constraints |
| `load_payments_fixed.py` | Pagamentos com batch | ⏳ Parcial |
| `diagnose_payments.py` | Diagnóstico | ✅ Sucesso |

---

## 🔗 Endpoints Disponíveis

**Confirmados e Funcionando:**
- ✅ `/professional/list_all_professionals`
- ✅ `/appointment/list`
- ✅ `/financial/list_invoices`
- ✅ `/financial/list_payments` (agregado por mês)
- ✅ `/payment/list` (pagamentos individuais - **novo!**)
- ✅ `/procedures/list` (estrutura)
- ✅ `/estimates/get` (detalhes por ID)

**Não Encontrados:**
- ❌ `/patient/list`
- ❌ `/sales/estimatives_and_conversion`

---

## 📊 Status Atual do Banco

```sql
Profissionais: 140
Pacientes: 879
Agendamentos: 1.168
Clínicas: 1
Faturas: 0      (faltam constraints)
Pagamentos: 0   (faltam invoices)
Estimativas: 0  (requer loop de IDs)
```

**Total: 2.188 registros**

---

## 🎯 Próximas Ações

### Para Habilitar Pagamentos (474 registros)
1. Executar SQL para aliviar constraints:
   ```sql
   ALTER TABLE payments 
   ALTER COLUMN invoice_id DROP NOT NULL;
   ```

2. Re-executar `load_payments_fixed.py`

### Para Carregar Estimativas
1. Extrair `treatment_id` de agendamentos
2. Loop chamando `/estimates/get`
3. Inserir em `estimates` table

### Para Faturas Corretas
1. Usar dados de `/financial/list_invoices`
2. Mapear pacientes corretamente
3. Re-executar inserção com constraint completa

---

## 📝 Conclusão

- ✅ **Pagamentos individuais descobertos** - 474 registros aguardando apenas constraint
- ✅ **Estimativas endpoint funcionando** - precisa de implementação de loop
- ❌ **Sales Summary não encontrado** - pode usar endpoint alternativo
- ⚠️ **Tabelas têm constraints rigorosas** - precisam dados válidos

**Recomendação:** Ajustar constraints ou fornecer dados completos antes de inserção.

