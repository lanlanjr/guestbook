import sqlite3
import os

def migrate_database():
    # Database file path
    db_path = 'portalshare.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns exist before adding them
    cursor.execute("PRAGMA table_info(event)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add new columns if they don't exist
    columns_to_add = {
        'show_photos_in_gallery': 'BOOLEAN DEFAULT 1',
        'show_audio_in_gallery': 'BOOLEAN DEFAULT 1',
        'show_guestbook_in_gallery': 'BOOLEAN DEFAULT 1'
    }
    
    for column_name, column_type in columns_to_add.items():
        if column_name not in columns:
            print(f"Adding column {column_name} to event table...")
            cursor.execute(f"ALTER TABLE event ADD COLUMN {column_name} {column_type}")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database migration completed successfully.")

if __name__ == "__main__":
    migrate_database() 