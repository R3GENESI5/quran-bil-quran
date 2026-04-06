@echo off
title Quran bil-Quran
echo.
echo   Starting Quran bil-Quran...
echo.

:: Find an available port
set PORT=8080

:: Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   Python not found. Install Python 3 from https://python.org
    echo   Or open app\index.html directly in your browser.
    pause
    exit /b 1
)

:: Get local IP for phone access
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set LOCAL_IP=%%b
)

echo   Local:   http://localhost:%PORT%
if defined LOCAL_IP echo   Phone:   http://%LOCAL_IP%:%PORT%
echo.
echo   Press Ctrl+C to stop.
echo.

:: Open browser
start http://localhost:%PORT%

:: Start server
cd /d "%~dp0app"
python -m http.server %PORT%
