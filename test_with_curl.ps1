#!/usr/bin/env pwsh
# Script para testar os parametros da API usando cURL (nativo no Windows)

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "TESTE DOS PARAMETROS CORRIGIDOS - USANDO CURL" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

# Carregar variáveis do .env
$envContent = Get-Content .env -Raw
$envContent | ForEach-Object {
    if ($_ -match '^\s*([^=]+?)\s*=\s*(.+?)\s*$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Variable -Name $name -Value $value -Scope Global
    }
}

$API_URL = if ($ERP_CLINICORP_API_URL) { "$ERP_CLINICORP_API_URL/rest/v1" } else { "https://api.clinicorp.com/rest/v1" }
$API_USER = if ($ERP_CLINICORP_USUARIO_API) { $ERP_CLINICORP_USUARIO_API } else { "praxis" }
$API_PASS = if ($ERP_CLINICORP_API_SENHA) { $ERP_CLINICORP_API_SENHA } else { "" }
$BUSINESS_ID = if ($ERP_CLINICORP_BUSINESS_ID) { $ERP_CLINICORP_BUSINESS_ID } else { "5292365675823104" }
$SUBSCRIBER_ID = if ($ERP_CLINICORP_SUBSCRIBER_ID) { $ERP_CLINICORP_SUBSCRIBER_ID } else { "praxis" }

# Calcular datas
$today = Get-Date
$oneYearAgo = $today.AddDays(-365)
$date_from = $oneYearAgo.ToString("yyyy-MM-dd")
$date_to = $today.ToString("yyyy-MM-dd")

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$($API_USER):$($API_PASS)"))

Write-Host "`n[CONFIG]"
Write-Host "  API URL: $API_URL"
Write-Host "  Usuario: $API_USER"
Write-Host "  Subscriber: $SUBSCRIBER_ID"
Write-Host "  Business ID: $BUSINESS_ID"
Write-Host "  Periodo: $date_from a $date_to`n"

# ============================================================================
# TEST 1: /appointment/list
# ============================================================================

Write-Host "[TEST 1] GET /appointment/list" -ForegroundColor Yellow
Write-Host "-" * 80

$url = "$API_URL/appointment/list?subscriber_id=$SUBSCRIBER_ID&from=$date_from&to=$date_to&businessId=$BUSINESS_ID&includeCanceled=true"

Write-Host "URL: $url`n"

try {
    $response = Invoke-WebRequest -Uri $url `
        -Method GET `
        -Headers @{ "Authorization" = "Basic $auth" } `
        -ContentType "application/json" `
        -TimeoutSec 10

    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green

    $data = $response.Content | ConvertFrom-Json
    $count = if ($data -is [array]) { $data.Count } else { 1 }
    Write-Host "[OK] Retornou $count agendamentos" -ForegroundColor Green

} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "Response: $body" -ForegroundColor Red
    }
}

# ============================================================================
# TEST 2: /financial/list_invoices
# ============================================================================

Write-Host "`n[TEST 2] GET /financial/list_invoices" -ForegroundColor Yellow
Write-Host "-" * 80

$url = "$API_URL/financial/list_invoices?subscriber_id=$SUBSCRIBER_ID&from=$date_from&to=$date_to&business_id=$BUSINESS_ID"

Write-Host "URL: $url`n"

try {
    $response = Invoke-WebRequest -Uri $url `
        -Method GET `
        -Headers @{ "Authorization" = "Basic $auth" } `
        -ContentType "application/json" `
        -TimeoutSec 10

    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green

    $data = $response.Content | ConvertFrom-Json
    $count = if ($data -is [array]) { $data.Count } else { 1 }
    Write-Host "[OK] Retornou $count faturas" -ForegroundColor Green

} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "Response: $body" -ForegroundColor Red
    }
}

# ============================================================================
# TEST 3: /financial/list_payments
# ============================================================================

Write-Host "`n[TEST 3] GET /financial/list_payments" -ForegroundColor Yellow
Write-Host "-" * 80

$url = "$API_URL/financial/list_payments?subscriber_id=$SUBSCRIBER_ID&from=$date_from&to=$date_to&business_id=$BUSINESS_ID"

Write-Host "URL: $url`n"

try {
    $response = Invoke-WebRequest -Uri $url `
        -Method GET `
        -Headers @{ "Authorization" = "Basic $auth" } `
        -ContentType "application/json" `
        -TimeoutSec 10

    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green

    $data = $response.Content | ConvertFrom-Json
    $count = if ($data -is [array]) { $data.Count } else { 1 }
    Write-Host "[OK] Retornou $count pagamentos" -ForegroundColor Green

} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "Response: $body" -ForegroundColor Red
    }
}

# ============================================================================
# RESUMO
# ============================================================================

Write-Host "`n" + "=" * 80
Write-Host "RESUMO DOS TESTES"
Write-Host "=" * 80
Write-Host @"

Se todos os testes retornaram status 200:
  [OK] Os parametros estao corretos!
  [PROXIMO] Execute: python expand_with_subscriber.py

Se algum teste retornou status diferente:
  [CHECK] Verifique as mensagens de erro acima
  [CHECK] Consulte QUICK_REFERENCE.txt para parametros corretos
  [HELP] Entre em contato com suporte Clinicorp se necessario
"@
