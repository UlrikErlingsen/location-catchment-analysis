@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo Reach Signal needs Python 3.10 or newer.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating Reach Signal's private Python environment...
  py -m venv .venv
)
".venv\Scripts\python.exe" -c "import streamlit, plotly, openpyxl" >nul 2>&1
if errorlevel 1 (
  echo Installing Reach Signal's open-source packages...
  ".venv\Scripts\python.exe" -m pip --disable-pip-version-check install --prefer-binary -r requirements.txt
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
if not defined ARROW_DEFAULT_MEMORY_POOL set ARROW_DEFAULT_MEMORY_POOL=system
if "%REACHSIGNAL_PORT%"=="" set REACHSIGNAL_PORT=8599
if "%REACHSIGNAL_MAX_UPLOAD_MB%"=="" set REACHSIGNAL_MAX_UPLOAD_MB=10000
echo Starting Reach Signal at http://127.0.0.1:%REACHSIGNAL_PORT% ...
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless=true --server.address=127.0.0.1 --server.port=%REACHSIGNAL_PORT% --server.maxUploadSize=%REACHSIGNAL_MAX_UPLOAD_MB% --server.fileWatcherType=none --browser.gatherUsageStats=false
if errorlevel 1 pause
