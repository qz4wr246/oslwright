@echo off
@REM -----------------------------------------------
@REM - CMake building
@REM -----------------------------------------------
setlocal EnableDelayedExpansion
SET _LD=%~dp0
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
@REM - User Settings
@REM   VS_VERSION: Visual Studio version number
@REM   VS_EDITION: Visual Studio Edition
@REM   BUILD_DIR: build directory
@REM ----------------------------------------------------------------
set VS_VERSION=2022
set VS_EDITION=Community
set "BUILD_DIR=%SCRIPT_DIR%\build_x64"

@REM -----------------------------------------------
@REM Setup building environment
@REM -----------------------------------------------
@REM msvc building environment
set VS_ROOT=C:\Program Files\Microsoft Visual Studio\%VS_VERSION%\%VS_EDITION%
set VS_DEVCMD_BAT=%VS_ROOT%\Common7\Tools\VsDevCmd.bat

@REM cmake
set CMAKE_EXE=C:\Program Files\CMake\bin\cmake.exe

@REM Setup MSBuild environment.
if "%VCINSTALLDIR%"=="" (
  call "%VS_DEVCMD_BAT%" -arch=amd64 >nul 2>&1
)
if not exist "%BUILD_DIR%\CMakeCache.txt" (
  echo Run configure.bat to set up the CMake configuration.
  exit 1
)

@REM Release build
echo ------------------------------------------------
echo - Build for release.
echo ------------------------------------------------
"%CMAKE_EXE%" --build "%BUILD_DIR%" --config Release -j4
if errorlevel 1 (
  echo ERROR build failed.
  echo Press return key to exit.
  set /P CONFIRM=
  exit %ERRORLEVEL%
)

@REM @REM Debug build
@REM echo -----------------------------------------------
@REM echo - Build for debug.
@REM echo -----------------------------------------------
@REM "%CMAKE_EXE%" --build "%BUILD_DIR%" --config Debug -j4
@REM if errorlevel 1 (
@REM   echo ERROR build failed.
@REM   echo Press return key to exit.
@REM   set /P CONFIRM=
@REM   exit %ERRORLEVEL%
@REM )

@REM Instal
echo -----------------------------------------------
echo - Install the application.
echo -----------------------------------------------
"%CMAKE_EXE%" --install "%BUILD_DIR%" --config Release
if errorlevel 1 (
  echo ERROR install failed.
  echo Press return key to exit.
  set /P CONFIRM=
  exit %ERRORLEVEL%
)

@REM Make a package
if exist "%BUILD_DIR%\CPackConfig.cmake" (
  echo -----------------------------------------------
  echo - Make the package of application.
  echo -----------------------------------------------
  "%CMAKE_EXE%" --build  "%BUILD_DIR%" --target package --config Release
  if errorlevel 1 (
    echo ERROR make package failed.
    echo Press return key to exit.
    set /P CONFIRM=
    exit %ERRORLEVEL%
  )
)
exit /b 0
@REM ------------------------ End of file. ------------------------
