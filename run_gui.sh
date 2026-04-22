#!/bin/bash

# MyPySkinDose GUI Launcher for Mac/Linux

echo "=========================================="
echo "      MyPySkinDose GUI Launcher"
echo "=========================================="
echo ""
echo "How would you like to run the GUI?"
echo "[1] Browser (Standard)"
echo "[2] Native Window (Requires pywebview)"
echo ""
read -p "Enter your choice (1 or 2, default is 1): " choice

# Use .venv if it exists, otherwise fall back to system python
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

if [ "$choice" == "2" ]; then
    echo ""
    echo "Starting MyPySkinDose in Native Window mode..."
    $PYTHON -m mypyskindose --mode gui --native
else
    echo ""
    echo "Starting MyPySkinDose in Browser mode..."
    $PYTHON -m mypyskindose --mode gui
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] The application failed to start."
    echo "Ensure you have installed the dependencies: pip install .[gui]"
    read -p "Press Enter to exit..."
fi
