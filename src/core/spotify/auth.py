import base64
import time
from functools import cached_property
from urllib.parse import urlencode

import requests
from fastapi.responses import RedirectResponse

from core.logger import logger
from core.spotify.const import (
    SPOTIFY_AUTH_ENDPOINT,
    SPOTIFY_AUTH_TOKEN_ENDPOINT,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
)
from core.spotify.schemas import (
    SpotifyAccessTokenPayload,
    SpotifyAuthrorizationQuery,
    SpotifyRefreshTokenPayload,
    SpotifyTokenMetadata,
)
from core.spotify.user import SpotifyUserInfo


class SpotifyAuthHandler:
    states = []  # TODO: move this since this is mutable

    def __init__(self, user=None) -> None:
        self.user = user

    @property
    def authorize_redirect(self):
        url_queries = SpotifyAuthrorizationQuery()
        self.states.append(url_queries.state)
        queryparams = urlencode(url_queries.model_dump())
        auth_url = f"{SPOTIFY_AUTH_ENDPOINT}{queryparams}"
        return RedirectResponse(auth_url)

    @property
    def app_creds(self):
        return base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()

    @cached_property
    def base_headers(self):
        return {
             "content-type": 'application/x-www-form-urlencoded',
             "Authorization": f"Basic {self.app_creds}",
        }

    # for callback handler when creating new users
    def get_tokens(self, code):
        response = requests.post(
            SPOTIFY_AUTH_TOKEN_ENDPOINT,
            headers=self.base_headers,
            data=SpotifyAccessTokenPayload(code=code).model_dump(),
        )
        if response.ok:
            response_data = response.json()
            user_meta = SpotifyTokenMetadata(**response_data)
            user_meta.user_info = SpotifyUserInfo.get_user_info(user_meta.access_token)
            if not user_meta.user_info:
                 return False
            return user_meta
        else:
             logger.info(f"bad response from token request endpoint:{response.content}")
             return False

    def refresh_access_token(self, user=None):
        user = user or self.user
        if not getattr(self, "last_refresh_time", None):
            self.last_refresh_time = time.time()
        else:
            if time.time() - self.last_refresh_time < 1800:
                return
        response = requests.post(
            SPOTIFY_AUTH_TOKEN_ENDPOINT,
            headers=self.base_headers,
            data=SpotifyRefreshTokenPayload(
                refresh_token=user.refresh_token
            ).model_dump(),
        )
        if response.ok:
            logger.info(f"access token refreshed for {self.user.username}")
            user.access_token = response.json().get("access_token")
        else:
            logger.warning(
                f"response from spotify not okay: status={response.status_code}, content={response.content}"
            )

    def validate_state(self, state):
        try:
            self.states.remove(state)
            return True
        except:
             return False
