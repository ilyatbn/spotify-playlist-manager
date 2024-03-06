# import routers here
from .login import LoginRouter, AuthCallbackRouter
from .users import UserManagementRouter
from .playlist_manager import PlaylistManagerRouter
# from .home import router as homepage

ACTIVE_ROUTERS = [LoginRouter, AuthCallbackRouter, UserManagementRouter, PlaylistManagerRouter]
