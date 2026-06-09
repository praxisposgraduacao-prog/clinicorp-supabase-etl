# SQL FIX MANUAL - Remover Constraints NOT NULL

## ⚠️ Situação Atual

- ✅ **474 pagamentos obtidos** da API
- ✅ **Dados preparados** e prontos para inserção
- ❌ **Bloqueado por constraint** NOT NULL em `payments.clinic_id`

---

## 🔧 Como Executar o Fix

### Passo 1: Abrir SQL Editor do Supabase

1. Acesse: https://app.supabase.com
2. Selecione seu projeto
3. Vá em: **SQL Editor** (menu esquerdo)
4. Clique em **New Query**

---

### Passo 2: Execute Este SQL

Copie e cole **TODO** este código no editor:

```sql
-- =================================================================
-- REMOVE NOT NULL CONSTRAINTS EM TABELA PAYMENTS
-- =================================================================

-- Remove NOT NULL de clinic_id
ALTER TABLE payments
ALTER COLUMN clinic_id DROP NOT NULL;

-- Remove NOT NULL de invoice_id (também pode estar causando problema)
ALTER TABLE payments
ALTER COLUMN invoice_id DROP NOT NULL;

-- Remove NOT NULL de payment_method (se necessário)
ALTER TABLE payments
ALTER COLUMN payment_method DROP NOT NULL;

-- =================================================================
-- VERIFICACAO
-- =================================================================

-- Verifique se os constraints foram removidos
SELECT 
    column_name, 
    is_nullable,
    data_type
FROM information_schema.columns
WHERE table_name = 'payments'
AND column_name IN ('clinic_id', 'invoice_id', 'payment_method')
ORDER BY column_name;

-- RESULTADO ESPERADO:
-- column_name    | is_nullable | data_type
-- ============================================
-- clinic_id      | YES         | bigint
-- invoice_id     | YES         | bigint  
-- payment_method | YES         | character varying
```

### Passo 3: Clique em "RUN"

- Aguarde a execução
- Você verá a tabela de verificação
- Confirme que `is_nullable` = `YES` para as 3 colunas

---

## ✅ Após Executar o SQL

Volte ao terminal e execute:

```bash
python apply_fix_and_reload.py
```

Isso irá:
1. ✅ Obter 474 pagamentos da API
2. ✅ Criar pacientes e clínicas necessárias
3. ✅ **Inserir todos os 474 pagamentos**

---

## 📋 Verificação Pós-Carregamento

Após a execução, consulte no SQL Editor:

```sql
-- Contar pagamentos carregados
SELECT COUNT(*) as total_payments FROM payments;

-- Resultado esperado: 474
```

---

## 🆘 Se Ainda Tiver Erro

Se receber erro de **Foreign Key** mesmo após remover NOT NULL:

```sql
-- Verifique os constraints atuais
\d payments

-- Se necessário, remova o FK temporariamente
ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_clinic_id_fkey;

-- Depois recriar mais permissivo
ALTER TABLE payments
ADD CONSTRAINT payments_clinic_id_fkey
FOREIGN KEY (clinic_id) REFERENCES clinics(id) ON DELETE SET NULL;
```

---

## 📊 Status Esperado Após Conclusão

```
Profissionais.....: 140
Pacientes.........: 879
Agendamentos......: 1.168
Pagamentos........: 474  ← Será adicionado!
Faturas..........: 0
━━━━━━━━━━━━━━━━━━━━━━
TOTAL.............: 2.661 registros
```

---

## 📝 Resumo Rápido

1. 🔗 Link: https://app.supabase.com/project/duydqaxviyyzqawqhmgy/sql/new
2. 📋 Cole o SQL acima
3. ▶️ Clique RUN
4. ✅ Verifique que `is_nullable = YES`
5. 💻 Execute: `python apply_fix_and_reload.py`

Pronto! 🎉

