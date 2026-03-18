@echo off
echo ========================================
echo   Sistema de Gerenciamento - Ministerio
echo ========================================
echo.
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.
echo Iniciando servidor Flask...
.venv\Scripts\python.exe app.py

pause