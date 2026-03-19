@echo off
echo ========================================
echo   Iniciar Servidor com ngrok (HTTPS)
echo ========================================
echo.
echo IMPORTANTE: Este script expoe seu servidor localmente via tunel HTTPS
echo para permitir testes de Push Notifications em dispositivos moveis.
echo.

REM Verificar se ngrok existe
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] ngrok nao encontrado!
    echo.
    echo Por favor, instale o ngrok:
    echo 1. Baixe de: https://ngrok.com/download
    echo 2. Extraia ngrok.exe para uma pasta no PATH
    echo    OU coloque ngrok.exe nesta pasta
    echo.
    pause
    exit /b 1
)

echo ngrok encontrado! Iniciando tunel...
echo.

REM Iniciar ngrok em background
echo Abrindo tunel HTTPS na porta 5000...
start "ngrok" ngrok http 5000 --log=stdout

echo.
echo ========================================
echo   Servidor Exposto via ngrok!
echo ========================================
echo.
echo 1. Aguarde alguns segundos para ngrok iniciar
echo 2. Acesse: http://localhost:4040
echo 3. Copie a URL HTTPS (ex: https://abc123.ngrok.io)
echo 4. Use essa URL no celular para acessar o sistema
echo 5. Notificacoes Push funcionarao via HTTPS!
echo.
echo IMPORTANTE: Mantenha esta janela aberta enquanto testa
echo Para parar, feche a janela do ngrok
echo.
pause
