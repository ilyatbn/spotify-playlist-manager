import base64
from functools import cached_property
from typing import Optional
from urllib.parse import urlencode
from uuid import uuid4

import requests
from fastapi.responses import RedirectResponse

from core.app_config import config
from core.logger import logger
from core.spotify.user import SpotifyUserInfo

#### move, merge/nuke after..
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
BASE_URL = "http://localhost:8102"

SPOTIFY_AUTH_SCOPES=['playlist-read-private', 'playlist-read-collaborative', 'playlist-modify-private' , 'playlist-modify-public', 'user-library-modify', 'user-library-read', 'user-read-email']
SPOTIFY_BASE_URL = 'https://accounts.spotify.com'
SPOTIFY_AUTH_ENDPOINT=f'{SPOTIFY_BASE_URL}/authorize?'
SPOTIFY_AUTH_TOKEN_ENDPOINT = f'{SPOTIFY_BASE_URL}/api/token'
AUTH_CALLBACK_ENDPOINT = f"/auth_callback"

from pydantic import BaseModel


class SpotifyAuthrorizationQuery(BaseModel):
      response_type:str = 'code'
      client_id: str = SPOTIFY_CLIENT_ID
      scope:str = " ".join(SPOTIFY_AUTH_SCOPES)
      redirect_uri:str = f"{BASE_URL}{AUTH_CALLBACK_ENDPOINT}"
      state: str = str(uuid4()).replace('-',"Z")

class SpotifyTokenMetadata(BaseModel):
     access_token: str
     token_type: str
     expires_in: int
     refresh_token: str
     user_info: Optional[dict] = None

class SpotifyAccessTokenPayload(BaseModel):
      grant_type:str = 'authorization_code'
      code: str
      redirect_uri:str = f"{BASE_URL}{AUTH_CALLBACK_ENDPOINT}"

class SpotifyRefreshTokenPayload(BaseModel):
    grant_type: str = "refresh_token"
    refresh_token: str
    client_id: str = SPOTIFY_CLIENT_ID


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

    def get_access_token(self, code):
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
        response = requests.post(
            SPOTIFY_AUTH_TOKEN_ENDPOINT,
            headers=self.base_headers,
            data=SpotifyRefreshTokenPayload(
                refresh_token=user.refresh_token
            ).model_dump(),
        )
        if response.ok:
            user.access_token = response.json().get("access_token")

    def validate_state(self, state):
        try:
            self.states.remove(state)
            return True
        except:
             return False
