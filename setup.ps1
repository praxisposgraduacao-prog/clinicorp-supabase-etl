# Script de Setup - Clinicorp ETL
# Executa todo o setup necessário

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Clinicorp ETL - Setup Inicial" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar se Python está instalado
Write-Host "[1/3] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python instalado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python não encontrado. Instale Python 3.8+" -ForegroundColor Red
    exit 1
}

# 2. Instalar dependências
Write-Host ""
Write-Host "[2/3] Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependências instaladas" -ForegroundColor Green

# 3. Criar tabelas no Supabase
Write-Host ""
Write-Host "[3/3] Criando tabelas no Supabase..." -ForegroundColor Yellow
python setup_database.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Erro ao criar tabelas" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Setup concluído com sucesso!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximo passo:" -ForegroundColor Cyan
Write-Host "  python etl_clinicorp.py" -ForegroundColor Cyan
Write-Host ""
