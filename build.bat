@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==================================================
echo  Shopping Analytics - Compilar aplicacion
echo ==================================================

REM --- [1/4] Entorno virtual ---
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creando el entorno virtual en .venv...
    py -3.11 -m venv .venv 2>nul || python -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo ERROR: no se pudo crear .venv. Instala Python 3.11 y vuelve a intentarlo.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Entorno virtual encontrado.
)

set PY=.venv\Scripts\python.exe

REM --- [2/4] Dependencias + PyInstaller ---
"%PY%" -c "import cv2, numpy, scipy, PyQt5, PIL, qdarkstyle" >nul 2>&1
if errorlevel 1 (
    echo [2/4] Instalando dependencias de requirements.txt...
    "%PY%" -m pip install --disable-pip-version-check -q -r requirements.txt
    if errorlevel 1 (
        echo ERROR: fallo al instalar las dependencias.
        pause
        exit /b 1
    )
)
"%PY%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [2/4] Instalando PyInstaller...
    "%PY%" -m pip install --disable-pip-version-check -q pyinstaller
    if errorlevel 1 (
        echo ERROR: fallo al instalar PyInstaller.
        pause
        exit /b 1
    )
) else (
    echo [2/4] Dependencias y PyInstaller listos.
)

REM --- [3/4] Modelos (obligatorios para el build) ---
echo [3/4] Comprobando modelos (descarga los que falten)...
"%PY%" scripts\download_models.py
if errorlevel 1 (
    echo ERROR: faltan modelos y no se pudieron descargar. Necesitas internet la primera vez.
    pause
    exit /b 1
)

REM --- [4/4] Compilar ---
echo [4/4] Compilando con PyInstaller (puede tardar varios minutos)...
"%PY%" -m PyInstaller --noconfirm --clean --windowed --name ShoppingAnalytics ^
    --add-data "ui;ui" ^
    --add-data "processor\detectracker\yolov3.cfg;processor\detectracker" ^
    --add-data "processor\detectracker\model_data\yolov3.weights;processor\detectracker\model_data" ^
    --add-data "processor\detectracker\model_data\mars-small128-opencv.pb;processor\detectracker\model_data" ^
    --add-data "processor\detectracker\model_data\coco_classes.txt;processor\detectracker\model_data" ^
    --add-data "processor\agender\opencv_face_detector.pbtxt;processor\agender" ^
    --add-data "processor\agender\opencv_face_detector_uint8.pb;processor\agender" ^
    --add-data "processor\agender\model;processor\agender\model" ^
    footfall.py
if errorlevel 1 (
    echo ERROR: fallo la compilacion.
    pause
    exit /b 1
)

if not exist "dist\ShoppingAnalytics\ShoppingAnalytics.exe" (
    echo ERROR: no se genero el ejecutable.
    pause
    exit /b 1
)

for %%A in ("dist\ShoppingAnalytics\ShoppingAnalytics.exe") do set SIZE=%%~zA
echo.
echo ==================================================
echo  BUILD LISTO
echo  Ejecutable : dist\ShoppingAnalytics\ShoppingAnalytics.exe
echo  Tamano exe : %SIZE% bytes
echo  Para distribuir, copia la carpeta completa dist\ShoppingAnalytics
echo  (el exe necesita su carpeta _internal junto a el).
echo ==================================================
pause
exit /b 0
