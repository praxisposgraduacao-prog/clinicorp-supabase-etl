@echo off
REM Script de Setup - Clinicorp ETL

echo ========================================
echo Clinicorp ETL - Setup Inicial
echo ========================================
echo.

REM 1. Instalar dependências
echo [1/2] Instalando dependências...
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Erro ao instalar dependencias
    pause
    exit /b 1
)

echo.
REM 2. Criar tabelas
echo [2/2] Criando tabelas no Supabase...
python setup_database.py
if %ERRORLEVEL% neq 0 (
    echo Erro ao criar tabelas
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup concluido com sucesso!
echo ========================================
echo.
echo Proximo passo:
echo   python etl_clinicorp.py
echo.
pause
