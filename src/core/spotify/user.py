import requests
from core.logger import logger

from core.spotify.const import SPOTIFY_USER_ENDPOINT


class SpotifyUserInfo:
    @staticmethod
    def get_user_info(token):
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(SPOTIFY_USER_ENDPOINT, headers=headers)
        if res.ok:
            return res.json()
        else:
            logger.error(f"Error getting user info from spotify API: {res.content}")
            return None
