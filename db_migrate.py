import sqlite3
import os
import sys

# Path to the SQLite database file
DB_PATH = 'portalshare.db'

def migrate_database():
    print(f"Connecting to database at {DB_PATH}...")
    
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if compress_images column exists in Event table
        cursor.execute("PRAGMA table_info(event)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'compress_images' not in columns:
            print("Adding 'compress_images' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN compress_images BOOLEAN DEFAULT 0")
            conn.commit()
            print("Migration successful: Added 'compress_images' column to Event table")
        else:
            print("Column 'compress_images' already exists in Event table. Skipping.")
            
        # Check if theme column exists in Event table
        if 'theme' not in columns:
            print("Adding 'theme' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN theme VARCHAR(50) DEFAULT 'default'")
            conn.commit()
            print("Migration successful: Added 'theme' column to Event table")
        else:
            print("Column 'theme' already exists in Event table. Skipping.")
            
        # Check if gallery_enabled column exists in Event table
        if 'gallery_enabled' not in columns:
            print("Adding 'gallery_enabled' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN gallery_enabled BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added 'gallery_enabled' column to Event table")
        else:
            print("Column 'gallery_enabled' already exists in Event table. Skipping.")
            
        # Check if photo_upload_enabled column exists in Event table
        if 'photo_upload_enabled' not in columns:
            print("Adding 'photo_upload_enabled' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN photo_upload_enabled BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added 'photo_upload_enabled' column to Event table")
        else:
            print("Column 'photo_upload_enabled' already exists in Event table. Skipping.")
            
        # Check if audio_upload_enabled column exists in Event table
        if 'audio_upload_enabled' not in columns:
            print("Adding 'audio_upload_enabled' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN audio_upload_enabled BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added 'audio_upload_enabled' column to Event table")
        else:
            print("Column 'audio_upload_enabled' already exists in Event table. Skipping.")
            
        # Check if guestbook_enabled column exists in Event table
        if 'guestbook_enabled' not in columns:
            print("Adding 'guestbook_enabled' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN guestbook_enabled BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added 'guestbook_enabled' column to Event table")
        else:
            print("Column 'guestbook_enabled' already exists in Event table. Skipping.")
            
        # Check if show_photos_in_gallery column exists in Event table
        if 'show_photos_in_gallery' not in columns:
            print("Adding 'show_photos_in_gallery' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN show_photos_in_gallery BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added 'show_photos_in_gallery' column to Event table")
        else:
            print("Column 'show_photos_in_gallery' already exists in Event table. Skipping.")
            
        # Check if show_audio_in_gallery column exists in Event table
        if 'show_audio_in_gallery' not in columns:
            print("Adding 'show_audio_in_gallery' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN show_audio_in_gallery BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added 'show_audio_in_gallery' column to Event table")
        else:
            print("Column 'show_audio_in_gallery' already exists in Event table. Skipping.")
            
        # Check if show_guestbook_in_gallery column exists in Event table
        if 'show_guestbook_in_gallery' not in columns:
            print("Adding 'show_guestbook_in_gallery' column to Event table...")
            cursor.execute("ALTER TABLE event ADD COLUMN show_guestbook_in_gallery BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful: Added 'show_guestbook_in_gallery' column to Event table")
        else:
            print("Column 'show_guestbook_in_gallery' already exists in Event table. Skipping.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
        
    return True

if __name__ == "__main__":
    print("Starting database migration...")
    success = migrate_database()
    
    if success:
        print("Database migration completed successfully.")
    else:
        print("Database migration failed.")
        sys.exit(1) 