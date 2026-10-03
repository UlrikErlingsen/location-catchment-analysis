@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto fail
  ".venv\Scripts\python.exe" -m pip install -e ".[ui]"
  if errorlevel 1 goto fail
)
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8523 --server.address 127.0.0.1
if errorlevel 1 goto fail
exit /b 0
:fail
pause
exit /b 1
