@echo off
py -3 "%~dp0tools\install_windows.py" --uninstall %*
if errorlevel 1 (
  echo Uninstall failed. Read the message above.
  pause
  exit /b 1
)
pause
