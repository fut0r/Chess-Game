#!/bin/bash

# run_chess.sh - Universal Linux/macOS Launcher for Chess Game

echo "------------------------------------------"
echo "   CHESS GAME - UNIVERSAL LAUNCHER        "
echo "------------------------------------------"

# 1. Check for Python
if ! command -v python3 &> /dev/null
then
    echo "ERROR: Python 3 is not installed. Please install it first."
    exit
fi

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Install/Update Dependencies
echo "[2/3] Checking dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Launch Game
echo "[3/3] Launching Chess Game..."
python3 main.py

# Deactivate on exit
deactivate
