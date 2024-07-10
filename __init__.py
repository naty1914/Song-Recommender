
"""
This module imports the necessary modules for the Flask application.

Imported modules:
- `app`: The main Flask application object.
- `get_valid_token`: A function that retrieves a valid access token from the Spotify API.
- `get_spotify_headers`: A function that generates Spotify API request headers.
- `requests`: A module for making HTTP requests.
"""

from app import app, get_valid_token, get_spotify_headers
import requests
