"""
A Test suite for the `get_spotify_headers` function.
"""

import unittest
from unittest.mock import patch
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import get_spotify_headers

class TestGetSpotifyHeaders(unittest.TestCase):
    """
    Test suite for the `get_spotify_headers` function.
    """

    @patch.dict('os.environ', {'CLIENT_ID': 'test_client_id', 'CLIENT_SECRET': 'test_client_secret'})
    def test_get_spotify_headers_returns_correct_headers(self):
        """
        Test that the `get_spotify_headers` returns the correct headers.
        """
        token = 'test_token'
        expected_headers = {
            'Authorization': 'Bearer test_token',
            'Content-Type': 'application/json'
        }
        self.assertEqual(get_spotify_headers(token), expected_headers)

    @patch.dict('os.environ', {}, clear=True)
    def test_get_spotify_headers_raises_value_error_if_client_id_or_secret_is_missing(self):
        """
        Test that `get_spotify_headers` raises a `ValueError` if the
        `CLIENT_ID` or `CLIENT_SECRET` is missing.
        """
        token = 'test_token'
        with self.assertRaises(ValueError):
            get_spotify_headers(token)

if __name__ == '__main__':
    unittest.main()
