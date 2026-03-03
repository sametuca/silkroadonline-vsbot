@echo off

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator privileges confirmed.
) else (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
echo.
echo ======================================
echo   Silkroad Vision Bot - GUI Mode
echo   Running with Administrator Rights
echo ======================================
echo.
python bot_gui.py
pause
