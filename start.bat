@echo off
echo Starting PortalShare Application...

REM Check if virtual environment exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Check if .env file exists, create from example if not
if not exist .env (
    echo No .env file found, creating from example...
    copy .env.example .env
    echo Please edit the .env file with your Google OAuth credentials
    pause
)

REM Initialize database if it doesn't exist
if not exist instance\portalshare.db (
    echo Initializing database...
    python init_db.py
)

REM Run database migrations
echo Running database migrations...
python migrate.py

REM Start the application
echo Starting application...
python run.py

pause