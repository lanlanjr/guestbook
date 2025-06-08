from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os
from datetime import datetime
import uuid
import qrcode
from io import BytesIO
import base64
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import tempfile
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'development' else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger('app')

# Load environment variables
load_dotenv()

# Import db and models
from models import db, User, Event, GuestbookEntry, Photo, AudioMessage

# Import OAuth and Google Auth
from oauth import init_oauth
from google_auth import CLIENT_CONFIG

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Database configuration
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
temp_dir = tempfile.gettempdir()

# Try to use instance directory first, fall back to temp directory if needed
try:
    os.makedirs(instance_path, exist_ok=True)
    test_file = os.path.join(instance_path, 'test_write.tmp')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    db_dir = instance_path
except Exception as e:
    logger.warning(f"Instance directory is not writable, using temp directory: {str(e)}")
    db_dir = temp_dir

# Set database path using absolute path
db_path = os.path.join(db_dir, "portalshare.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload configuration
uploads_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['UPLOAD_FOLDER'] = uploads_path
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Google OAuth configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', CLIENT_CONFIG["web"]["client_id"])
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', CLIENT_CONFIG["web"]["client_secret"])
app.config['CLIENT_CONFIG'] = CLIENT_CONFIG

# Ensure upload directory exists
try:
    os.makedirs(uploads_path, exist_ok=True)
    os.makedirs(os.path.join(uploads_path, 'photos'), exist_ok=True)
    os.makedirs(os.path.join(uploads_path, 'audio'), exist_ok=True)
except Exception as e:
    logger.error(f"Error creating upload directories: {str(e)}")
    raise

# Initialize extensions with app
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize OAuth
init_oauth(app)

# Context processor to make variables available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Import routes after models
from routes import register_routes
register_routes(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

if __name__ == '__main__':
    # Initialize database before running the app
    init_db()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development') 