#!/usr/bin/env python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys

# Create a minimal Flask app for initialization
app = Flask(__name__)

# Get the absolute path to the instance directory
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'portalshare.db')

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Import the models
from models import GuestbookEntry, Photo, AudioMessage

def check_migration():
    with app.app_context():
        # Check if the columns exist
        inspector = db.inspect(db.engine)
        
        has_user_id_photo = 'user_id' in [col['name'] for col in inspector.get_columns('photo')]
        has_user_id_guestbook = 'user_id' in [col['name'] for col in inspector.get_columns('guestbook_entry')]
        has_user_id_audio = 'user_id' in [col['name'] for col in inspector.get_columns('audio_message')]
        
        print("\n=== Migration Test Results ===")
        print(f"Photo user_id column exists: {has_user_id_photo}")
        print(f"GuestbookEntry user_id column exists: {has_user_id_guestbook}")
        print(f"AudioMessage user_id column exists: {has_user_id_audio}")
        
        # Check if there are any records without user_id
        photos_missing_user = Photo.query.filter_by(user_id=None).count()
        guestbook_missing_user = GuestbookEntry.query.filter_by(user_id=None).count()
        audio_missing_user = AudioMessage.query.filter_by(user_id=None).count()
        
        print("\n=== Content Without User ID ===")
        print(f"Photos without user_id: {photos_missing_user}")
        print(f"Guestbook entries without user_id: {guestbook_missing_user}")
        print(f"Audio messages without user_id: {audio_missing_user}")
        
        # Count total records
        total_photos = Photo.query.count()
        total_guestbook = GuestbookEntry.query.count()
        total_audio = AudioMessage.query.count()
        
        print("\n=== Total Content Counts ===")
        print(f"Total photos: {total_photos}")
        print(f"Total guestbook entries: {total_guestbook}")
        print(f"Total audio messages: {total_audio}")
        
        if not all([has_user_id_photo, has_user_id_guestbook, has_user_id_audio]):
            print("\n❌ Migration incomplete - some columns are missing")
        elif photos_missing_user > 0 or guestbook_missing_user > 0 or audio_missing_user > 0:
            print("\n⚠️ Migration partially complete - columns exist but some records have NULL user_id")
        else:
            print("\n✅ Migration successful - all columns exist and all records have user_id values")

if __name__ == "__main__":
    check_migration() 