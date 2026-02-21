@echo off
echo ========================================
echo AI Health Assistant - Installation Script
echo ========================================
echo.

echo [1/3] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo [2/3] Installing/Updating dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirement.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Starting the application...
echo.
echo The application will open in your browser automatically.
echo If it doesn't, navigate to: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

python -m streamlit run chat.py

pause



