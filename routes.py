from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, Event, GuestbookEntry, Photo, AudioMessage
from app import db
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
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            if user:
                flash('Username already exists.')
                return redirect(url_for('register'))
            
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email already registered.')
                return redirect(url_for('register'))
            
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                flash('Please check your login details and try again.')
                return redirect(url_for('login'))
            
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        events = Event.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', events=events)
    
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
                flash('Invalid date format.')
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
            
            flash('Event created successfully!')
            return redirect(url_for('dashboard'))
        
        return render_template('create_event.html')
    
    @app.route('/event/<uuid:event_uuid>')
    @login_required
    def view_event(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to view this event.')
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
        
        # Check if guestbook is enabled
        if not event.guestbook_enabled and (not current_user.is_authenticated or event.user_id != current_user.id):
            flash('The guestbook is currently disabled by the event creator.')
            return redirect(url_for('index'))
        
        return render_template('guestbook.html', event=event)
    
    @app.route('/event/<uuid:event_uuid>/guestbook/submit', methods=['POST'])
    def submit_guestbook(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if guestbook is enabled
        if not event.guestbook_enabled and (not current_user.is_authenticated or event.user_id != current_user.id):
            flash('The guestbook is currently disabled by the event creator.')
            return redirect(url_for('index'))
        
        name = request.form.get('name')
        message = request.form.get('message')
        
        if not name or not message:
            flash('Please fill out all fields.')
            return redirect(url_for('guestbook', event_uuid=event.uuid))
        
        entry = GuestbookEntry(
            name=name,
            message=message,
            event_id=event.id
        )
        
        db.session.add(entry)
        db.session.commit()
        
        flash('Thank you for your message!')
        return redirect(url_for('guestbook', event_uuid=event.uuid))
    
    @app.route('/event/<uuid:event_uuid>/upload-photo')
    def upload_photo(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if photo uploads are enabled
        if not event.photo_upload_enabled and (not current_user.is_authenticated or event.user_id != current_user.id):
            flash('Photo uploads are currently disabled by the event creator.')
            return redirect(url_for('index'))
        
        return render_template('upload_photo.html', event=event)
    
    @app.route('/event/<uuid:event_uuid>/upload-photo/submit', methods=['POST'])
    def submit_photo(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if photo uploads are enabled
        if not event.photo_upload_enabled and (not current_user.is_authenticated or event.user_id != current_user.id):
            flash('Photo uploads are currently disabled by the event creator.')
            return redirect(url_for('index'))
        
        if 'photo' not in request.files:
            flash('No photo selected.')
            return redirect(url_for('upload_photo', event_uuid=event.uuid))
        
        photo = request.files['photo']
        guest_name = request.form.get('name', 'Anonymous')
        caption = request.form.get('caption', '')
        
        if photo.filename == '':
            flash('No photo selected.')
            return redirect(url_for('upload_photo', event_uuid=event.uuid))
        
        if not allowed_photo_file(photo.filename):
            flash('Invalid file type. Please upload a JPG, PNG, or GIF file.')
            return redirect(url_for('upload_photo', event_uuid=event.uuid))
        
        filename = save_file(photo, 'photos', event_id=event.id)
        
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
            
            flash('Photo uploaded successfully!')
        else:
            flash('Error saving photo.')
        
        return redirect(url_for('upload_photo', event_uuid=event.uuid))
    
    @app.route('/event/<uuid:event_uuid>/record-audio')
    def record_audio(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if audio messages are enabled
        if not event.audio_upload_enabled and (not current_user.is_authenticated or event.user_id != current_user.id):
            flash('Audio messages are currently disabled by the event creator.')
            return redirect(url_for('index'))
        
        return render_template('record_audio.html', event=event)
    
    @app.route('/event/<uuid:event_uuid>/record-audio/submit', methods=['POST'])
    def submit_audio(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if audio messages are enabled
        if not event.audio_upload_enabled and (not current_user.is_authenticated or event.user_id != current_user.id):
            flash('Audio messages are currently disabled by the event creator.')
            return redirect(url_for('index'))
        
        if 'audio' not in request.files:
            flash('No audio file selected.')
            return redirect(url_for('record_audio', event_uuid=event.uuid))
        
        audio = request.files['audio']
        guest_name = request.form.get('name', 'Anonymous')
        duration = request.form.get('duration', 0)
        
        if audio.filename == '':
            flash('No audio file selected.')
            return redirect(url_for('record_audio', event_uuid=event.uuid))
        
        if not allowed_audio_file(audio.filename):
            flash('Invalid file type. Please upload an MP3, WAV, OGG, or M4A file.')
            return redirect(url_for('record_audio', event_uuid=event.uuid))
        
        filename = save_file(audio, 'audio')
        
        if filename:
            new_audio = AudioMessage(
                filename=filename,
                guest_name=guest_name,
                duration=duration,
                event_id=event.id
            )
            
            db.session.add(new_audio)
            db.session.commit()
            
            flash('Audio message recorded successfully!')
        else:
            flash('Error saving audio message.')
        
        return redirect(url_for('record_audio', event_uuid=event.uuid))
    
    @app.route('/event/<uuid:event_uuid>/slideshow')
    def slideshow(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if gallery is enabled
        if not event.gallery_enabled:
            # Check if user is authenticated and is the event owner
            if not current_user.is_authenticated or event.user_id != current_user.id:
                flash('This slideshow is currently disabled by the event creator.')
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
            flash('You do not have permission to manage this event.')
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
            flash('You do not have permission to delete content from this event.')
            return redirect(url_for('dashboard'))
        
        message = GuestbookEntry.query.filter_by(id=message_id, event_id=event.id).first_or_404()
        
        db.session.delete(message)
        db.session.commit()
        
        flash('Message deleted successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
    
    @app.route('/event/<uuid:event_uuid>/delete/photo/<int:photo_id>', methods=['POST'])
    @login_required
    def delete_photo(event_uuid, photo_id):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to delete content from this event.')
            return redirect(url_for('dashboard'))
        
        photo = Photo.query.filter_by(id=photo_id, event_id=event.id).first_or_404()
        
        # Delete the file from the filesystem
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            app.logger.error(f"Error deleting file: {e}")
        
        db.session.delete(photo)
        db.session.commit()
        
        flash('Photo deleted successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
    
    @app.route('/event/<uuid:event_uuid>/delete/audio/<int:audio_id>', methods=['POST'])
    @login_required
    def delete_audio(event_uuid, audio_id):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to delete content from this event.')
            return redirect(url_for('dashboard'))
        
        audio = AudioMessage.query.filter_by(id=audio_id, event_id=event.id).first_or_404()
        
        # Delete the file from the filesystem
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            app.logger.error(f"Error deleting file: {e}")
        
        db.session.delete(audio)
        db.session.commit()
        
        flash('Audio message deleted successfully.')
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
                flash('This gallery is currently disabled by the event creator.')
                return redirect(url_for('upload_photo', event_uuid=event.uuid))
        
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        audio_messages = AudioMessage.query.filter_by(event_id=event.id).order_by(AudioMessage.created_at.desc()).all()
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).order_by(GuestbookEntry.created_at.desc()).all()
        
        # Prepare JSON data for photos
        photos_data = []
        for photo in photos:
            photos_data.append({
                'url': url_for('uploaded_file', folder='photos', filename=photo.filename, _external=True),
                'guest_name': photo.guest_name or 'Anonymous',
                'caption': photo.caption or '',
                'timestamp': photo.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        photos_json = json.dumps(photos_data)
        
        return render_template(
            'event_gallery.html',
            event=event,
            photos=photos,
            photos_json=photos_json,
            audio_messages=audio_messages,
            guestbook_entries=guestbook_entries
        )
    
    @app.route('/event/<uuid:event_uuid>/gallery/slideshow')
    def guest_slideshow(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        # Check if gallery is enabled and photos are enabled in gallery
        if not event.gallery_enabled or not event.show_photos_in_gallery:
            # Check if user is authenticated and is the event owner
            if not current_user.is_authenticated or event.user_id != current_user.id:
                flash('This slideshow is currently disabled by the event creator.')
                return redirect(url_for('event_gallery', event_uuid=event.uuid))
        
        photos = Photo.query.filter_by(event_id=event.id).order_by(Photo.created_at.desc()).all()
        
        # Generate QR code for photo uploads
        photo_upload_url = url_for('upload_photo', event_uuid=event.uuid, _external=True)
        photo_upload_qr = generate_qr_code(photo_upload_url)
        
        return render_template('guest_slideshow.html', event=event, photos=photos, photo_upload_qr=photo_upload_qr)
    
    # New route for updating event settings
    @app.route('/event/<uuid:event_uuid>/update-settings', methods=['POST'])
    @login_required
    def update_event_settings(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to update this event.')
            return redirect(url_for('dashboard'))
        
        # Update gallery and feature settings
        event.gallery_enabled = 'gallery_enabled' in request.form
        event.photo_upload_enabled = 'photo_upload_enabled' in request.form
        event.audio_upload_enabled = 'audio_upload_enabled' in request.form
        event.guestbook_enabled = 'guestbook_enabled' in request.form
        event.compress_images = 'compress_images' in request.form
        
        # Update gallery visibility settings
        event.show_photos_in_gallery = 'show_photos_in_gallery' in request.form
        event.show_audio_in_gallery = 'show_audio_in_gallery' in request.form
        event.show_guestbook_in_gallery = 'show_guestbook_in_gallery' in request.form
        
        # Update theme if provided
        if 'theme' in request.form:
            event.theme = request.form.get('theme')
        
        db.session.commit()
        
        flash('Event settings updated successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
    
    # New routes for resetting content
    @app.route('/event/<uuid:event_uuid>/reset/all', methods=['POST'])
    @login_required
    def reset_all_content(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.')
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
            
        # Delete all guestbook entries
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).all()
        for entry in guestbook_entries:
            db.session.delete(entry)
            
        db.session.commit()
        
        flash('All content has been reset successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    @app.route('/event/<uuid:event_uuid>/reset/photos', methods=['POST'])
    @login_required
    def reset_photos(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.')
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
        
        flash('All photos have been reset successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    @app.route('/event/<uuid:event_uuid>/reset/audio', methods=['POST'])
    @login_required
    def reset_audio(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.')
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
        
        flash('All audio messages have been reset successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    @app.route('/event/<uuid:event_uuid>/reset/messages', methods=['POST'])
    @login_required
    def reset_messages(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to reset content for this event.')
            return redirect(url_for('dashboard'))
            
        # Delete all guestbook entries
        guestbook_entries = GuestbookEntry.query.filter_by(event_id=event.id).all()
        for entry in guestbook_entries:
            db.session.delete(entry)
            
        db.session.commit()
        
        flash('All guestbook messages have been reset successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid))
        
    # New route for updating event details
    @app.route('/event/<uuid:event_uuid>/update-details', methods=['POST'])
    @login_required
    def update_event_details(event_uuid):
        event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
        
        if event.user_id != current_user.id:
            flash('You do not have permission to update this event.')
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
                flash('Please select today or a future date for your event.')
                return redirect(url_for('manage_content', event_uuid=event.uuid, _anchor='event-details-content'))
                
            event.date = new_date
        except ValueError:
            flash('Invalid date format.')
            return redirect(url_for('manage_content', event_uuid=event.uuid, _anchor='event-details-content'))
        
        db.session.commit()
        
        flash('Event details updated successfully.')
        return redirect(url_for('manage_content', event_uuid=event.uuid, _anchor='event-details-content')) 