@echo off
@REM ----------------------------------------------------------------
@REM - CMake configuration script
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
@REM - User Settings
@REM   VS_VERSION: Visual Studio version number
@REM   VS_EDITION: Visual Studio Edition
@REM   OSLW_ROOT_DIR: oslwright's root directory. if undefined, the 3rdparty directory will be used.
@REM   BUILD_DIR: build directory
@REM   INSTALL_DIR: install directory
@REM   CMAKE_OPTIONS: cmake options
@REM ----------------------------------------------------------------
set VS_VERSION=2022
set VS_EDITION=Community
set "OSLW_ROOT_DIR=%SCRIPT_DIR%\..\.."
set "BUILD_DIR=%SCRIPT_DIR%\build_x64"
set "INSTALL_DIR=%SCRIPT_DIR%\dist"
@REM set "CMAKE_OPTIONS="

@REM ----------------------------------------------------------------
@REM cmake generator
@REM ----------------------------------------------------------------
set CMAKE_CONFIGURATION_TYPES=Release;Debug

call :GetMsvcGenerator %VS_VERSION% MSVC_GENERATOR_VERSION
set MSVC_GENERATOR_ARCH=x64
set MSVC_GENERATOR=-G "Visual Studio %MSVC_GENERATOR_VERSION%" -A %MSVC_GENERATOR_ARCH%
set CMAKE_GENERATOR=%MSVC_GENERATOR%

@REM ----------------------------------------------------------------
@REM Setup building environment
@REM ----------------------------------------------------------------
@REM msvc building environment
set VS_ROOT=C:\Program Files\Microsoft Visual Studio\%VS_VERSION%\%VS_EDITION%
set VS_DEVCMD_BAT=%VS_ROOT%\Common7\Tools\VsDevCmd.bat

@REM cmake
set CMAKE_EXE=C:\Program Files\CMake\bin\cmake.exe

@REM  CMAKE_TOOLCHAIN_FILE default stting
if not defined CMAKE_TOOLCHAIN_FILE (
  if defined OSLW_ROOT_DIR (
    set CMAKE_TOOLCHAIN_FILE=%OSLW_ROOT_DIR%\cmake\oslwright.cmake
  )
)

@REM Setup MSBuild environment.
if "%VCINSTALLDIR%"=="" (
  call "%VS_DEVCMD_BAT%" -arch=amd64 >nul 2>&1
)

@REM pkg-condig
if not exist "%SCRIPT_DIR%\tools\pkg-config\bin\pkg-config.exe" (
  call "%SCRIPT_DIR%\tools\pkg-config\setup.bat"
)
if exist "%SCRIPT_DIR%\tools\pkg-config\bin\pkg-config.exe" (
  set "PATH=%PATH%;%SCRIPT_DIR%\tools\pkg-config\bin"
)

@REM ----------------------------------------------------------------
@REM CMake configuration
@REM ----------------------------------------------------------------
@REM set CMAKE OPTIONS
if defined CMAKE_TOOLCHAIN_FILE (
  set CMAKE_OPTIONS=%CMAKE_OPTIONS% ^
    -DCMAKE_TOOLCHAIN_FILE="%CMAKE_TOOLCHAIN_FILE%"
)

@REM Remove cmake cache files.
if exist "%BUILD_DIR%" (
  del /q /s "%BUILD_DIR%\CMakeCache.txt" "%BUILD_DIR%\CMakeFiles\" "%BUILD_DIR%\*.cmake" >nul 2>&1
)

@REM Generate Visual Studio solution file, and configuration.
echo ----------------------------------------------------------------
echo - Configuration for the applicaion.
echo ----------------------------------------------------------------
echo CMake command options
echo - GENERATOR           %CMAKE_GENERATOR%
echo - CONFIGURATION_TYPES %CMAKE_CONFIGURATION_TYPES%
echo - BUILD_DIR           %BUILD_DIR%
echo - INSTALL_DIR         %INSTALL_DIR%
echo - CMAKE_OPTIONS       %CMAKE_OPTIONS%
echo.

"%CMAKE_EXE%" %CMAKE_GENERATOR% ^
  -DCMAKE_INSTALL_PREFIX="%INSTALL_DIR%" ^
  -DCMAKE_CONFIGURATION_TYPES="%CMAKE_CONFIGURATION_TYPES%" ^
  %CMAKE_OPTIONS% ^
  -S . -B "%BUILD_DIR%"
if errorlevel 1 (
  echo ERROR configuration failed.
  echo Press return key to exit.
  set /p CONFIRM=
  exit /b %ERRORLEVEL%
)
exit /b 0
goto eof
@REM ----------------------------------------------------------------
@REM Functions
@REM ----------------------------------------------------------------

@REM ----------------------------------------------------------------
@REM  call GetMsvcGenerator <VERSION> <RESULT>
@REM ----------------------------------------------------------------
:GetMsvcGenerator
setlocal EnableDelayedExpansion
set "input=%~1"
set "outvar=%~2"
set "FOUND=0"

:: generator mapping
set "MAP[0]=2019=16 2019"
set "MAP[1]=2022=17 2022"

for /L %%i in (0,1,3) do (
    set "entry=!MAP[%%i]!"
    for /F "tokens=1,* delims==" %%A in ("!entry!") do (
        if "%%A"=="%input%" (
            set "result=%%B"
            set "FOUND=1"
        )
    )
)
if "!FOUND!"=="0" (
    set "result=?? %input%"
)
set "_ret=& set "%outvar%=%result%""
endlocal %_ret%
exit /b 0
@REM ------------------------ End of file. --------------------------
