# Sincronização Incremental - Guia de Setup

**Data:** 2026-06-09  
**Status:** ✅ Pronto para produção

---

## 📋 O Que É Sincronização Incremental

Sincronização incremental carrega **apenas dados novos ou modificados** desde a última execução, em vez de recarregar tudo do zero.

**Benefícios:**
- ⚡ **Mais rápido:** Carrega apenas deltas
- 💾 **Menos banda:** Reduz dados transferidos
- 💰 **Mais barato:** Menos requisições à API
- 🔄 **Sempre atualizado:** Executa automaticamente

---

## 🚀 Como Configurar

### Opção 1: Agendamento Automático (Windows Task Scheduler)

```powershell
# Execute como Administrador
cd C:\projetos_praxis\Clinicorp
.\setup_scheduler.ps1
```

Isso criará uma task que executa a cada **6 horas automaticamente**.

### Opção 2: Executar Manualmente

```bash
python incremental_sync.py
```

Isso sincronizará dados desde a última execução.

### Opção 3: Cron Job (Linux/Mac)

```bash
# Adicione ao crontab (a cada 6 horas)
0 */6 * * * cd /path/to/Clinicorp && python incremental_sync.py
```

---

## 📊 Como Funciona

### Arquivo de Estado: `sync_state.json`

Rastreia quando foi a última sincronização:

```json
{
  "last_sync": "2026-06-09T19:11:55.731010",
  "appointments_count": 98,
  "payments_count": 32,
  "invoices_count": 11
}
```

### Fluxo de Execução

```
1. Carrega último timestamp de sync_state.json
2. Consulta API com período desde última sync
3. Obtém apenas dados modificados/novos
4. Faz upsert (insert or update) no Supabase
5. Atualiza sync_state.json com novo timestamp
6. Próxima execução usa novo timestamp
```

---

## 📈 Dados Sincronizados

Por padrão, a sincronização incremental cobre:

| Recurso | Endpoint | Comportamento |
|---------|----------|---------------|
| **Agendamentos** | `/appointment/list` | Upsert por ID |
| **Pagamentos** | `/payment/list` | Upsert por ID |
| **Faturas** | `/financial/list_invoices` | Upsert por ID |

---

## 🔍 Monitorando a Sincronização

### Ver Último Sync

```bash
# Windows
type sync_state.json

# Linux/Mac
cat sync_state.json
```

### Verificar Histórico (Windows)

```powershell
Get-ScheduledTask -TaskName "Clinicorp-Incremental-Sync"
Get-ScheduledTaskInfo -TaskName "Clinicorp-Incremental-Sync"
```

### Executar Agora (Windows)

```powershell
Start-ScheduledTask -TaskName "Clinicorp-Incremental-Sync"
```

---

## 🛠️ Troubleshooting

### A task não executa

```powershell
# Verificar status
Get-ScheduledTask -TaskName "Clinicorp-Incremental-Sync" | Select-Object TaskName, State

# Se desabilitada, habilitar:
Enable-ScheduledTask -TaskName "Clinicorp-Incremental-Sync"
```

### Erro: Python não encontrado

Edite `setup_scheduler.ps1` e atualize o caminho do Python:

```powershell
$pythonPath = "C:\path\to\python.exe"  # Seu caminho real
```

### Resetar sincronização (recarregar tudo)

```bash
# Delete o arquivo de estado
del sync_state.json

# Próxima execução será de 24 horas atrás
```

---

## 📅 Intervalos Recomendados

| Caso de Uso | Intervalo | Razão |
|------------|-----------|-------|
| **Produção Alta Frequência** | 1 hora | Atualização quase real-time |
| **Produção Normal** | 6 horas | Balanço entre atualização e custo |
| **Desenvolvimento** | Manual | Flexibilidade para testes |
| **Backup Noturno** | Diariamente | Uma sincronização por dia |

**Configuração atual:** 6 horas

---

## 📊 Exemplo de Execução

```
================================================================================
SINCRONIZACAO INCREMENTAL - CLINICORP
================================================================================

[1] CARREGANDO ESTADO ANTERIOR...
    Última sincronização: 2026-06-09T13:11:55

[2] PERIODO DE SINCRONIZACAO: 2026-06-09 a 2026-06-09

[3] SINCRONIZANDO AGENDAMENTOS...
    API retornou: 98 agendamentos
    [OK] 98 agendamentos sincronizados

[4] SINCRONIZANDO PAGAMENTOS...
    API retornou: 32 pagamentos
    [OK] 32 pagamentos sincronizados

[5] SINCRONIZANDO FATURAS...
    API retornou: 11 faturas
    [OK] 11 faturas sincronizadas

[6] SALVANDO ESTADO...
    [OK] Estado salvo

================================================================================
RESULTADO DA SINCRONIZACAO
================================================================================

[TOTAL ADICIONADO]: 141 registros
```

---

## 🔐 Segurança

- ✅ Credenciais em `.env` (não commitadas)
- ✅ Sem armazenamento de senhas no script
- ✅ HTTPS para todas as requisições à API
- ✅ Task scheduler executa com permissões limitadas

---

## 📞 Próximos Passos

1. **Configure a task:**
   ```powershell
   .\setup_scheduler.ps1
   ```

2. **Monitore a primeira execução:**
   ```powershell
   Get-ScheduledTaskInfo -TaskName "Clinicorp-Incremental-Sync"
   ```

3. **Verifique os dados:**
   ```sql
   SELECT COUNT(*) FROM appointments WHERE last_sync_at > '2026-06-09'::date;
   ```

---

## 📝 Notas

- Sincronização incremental começa com **últimas 24 horas** na primeira execução
- `sync_state.json` é atualizado automaticamente a cada execução
- Upsert garante que atualizações no Clinicorp sincronizem para Supabase
- O script é idempotente (seguro executar múltiplas vezes)

---

**Status:** ✅ Pronto para produção  
**Atualizado:** 2026-06-09  
**Versão:** 1.0

