@echo off
cd /d "%~dp0"
title Portal de Manutencao Nuno Correia Centrocar
set PORTAL_ADMIN_PASSWORD=centrocar
set PORTAL_SECRET=centrocar-nuno-local
cls
echo =============================================
echo  PORTAL DE MANUTENCAO - NUNO CORREIA
echo              CENTROCAR
echo =============================================
echo.
python -c "import flask" >nul 2>&1
if errorlevel 1 (
 echo A instalar componentes necessarios...
 python -m pip install -r requirements.txt
)
echo Portal: http://127.0.0.1:5000
echo Administracao: palavra-passe inicial = centrocar
echo.
echo Pode alterar a palavra-passe neste ficheiro BAT.
echo Nao feche esta janela enquanto utilizar o portal.
echo.
start "" http://127.0.0.1:5000
python app.py
pause
