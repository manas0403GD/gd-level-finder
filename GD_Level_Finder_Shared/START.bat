@echo off
setlocal
cd /d "%~dp0"
title GD Level Finder - Offline Database
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.10+ was not found. Install it from https://www.python.org/downloads/
  echo Make sure "Add Python to PATH" is checked.
  pause
  exit /b 1
)
if not exist gdlf.sqlite3 (
  echo ERROR: gdlf.sqlite3 is missing. Keep it beside server.py.
  pause
  exit /b 1
)
if not exist .venv py -m venv .venv
call .venv\Scripts\activate.bat
py -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo Could not install Flask. Check your internet connection.
  pause
  exit /b 1
)
echo Starting fully preloaded GD Level Finder...
start "" http://127.0.0.1:5000
py server.py
pause
