@echo off
echo ============================================
echo    Starting Voice Assistant Agent
echo ============================================
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Run the agent
echo Starting LiveKit agent...
echo Press Ctrl+C to stop
echo.
python agent.py dev

pause
