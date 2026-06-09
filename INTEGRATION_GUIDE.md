# Guia de Integração Clinicorp ↔ Supabase

Integração ETL para extrair dados do Clinicorp e armazenar no Supabase com suporte a sincronizações iniciais e incrementais.

## 📋 Arquivos Criados

1. **schema.sql** - Definição completa do banco de dados Supabase
2. **etl_clinicorp.py** - Script Python para extração e carregamento de dados
3. **requirements.txt** - Dependências Python
4. **.env** - Credenciais (já existente)

## 🚀 Passo a Passo de Implementação

### 1. **Criar as Tabelas no Supabase**

Acesse o Supabase Dashboard SQL Editor e execute o conteúdo de `schema.sql`:

```bash
1. Acesse: https://app.supabase.com/project/duydqaxviyyzqawqhmgy/sql
2. Cole todo o conteúdo de schema.sql
3. Clique em "RUN"
```

Ou via CLI (se tiver instalado):

```bash
supabase db push
```

### 2. **Instalar Dependências Python**

```bash
pip install -r requirements.txt
```

Ou instalar manualmente:

```bash
pip install requests supabase python-dotenv
```

### 3. **Executar a Extração Inicial**

```bash
# Extração completa (primeira carga)
python etl_clinicorp.py --mode initial

# Ou simplesmente (padrão é initial):
python etl_clinicorp.py
```

**O que acontece:**
- ✓ Conecta na API do Clinicorp com suas credenciais
- ✓ Extrai todos os dados (pacientes, agendamentos, profissionais, etc.)
- ✓ Carrega no Supabase
- ✓ Registra o sync_log para rastrear a última sincronização

### 4. **Sincronizações Incrementais (Futura)**

Depois de completar a carga inicial, você pode fazer sincronizações incrementais:

```bash
# Sincronização incremental (dados novos/alterados)
python etl_clinicorp.py --mode incremental
```

---

## 📊 Estrutura de Dados

### Tabelas Principais

| Tabela | Descrição | Registros |
|--------|-----------|-----------|
| **clinics** | Clínicas/Unidades | - |
| **patients** | Pacientes | - |
| **professionals** | Profissionais/Dentistas | - |
| **appointments** | Agendamentos | - |
| **procedures** | Procedimentos | - |
| **estimates** | Orçamentos | - |
| **invoices** | Faturas/Recibos | - |
| **payments** | Pagamentos | - |
| **users** | Usuários do sistema | - |
| **leads** | Leads/Prospects | - |
| **sales_summary** | Resumo de vendas | - |
| **sync_log** | Log de sincronizações | - |

### Índices para Performance

Todas as tabelas têm índices otimizados para:
- Filtros por clinic_id
- Ordenação por updated_at (para incrementais)
- Buscas rápidas (email, cpf, etc)

### Campos de Rastreamento

Cada tabela possui:
- `created_at` - Data de criação
- `updated_at` - Data da última atualização
- `last_sync_at` - Data do último sync
- `_sync_id` - ID do sync que carregou o registro

---

## 🔒 Segurança & RLS (Row Level Security)

### Configuração Atual

- ✓ RLS habilitado em todas as tabelas
- ✓ Permissões para `service_role` (usado no ETL)
- ✓ Dados protegidos do acesso anônimo

### Próximos Passos (Opcional)

Se você quiser acessar os dados via frontend:

```sql
-- Exemplo: Permitir que usuários acessem apenas seus próprios dados
CREATE POLICY "Users can read their own data"
ON public.patients
FOR SELECT
TO authenticated
USING (auth.uid()::text = user_id);
```

---

## 📝 Monitoramento

### Log de Sincronização

A tabela `sync_log` rastreia cada sincronização:

```sql
SELECT * FROM sync_log ORDER BY last_sync_time DESC;
```

Campos:
- `entity_type` - Tipo de dado (patients, appointments, etc)
- `last_sync_time` - Quando foi o último sync
- `last_sync_count` - Quantos registros foram sincronizados
- `status` - completed, failed, in_progress
- `error_message` - Detalhes de erros (se houver)

### Logs do Script

Os logs são salvos em `etl_clinicorp.log`:

```bash
tail -f etl_clinicorp.log
```

---

## 🔄 Fluxo de Sincronização Incremental

Quando você executar `--mode incremental`:

1. Script verifica `sync_log` para última sincronização
2. API Clinicorp retorna apenas registros novos/modificados
3. Faz upsert no Supabase (insert or update)
4. Atualiza `sync_log` com novo timestamp

---

## ⚙️ Configuração Avançada

### Modificar Intervalo de Sync

Edite `etl_clinicorp.py` para agendar execuções:

```python
# Adicione ao final de main():
import schedule
import time

schedule.every().day.at("02:00").do(etl.run_full_extraction, mode='incremental')

while True:
    schedule.run_pending()
    time.sleep(60)
```

Ou use `cron` (Linux/Mac):

```bash
# Sincronização diária às 2 da manhã
0 2 * * * python /caminho/para/etl_clinicorp.py --mode incremental
```

### Agendar com Windows Task Scheduler

```powershell
# Criar tarefa agendada
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\projetos_praxis\Clinicorp\etl_clinicorp.py"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "ClinicorpETL" -Description "Sincronização Clinicorp"
```

---

## 🆘 Troubleshooting

### Erro: "Connection refused"

```
Solução: Verifique se a API Clinicorp está acessível
- Teste: curl https://api.clinicorp.com/rest/v1
- Verifique firewall/proxy
```

### Erro: "Supabase key invalid"

```
Solução: Verifique as credenciais no .env
- ERP_CLINICORP_URL deve ser a URL do projeto
- ERP_SERVICE_ROLE deve ser a chave de service_role (não anon)
```

### Erro: "Table does not exist"

```
Solução: Execute schema.sql no Supabase SQL Editor
- Verifique se todas as tabelas foram criadas
- Verifique permissões do service_role
```

### Dados não aparecem no Supabase

```
Solução:
1. Verifique os logs: tail -f etl_clinicorp.log
2. Confirme que schema.sql foi executado
3. Verifique RLS policies: SELECT * FROM pg_policies;
4. Teste manualmente: SELECT COUNT(*) FROM patients;
```

---

## 📞 Suporte

Para dúvidas sobre:
- **API Clinicorp**: Consulte `users.txt` para lista de endpoints
- **Supabase**: https://supabase.com/docs
- **Python/ETL**: Verifique `etl_clinicorp.log` para detalhes

---

## ✅ Checklist de Implementação

- [ ] Executar `schema.sql` no Supabase SQL Editor
- [ ] Instalar dependências: `pip install -r requirements.txt`
- [ ] Verificar credenciais em `.env`
- [ ] Executar script: `python etl_clinicorp.py`
- [ ] Verificar logs: `tail -f etl_clinicorp.log`
- [ ] Confirmar dados no Supabase Dashboard
- [ ] (Opcional) Agendar sincronizações incrementais
- [ ] (Opcional) Configurar RLS policies customizadas

---

**Versão:** 1.0  
**Data:** 2026-06-09  
**Status:** Pronto para produção
