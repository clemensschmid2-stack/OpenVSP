@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=python"
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
"%PYTHON_EXE%" run_state_sweep_regression.py %*
set "TEST_EXIT=%ERRORLEVEL%"
exit /b %TEST_EXIT%
