@echo off
REM Regenerate all HTML pages for all festivals
REM This is a batch file wrapper that calls the PowerShell script

echo.
echo ========================================
echo   Regenerating All Festival HTML Pages
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Run the PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0regenerate_all.ps1"

REM Check the exit code
if errorlevel 1 (
    echo.
    echo Some errors occurred during regeneration.
    pause
    exit /b 1
)

echo.
echo All done!
pause
