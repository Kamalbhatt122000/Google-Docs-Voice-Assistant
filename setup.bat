@echo off
echo ============================================
echo    Voice Assistant Setup Script
echo    LiveKit + Gemini Computer Use
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing Python dependencies...
pip install -r requirements.txt

echo [5/5] Installing Playwright browser...
playwright install chromium

echo.
echo ============================================
echo    Creating .env file...
echo ============================================

if not exist .env (
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit the .env file and add:
    echo   - LIVEKIT_URL
    echo   - LIVEKIT_API_KEY  
    echo   - LIVEKIT_API_SECRET
    echo   - GOOGLE_API_KEY
    echo.
)

echo.
echo ============================================
echo    Setup Complete!
echo ============================================
echo.
echo To start the assistant:
echo.
echo   Terminal 1 (Agent):
echo     venv\Scripts\activate
echo     python agent.py dev
echo.
echo   Terminal 2 (Web Server):
echo     venv\Scripts\activate
echo     python server.py
echo.
echo   Then open: http://localhost:5000
echo.
pause
