# Script PowerShell para iniciar o servidor Flask
# Usa o ambiente virtual automaticamente

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sistema de Gerenciamento - Ministerio" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Verificando ambiente virtual..." -ForegroundColor Yellow
$venvPath = ".venv\Scripts\python.exe"

if (Test-Path $venvPath) {
    Write-Host "✓ Ambiente virtual encontrado" -ForegroundColor Green
    Write-Host ""
    Write-Host "Iniciando servidor Flask..." -ForegroundColor Yellow
    Write-Host ""
    
    & $venvPath app.py
} else {
    Write-Host "✗ Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, crie o ambiente virtual primeiro:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor White
    Write-Host "  .venv\Scripts\activate" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
    pause
}
