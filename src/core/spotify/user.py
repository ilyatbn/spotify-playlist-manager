import requests
from urllib.parse import urljoin
from core.logger import logger

SPOTIFY_API_BASE_URL = "https://api.spotify.com"
SPOTIFY_USER_ENDPOINT = "/v1/me"

class SpotifyUserInfo:
    @staticmethod
    def get_user_info(token):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(urljoin(SPOTIFY_API_BASE_URL,SPOTIFY_USER_ENDPOINT), headers=headers)
        if res.ok:
            return res.json()
        else:
            logger.error(f"Error getting user info from spotify API: {res.content}")
            return None
