@echo off
setlocal
set "PYTHON_EXE=python"
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
"%PYTHON_EXE%" "%~dp0run_state_continuation_regression.py" --require-feature %*
set "TEST_EXIT=%ERRORLEVEL%"
exit /b %TEST_EXIT%
