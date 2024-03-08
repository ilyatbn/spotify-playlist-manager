from api.routers.base_router import BaseRouter
from api.schemas.api_schemas import (
    UserModelDataCreate,
    UserModelDataGet,
    UserModelDataUpdate,
)
from db.models import User
from fastapi import Request, Depends
from async_fastapi_jwt_auth import AuthJWT
from core.logger import logger

class UserManagementRouter(BaseRouter):
    query_object_schema = UserModelDataGet
    create_object_schema = UserModelDataCreate
    update_object_schema = UserModelDataUpdate
    prefix = "/manage"
    model = User

    def __init__(self) -> None:
        self.reconfigure_annotations()
        super().__init__()

    async def list(self, request: Request, Authorize: AuthJWT = Depends()):
        await Authorize.jwt_required()
        current_user = await Authorize.get_jwt_subject()
        logger.info(current_user)
        user = await self.model.get_item_by_user(current_user)
        if user.is_admin:
            #whoopie, an admin just logged in. give him more stuff to do.
            return await self.model.all()
        return []
