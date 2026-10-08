@echo off
setlocal
py -3 -c "import sys; sys.exit(sys.version_info < (3,12))" >nul 2>nul
if not errorlevel 1 goto use_py
python -c "import sys; sys.exit(sys.version_info < (3,12))" >nul 2>nul
if not errorlevel 1 goto use_python
echo Could not find Python 3.12 or newer through py or python.
echo If Python 3.14 is installed, run its python.exe with tools\install_windows.py.
pause
exit /b 1
:use_py
py -3 "%~dp0tools\install_windows.py" %*
goto result
:use_python
python "%~dp0tools\install_windows.py" %*
:result
if errorlevel 1 (
  echo Installation failed. The actual error is shown above.
  echo Installation log: "%LOCALAPPDATA%\Pulse\install.log"
  pause
  exit /b 1
)
endlocal
