@echo off
py -3 "%~dp0tools\install_windows.py" %*
if errorlevel 1 (
  echo Installation failed. Python 3.12 or newer is required.
  pause
  exit /b 1
)
