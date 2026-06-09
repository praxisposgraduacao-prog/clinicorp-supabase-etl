# Como Executar o ETL Atualizado

**Problema:** Python via Microsoft Store tem problemas com aliases em linha de comando

**Solução:** Use uma das opções abaixo

---

## Opção 1: PowerShell (Recomendado)

Abra o PowerShell como **Administrador**:

```powershell
cd C:\projetos_praxis\Clinicorp
py -3 expand_with_subscriber.py
```

Ou:

```powershell
cd C:\projetos_praxis\Clinicorp
python expand_with_subscriber.py
```

---

## Opção 2: VS Code Terminal

1. Abra a pasta `C:\projetos_praxis\Clinicorp` no VS Code
2. Clique em `expand_with_subscriber.py`
3. Clique no botão **▶ Run** (canto superior direito)
   - Ou pressione `Ctrl+F5`

---

## Opção 3: Instalar Python Oficial

Se as opções acima não funcionarem, instale Python do site oficial:

1. Acesse https://www.python.org/downloads/
2. Baixe Python 3.12 ou mais recente
3. **IMPORTANTE:** Marque a opção "Add Python to PATH" durante a instalação
4. Reinicie o terminal
5. Execute:
   ```bash
   cd C:\projetos_praxis\Clinicorp
   python expand_with_subscriber.py
   ```

---

## O Que o Script Faz

Quando executado, o script `expand_with_subscriber.py`:

### 1. Carrega Agendamentos (Appointments)
- **Parâmetros:** subscriber_id, from (2025-06-09), to (2026-06-09), businessId, includeCanceled
- **Campos:** id, clinic_id, patient_id, professional_id, scheduled_date, duration_minutes, status, notes, reason_cancellation, updated_at, last_sync_at
- **Tabela:** `appointments` no Supabase

### 2. Carrega Faturas (Invoices)
- **Parâmetros:** subscriber_id, from, to, business_id
- **Campos:** id, clinic_id, patient_id, number, total_amount, paid_amount, due_date, issue_date, status, payment_method, updated_at, last_sync_at
- **Tabela:** `invoices` no Supabase

### 3. Carrega Pagamentos (Payments)
- **Parâmetros:** subscriber_id, from, to, business_id
- **Campos:** id, clinic_id, invoice_id, patient_id, amount, payment_method, payment_date, reference, status, notes, updated_at, last_sync_at
- **Tabela:** `payments` no Supabase

### 4. Pacientes (Nota)
- O script avisa que `/patient/list` não existe na API
- Alternativa: extrair IDs de agendamentos/faturas e usar `/patient/get` para cada um
- Ou aguardar suporte Clinicorp para endpoint correto

---

## Esperado na Saída

```
================================================================================
EXPANSAO DO CARREGAMENTO - CLINICORP ETL
================================================================================

[OK] Subscriber ID encontrado: praxis

[*] Período de consulta: 2025-06-09 a 2026-06-09

[1] CARREGANDO PACIENTES...
[INFO] Endpoint /patient/list não existe na API
[INFO] Pacientes podem ser obtidos via /patient/get (requer ID específico)
[INFO] Ou através da lista de agendamentos/faturas
[SKIP] Pulando carregamento direto de pacientes por enquanto

[2] CARREGANDO AGENDAMENTOS...
[OK] Agendamentos carregados: XXXX

[3] CARREGANDO FATURAS...
[OK] Faturas carregadas: XXXX

[4] CARREGANDO PAGAMENTOS...
[OK] Pagamentos carregados: XXXX

================================================================================
CARREGAMENTO EXPANDIDO CONCLUIDO
================================================================================

[RESULTADO FINAL]
Profissionais: 140
Pacientes: 0
Agendamentos: XXXX
Faturas: XXXX
Pagamentos: XXXX

TOTAL: XXXX registros
```

---

## Se Receber Erros

### Erro: "ERP_CLINICORP_SUBSCRIBER_ID not configured"
- Abra o arquivo `.env`
- Confirme que existe a linha: `ERP_CLINICORP_SUBSCRIBER_ID=praxis`

### Erro: HTTP 400
- A API pode estar retornando erro nos parâmetros
- O script mostrará a mensagem de erro da API
- Compare com `API_PARAMETERS_ANALYSIS.md`

### Erro: HTTP 401 (Unauthorized)
- Credenciais podem estar expiradas
- Verifique no `.env`:
  - `ERP_CLINICORP_USUARIO_API=praxis`
  - `ERP_CLINICORP_API_SENHA=<seu_token>`

---

## Próximas Etapas Após Execução

1. **Verificar dados no Supabase:**
   ```sql
   SELECT COUNT(*) FROM appointments;
   SELECT COUNT(*) FROM invoices;
   SELECT COUNT(*) FROM payments;
   SELECT * FROM sync_log ORDER BY sync_date DESC LIMIT 5;
   ```

2. **Se tudo carregou com sucesso:**
   - Próximo: Configurar sincronização incremental (apenas dados novos)
   - Próximo: Agendamento automático (cron jobs)

3. **Se houver falta de pacientes:**
   - Opção A: Extrair de agendamentos e fazer chamadas `/patient/get` em loop
   - Opção B: Contatar suporte Clinicorp para endpoint `/patient/list`

---

## Dúvidas?

Consulte:
- `API_PARAMETERS_ANALYSIS.md` - Detalhes técnicos dos parâmetros
- `CLINICORP_API_SUPPORT_REQUEST.md` - Histórico de problemas encontrados
- `.env` - Configurações e credenciais
