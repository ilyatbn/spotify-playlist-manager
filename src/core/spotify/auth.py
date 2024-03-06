import requests
from core.app_config import config
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from uuid import uuid4
import base64
from core.logger import logger
from core.spotify.user import SpotifyUserInfo
from typing import Optional

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

class SpotifyAuthHandler:
    states = []

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
         
    def get_access_token(self, code):
        headers = {
             "content-type": 'application/x-www-form-urlencoded',
             "Authorization": f"Basic {self.app_creds}",
        }
        response = requests.post(SPOTIFY_AUTH_TOKEN_ENDPOINT, headers=headers, data=SpotifyAccessTokenPayload(code=code).model_dump())
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

    def refresh_access_token(self, access_token):
        pass

    def validate_state(self, state): 
        try:
            self.states.remove(state)
            return True
        except:
             return False