@echo off
echo.
echo ========================================
echo   Creating Desktop Shortcut
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Silkroad Bot.lnk
set TARGET_PATH=%SCRIPT_DIR%run_gui.bat
set ICON_PATH=%SCRIPT_DIR%run_gui.bat

:: Create shortcut using PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'Silkroad Vision Bot - Auto start with Admin rights'; $Shortcut.Save()"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo SUCCESS! Desktop shortcut created.
    echo.
    echo Shortcut location: %SHORTCUT_PATH%
    echo.
    echo Now you can double-click "Silkroad Bot" on your Desktop!
    echo It will automatically request administrator privileges.
    echo.
) else (
    echo.
    echo ERROR: Failed to create shortcut.
    echo.
)

pause
