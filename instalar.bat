@echo off
chcp 65001 >nul
cd /d "%~dp0"
title HoraVerde

echo.
echo   HoraVerde
echo   ---------
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo   No encuentro Python en este ordenador.
  echo.
  echo   Instalalo desde https://www.python.org/downloads/
  echo   IMPORTANTE: marca la casilla "Add Python to PATH"
  echo   cuando te lo pregunte el instalador.
  echo.
  pause
  exit /b 1
)

if not exist venv (
  echo   Preparando todo por primera vez. Esto tarda un poco...
  python -m venv venv
  if errorlevel 1 (
    echo   Algo fallo creando el entorno virtual.
    pause
    exit /b 1
  )
)

echo   Comprobando las librerias...
venv\Scripts\python.exe -m pip install --quiet --upgrade pip
venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo   No pude instalar las librerias. Mira si tienes internet.
  pause
  exit /b 1
)

echo.
echo   Listo. Abriendo HoraVerde en el navegador...
echo.
echo   Si no se abre solo, entra en:  http://127.0.0.1:5000
echo   Para cerrarlo, cierra esta ventana.
echo.

start "" /min cmd /c "timeout /t 4 >nul && start "" http://127.0.0.1:5000"

venv\Scripts\python.exe app.py

echo.
echo   HoraVerde se ha cerrado.
pause
