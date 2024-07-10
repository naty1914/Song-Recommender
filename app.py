"""
This module contains the necessary imports for the Flask application.
"""
import base64
import logging
from flask import Flask, redirect, request, send_from_directory, session, url_for, render_template
import requests
import urllib.parse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Generate a random secret key for the application.
# This key is used to secure session data and other
# sensitive information.
app.secret_key = os.urandom(24)

# Set CLIENT_ID and CLIENT_SECRET variables from environment variables
# or exit if these variables are not set.
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables")

# Spotify API endpoints
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# URL to sign up for Spotify
SIGNUP_URL = "https://www.spotify.com/signup/"



def get_spotify_headers(token):
    """
    Generates Spotify API request headers.
    """
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables")

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    return headers

def get_user_id(token):
    """
    Retrieves user ID from Spotify API.
    """
    headers = get_spotify_headers(token)
    url = 'https://api.spotify.com/v1/me'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return user_data['id']
    else:
        logging.error(f'Failed to retrieve user data: {response.text}')
        return None

@app.route('/images/<path:filename>')
def custom_static(filename):
    """
    A route decorator that serves static files from the 'images' directory.

    Parameters: filename (str): The name of the file to be served.

    Returns: Response: The response object containing the requested file.
    """
    
    return send_from_directory('images', filename)

@app.route('/')
def landing():
    """
    Renders the landingpage.html template and returns it as the response for the root URL ('/').

    Returns: The rendered landingpage.html template as a response.
    """
    return render_template('landingpage.html')

@app.route('/home')
def home():
    """
    Renders the homepage template.
    """
    return render_template('homepage.html')

@app.route('/login')
def login():
    """
    Create the Spotify authorization URL with the necessary scopes and redirect to the login page.
    """
    scope = 'user-read-private user-read-email playlist-read-private user-top-read playlist-modify-public playlist-modify-private'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return render_template('login.html', auth_url=auth_url, signup_url=SIGNUP_URL)

@app.route('/signup')
def signup():
    """
    Redirect the user to the Spotify signup page.
    """
    return redirect(SIGNUP_URL)

@app.route('/callback')
def callback():
    """
    Handle the Spotify callback after user authorization.
    """
    code = request.args.get('code')
    token_data = get_token(code)
    if token_data:
        session['token'] = token_data['access_token']
        session['refresh_token'] = token_data['refresh_token']
        return redirect(url_for('home'))
    else:
        logging.error('Failed to get token')
        return 'Failed to get token', 400

def get_token(code):
    """
    Get access and refresh tokens using the authorization code.
    """
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.urlsafe_b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response_data = response.json()
    return {
        'access_token': response_data.get('access_token'),
        'refresh_token': response_data.get('refresh_token')
    }

def refresh_access_token(refresh_token):
    """
    Refresh the Spotify access token using the provided refresh token.

    Args:
    refresh_token (str): The refresh token used to obtain a new access token.

    Returns:
    str: A new access token if the refresh is successful, None otherwise.
    """
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.urlsafe_b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        response_data = response.json()
        return response_data.get('access_token')
    else:
        logging.error('Failed to refresh token')
        return None

def get_valid_token():
    """
    Retrieve a valid Spotify access token. If the current token is expired, refresh it.
    """
    token = session.get('token')
    refresh_token = session.get('refresh_token')
    if token:
        headers = get_spotify_headers(token)
        test_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        if test_response.status_code == 401 and refresh_token:
            token = refresh_access_token(refresh_token)
            if token:
                session['token'] = token
    return token

@app.route('/profile')
def profile():
    """
    Retrieves user profile information from Spotify API and renders it on the 'profile.html' template.
    """
    token = get_valid_token()
    if not token:
        return redirect(url_for('login'))

    headers = get_spotify_headers(token)
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    if response.status_code != 200:
        return f'Failed to retrieve user info: {response.text}', response.status_code

    try:
        user_info = response.json()
    except ValueError as e:
        return f'Error decoding JSON: {e}, Response content: {response.text}', 500

    session['user_id'] = user_info['id']

    return render_template('profile.html', user_info=user_info)

@app.route('/playlists')
def get_playlists():
    """
    Retrieves playlists from Spotify API and renders them on the playlists.html template.
    """
    token = get_valid_token()
    if not token:
        return redirect(url_for('login'))

    headers = get_spotify_headers(token)
    response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers, params={'limit': 20})
    if response.status_code != 200:
        return f'Failed to retrieve playlists: {response.text}', response.status_code

    try:
        playlists = response.json()
    except ValueError as e:
        return f'Error decoding JSON: {e}, Response content: {response.text}', 500

    return render_template('playlists.html', playlists=playlists)

@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    """
    Retrieve recommendations for the user and store them in the session.

    """
    token = get_valid_token()
    if not token:
        return redirect(url_for('login'))

    headers = get_spotify_headers(token)
    top_tracks_response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers)
    top_tracks = top_tracks_response.json().get('items', [])

    if top_tracks:
        seed_track = top_tracks[0]['id']
        recommendations_response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params={
            'seed_tracks': seed_track,
            'limit': 10
        })
    else:
        user_location = request.form.get('location') or 'ET'
        recommendations_response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params={
            'seed_genres': 'pop,rock',
            'limit': 10,
            'market': user_location
        })

    recommendations = recommendations_response.json()
    session['recommendations'] = recommendations

    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/tracks/<track_id>')
def get_track(track_id):
    """
    Retrieve a track by its ID and render the track info in a template.
    
    Args:
        track_id (str): The ID of the track to retrieve.
    
    Returns:
        The rendered 'track.html' template with the track info.
    """
    token = get_valid_token()
    if not token:
        return redirect(url_for('login'))

    headers = get_spotify_headers(token)
    response = requests.get(f'https://api.spotify.com/v1/tracks/{track_id}', headers=headers)
    if response.status_code == 200:
        track_info = response.json()
        return render_template('track.html', track=track_info)
    else:
        return f'Error retrieving track: {response.text}', response.status_code

@app.route('/artists/<artist_id>')
def get_artist(artist_id):
    """
    Retrieves artist information by ID and renders it in 'artist.html'.
    """
    
    token = get_valid_token()
    if not token:
        return redirect(url_for('login'))

    headers = get_spotify_headers(token)
    response = requests.get(f'https://api.spotify.com/v1/artists/{artist_id}', headers=headers)
    if response.status_code == 200:
        artist_info = response.json()
        return render_template('artist.html', artist=artist_info)
    else:
        return f'Error retrieving artist: {response.text}', response.status_code


if __name__ == '__main__':
    app.run(debug=True)

