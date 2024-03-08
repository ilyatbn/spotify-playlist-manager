from typing import List

from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, Request

from api.routers.base_router import BaseRouter
from api.schemas.api_schemas import SpotifyPlaylistGet
from core.logger import logger
from db.models import SpotifyPlaylist, User

user_model = User()


class SpotifyPlaylistType:
    MANAGED = "managed"
    UNMANAGED = "unmanaged"


class SpotifyMetadata(BaseRouter):
    query_object_schema = SpotifyPlaylistGet
    create_object_schema = None
    update_object_schema = None
    prefix = "/spotify"
    model = SpotifyPlaylist

    def __init__(self) -> None:
        self.reconfigure_annotations()
        super().__init__()

    async def list(
        self,
        request: Request,
        request_source: str = SpotifyPlaylistType.MANAGED,
        Authorize: AuthJWT = Depends(),
    ):
        logger.info("user requested playlists")
        await Authorize.jwt_required()
        current_user = await Authorize.get_jwt_subject()
        user = await user_model.get_item_by_user(current_user)

        if request_source == SpotifyPlaylistType.MANAGED:
            playlists = await self.model.get_item_by_user(current_user) or []
            # playlists = [self.query_object_schema(item) for item in managed_playlists]
        if request_source == SpotifyPlaylistType.UNMANAGED:
            playlists = user.spotify.get_user_playlists()

        return playlists
