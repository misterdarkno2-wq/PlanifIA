@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\iniciar_local.py
) else (
  echo Primero instala Python y las dependencias siguiendo README.md.
)
pause
