#!/usr/bin/env python
from app import app, init_db
import os

if __name__ == '__main__':
    # Ensure instance directory exists
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"Created instance directory at {instance_path}")
    
    # Initialize the database
    init_db()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000) 

    