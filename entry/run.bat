@echo off
setlocal
REM Run the real-time Vibe Demo player (Assembly Summer 2026)
cd /d "%~dp0.."

if not exist "source\audio\playback.wav" (
  echo ERROR: required live audio master is missing:
  echo   %CD%\source\audio\playback.wav
  echo Re-extract the complete submission package. No quiet fallback will be used.
  pause
  exit /b 1
)

set "PYTHON_CMD=python"
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not exist ".venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :error
)

.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pip uninstall -y pygame >nul 2>nul
.venv\Scripts\python.exe -m pip install --upgrade --prefer-binary -r requirements.txt
if errorlevel 1 goto :error
.venv\Scripts\python.exe source\demo_player.py --audio %*
exit /b %errorlevel%

:error
echo.
echo Setup failed. Python 3.10 or newer and an internet connection are required.
pause
exit /b 1
