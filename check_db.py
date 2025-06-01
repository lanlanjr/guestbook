import sqlite3
import os

# Path to the SQLite database file
DB_PATH = os.path.join('instance', 'portalshare.db')

def check_schema():
    print(f"Connecting to database at {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return
        
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", [table[0] for table in tables])
    
    # Check event table schema
    try:
        cursor.execute("PRAGMA table_info(event)")
        columns = cursor.fetchall()
        if columns:
            print("\nEvent table schema:")
            for column in columns:
                print(f"  {column[1]} ({column[2]}){' PRIMARY KEY' if column[5] else ''}")
        else:
            print("\nEvent table exists but has no columns")
    except sqlite3.OperationalError as e:
        print(f"\nError checking event table: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_schema() 