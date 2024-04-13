from typing import Optional
from uuid import uuid4

from pydantic import BaseModel

from core.spotify.const import (
    SERVICE_BASE_URL,
    SPOTIFY_AUTH_CALLBACK_ENDPOINT,
    SPOTIFY_AUTH_SCOPES,
    SPOTIFY_CLIENT_ID,
)


class SpotifyAuthrorizationQuery(BaseModel):
    response_type: str = "code"
    client_id: str = SPOTIFY_CLIENT_ID
    scope: str = " ".join(SPOTIFY_AUTH_SCOPES)
    redirect_uri: str = SPOTIFY_AUTH_CALLBACK_ENDPOINT
    state: str = str(uuid4()).replace("-", "Z")


class SpotifyTokenMetadata(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    user_info: Optional[dict] = None


class SpotifyAccessTokenPayload(BaseModel):
    grant_type: str = "authorization_code"
    code: str
    redirect_uri: str = SPOTIFY_AUTH_CALLBACK_ENDPOINT


class SpotifyRefreshTokenPayload(BaseModel):
    grant_type: str = "refresh_token"
    refresh_token: str
    client_id: str = SPOTIFY_CLIENT_ID


class SpotifyPlaylist(BaseModel):
    username: str
    playlist_id: str
    name: str
    snapshot_id: str  # used to trigger updates
    image_url: str


class Track(BaseModel):
    id: str
    name: str
    added_at: Optional[str]
    artists: list
    album_id: str


class Artist(BaseModel):
    id: str
    genres: list
    name: str


class Album(BaseModel):
    id: str
    label: str
    genres: Optional[list] = list()
    tracks: Optional[list] = list()
    copyrights: Optional[list] = list()
    release_date: Optional[str] = None
