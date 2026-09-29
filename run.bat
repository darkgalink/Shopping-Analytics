@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==================================================
echo  Shopping Analytics - Lanzar aplicacion
echo ==================================================

REM --- [1/3] Entorno virtual ---
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando el entorno virtual en .venv...
    py -3.11 -m venv .venv 2>nul || python -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo ERROR: no se pudo crear .venv. Instala Python 3.11 y vuelve a intentarlo.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Entorno virtual encontrado.
)

set PY=.venv\Scripts\python.exe

REM --- [2/3] Dependencias ---
"%PY%" -c "import cv2, numpy, scipy, PyQt5, PIL, qdarkstyle" >nul 2>&1
if errorlevel 1 (
    echo [2/3] Instalando dependencias de requirements.txt...
    "%PY%" -m pip install --disable-pip-version-check -q -r requirements.txt
    if errorlevel 1 (
        echo ERROR: fallo al instalar las dependencias.
        pause
        exit /b 1
    )
) else (
    echo [2/3] Dependencias al dia.
)

REM --- [3/3] Modelos + aplicacion ---
echo [3/3] Comprobando modelos (descarga los que falten)...
"%PY%" scripts\download_models.py >nul 2>&1
if errorlevel 1 (
    echo AVISO: faltan modelos; la aplicacion volvera a intentarlo al arrancar.
)

echo.
echo Iniciando la aplicacion...
echo.
"%PY%" footfall.py
set APPERR=%ERRORLEVEL%
if not "%APPERR%"=="0" (
    echo.
    echo ERROR: la aplicacion termino con el codigo %APPERR%.
    pause
)
exit /b %APPERR%
