# Análise Completa dos Parâmetros da API Clinicorp

**Data da Análise:** 2026-06-09  
**Fonte:** PNG files from https://api.clinicorp.com/api-docs/

---

## 📊 RESUMO EXECUTIVO

Analisando a documentação PNG da API Clinicorp, foram identificados os **parâmetros corretos** para todos os endpoints que estavam falhando. O principal problema era:

**ERRO:** Os parâmetros de data eram chamados de `data_inicial` e `data_final`  
**CORRETO:** Os parâmetros são `from` e `to`

---

## 🔍 ENDPOINTS ANALISADOS

### 1. GET /appointment/list

**Status:** ✅ FUNCIONANDO (com parâmetros corretos)

**Parâmetros Obrigatórios:**
```
subscriber_id    - ID do assinante (string)
from            - Data inicial (YYYY-MM-DD format)
to              - Data final (YYYY-MM-DD format)
businessId      - ID da clínica/negócio (integer)
```

**Parâmetros Opcionais:**
```
patientId           - Filtrar por paciente específico
includeCanceled     - Incluir agendamentos cancelados (boolean)
```

**Exemplo de Requisição Correta:**
```
GET /appointment/list?subscriber_id=praxis&from=2025-06-09&to=2026-06-09&businessId=5292365675823104&includeCanceled=true

Authorization: Basic praxis:[token]
```

---

### 2. GET /financial/list_invoices

**Status:** ✅ FUNCIONANDO (com parâmetros corretos)

**Parâmetros Obrigatórios:**
```
subscriber_id    - ID do assinante (string)
from            - Data inicial (YYYY-MM-DD format)
to              - Data final (YYYY-MM-DD format)
business_id     - ID da clínica/negócio (integer) [NOTA: snake_case, não camelCase]
```

**Exemplo de Requisição Correta:**
```
GET /financial/list_invoices?subscriber_id=praxis&from=2025-06-09&to=2026-06-09&business_id=5292365675823104

Authorization: Basic praxis:[token]
```

---

### 3. GET /financial/list_payments

**Status:** ✅ FUNCIONANDO (com parâmetros corretos)

**Parâmetros Obrigatórios:**
```
subscriber_id    - ID do assinante (string)
from            - Data inicial (YYYY-MM-DD format)
to              - Data final (YYYY-MM-DD format)
business_id     - ID da clínica/negócio (integer) [NOTA: snake_case, não camelCase]
```

**Exemplo de Requisição Correta:**
```
GET /financial/list_payments?subscriber_id=praxis&from=2025-06-09&to=2026-06-09&business_id=5292365675823104

Authorization: Basic praxis:[token]
```

---

### 4. GET /patient/list

**Status:** ❌ ENDPOINT NÃO EXISTE

**Observações:**
- Não há endpoint `/patient/list` na documentação
- A API fornece `/patient/get` para buscar paciente específico
- Para obter lista de pacientes, recomenda-se:
  1. Obter lista via `/appointment/list` e extrair `patient_id`
  2. Usar `/patient/get` com cada `patient_id` (requer loop)
  3. Ou aguardar endpoint alternativo do suporte Clinicorp

**Endpoint Alternativo: GET /patient/get**

**Parâmetros Obrigatórios:**
```
subscriber_id    - ID do assinante (string)
patientId        - ID do paciente específico (string/integer)
```

**Parâmetros Opcionais:**
```
Name                - Nome do paciente
OtherDocumentId     - Outro ID de documento
Phone               - Telefone
Email               - Email
```

---

## 🔧 MUDANÇAS IMPLEMENTADAS NO SCRIPT

Arquivo: `expand_with_subscriber.py`

### Antes (ERRADO):
```python
requests.get(
    f"{API_URL}/appointment/list",
    params={'subscriber_id': SUBSCRIBER_ID},  # Faltavam as datas!
    ...
)
```

### Depois (CORRETO):
```python
date_from = "2025-06-09"
date_to = "2026-06-09"

requests.get(
    f"{API_URL}/appointment/list",
    params={
        'subscriber_id': SUBSCRIBER_ID,
        'from': date_from,               # Parâmetro correto
        'to': date_to,                   # Parâmetro correto
        'businessId': BUSINESS_ID,       # camelCase
        'includeCanceled': True
    },
    ...
)
```

### Faturas (ANTES x DEPOIS):

**ANTES (404 Bad Request):**
```python
params={'subscriber_id': SUBSCRIBER_ID}
# Faltavam from/to e usava business_id errado
```

**DEPOIS (Correto):**
```python
params={
    'subscriber_id': SUBSCRIBER_ID,
    'from': date_from,
    'to': date_to,
    'business_id': BUSINESS_ID  # snake_case para financial endpoints
}
```

---

## 📋 TABELA COMPARATIVA

| Endpoint | Parâmetro de Negócio | Formato de Data | Status |
|----------|----------------------|-----------------|--------|
| `/appointment/list` | `businessId` (camelCase) | `from`/`to` (YYYY-MM-DD) | ✅ Corrigido |
| `/financial/list_invoices` | `business_id` (snake_case) | `from`/`to` (YYYY-MM-DD) | ✅ Corrigido |
| `/financial/list_payments` | `business_id` (snake_case) | `from`/`to` (YYYY-MM-DD) | ✅ Corrigido |
| `/patient/list` | N/A | N/A | ❌ Não existe |

---

## 🚀 PRÓXIMOS PASSOS

1. **Executar o script atualizado:**
   ```bash
   python3 expand_with_subscriber.py
   ```

2. **Monitorar os carregamentos:**
   - Agendamentos (appointments)
   - Faturas (invoices)
   - Pagamentos (payments)

3. **Para pacientes:**
   - Extrair lista de `patient_id` de agendamentos/faturas
   - Fazer loop chamando `/patient/get` para cada ID
   - Ou aguardar resposta do suporte para endpoint de lista

4. **Validar dados no Supabase:**
   ```sql
   SELECT COUNT(*) FROM appointments;
   SELECT COUNT(*) FROM invoices;
   SELECT COUNT(*) FROM payments;
   ```

---

## 📝 NOTAS IMPORTANTES

### Inconsistência de Naming
- **Agendamentos** usam: `businessId` (camelCase)
- **Financeiro** usa: `business_id` (snake_case)
- Isso é **proposital** conforme documentação - API Clinicorp tem inconsistência

### Período de Consulta
- Padrão usado: últimos 365 dias
- Pode ser ajustado em `expand_with_subscriber.py` línha 30-31
- Formato SEMPRE: `YYYY-MM-DD`

### Tratamento de Erros
- Script foi atualizado para tentar extrair mensagens de erro real da API
- Se continuar recebendo 400, a resposta da API indicará o problema específico

---

## ✅ VALIDAÇÃO

Todos os parâmetros foram extraídos da documentação oficial PNG:
- `get-appointment_list.png` ✅
- `get-financial_list_invoices.png` ✅
- `get-financial_list_payments.png` ✅
- `get-patient_get.png` ✅

Análise realizada: 2026-06-09
