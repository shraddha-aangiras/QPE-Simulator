@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found.
    echo Please go to the 'setup' folder and run 'install.bat' first.
    echo.
    pause
    exit /b
)

call .venv\Scripts\activate

if %errorlevel% NEQ 0 (
    echo.
    echo [ERROR] The application encountered an error or crashed.
    pause
    exit /b
)

echo Starting QPE Simulation...
python main.py

echo.
echo Application closed.
pause
