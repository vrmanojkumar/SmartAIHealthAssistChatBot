#!/bin/bash

echo "========================================"
echo "AI Health Assistant - Installation Script"
echo "========================================"
echo ""

echo "[1/3] Checking Python installation..."
python3 --version || python --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python is not installed or not in PATH"
    exit 1
fi

echo ""
echo "[2/3] Installing/Updating dependencies..."
python3 -m pip install --upgrade pip || python -m pip install --upgrade pip
python3 -m pip install -r requirement.txt || python -m pip install -r requirement.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "[3/3] Starting the application..."
echo ""
echo "The application will open in your browser automatically."
echo "If it doesn't, navigate to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m streamlit run chat.py || python -m streamlit run chat.py



