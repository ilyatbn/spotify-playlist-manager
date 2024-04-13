from fastapi import Request, status, Depends
from fastapi.responses import JSONResponse
from api.routers.base_router import BaseRouter
from core.spotify.auth import SpotifyAuthHandler
from fastapi.responses import RedirectResponse
from async_fastapi_jwt_auth import AuthJWT
from db.models import User
from core.logger import logger

auth_handler = SpotifyAuthHandler()
users_model = User()

class LoginRouter(BaseRouter):
    prefix = "/login"

    def __init__(self) -> None:
        super().__init__()
        self.router.add_api_route(
            "", self.login, methods=["GET"], include_in_schema=False
        )

    def _logged_in(self, request: Request):
        return True if getattr(request.state, "user", None) else False

    async def login(self, request: Request):
        if not self._logged_in(request):
            return auth_handler.authorize_redirect

class AuthCallbackRouter(BaseRouter):
    prefix = "/auth_callback"

    def __init__(self) -> None:
        super().__init__()
        self.router.add_api_route(
            "", self.handle_callback, methods=["GET"], include_in_schema=False
        )

    async def handle_callback(self, request: Request, state:str = None, code:str = None, error:str =None, Authorize: AuthJWT = Depends()):
        if not state or not auth_handler.validate_state(state):
            return JSONResponse({"error": "authorization state error."}, status_code=status.HTTP_401_UNAUTHORIZED)

        if not code:
            error = request.headers.get("error", "unknown error.")
            return JSONResponse({"error": "authorization failed", "error_details": error}, status_code=status.HTTP_401_UNAUTHORIZED)

        token_metadata = auth_handler.get_tokens(code)
        if not token_metadata:
            error = "something went wrong during access token request."
            return JSONResponse({"error": "authorization failed", "error_details": error}, status_code=status.HTTP_401_UNAUTHORIZED)

        # TODO: Obviously need to encrypt the access and refresh tokens, or better yet, store them in Vault and query by the username when required.
        if not (
            user := await users_model.get_item_by_user(
                token_metadata.user_info.get("id")
            )
        ):
            user = await users_model.create_item(
                username=token_metadata.user_info.get("id"),
                display_name=token_metadata.user_info.get("display_name"),
                refresh_token=token_metadata.refresh_token,
            )
            logger.info(f"new user {user.get('display_name')} created")
        else:
            logger.info(f"existing user {user.display_name} logged in")
            user=user.__dict__

        # generate jwt. we don't actually want to expose the users' spotify access token, but the app access token.
        access_token = await Authorize.create_access_token(subject=user.get("username"))
        # refresh_token = await Authorize.create_refresh_token(subject=user.get("username"))
        # Set the JWT and CSRF double submit cookies in the response
        redirect = RedirectResponse('/')
        await Authorize.set_access_cookies(access_token, redirect, max_age=3599)
        # await Authorize.set_refresh_cookies(refresh_token, redirect, max_age=3599)
        redirect.set_cookie(
            key="spm_access",
            value=1,
            path="/",
            max_age=3599,
            samesite="strict",
        )
        return redirect
