@echo off
REM Run the real-time Vibe Demo player (Assembly Summer 2026)
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
.venv\Scripts\pip install -q -r requirements.txt
.venv\Scripts\python.exe source\demo_player.py %*
