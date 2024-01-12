# import routers here
from .home import HomeRouter
from .login import LoginRouter, AuthCallbackRouter

# from .home import router as homepage

ACTIVE_ROUTERS = [LoginRouter, HomeRouter, AuthCallbackRouter]
