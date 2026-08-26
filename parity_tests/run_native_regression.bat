@echo off
setlocal
cd /d "%~dp0"
call run_parity_tests.bat %*
if errorlevel 1 exit /b %ERRORLEVEL%
call run_state_sweep_regression.bat %*
exit /b %ERRORLEVEL%
