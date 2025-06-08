from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for, redirect, session, request, flash, jsonify
from flask_login import login_user, current_user
from models import db, User, GuestAccess
import os
import json
import logging
from authlib.integrations.requests_client import OAuth2Session
from google_auth import CLIENT_CONFIG, SCOPES, get_user_info, validate_token, create_flow

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'development' else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('oauth')

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    
    # Configure Google OAuth using CLIENT_CONFIG
    google = oauth.register(
        name='google',
        client_id=CLIENT_CONFIG["web"]["client_id"],
        client_secret=CLIENT_CONFIG["web"]["client_secret"],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': ' '.join(SCOPES)
        },
        authorize_url=CLIENT_CONFIG["web"]["auth_uri"],
        access_token_url=CLIENT_CONFIG["web"]["token_uri"],
    )
    
    @app.route('/login/google')
    def login_google():
        try:
            # Use SERVER_NAME from environment if available
            server_name = os.getenv("SERVER_NAME", request.host_url.rstrip('/'))
            redirect_uri = f"{server_name}/login/google/authorize"
            session['oauth_redirect_uri'] = redirect_uri
            
            # Use the flow for authentication
            flow = create_flow(redirect_uri)
            if not flow:
                flash("Error with Google authentication configuration. Please contact the administrator.", 'error')
                return redirect(url_for('login'))
                
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store the state in the session
            session['oauth_state'] = state
            
            return redirect(authorization_url)
        except Exception as e:
            logger.error(f"Error in login_google: {str(e)}")
            flash("Error initiating authentication. Please try again.", 'error')
            return redirect(url_for('login'))
    
    @app.route('/login/google/authorize')
    def authorize_google():
        try:
            # Check for error parameter
            if request.args.get('error'):
                error = request.args.get('error')
                logger.error(f"OAuth error: {error}")
                flash(f"Authentication error: {error}", 'error')
                return redirect(url_for('login'))
            
            # Get the authorization code
            code = request.args.get('code')
            if not code:
                logger.error("No authorization code in request")
                flash("Authentication error: No authorization code received.", 'error')
                return redirect(url_for('login'))
            
            # Get the redirect URI from the session
            redirect_uri = session.get('oauth_redirect_uri')
            if not redirect_uri:
                # Use SERVER_NAME from environment if available
                server_name = os.getenv("SERVER_NAME", request.host_url.rstrip('/'))
                redirect_uri = f"{server_name}/login/google/authorize"
                logger.warning(f"No redirect URI in session, using default: {redirect_uri}")
            
            # Create a new flow
            flow = create_flow(redirect_uri)
            if not flow:
                flash("Error with Google authentication configuration. Please contact the administrator.", 'error')
                return redirect(url_for('login'))
            
            # Exchange the authorization code for tokens
            try:
                flow.fetch_token(code=code)
            except Exception as token_error:
                logger.error(f"Error fetching token: {str(token_error)}")
                flash("Error obtaining access token. Please try again.", 'error')
                return redirect(url_for('login'))
            
            # Get credentials
            credentials = flow.credentials
            if not credentials:
                logger.error("No credentials obtained from flow")
                flash("Authentication error: Failed to obtain credentials.", 'error')
                return redirect(url_for('login'))
            
            # Get user info
            try:
                google_session = flow.authorized_session()
                user_info = google_session.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
            except Exception as user_info_error:
                logger.error(f"Error getting user info: {str(user_info_error)}")
                
                # Try alternative method to get user info
                try:
                    user_info = get_user_info(credentials.token)
                    if not user_info:
                        raise Exception("Failed to get user info from token")
                except Exception as alt_error:
                    logger.error(f"Alternative method also failed: {str(alt_error)}")
                    flash("Error retrieving user information. Please try again.", 'error')
                    return redirect(url_for('login'))
            
            # Verify required user info fields
            if 'sub' not in user_info or 'email' not in user_info:
                logger.error(f"Missing required fields in user info")
                flash("Authentication error: Incomplete user information.", 'error')
                return redirect(url_for('login'))
            
            # Check if this Google account is already linked to a user
            user = User.query.filter_by(google_id=user_info['sub']).first()
            
            if not user:
                # Check if email exists
                user = User.query.filter_by(email=user_info['email']).first()
                
                if user:
                    # Link existing account with Google
                    user.google_id = user_info['sub']
                    user.profile_pic = user_info.get('picture', '')
                    db.session.commit()
                else:
                    # Create new user
                    try:
                        username = user_info.get('name') or user_info['email'].split('@')[0]
                        
                        # Check if username already exists and make it unique if needed
                        base_username = username
                        counter = 1
                        while User.query.filter_by(username=username).first():
                            username = f"{base_username}_{counter}"
                            counter += 1
                        
                        user = User(
                            username=username,
                            email=user_info['email'],
                            google_id=user_info['sub'],
                            profile_pic=user_info.get('picture', ''),
                            is_guest=True if 'event_uuid' in session else False,
                            password_hash=''
                        )
                        db.session.add(user)
                        db.session.commit()
                    except Exception as db_error:
                        logger.error(f"Error creating user: {str(db_error)}")
                        flash("Error creating user account. Please try again.", 'error')
                        return redirect(url_for('login'))
            
            # Log in the user
            login_user(user)
            
            # Clear OAuth session data
            session.pop('oauth_state', None)
            session.pop('oauth_redirect_uri', None)
            
            # If user was trying to access an event as a guest, redirect there
            if 'event_uuid' in session:
                event_uuid = session.pop('event_uuid')
                flash("Successfully signed in with Google.", 'success')
                return redirect(url_for('guestbook', event_uuid=event_uuid))
            
            # Otherwise redirect to dashboard
            flash("Successfully signed in with Google.", 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Error in Google OAuth: {str(e)}")
            flash("Authentication error. Please try again.", 'error')
            return redirect(url_for('login'))
    
    @app.route('/guest/login/<uuid:event_uuid>')
    def guest_login(event_uuid):
        # Store the event UUID in the session
        session['event_uuid'] = str(event_uuid)
        return redirect(url_for('login_google')) 