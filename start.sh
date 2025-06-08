#!/bin/bash
echo "Starting PortalShare Application..."

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if .env file exists, create from example if not
if [ ! -f ".env" ]; then
    echo "No .env file found, creating from example..."
    cp .env.example .env
    echo "Please edit the .env file with your Google OAuth credentials"
    read -p "Press Enter to continue..."
fi

# Initialize database if it doesn't exist
if [ ! -f "instance/portalshare.db" ]; then
    echo "Initializing database..."
    python init_db.py
fi

# Run database migrations
echo "Running database migrations..."
python migrate.py

# Start the application
echo "Starting application..."
python run.py 