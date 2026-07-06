@echo off
echo =========================================================
echo       Sunshine RCA Dashboard Starter (Local Host)
echo =========================================================
echo.
echo Checking python dependencies...
python -c "import fastapi, uvicorn, pandas, numpy" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Missing libraries detected. Installing from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Please run 'pip install -r requirements.txt' manually.
        pause
        exit /b %errorlevel%
    )
) else (
    echo [INFO] All python dependencies are satisfied.
)

echo.
echo [INFO] Launching FastAPI Backend Server on port 2026...
python backend/server.py
pause
