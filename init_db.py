#!/usr/bin/env python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('init_db')

# Create a minimal Flask app for initialization
app = Flask(__name__)

# Get the absolute path to the instance directory
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'portalshare.db')

# Ensure instance directory exists
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
    logger.info(f"Created instance directory at {instance_path}")

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define minimal models required for initial database setup
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)
    is_guest = db.Column(db.Boolean, default=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class GuestbookEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    guest_name = db.Column(db.String(100))
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

class AudioMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

class GuestAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    access_time = db.Column(db.DateTime, default=db.func.current_timestamp())

def init_database():
    """
    Initializes the database with the required tables
    """
    try:
        logger.info(f"Initializing database at: {db_path}")
        
        # Check if database already exists
        if os.path.exists(db_path):
            logger.warning(f"Database already exists at {db_path}")
            response = input("Do you want to reinitialize the database? This will erase all data. (y/N): ")
            if response.lower() != 'y':
                logger.info("Database initialization cancelled.")
                return
            
        # Create all tables
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully!")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info(f"Starting database initialization for {db_path}")
    init_database() 