from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Event, GuestbookEntry, Photo, AudioMessage, GuestAccess
import os
import uuid
import qrcode
from io import BytesIO
import base64
from datetime import datetime
import mimetypes
import re
import json
from PIL import Image

def register_routes(app):
    # Allowed file extensions
    ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
    
    def allowed_photo_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS
    
    def allowed_audio_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS
    
    def save_file(file, folder, event_id=None):
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, unique_filename)
            
            # Check if we should compress the image
            if folder == 'photos' and event_id is not None:
                event = Event.query.get(event_id)
                if event and event.compress_images:
                    # Save to a temporary location
                    file.save(file_path)
                    
                    # Open and compress the image
                    try:
                        img = Image.open(file_path)
                        # Convert to RGB if needed (for PNG with transparency)
                        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                            img = background
                        
                        # Resize if larger than 1600px on any side
                        max_size = (1600, 1600)
                        if img.width > max_size[0] or img.height > max_size[1]:
                            img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # Save with reduced quality
                        img.save(file_path, optimize=True, quality=85)
                        return unique_filename
                    except Exception as e:
                        app.logger.error(f"Error compressing image: {e}")
                        # If compression fails, save the original file
                        file.seek(0)
                        file.save(file_path)
                        return unique_filename
            
            # If not a photo or compression not enabled, save normally
            file.save(file_path)
            return unique_filename
        return None

    def generate_qr_code(data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/register')
    def register():
        # Redirect to Google login instead of manual registration
        flash('Please sign in with your Google account to continue.', 'info')
        return redirect(url_for('login_google'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # For GET requests, show login page with Google sign-in option
        if request.method == 'GET':
            return render_template('login.html')
        
        # For POST requests (legacy login form)
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out successfully.', 'success')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        events = Event.query.filter_by(user_id=current_user.id).all()
        
        # Find the last viewed event for this user
        last_viewed_event = None
        last_access_time = None
        
        # Get the most recent guest access by this user
        latest_access = GuestAccess.query.filter_by(
            user_id=current_user.id
        ).order_by(GuestAccess.access_time.desc()).first()
        
        if latest_access:
            last_viewed_event = Event.query.get(latest_access.event_id)
            last_access_time = latest_access.access_time
            
            # For testing purposes, show the event even if it belongs to the current user
            # In production, you might want to uncomment the following code to hide own events
            '''
            # If the event belongs to this user, don't show it as "last viewed"
            if last_viewed_event and last_viewed_event.user_id == current_user.id:
                last_viewed_event = None
                last_access_time = None
                
                # Get the next most recent access that's not the user's own event
                guest_accesses = GuestAccess.query.filter_by(
                    user_id=current_user.id
                ).order_by(GuestAccess.access_time.desc()).all()
                
                for access in guest_accesses:
                    event = Event.query.get(access.event_id)
                    if event and event.user_id != current_user.id:
                        last_viewed_event = event
                        last_access_time = access.access_time
                        break
            '''
        
        # Debug information
        app.logger.info(f"User: {current_user.username}, Last viewed event: {last_viewed_event.name if last_viewed_event else 'None'}")
        
        return render_template('dashboard.html', events=events, last_viewed_event=last_viewed_event, last_access_time=last_access_time)
    
    @app.route('/event/create', methods=['GET', 'POST'])
    @login_required
    def create_event():
        if request.method == 'POST':
            name = request.form.get('name')
            date_str = request.form.get('date')
            description = request.form.get('description')
            location = request.form.get('location')
            
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format.', 'error')
                return redirect(url_for('create_event'))
            
            new_event = Event(
                name=name,
                date=date,
                description=description,
                location=location,
                user_id=current_user.id
            )
            
            db.session.add(new_event)
            db.session.commit()
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('create_event.html')
    
    @app.route('/event/<uuid:event_uuid>')
    @login_required
    def view_event(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to view this event.', 'error')
            return redirect(url_for('dashboard'))
        
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).order_by(GuestbookEntry.created_at.desc()).all()
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        audio_messages = AudioMessage.query.filter_by(event_id=event.id).order_by(AudioMessage.created_at.desc()).all()
        
        guestbook_url = url_for('guestbook', event_uuid=event.uuid, _external=True)
        photo_upload_url = url_for('upload_photo', event_uuid=event.uuid, _external=True)
        audio_message_url = url_for('record_audio', event_uuid=event.uuid, _external=True)
        
        guestbook_qr = generate_qr_code(guestbook_url)
        photo_upload_qr = generate_qr_code(photo_upload_url)
        audio_message_qr = generate_qr_code(audio_message_url)
        
        return render_template(
            'event.html', 
            event=event, 
            guestbook_entries=guestbook_entries,
            photos=photos,
            audio_messages=audio_messages,
            guestbook_qr=guestbook_qr,
            photo_upload_qr=photo_upload_qr,
            audio_message_qr=audio_message_qr,
            guestbook_url=guestbook_url,
            photo_upload_url=photo_upload_url,
            audio_message_url=audio_message_url
        )
    
    @app.route('/event/<uuid:event_uuid>/guestbook')
    def guestbook(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            # Redirect to Google login
            return redirect(url_for('guest_login', event_uuid=event_uuid))
        
        # Record guest access
        if current_user.is_guest:
            access = GuestAccess(
                user_id=current_user.id,
                event_id=event.id
            )
            db.session.add(access)
            db.session.commit()
        
        return render_template('guestbook.html', event=event)
    
    @app.route('/event/<uuid:event_uuid>/guestbook/submit', methods=['POST'])
    def submit_guestbook(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return redirect(url_for('guest_login', event_uuid=event_uuid))
        
        if request.method == 'POST':
            name = request.form.get('name') or current_user.username
            message = request.form.get('message')
            
            if not message:
                flash('Please provide a message.', 'warning')
                return redirect(url_for('guestbook', event_uuid=event_uuid))
            
            entry = GuestbookEntry(
                name=name,
                message=message,
                event_id=event.id
            )
            
            db.session.add(entry)
            db.session.commit()
            
            flash('Your message has been added to the guestbook!', 'success')
            return redirect(url_for('guestbook', event_uuid=event_uuid))
        
        return redirect(url_for('guestbook', event_uuid=event_uuid))
    
    @app.route('/event/<uuid:event_uuid>/upload-photo')
    def upload_photo(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return redirect(url_for('guest_login', event_uuid=event_uuid))
        
        # Record guest access
        if current_user.is_guest:
            access = GuestAccess(
                user_id=current_user.id,
                event_id=event.id
            )
            db.session.add(access)
            db.session.commit()
        
        return render_template('upload_photo.html', event=event)
    
    @app.route('/event/<uuid:event_uuid>/upload-photo/submit', methods=['POST'])
    def submit_photo(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return redirect(url_for('guest_login', event_uuid=event_uuid))
        
        if request.method == 'POST':
            guest_name = request.form.get('name') or current_user.username
            caption = request.form.get('caption')
            photo = request.files.get('photo')
            
            if not photo:
                flash('Please select a photo to upload.', 'warning')
                return redirect(url_for('upload_photo', event_uuid=event_uuid))
            
            if not allowed_photo_file(photo.filename):
                flash('Invalid file type. Please upload a JPG, PNG, or GIF image.', 'error')
                return redirect(url_for('upload_photo', event_uuid=event_uuid))
            
            filename = save_file(photo, 'photos', event.id)
            
            if filename:
                new_photo = Photo(
                    filename=filename,
                    original_filename=secure_filename(photo.filename),
                    guest_name=guest_name,
                    caption=caption,
                    event_id=event.id
                )
                
                db.session.add(new_photo)
                db.session.commit()
                
                flash('Your photo has been uploaded!', 'success')
                return redirect(url_for('upload_photo', event_uuid=event_uuid))
            
            flash('Error uploading photo. Please try again.', 'error')
            return redirect(url_for('upload_photo', event_uuid=event_uuid))
        
        return redirect(url_for('upload_photo', event_uuid=event_uuid))
    
    @app.route('/event/<uuid:event_uuid>/record-audio')
    def record_audio(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return redirect(url_for('guest_login', event_uuid=event_uuid))
        
        # Record guest access
        if current_user.is_guest:
            access = GuestAccess(
                user_id=current_user.id,
                event_id=event.id
            )
            db.session.add(access)
            db.session.commit()
        
        return render_template('record_audio.html', event=event)
    
    @app.route('/event/<uuid:event_uuid>/record-audio/submit', methods=['POST'])
    def submit_audio(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return redirect(url_for('guest_login', event_uuid=event_uuid))
        
        if request.method == 'POST':
            guest_name = request.form.get('name') or current_user.username
            audio_file = request.files.get('audio')
            duration = request.form.get('duration')
            
            if not audio_file:
                flash('Please provide an audio recording.', 'warning')
                return redirect(url_for('record_audio', event_uuid=event_uuid))
            
            if not allowed_audio_file(audio_file.filename):
                flash('Invalid file type. Please upload an MP3, WAV, or OGG audio file.', 'error')
                return redirect(url_for('record_audio', event_uuid=event_uuid))
            
            filename = save_file(audio_file, 'audio')
            
            if filename:
                new_audio = AudioMessage(
                    filename=filename,
                    guest_name=guest_name,
                    duration=duration,
                    event_id=event.id
                )
                
                db.session.add(new_audio)
                db.session.commit()
                
                flash('Your audio message has been uploaded!', 'success')
                return redirect(url_for('record_audio', event_uuid=event_uuid))
            
            flash('Error uploading audio. Please try again.', 'error')
            return redirect(url_for('record_audio', event_uuid=event_uuid))
        
        return redirect(url_for('record_audio', event_uuid=event_uuid))
    
    @app.route('/event/<uuid:event_uuid>/slideshow')
    def slideshow(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if gallery is enabled
        if not event.gallery_enabled:
            # Check if user is authenticated and is the event owner
            if not current_user.is_authenticated or event.user_id != current_user.id:
                flash('This slideshow is currently disabled by the event creator.', 'info')
                return redirect(url_for('upload_photo', event_uuid=event.uuid))
                
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        
        # Generate QR code for photo uploads
        photo_upload_url = url_for('upload_photo', event_uuid=event.uuid, _external=True)
        photo_upload_qr = generate_qr_code(photo_upload_url)
        
        return render_template('slideshow.html', event=event, photos=photos, photo_upload_qr=photo_upload_qr)
    
    @app.route('/uploads/<folder>/<filename>')
    def uploaded_file(folder, filename):
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), filename)
    
    # New routes for content management
    @app.route('/event/<uuid:event_uuid>/manage')
    @login_required
    def manage_content(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to manage this event.', 'error')
            return redirect(url_for('dashboard'))
        
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).order_by(GuestbookEntry.created_at.desc()).all()
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        audio_messages = AudioMessage.query.filter_by(event_id=event.id).order_by(AudioMessage.created_at.desc()).all()
        
        # Get today's date for date picker
        today_date = datetime.today().strftime('%Y-%m-%d')
        
        return render_template(
            'manage_content.html', 
            event=event, 
            guestbook_entries=guestbook_entries,
            photos=photos,
            audio_messages=audio_messages,
            today_date=today_date
        )
    
    @app.route('/event/<uuid:event_uuid>/delete/message/<int:message_id>', methods=['POST'])
    @login_required
    def delete_message(event_uuid, message_id):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to delete content from this event.', 'error')
            return redirect(url_for('dashboard'))
        
        message = GuestbookEntry.query.filter_by(id=message_id, event_id=event.id).first_or_404()
        
        db.session.delete(message)
        db.session.commit()
        
        flash('Message deleted successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
    
    @app.route('/event/<uuid:event_uuid>/delete/photo/<int:photo_id>', methods=['POST'])
    @login_required
    def delete_photo(event_uuid, photo_id):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to delete content from this event.', 'error')
            return redirect(url_for('dashboard'))
        
        photo = Photo.query.filter_by(id=photo_id, event_id=event.id).first_or_404()
        
        # Delete the file from the filesystem
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo.filename))
        except Exception as e:
            app.logger.error(f"Error deleting photo file: {e}")
        
        db.session.delete(photo)
        db.session.commit()
        
        flash('Photo deleted successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
    
    @app.route('/event/<uuid:event_uuid>/delete/audio/<int:audio_id>', methods=['POST'])
    @login_required
    def delete_audio(event_uuid, audio_id):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to delete content from this event.', 'error')
            return redirect(url_for('dashboard'))
        
        audio = AudioMessage.query.filter_by(id=audio_id, event_id=event.id).first_or_404()
        
        # Delete the file from the filesystem
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio.filename))
        except Exception as e:
            app.logger.error(f"Error deleting audio file: {e}")
        
        db.session.delete(audio)
        db.session.commit()
        
        flash('Audio message deleted successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
    
    @app.route('/api/event/<uuid:event_uuid>/photos')
    def api_photos(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        
        result = []
        for photo in photos:
            result.append({
                'id': photo.id,
                'url': url_for('uploaded_file', folder='photos', filename=photo.filename),
                'guest_name': photo.guest_name,
                'caption': photo.caption,
                'created_at': photo.created_at.isoformat()
            })
        
        return jsonify(result)
    
    @app.route('/api/event/<uuid:event_uuid>/guestbook')
    def api_guestbook(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        entries = GuestbookEntry.query.filter_by(event_id=event.id).order_by(GuestbookEntry.created_at.desc()).all()
        
        result = []
        for entry in entries:
            result.append({
                'id': entry.id,
                'name': entry.name,
                'message': entry.message,
                'created_at': entry.created_at.isoformat()
            })
        
        return jsonify(result)
    
    @app.route('/api/event/<uuid:event_uuid>/audio')
    def api_audio(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        messages = AudioMessage.query.filter_by(event_id=event.id).order_by(AudioMessage.created_at.desc()).all()
        
        result = []
        for message in messages:
            result.append({
                'id': message.id,
                'url': url_for('uploaded_file', folder='audio', filename=message.filename),
                'guest_name': message.guest_name,
                'duration': message.duration,
                'created_at': message.created_at.isoformat()
            })
        
        return jsonify(result)
    
    @app.route('/event/<uuid:event_uuid>/gallery')
    def event_gallery(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if gallery is enabled
        if not event.gallery_enabled:
            # Check if user is authenticated and is the event owner
            if not current_user.is_authenticated or event.user_id != current_user.id:
                flash('This gallery is currently disabled by the event creator.', 'info')
                return redirect(url_for('guestbook', event_uuid=event.uuid))
        
        # Record guest access if user is authenticated
        if current_user.is_authenticated:
            # Only record access if the user is not the event owner
            if event.user_id != current_user.id:
                access = GuestAccess(
                    user_id=current_user.id,
                    event_id=event.id
                )
                db.session.add(access)
                db.session.commit()
                
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).order_by(GuestbookEntry.created_at.desc()).all()
        audio_messages = AudioMessage.query.filter_by(event_id=event.id).order_by(AudioMessage.created_at.desc()).all()
        
        # Generate QR codes for different features
        guestbook_url = url_for('guestbook', event_uuid=event.uuid, _external=True)
        photo_upload_url = url_for('upload_photo', event_uuid=event.uuid, _external=True)
        audio_message_url = url_for('record_audio', event_uuid=event.uuid, _external=True)
        
        guestbook_qr = generate_qr_code(guestbook_url)
        photo_upload_qr = generate_qr_code(photo_upload_url)
        audio_message_qr = generate_qr_code(audio_message_url)
        
        # Prepare photos data for the modal
        photos_json = []
        for photo in photos:
            photos_json.append({
                'id': photo.id,
                'url': url_for('uploaded_file', folder='photos', filename=photo.filename),
                'caption': photo.caption or '',
                'guest_name': photo.guest_name or 'Anonymous',
                'timestamp': photo.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        # Prepare audio messages data for the modal
        audio_messages_json = []
        for message in audio_messages:
            audio_messages_json.append({
                'id': message.id,
                'url': url_for('uploaded_file', folder='audio', filename=message.filename),
                'guest_name': message.guest_name or 'Anonymous',
                'timestamp': message.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        # Prepare guestbook entries data for the modal
        guestbook_entries_json = []
        for entry in guestbook_entries:
            guestbook_entries_json.append({
                'id': entry.id,
                'message': entry.message,
                'name': entry.name or 'Anonymous',
                'timestamp': entry.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        return render_template(
            'event_gallery.html', 
            event=event, 
            photos=photos,
            guestbook_entries=guestbook_entries,
            audio_messages=audio_messages,
            guestbook_qr=guestbook_qr,
            photo_upload_qr=photo_upload_qr,
            audio_message_qr=audio_message_qr,
            show_photos=event.show_photos_in_gallery,
            show_audio=event.show_audio_in_gallery,
            show_guestbook=event.show_guestbook_in_gallery,
            photos_json=json.dumps(photos_json),
            audio_messages_json=json.dumps(audio_messages_json),
            guestbook_entries_json=json.dumps(guestbook_entries_json)
        )
    
    @app.route('/event/<uuid:event_uuid>/gallery/slideshow')
    def guest_slideshow(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if gallery is enabled
        if not event.gallery_enabled:
            # Check if user is authenticated and is the event owner
            if not current_user.is_authenticated or event.user_id != current_user.id:
                flash('This slideshow is currently disabled by the event creator.', 'info')
                return redirect(url_for('guestbook', event_uuid=event.uuid))
                
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        
        return render_template('guest_slideshow.html', event=event, photos=photos)
    
    # New route for updating event settings
    @app.route('/event/<uuid:event_uuid>/update-settings', methods=['POST'])
    @login_required
    def update_event_settings(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to update this event.', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            # Update event settings
            event.gallery_enabled = 'gallery_enabled' in request.form
            event.photo_upload_enabled = 'photo_upload_enabled' in request.form
            event.audio_upload_enabled = 'audio_upload_enabled' in request.form
            event.guestbook_enabled = 'guestbook_enabled' in request.form
            event.compress_images = 'compress_images' in request.form
            event.theme = request.form.get('theme', 'default')
            
            # Update gallery visibility settings
            event.show_photos_in_gallery = 'show_photos_in_gallery' in request.form
            event.show_audio_in_gallery = 'show_audio_in_gallery' in request.form
            event.show_guestbook_in_gallery = 'show_guestbook_in_gallery' in request.form
            
            db.session.commit()
            
            flash('Event settings updated successfully.', 'success')
            return redirect(url_for('manage_content', event_uuid=event.uuid))
    
    # New routes for resetting content
    @app.route('/event/<uuid:event_uuid>/reset/all', methods=['POST'])
    @login_required
    def reset_all_content(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.', 'error')
            return redirect(url_for('dashboard'))
        
        # Delete all photos, audio messages, and guestbook entries
        photos = Photo.query.filter_by(event_id=event.id).all()
        audio_messages = AudioMessage.query.filter_by(event_id=event.id).all()
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).all()
        
        # Delete photo files
        for photo in photos:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting photo file: {e}")
        
        # Delete audio files
        for audio in audio_messages:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting audio file: {e}")
        
        # Delete database records
        for photo in photos:
            db.session.delete(photo)
        
        for audio in audio_messages:
            db.session.delete(audio)
        
        for entry in guestbook_entries:
            db.session.delete(entry)
        
        db.session.commit()
        
        flash('All content has been reset successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    @app.route('/event/<uuid:event_uuid>/reset/photos', methods=['POST'])
    @login_required
    def reset_photos(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.', 'error')
            return redirect(url_for('dashboard'))
            
        # Delete all photos
        photos = Photo.query.filter_by(event_id=event.id).all()
        for photo in photos:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting file: {e}")
            db.session.delete(photo)
            
        db.session.commit()
        
        flash('All photos have been reset successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    @app.route('/event/<uuid:event_uuid>/reset/audio', methods=['POST'])
    @login_required
    def reset_audio(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.', 'error')
            return redirect(url_for('dashboard'))
            
        # Delete all audio messages
        audio_messages = AudioMessage.query.filter_by(event_id=event.id).all()
        for audio in audio_messages:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting file: {e}")
            db.session.delete(audio)
            
        db.session.commit()
        
        flash('All audio messages have been reset successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    @app.route('/event/<uuid:event_uuid>/reset/messages', methods=['POST'])
    @login_required
    def reset_messages(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.', 'error')
            return redirect(url_for('dashboard'))
            
        # Delete all guestbook entries
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).all()
        for entry in guestbook_entries:
            db.session.delete(entry)
            
        db.session.commit()
        
        flash('All guestbook messages have been reset successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    # New route for updating event details
    @app.route('/event/<uuid:event_uuid>/update-details', methods=['POST'])
    @login_required
    def update_event_details(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to update this event.', 'error')
            return redirect(url_for('dashboard'))
        
        # Update event details
        event.name = request.form.get('name')
        date_str = request.form.get('date')
        event.location = request.form.get('location')
        event.description = request.form.get('description')
        
        try:
            new_date = datetime.strptime(date_str, '%Y-%m-%d')
            # Check if the date is in the past and not the same as the current event date
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            current_event_date = event.date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if new_date < today and new_date != current_event_date:
                flash('Please select today or a future date for your event.', 'error')
                return redirect(url_for('manage_content', event_uuid=event.uuid, _anchor='event-details-content'))
                
            event.date = new_date
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('manage_content', event_uuid=event.uuid, _anchor='event-details-content'))
        
        db.session.commit()
        
        flash('Event details updated successfully.', 'success')
        return redirect(url_for('manage_content', event_uuid=event.uuid, _anchor='event-details-content'))
    
    # Route for deleting an event
    @app.route('/event/<uuid:event_uuid>/delete', methods=['POST'])
    @login_required
    def delete_event(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if the current user is the owner of the event
        if event.user_id != current_user.id:
            flash('You do not have permission to delete this event.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get all content associated with this event
        photos = Photo.query.filter_by(event_id=event.id).all()
        audio_messages = AudioMessage.query.filter_by(event_id=event.id).all()
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).all()
        guest_accesses = GuestAccess.query.filter_by(event_id=event.id).all()
        
        # Delete photo files
        for photo in photos:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting photo file: {e}")
        
        # Delete audio files
        for audio in audio_messages:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting audio file: {e}")
        
        # Delete all database records
        for photo in photos:
            db.session.delete(photo)
        
        for audio in audio_messages:
            db.session.delete(audio)
        
        for entry in guestbook_entries:
            db.session.delete(entry)
            
        for access in guest_accesses:
            db.session.delete(access)
        
        # Delete the event itself
        event_name = event.name  # Store name for flash message
        db.session.delete(event)
        db.session.commit()
        
        flash(f'Event "{event_name}" has been permanently deleted.', 'success')
        return redirect(url_for('dashboard')) 