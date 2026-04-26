@echo off
title OSINT Dashboard - Starting...
color 0A

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║     OSINT Dashboard - Telegram Bridge     ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Check if .env exists
if not exist "backend\.env" (
    echo [!] .env file not found! Copying from .env.example...
    copy "backend\.env.example" "backend\.env"
    echo [!] Please edit backend\.env with your Telegram API credentials!
    echo [!] Then run this script again.
    pause
    exit /b
)

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b
)

:: Install dependencies
echo [*] Installing Python dependencies...
cd backend
pip install -r requirements.txt -q
echo [OK] Dependencies installed!
echo.

:: Start the server
echo [*] Starting OSINT Dashboard server...
echo [*] Open http://localhost:8000 in your browser
echo [*] Default login: admin / admin123
echo.
echo ─────────────────────────────────────────────
echo.
python main.py

pause
