#!/usr/bin/env python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import logging
import sqlite3
from sqlalchemy import text, inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('migrate')

# Create a minimal Flask app for migration
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

# Define the GuestAccess table creation SQL
GUEST_ACCESS_TABLE_SQL = '''
CREATE TABLE guest_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (event_id) REFERENCES event (id)
)
'''

def migrate_google_auth():
    """
    Updates the database schema to support Google authentication
    """
    try:
        logger.info(f"Starting Google OAuth migration...")
        
        # Check if the google_id column already exists
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('user')]
        
        # SQLite doesn't support adding UNIQUE constraint with ALTER TABLE
        # We need to use a different approach
        if 'google_id' not in columns:
            logger.info("Adding Google authentication columns to User table...")
            with db.engine.begin() as conn:
                # Add columns without UNIQUE constraint
                conn.execute(text('ALTER TABLE user ADD COLUMN google_id VARCHAR(120)'))
                conn.execute(text('ALTER TABLE user ADD COLUMN profile_pic VARCHAR(255)'))
                conn.execute(text('ALTER TABLE user ADD COLUMN is_guest BOOLEAN DEFAULT 0'))
                
                # Create a unique index instead of a UNIQUE constraint
                conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS idx_user_google_id ON user (google_id) WHERE google_id IS NOT NULL'))
            logger.info("User table updated successfully.")
        else:
            logger.info("Google authentication columns already exist in User table.")
            
            # Check if the unique index exists, create it if not
            indexes = inspector.get_indexes('user')
            has_google_id_index = any(idx['name'] == 'idx_user_google_id' for idx in indexes)
            
            if not has_google_id_index:
                logger.info("Creating unique index for google_id column...")
                with db.engine.begin() as conn:
                    conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS idx_user_google_id ON user (google_id) WHERE google_id IS NOT NULL'))
                logger.info("Index created successfully.")
        
        # Check if the GuestAccess table exists
        tables = inspector.get_table_names()
        if 'guest_access' not in tables:
            logger.info("Creating GuestAccess table...")
            # Use raw SQL to create the table
            with db.engine.begin() as conn:
                conn.execute(text(GUEST_ACCESS_TABLE_SQL))
            logger.info("GuestAccess table created successfully.")
        else:
            logger.info("GuestAccess table already exists.")
            
        logger.info("Google OAuth migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during Google OAuth migration: {e}")
        return False

def migrate_event_features():
    """
    Updates the database schema to add event features like image compression and themes
    """
    try:
        logger.info("Starting event features migration...")
        
        # Check if columns exist in Event table
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('event')]
        
        # Define columns to add with their default values
        columns_to_add = {
            'compress_images': 'BOOLEAN DEFAULT 0',
            'theme': 'VARCHAR(50) DEFAULT "default"',
            'gallery_enabled': 'BOOLEAN DEFAULT 1',
            'photo_upload_enabled': 'BOOLEAN DEFAULT 1',
            'audio_upload_enabled': 'BOOLEAN DEFAULT 1',
            'guestbook_enabled': 'BOOLEAN DEFAULT 1',
            'show_photos_in_gallery': 'BOOLEAN DEFAULT 1',
            'show_audio_in_gallery': 'BOOLEAN DEFAULT 1',
            'show_guestbook_in_gallery': 'BOOLEAN DEFAULT 1'
        }
        
        # Add columns if they don't exist
        for column_name, column_type in columns_to_add.items():
            if column_name not in columns:
                logger.info(f"Adding '{column_name}' column to Event table...")
                with db.engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE event ADD COLUMN {column_name} {column_type}"))
                logger.info(f"Added '{column_name}' column successfully.")
            else:
                logger.info(f"Column '{column_name}' already exists in Event table. Skipping.")
        
        logger.info("Event features migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during event features migration: {e}")
        return False

def run_migrations():
    """
    Run all migrations in the correct order
    """
    success = True
    
    # Run Google Auth migration
    if not migrate_google_auth():
        success = False
        logger.warning("Google Auth migration had issues.")
    
    # Run Event Features migration
    if not migrate_event_features():
        success = False
        logger.warning("Event Features migration had issues.")
    
    return success

if __name__ == "__main__":
    logger.info(f"Starting database migrations for {db_path}")
    
    # Check if the database file exists
    if os.path.exists(db_path):
        logger.info(f"Found database at {db_path}")
        # Check if we have read/write permissions
        try:
            with open(db_path, 'a'):
                pass
            logger.info("Database file is accessible with read/write permissions.")
        except IOError:
            logger.error(f"Cannot write to database file at {db_path}")
            logger.error("Please check file permissions.")
            sys.exit(1)
    else:
        logger.error(f"Database file not found at {db_path}")
        logger.error("Please run the application first to initialize the database.")
        sys.exit(1)
    
    # Run migrations within app context
    with app.app_context():
        if run_migrations():
            logger.info("All migrations completed successfully!")
        else:
            logger.warning("Some migrations had issues. Check the logs for details.")
            sys.exit(1) 