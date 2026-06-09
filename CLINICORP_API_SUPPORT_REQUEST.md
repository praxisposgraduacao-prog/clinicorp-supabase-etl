# Solicitação de Suporte - Integração API Clinicorp

**Data:** 2026-06-09  
**Conta:** Praxis  
**Subscriber ID:** praxis  
**Business ID:** 5292365675823104

---

## 📋 Resumo da Solicitação

Estamos desenvolvendo uma integração entre o Clinicorp e o Supabase (banco de dados PostgreSQL) para extrair e sincronizar dados operacionais em tempo real.

**Status Atual:**
- ✅ Autenticação API funcionando (username + token)
- ✅ Extração de Profissionais: 140 registros carregados com sucesso
- ❌ Bloqueado em endpoints que requerem `subscriber_id` e datas

---

## 🔴 Problemas Encontrados

### Problema 1: Endpoint `/patient/list`
**Erro:** `HTTP 404 Not Found`  
**Descrição:** O endpoint não responde ou não existe para o subscriber_id fornecido

**Pergunta:** 
- O endpoint `/patient/list` existe para integração via API?
- Qual é o endpoint correto para listar pacientes?
- Qual subscriber_id devo usar?

---

### Problema 2: Endpoints com Parâmetro de Data
**Erro:** `HTTP 400 Bad Request`  
**Mensagem:** "É necessário informar a data inicial no formato JSON (YYYY-MM-DD)"

**Endpoints Afetados:**
- `GET /appointment/list`
- `GET /financial/list_invoices`
- `GET /financial/list_payments`

**Requisição Testada:**
```
GET https://api.clinicorp.com/rest/v1/appointment/list
  ?subscriber_id=praxis
  &data_inicial=2025-06-09
  &data_final=2026-06-09

Authorization: Basic praxis:[token]
Content-Type: application/json
```

**Pergunta:** 
- Qual é o formato correto para passar datas nestes endpoints?
- Os parâmetros devem estar no body (JSON) em vez da query string?
- Os nomes dos parâmetros estão corretos? (`data_inicial`, `data_final`)
- Existe um exemplo de requisição funcionando?

---

## 📊 O Que Está Funcionando

### Profissionais - ✅ Sucesso
```
GET https://api.clinicorp.com/rest/v1/professional/list_all_professionals
  ?business_id=5292365675823104

Resultado: 140 profissionais
Status: 200 OK
```

### Procedimentos - ✅ Sucesso
```
GET https://api.clinicorp.com/rest/v1/procedures/list
  ?business_id=5292365675823104

Resultado: Estrutura de dict com especialidades
Status: 200 OK
```

---

## 📝 Endpoints Necessários

Para completar a integração, precisamos de:

| Endpoint | Finalidade | Status | Prioridade |
|----------|-----------|--------|-----------|
| `GET /patient/list` | Listar pacientes | ❌ 404 | ALTA |
| `GET /appointment/list` | Listar agendamentos | ❌ 400 | ALTA |
| `GET /security/list_users` | Listar usuários | ❓ Não testado | MÉDIA |
| `GET /financial/list_invoices` | Listar faturas | ❌ 400 | ALTA |
| `GET /financial/list_payments` | Listar pagamentos | ❌ 400 | ALTA |
| `GET /estimates/list` | Listar orçamentos | ❓ Não testado | MÉDIA |

---

## 🔧 Informações Técnicas da Integração

**Stack:**
- Backend: Python 3.14
- Banco de Dados: Supabase (PostgreSQL)
- Autenticação: Basic Auth (username + token)
- Framework: REST API

**Credenciais Configuradas:**
```
URL Base: https://api.clinicorp.com/rest/v1
Usuario: praxis
Business ID: 5292365675823104
Subscriber ID: praxis
```

**Teste de Conectividade:**
- ✅ Autenticação: Funcionando
- ✅ Endpoints genéricos: Funcionando (professionals, procedures)
- ❌ Endpoints com subscriber_id: Falhando
- ❌ Endpoints com datas: Falhando

---

## 📌 Dúvidas Específicas

### 1. Subscriber ID
**Pergunta:** Está correto usar `subscriber_id=praxis`?
- É um slug/identificador?
- Precisa ser outro valor?
- Onde posso encontrar o subscriber_id correto da minha conta?

### 2. Parâmetros de Data
**Pergunta:** Como passar datas corretamente?

**Opção A - Query String (testada, não funcionou):**
```
GET /appointment/list?subscriber_id=praxis&data_inicial=2025-06-09&data_final=2026-06-09
```

**Opção B - JSON Body (não testada):**
```
POST /appointment/list
Content-Type: application/json

{
  "subscriber_id": "praxis",
  "data_inicial": "2025-06-09",
  "data_final": "2026-06-09"
}
```

**Opção C - Headers (não testada):**
```
GET /appointment/list?subscriber_id=praxis
X-Data-Inicial: 2025-06-09
X-Data-Final: 2026-06-09
```

Qual é a forma correta?

### 3. Endpoints Faltantes
**Pergunta:** Qual é o endpoint correto para:
- Listar pacientes (em vez de `/patient/list`)
- Listar usuários
- Listar orçamentos

---

## 📞 Próximas Etapas

Após receber as respostas:
1. Atualizaremos o script de integração
2. Testaremos os endpoints corrigidos
3. Sincronizaremos todos os dados
4. Configuraremos sincronizações incrementais automáticas

---

## 📎 Anexos

**Arquivo:** Script de teste disponível  
**Linguagem:** Python 3.14  
**Bibliotecas:** requests, supabase-py

---

## 📧 Informações de Contato

**Para Responder Esta Solicitação:**

Nome: Praxis  
Email: joaorego2005@gmail.com  
Conta: praxis  
Data da Solicitação: 2026-06-09

---

## ✅ Checklist de Resposta Esperada

Solicitamos que o suporte forneça:

- [ ] Documentação atualizada dos endpoints com subscriber_id
- [ ] Exemplos de requisições funcionando para cada endpoint
- [ ] Confirmação do subscriber_id correto
- [ ] Detalhes sobre como passar parâmetros de data
- [ ] Quais endpoints requerem autenticação Basic Auth
- [ ] Rate limits ou throttling que devemos considerar
- [ ] Campos obrigatórios vs opcionais em cada endpoint
- [ ] Tamanho máximo de resposta / paginação

---

**Obrigado pela atenção!**

Aguardamos retorno para completar a integração.

---

**Versão:** 1.0  
**Tipo:** Solicitação Técnica  
**Prioridade:** Alta
