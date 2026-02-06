@echo off
echo ============================================
echo    Starting Voice Assistant Web Server
echo ============================================
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Run the server
echo Starting web server on http://localhost:5000
echo Press Ctrl+C to stop
echo.
python server.py

pause
