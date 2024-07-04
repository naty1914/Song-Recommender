import unittest
from unittest.mock import patch
from app import get_spotify_headers

class TestGetSpotifyHeaders(unittest.TestCase):

    @patch.dict('os.environ', {'CLIENT_ID': 'test_client_id', 'CLIENT_SECRET': 'test_client_secret'})
    def test_get_spotify_headers_returns_correct_headers(self):
        token = 'test_token'
        expected_headers = {
            'Authorization': 'Bearer test_token',
            'Content-Type': 'application/json'
        }
        self.assertEqual(get_spotify_headers(token), expected_headers)

    @patch.dict('os.environ', {}, clear=True)
    def test_get_spotify_headers_raises_value_error_if_client_id_or_secret_is_missing(self):
        token = 'test_token'
        with self.assertRaises(ValueError):
            get_spotify_headers(token)

if __name__ == '__main__':
    unittest.main()
