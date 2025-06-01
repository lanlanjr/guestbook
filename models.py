from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

# Create db instance without binding to app yet
db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    events = db.relationship('Event', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entries = db.relationship('GuestbookEntry', backref='event', lazy=True, cascade='all, delete-orphan')
    photos = db.relationship('Photo', backref='event', lazy=True, cascade='all, delete-orphan')
    audio_messages = db.relationship('AudioMessage', backref='event', lazy=True, cascade='all, delete-orphan')
    
    # Control settings
    gallery_enabled = db.Column(db.Boolean, default=True)
    photo_upload_enabled = db.Column(db.Boolean, default=True)
    audio_upload_enabled = db.Column(db.Boolean, default=True)
    guestbook_enabled = db.Column(db.Boolean, default=True)
    compress_images = db.Column(db.Boolean, default=False)
    theme = db.Column(db.String(50), default='default')
    
    # Gallery visibility settings
    show_photos_in_gallery = db.Column(db.Boolean, default=True)
    show_audio_in_gallery = db.Column(db.Boolean, default=True)
    show_guestbook_in_gallery = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Event {self.name}>'

class GuestbookEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def __repr__(self):
        return f'<GuestbookEntry {self.name}>'

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    guest_name = db.Column(db.String(100))
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def __repr__(self):
        return f'<Photo {self.filename}>'

class AudioMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    guest_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer)  # Duration in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def __repr__(self):
        return f'<AudioMessage {self.filename}>' 