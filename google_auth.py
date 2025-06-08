import os
import requests
import logging
from flask import current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'development' else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('google_auth')

# Google OAuth configuration
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:5000/login/google/authorize"]
    }
}

# Add SERVER_NAME to redirect_uris if available
server_name = os.getenv("SERVER_NAME")
if server_name:
    server_redirect = f"{server_name}/login/google/authorize"
    if server_redirect not in CLIENT_CONFIG["web"]["redirect_uris"]:
        CLIENT_CONFIG["web"]["redirect_uris"].append(server_redirect)

SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']

def create_flow(redirect_uri=None):
    """
    Create an OAuth flow for Google authentication
    
    Args:
        redirect_uri: The URI to redirect to after authentication
                     If None, defaults to http://localhost:5000/login/google/authorize
    
    Returns:
        A Flow object that can be used for OAuth authentication
    """
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        logger.error("Missing Google OAuth credentials in environment variables")
        return None
        
    if redirect_uri is None:
        redirect_uri = "http://localhost:5000/login/google/authorize"
    
    # Make a copy of CLIENT_CONFIG to avoid modifying the original
    config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    try:
        flow = Flow.from_client_config(
            client_config=config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        return flow
    except Exception as e:
        logger.error(f"Error creating flow: {str(e)}")
        return None

def get_user_info(access_token):
    """
    Get user info from Google API using the access token
    """
    if not access_token:
        logger.error("No access token provided")
        return None
        
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error getting user info: {response.text}")
        return None

def validate_token(token):
    """
    Validate a Google OAuth token
    """
    if not token:
        logger.error("No token provided")
        return None
        
    try:
        response = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
        )
        
        if response.status_code == 200:
            token_info = response.json()
            
            # Verify that the token was issued for our client
            if token_info.get('aud') != os.getenv("GOOGLE_CLIENT_ID"):
                logger.error(f"Token was not issued for this application")
                return None
                
            return token_info
        else:
            logger.error(f"Token validation failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return None

def get_google_login_url(redirect_uri):
    """
    Generate a Google OAuth login URL
    """
    params = {
        'client_id': os.getenv("GOOGLE_CLIENT_ID"),
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
    }
    
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    return f"{CLIENT_CONFIG['web']['auth_uri']}?{query_string}"

def create_credentials_from_token(token_info):
    """
    Create Google OAuth credentials from token info
    
    Args:
        token_info: A dictionary containing token information
                   Must include 'access_token' and may include 'refresh_token'
    
    Returns:
        A Credentials object that can be used for authenticated requests
    """
    if not token_info or 'access_token' not in token_info:
        logger.error("Invalid token info provided")
        return None
        
    try:
        credentials = Credentials(
            token=token_info.get('access_token'),
            refresh_token=token_info.get('refresh_token'),
            token_uri=CLIENT_CONFIG['web']['token_uri'],
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=SCOPES
        )
        
        # Check if the credentials are valid
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            
        return credentials
    except Exception as e:
        logger.error(f"Error creating credentials: {str(e)}")
        return None 