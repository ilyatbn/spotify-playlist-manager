# import routers here
from .login import AuthCallbackRouter, LoginRouter
from .splam import SplamPlaylistManagerRouter
from .spotify import SpotifyMetadata
from .users import UserManagementRouter

# from .home import router as homepage

ACTIVE_ROUTERS = [
    LoginRouter,
    AuthCallbackRouter,
    UserManagementRouter,
    SplamPlaylistManagerRouter,
    SpotifyMetadata,
]
