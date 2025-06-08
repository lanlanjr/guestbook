# PortalShare - Digital Event Guestbook

PortalShare is a Flask-based web application that provides a modern digital guestbook solution for events. It allows guests to leave text messages, upload photos, and record audio messages, all accessible through QR codes. The application includes Google OAuth authentication for secure guest access.

## Features

- **Digital Guestbook**: Collect text messages from guests
- **Photo Sharing**: Allow guests to upload photos to a shared gallery
- **Audio Messages**: Record voice messages from guests
- **Live Slideshow**: Display photos in real-time during the event
- **QR Code Integration**: Easy access for guests via QR codes
- **User Authentication**: Secure access to event management
- **Google Authentication**: Guests sign in with Google to contribute content
- **Content Moderation**: Ability to review and delete inappropriate content

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/portalshare.git
cd portalshare
```

2. Create a virtual environment and activate it:
```
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env` and update the values
   - For Google OAuth, you need to set up a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth credentials and set the redirect URI to `http://localhost:5000/login/google/authorize` for development

```
# .env file example
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SERVER_NAME=http://localhost:5000
```

5. Initialize the database:
```
python init_db.py
```

6. Run the database migrations:
```
python migrate.py
```

## Running the Application

1. Start the application:
```
python run.py
```

2. Access the application at `http://localhost:5000`

3. For convenience, you can also use the provided start scripts:
```
# On Windows
start.bat

# On macOS/Linux
./start.sh
```

## Google OAuth Configuration

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Select "Web application" as the application type
6. Add the following Authorized redirect URIs:
   - For development: `http://localhost:5000/login/google/authorize`
   - For production: `https://yourdomain.com/login/google/authorize`
7. Click "Create" and note your Client ID and Client Secret
8. Add these credentials to your `.env` file

## Project Structure

- `app.py`: Main application file
- `models.py`: Database models
- `routes.py`: Application routes
- `oauth.py`: Google OAuth implementation
- `google_auth.py`: Google authentication utilities
- `run.py`: Application entry point
- `init_db.py`: Database initialization script
- `migrate.py`: Unified database migration script
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, uploads)

## Usage

1. Register an account as an event organizer
2. Create a new event
3. Share the generated QR codes with your guests
4. Guests will be prompted to sign in with Google when they scan the QR codes
5. After signing in, guests can:
   - Leave messages in the guestbook
   - Upload photos to the gallery
   - Record audio messages
6. Display the live slideshow during your event
7. Review and moderate content through the "Manage Content" page

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in your environment
2. Use a production WSGI server like Gunicorn:
   ```
   gunicorn "app:app" --bind=0.0.0.0:5000
   ```
3. Set up proper SSL/TLS for secure connections
4. Update the `SERVER_NAME` in your `.env` file to your production domain
5. Add your production domain to the authorized redirect URIs in Google Cloud Console

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Icons by Font Awesome
- Bootstrap for the responsive design
- All the users who make memories with PortalShare 