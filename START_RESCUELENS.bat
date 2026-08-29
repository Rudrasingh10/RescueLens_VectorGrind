@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo        RescueLens - Local Demo Launcher
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating Python 3.12 virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Python 3.12 was not found.
        echo Install Python 3.12 and make sure the py launcher is available.
        pause
        exit /b 1
    )
)

echo [2/3] Checking dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo [3/3] Starting RescueLens...
echo.
echo Open in browser: http://127.0.0.1:8000
echo Keep this window open while presenting.
echo Press CTRL+C to stop the server.
echo.

start "RescueLens Browser" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8000"
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

pause
