@echo off
setlocal EnableDelayedExpansion
set _LD=%~dp0
cd /d %_LD%
set SCRIPT_DIR=%_LD:~0,-1%
set SCRIPT_FILE=%~dpnx0
set VENV_DIR=%SCRIPT_DIR%\.venv

@REM Check python venv
if not exist "%VENV_DIR%" (
  echo #================================================
  echo # Setting up Python virtual environment.
  echo #================================================
  python -m venv .venv
  "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
  "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%\requirements.txt"
)
if not exist "%VENV_DIR%\Scripts\python3.exe" (
  pushd "%VENV_DIR%\Scripts"
  mklink python3.exe python.exe
  popd
)

@REM Launch oslwright
call "%VENV_DIR%\Scripts\activate.bat"
start /MIN "" python.exe -m oslwright
exit