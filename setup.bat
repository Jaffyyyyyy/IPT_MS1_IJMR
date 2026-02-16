@echo off
REM Quick setup script for Windows

echo ========================================
echo Connectly Project - Quick Setup
echo ========================================
echo.

REM Check if virtual environment exists
if exist "env\" (
    echo Virtual environment already exists.
) else (
    echo Creating virtual environment...
    python -m venv env
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Activating virtual environment...
call env\Scripts\activate.bat

echo.
echo Installing dependencies...
cd connectly_project
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Failed to run migrations
    pause
    exit /b 1
)

echo.
echo Generating authentication token...
python create_token.py

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Import Connectly_API.postman_collection.json into Postman
echo 2. Disable SSL verification in Postman (Settings -^> General)
echo 3. Run: python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
echo.
echo The server will be available at: https://127.0.0.1:8000
echo.
pause
