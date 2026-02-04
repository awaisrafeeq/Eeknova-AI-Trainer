@echo off
REM run.bat - Windows run script

echo Starting Chess Learning System...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist ".deps_installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo. > .deps_installed
)

REM Run the application
python main.py

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

pause