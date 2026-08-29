@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" goto installed

call run_parity_tests.bat --custom-vspaero "%~1"
if errorlevel 1 exit /b 1
call run_state_continuation_regression.bat --candidate "%~1"
if errorlevel 1 exit /b 1
exit /b 0

:installed
call run_parity_tests.bat
if errorlevel 1 exit /b 1
call run_state_continuation_regression.bat
if errorlevel 1 exit /b 1
exit /b 0
