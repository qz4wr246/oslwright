@echo off
@REM ----------------------------------------------------------------
@REM - Download Tools
@REM ----------------------------------------------------------------
setlocal EnableDelayedExpansion
set _LD=%~dp0
cd /d %_LD%
set SCRIPT_DIR=%_LD:~0,-1%
set SCRIPT_FILE=%~dpnx0

@REM Output log to file and console.
chcp 65001 >nul 2>&1
if defined LOGFILE goto :DO_SCRIPT
  set "LOGFILE=%SCRIPT_DIR%\Output.txt"
  "%~f0" %* 2>&1 | powershell -NoProfile -Command "$input | Tee-Object -FilePath \"%LOGFILE%\""
  exit /b
:DO_SCRIPT
@REM ----------------------------------------------------------------
@REM - downloading
@REM ----------------------------------------------------------------
set glib_url=https://download.gnome.org/binaries/win64/glib/2.26/glib_2.26.1-1_win64.zip
set glib_zip=%SCRIPT_DIR%\glib_2.26.1-1_win64.zip
set gettext_url=https://download.gnome.org/binaries/win64/dependencies/gettext-runtime_0.18.1.1-2_win64.zip
set gettext_zip=%SCRIPT_DIR%\gettext-runtime_0.18.1.1-2_win64.zip
set pkg_config_url=https://download.gnome.org/binaries/win64/dependencies/pkg-config_0.23-2_win64.zip
set pkg_config_zip=%SCRIPT_DIR%\pkg-config_0.23-2_win64.zip

if not exist "%glib_zip%" (
  curl.exe -L -s -o "%glib_zip%" "%glib_url%"
)
tar -xf "%glib_zip%" -C "%SCRIPT_DIR%"
if not exist "%gettext_zip%" (
  curl.exe -L -s -o "%gettext_zip%" "%gettext_url%"
)
tar -xf "%gettext_zip%" -C "%SCRIPT_DIR%"
if not exist "%pkg_config_zip%" (
  curl.exe -L -s -o "%pkg_config_zip%" "%pkg_config_url%"
)
tar -xf "%pkg_config_zip%" -C "%SCRIPT_DIR%"
exit /b 0
@REM -----------------------end of file------------------------------
