from app import app, db
from models import GuestAccess, User, Event
from flask_login import current_user

# Run this script with: python check_guest_access.py

with app.app_context():
    # Check total number of GuestAccess records
    total_records = GuestAccess.query.count()
    print(f"Total GuestAccess records: {total_records}")
    
    # List all GuestAccess records
    if total_records > 0:
        print("\nGuestAccess Records:")
        print("--------------------")
        for access in GuestAccess.query.all():
            user = User.query.get(access.user_id)
            event = Event.query.get(access.event_id)
            print(f"ID: {access.id}")
            print(f"User: {user.username if user else 'Unknown'} (ID: {access.user_id})")
            print(f"Event: {event.name if event else 'Unknown'} (ID: {access.event_id})")
            print(f"Access Time: {access.access_time}")
            print("--------------------")
    else:
        print("\nNo GuestAccess records found.")
        
    # Check if there are any users who have accessed events
    users_with_access = db.session.query(GuestAccess.user_id).distinct().count()
    print(f"\nUsers who have accessed events: {users_with_access}")
    
    # Check if there are any events that have been accessed
    events_accessed = db.session.query(GuestAccess.event_id).distinct().count()
    print(f"Events that have been accessed: {events_accessed}") 