# Clinicorp ETL Web — builds frontend and starts the production server
param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "Building frontend..."
Set-Location "$root\frontend"
npm run build

Write-Host "Starting backend server on port $Port..."
Set-Location "$root\backend"
& "$root\..\..\\.venv\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port $Port
