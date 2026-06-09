#!/usr/bin/env pwsh
# Script para executar o ETL Clinicorp com Python instalado via Microsoft Store

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "CLINICORP ETL - CARREGADOR DE DADOS" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

# Procurar Python em localizações comuns
$pythonLocations = @(
    "C:\Python39\python.exe",
    "C:\Python310\python.exe",
    "C:\Python311\python.exe",
    "C:\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
)

$pythonExe = $null

foreach ($loc in $pythonLocations) {
    if (Test-Path $loc) {
        $pythonExe = $loc
        Write-Host "[OK] Python encontrado: $loc" -ForegroundColor Green
        break
    }
}

if (-not $pythonExe) {
    Write-Host "`n[ERROR] Python nao encontrado em localizacoes padrao!" -ForegroundColor Red
    Write-Host "`nPor favor, instale Python 3.9+ ou execute o script diretamente:" -ForegroundColor Yellow
    Write-Host "  1. Abra PowerShell como Administrador" -ForegroundColor Yellow
    Write-Host "  2. Execute: python expand_with_subscriber.py" -ForegroundColor Yellow
    Write-Host "`nOu:" -ForegroundColor Yellow
    Write-Host "  py -3 expand_with_subscriber.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[*] Executando ETL..." -ForegroundColor Cyan
Write-Host "[*] Data/Hora: $(Get-Date)`n" -ForegroundColor Cyan

# Executar o script
& $pythonExe expand_with_subscriber.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Script executado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Script retornou codigo de erro: $LASTEXITCODE" -ForegroundColor Red
}
