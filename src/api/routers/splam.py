from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, Request

from api.routers.base_router import BaseRouter
from api.schemas.api_schemas import SpotifyPlaylistGet
from core.logger import logger
from db.models import SplamPlaylist, User

users_model = User()


class SplamPlaylistManagerRouter(BaseRouter):
    create_object_schema = None
    update_object_schema = None
    prefix = "/splam"
    model = SplamPlaylist

    def __init__(self) -> None:
        self.reconfigure_annotations()
        super().__init__()

    async def list(self, request: Request, Authorize: AuthJWT = Depends()):
        await Authorize.jwt_required()
        current_user = await Authorize.get_jwt_subject()
        splam_playlists = await self.model.get_item_by_user(current_user)
        return splam_playlists or []

    # async def create(automatic=True)
    # create a new set of playlists(in the model only) based on the user's selected playlists
