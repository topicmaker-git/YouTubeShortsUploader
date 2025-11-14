@echo off

REM Check if virtual environment exists
if not exist "venv\" (
    echo Error: Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment and run script
call venv\Scripts\activate.bat
python main.py %*

REM Deactivate virtual environment
call deactivate
