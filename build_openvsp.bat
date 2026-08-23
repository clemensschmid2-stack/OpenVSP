@echo off
setlocal
cd /d "%~dp0"
python build_openvsp.py %*
set "BUILD_EXIT=%ERRORLEVEL%"
if not "%BUILD_EXIT%"=="0" pause
exit /b %BUILD_EXIT%
