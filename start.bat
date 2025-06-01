@echo off
echo Starting PortalShare setup...

rem Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

rem Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

rem Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

rem Run the application
echo Starting PortalShare application...
python run.py

pause 