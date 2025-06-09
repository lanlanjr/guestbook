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
logger = logging.getLogger('migration_add_user_id')

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

# Import the models with the new user_id field already added
from models import GuestbookEntry, Photo, AudioMessage, Event, User

def run_migration():
    try:
        with app.app_context():
            logger.info("Beginning migration to add user_id fields...")
            
            # Check if the columns exist
            inspector = db.inspect(db.engine)
            has_user_id_photo = 'user_id' in [col['name'] for col in inspector.get_columns('photo')]
            has_user_id_guestbook = 'user_id' in [col['name'] for col in inspector.get_columns('guestbook_entry')]
            has_user_id_audio = 'user_id' in [col['name'] for col in inspector.get_columns('audio_message')]
            
            if not (has_user_id_photo and has_user_id_guestbook and has_user_id_audio):
                logger.info("Adding columns to tables...")
                # Add the columns using raw SQL if they don't exist
                if not has_user_id_photo:
                    db.engine.execute('ALTER TABLE photo ADD COLUMN user_id INTEGER')
                if not has_user_id_guestbook:
                    db.engine.execute('ALTER TABLE guestbook_entry ADD COLUMN user_id INTEGER')
                if not has_user_id_audio:
                    db.engine.execute('ALTER TABLE audio_message ADD COLUMN user_id INTEGER')
                
                logger.info("Columns added successfully.")
            else:
                logger.info("Columns already exist. Skipping column creation.")
            
            # Display total counts
            photos_count = Photo.query.count()
            guestbook_count = GuestbookEntry.query.count()
            audio_count = AudioMessage.query.count()
            
            logger.info(f"Found {photos_count} photos, {guestbook_count} guestbook entries, and {audio_count} audio messages.")
            
            # Get all events and associated owners
            events = Event.query.all()
            
            for event in events:
                owner_id = event.user_id
                logger.info(f"Processing event ID {event.id} owned by user ID {owner_id}...")
                
                # Update all content for this event to belong to the event owner
                Photo.query.filter_by(event_id=event.id, user_id=None).update({
                    'user_id': owner_id
                })
                
                GuestbookEntry.query.filter_by(event_id=event.id, user_id=None).update({
                    'user_id': owner_id
                })
                
                AudioMessage.query.filter_by(event_id=event.id, user_id=None).update({
                    'user_id': owner_id
                })
            
            # Commit the changes
            db.session.commit()
            logger.info("Migration completed successfully.")
            
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
    logger.info("Migration script completed.") 