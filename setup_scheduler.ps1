# Script PowerShell para agendar sincronização incremental
# Executa a cada 6 horas automaticamente

$pythonPath = "C:\Users\Usuário\AppData\Local\Programs\Python\Python314\python.exe"
$scriptPath = "C:\projetos_praxis\Clinicorp\incremental_sync.py"
$taskName = "Clinicorp-Incremental-Sync"

Write-Host "=" * 80
Write-Host "Configurar Sincronização Automática - Clinicorp" -ForegroundColor Cyan
Write-Host "=" * 80

# Verificar se já existe
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "`n[!] Task já existe. Removendo..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Criar ação
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory "C:\projetos_praxis\Clinicorp"

# Criar gatilho - a cada 6 horas
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(10) -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration (New-TimeSpan -Days 365)

# Criar configuração
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -StartWhenAvailable

# Registrar task
Write-Host "`n[*] Criando task agendada...`n"

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Sincronização incremental de dados Clinicorp com Supabase"

Write-Host "[OK] Task criada com sucesso!" -ForegroundColor Green

# Listar detalhes
Write-Host "`n[INFO] Detalhes da task:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, Description

Write-Host "`n[INFO] Próximas execuções:" -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $taskName
if ($task.LastRunTime) {
    Write-Host "  Última execução: $($task.LastRunTime)"
}
Write-Host "  Intervalo: A cada 6 horas"
Write-Host "  Próxima execução: Em aproximadamente 6 horas"

Write-Host "`n[COMANDOS ÚTEIS]" -ForegroundColor Yellow
Write-Host "  Ver status: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "  Executar agora: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  Remover: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
Write-Host "  Ver histórico: Get-ScheduledTaskInfo -TaskName '$taskName'"

Write-Host "`n" + ("=" * 80)
Write-Host "Sincronização incremental agora será executada a cada 6 horas!" -ForegroundColor Green
Write-Host "=" * 80 + "`n"
