# PortalShare - Digital Wedding Guestbook

PortalShare is a Flask-based web application that provides a modern digital guestbook solution for weddings and events. It allows guests to leave text messages, upload photos, and record audio messages, all accessible through QR codes.

## Features

- **Digital Guestbook**: Collect text messages from guests
- **Photo Sharing**: Allow guests to upload photos to a shared gallery
- **Audio Messages**: Record voice messages from guests
- **Live Slideshow**: Display photos in real-time during the event
- **QR Code Integration**: Easy access for guests via QR codes
- **User Authentication**: Secure access to event management
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

4. Set up environment variables (optional):
```
# On Windows
set SECRET_KEY=your_secret_key
set DATABASE_URL=your_database_url

# On macOS/Linux
export SECRET_KEY=your_secret_key
export DATABASE_URL=your_database_url
```

## Running the Application

1. Initialize the database:
```
python app.py
```

2. Run the development server:
```
flask run
```

3. Access the application at `http://localhost:5000`

## Project Structure

- `app.py`: Main application file
- `models.py`: Database models
- `routes.py`: Application routes
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, uploads)

## Usage

1. Register an account
2. Create a new event for your wedding
3. Share the generated QR codes with your guests
4. Guests can scan the QR codes to:
   - Leave messages in the guestbook
   - Upload photos to the gallery
   - Record audio messages
5. Display the live slideshow during your event
6. Review and moderate content through the "Manage Content" page

## Content Management

As an event creator, you have the ability to:
- Review all submitted content in one place
- Delete inappropriate photos, messages, or audio recordings
- Manage your event's content through a dedicated interface

## Technologies Used

- Flask: Web framework
- SQLAlchemy: Database ORM
- Flask-Login: User authentication
- QRCode: QR code generation
- Bootstrap: Frontend styling
- JavaScript: Interactive features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Icons by Font Awesome
- Bootstrap for the responsive design
- All the couples who make memories with PortalShare 