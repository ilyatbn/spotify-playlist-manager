from fastapi import FastAPI, Request
from core.app_config import AuthJWTConfig
from api.middleware import ACTIVE_MIDDLEWARE
from api.middleware.cors import add_cors_middleware
from api.routers import ACTIVE_ROUTERS
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse

app = FastAPI()

for router in ACTIVE_ROUTERS:
    app.include_router(router().router)
for middleware in ACTIVE_MIDDLEWARE:
    app.add_middleware(middleware)
    add_cors_middleware(app)


@AuthJWT.load_config
def get_config():
    return AuthJWTConfig()

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
