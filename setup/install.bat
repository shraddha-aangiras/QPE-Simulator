@echo off
cd /d "%~dp0.."

echo Setting up Python Virtual Environment for QPE...

:: Create venv if it doesn't exist
if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo.
echo Setup Complete! You can now use run.bat in the main folder.
pause
