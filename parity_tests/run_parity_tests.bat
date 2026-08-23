@echo off
setlocal
cd /d "%~dp0"
python run_parity_tests.py %*
set "TEST_EXIT=%ERRORLEVEL%"
if not "%TEST_EXIT%"=="0" pause
exit /b %TEST_EXIT%
