from api.routers.base_router import BaseRouter
# from api.schemas.api_schemas import

from db.models import User
from fastapi import Request, Depends
from async_fastapi_jwt_auth import AuthJWT
from core.logger import logger

usermodel = User()

class PlaylistManagerRouter(BaseRouter):
    query_object_schema = None
    create_object_schema = None
    update_object_schema = None
    prefix = "/plm"
    model = None #GenrePlaylist

    def __init__(self) -> None:
        self.reconfigure_annotations()
        super().__init__()

    async def list(self, request: Request, Authorize: AuthJWT = Depends()):
        await Authorize.jwt_required()
        current_user = await Authorize.get_jwt_subject()
        logger.info(current_user)
        user = await usermodel.get_username(current_user)
        # get user's playlists.
        # get user's GenrePlaylist (the ones we created).

    #async def create(automatic=True)
    #create a new set of playlists(in the model only) based on the user's selected playlists