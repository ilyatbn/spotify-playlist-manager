from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from celery.app import Celery
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import tasks
from api.middleware import ACTIVE_MIDDLEWARE
from api.middleware.cors import add_cors_middleware
from api.routers import ACTIVE_ROUTERS
from core.app_config import AuthJWTConfig, config

app = FastAPI(redoc_url=None)

for router in ACTIVE_ROUTERS:
    app.include_router(router().router)
for middleware in ACTIVE_MIDDLEWARE:
    app.add_middleware(middleware)
    add_cors_middleware(app)

app.mount('/', StaticFiles(directory='front',html=True))


@AuthJWT.load_config
def get_config():
    return AuthJWTConfig()

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


celery_app = Celery(__name__, broker=config.REDIS_URI, backend=config.REDIS_URI)
celery_app.autodiscover_tasks(["tasks.sync_tasks"])
