@echo off
setlocal
if defined CONDA_PREFIX (
  "%CONDA_PREFIX%\python.exe" "%~dp0run_state_continuation_regression.py" --require-feature %*
) else (
  python "%~dp0run_state_continuation_regression.py" --require-feature %*
)
exit /b %ERRORLEVEL%
