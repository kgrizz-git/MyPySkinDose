@echo off
setlocal
title MyPySkinDose GUI Launcher

echo ==========================================
echo       MyPySkinDose GUI Launcher
echo ==========================================
echo.
echo How would you like to run the GUI?
echo [1] Browser (Standard)
echo [2] Native Window (Requires pywebview)
echo.

set /p choice="Enter your choice (1 or 2, default is 1): "

if "%choice%"=="2" (
    echo.
    echo Starting MyPySkinDose in Native Window mode...
    if exist .venv\Scripts\python.exe (
        .venv\Scripts\python -m mypyskindose --mode gui --native
    ) else (
        python -m mypyskindose --mode gui --native
    )
) else (
    echo.
    echo Starting MyPySkinDose in Browser mode...
    if exist .venv\Scripts\python.exe (
        .venv\Scripts\python -m mypyskindose --mode gui
    ) else (
        python -m mypyskindose --mode gui
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The application failed to start. 
    echo Ensure you have installed the dependencies: pip install .[gui]
    pause
)

pause
