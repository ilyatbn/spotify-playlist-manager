from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from api.routers.base_router import BaseRouter
from core.spotify_api import SpotifyAuthHandler
from fastapi.responses import RedirectResponse

from db.models import User

auth_handler = SpotifyAuthHandler()
usermodel = User()

class LoginRouter(BaseRouter):
    prefix = "/login"

    def __init__(self) -> None:
        super().__init__()
        self.router.add_api_route(
            "", self.login, methods=["GET"], include_in_schema=False
        )

    def _logged_in(self, request: Request):
        #verify jwt..
        return True if getattr(request.state, "user", None) else False

    async def login(self, request: Request):
        if not self._logged_in(request):
            return auth_handler.authorize_redirect
        else:
            #get user settings from db?..
            pass

class AuthCallbackRouter(BaseRouter):
    prefix = "/auth_callback"

    def __init__(self) -> None:
        super().__init__()
        self.router.add_api_route(
            "", self.handle_callback, methods=["GET"], include_in_schema=False
        )

    async def handle_callback(self, request: Request, state:str = None, code:str = None, error:str =None):
        if not state or not auth_handler.validate_state(state):
            return JSONResponse({"error": "authorization state error."}, status_code=status.HTTP_401_UNAUTHORIZED)

        if not code:
            error = request.headers.get("error", "unknown error.")
            return JSONResponse({"error": "authorization failed", "error_details": error}, status_code=status.HTTP_401_UNAUTHORIZED)

        token_metadata = auth_handler.get_access_token(code)
        if not token_metadata:
            error = "something went wrong during access token request."
            return JSONResponse({"error": "authorization failed", "error_details": error}, status_code=status.HTTP_401_UNAUTHORIZED)
        # get user info from spotify.
        # check if local user exists (by email), if not create it. store auth token and refresh tokens since we need to update their playlists.
        # generate jwt
        redirect = RedirectResponse('/manage')
        redirect.set_cookie(key="Authorization", value=f"{token_metadata.token_type} {token_metadata.access_token}", expires=token_metadata.expires_in)
        return redirect




# create or refresh access token
# get user email
# get or create user in local database, 
# if get, redirect to /manage?
# if create, create new config and redirect to /home..
# home will 