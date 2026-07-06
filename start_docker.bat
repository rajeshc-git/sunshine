@echo off
echo =========================================================
echo       Sunshine RCA Dashboard Starter (Docker Container)
echo =========================================================
echo.
echo Checking if Docker is installed...
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not added to your PATH.
    echo Please install Docker Desktop and try again.
    pause
    exit /b 1
)

echo Checking if docker-compose is installed...
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] docker-compose command not found. Trying 'docker compose'...
    docker compose version >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Neither 'docker-compose' nor 'docker compose' is available.
        pause
        exit /b 1
    )
    echo [INFO] Building and starting container via 'docker compose'...
    docker compose up --build
) else (
    echo [INFO] Building and starting container via 'docker-compose'...
    docker-compose up --build
)
pause
