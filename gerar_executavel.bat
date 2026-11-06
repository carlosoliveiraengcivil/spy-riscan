@echo off
title Compilador SPY RiSCAN - Gerar .EXE Unico
color 0b
cd /d "%~dp0"

echo ======================================================================
echo              COMPILADOR AUTOMATICO - SPY RISCAN
echo          (Auditor de Inventarios Volumetricos - Standalone)
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado no PATH do Windows!
    pause
    exit /b 1
)

echo [1/3] Verificando dependencias necessarias...
pip install pyinstaller customtkinter uiautomation openpyxl pillow --quiet --disable-pip-version-check

echo.
echo [2/3] Compilando em um UNICO arquivo executavel (Standalone com icone 3D)...
echo Aguarde cerca de 1 minuto...
echo.

rmdir /s /q build dist 2>nul

pyinstaller --noconfirm --onefile --windowed ^
    --name "SPY RiSCAN" ^
    --icon="app_icon.ico" ^
    --add-data="app_icon.ico;." ^
    --collect-all customtkinter ^
    --clean ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] A compilacao falhou.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Movendo executavel e limpando temporarios...
powershell -Command "Copy-Item -Path 'dist\SPY RiSCAN.exe' -Destination 'SPY RiSCAN.exe' -Force; Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue"

echo.
echo ======================================================================
echo   SUCESSO! Executavel gerado com icone e protecao ativada:
echo   -> SPY RiSCAN.exe
echo ======================================================================
echo.
pause
