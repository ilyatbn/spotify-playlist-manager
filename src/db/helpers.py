from urllib.parse import urlparse, urlunparse

import asyncpg.exceptions as asyncpg_exc
from fastapi import responses, status
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.sql import text

from core.app_config import config
from core.db_client import DatabaseSessionManager
from core.logger import logger


def database_exception_handler(ex):
    message = "an unknown database error has occured. check logs for further details."

    # sqlalchemy integrity errors should have an original exception
    if isinstance(ex, IntegrityError):
        original_exception = getattr(ex, "orig")
        if type(original_exception.__cause__) == asyncpg_exc.UniqueViolationError:
            logger.error(
                f"unique constrait violation: {original_exception.__cause__.message}: {original_exception.__cause__.detail}"
            )
            message = original_exception.__cause__.detail
        else:
            logger.error(
                f"an error occured while performing database operation. original exception: {original_exception}"
            )
    else:
        logger.error(f"{message}: {ex}")

    return responses.JSONResponse(
        content={"error": f"could not create object: {message}"},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


# TODO: Temporary, need to implement Alembic.
async def create_db():
    if not config.DB_ENGINE.lower() == "postgres":
        return
    mgr = DatabaseSessionManager()
    conn_str = urlparse(config.DATABASE_URI)
    conn = urlunparse(conn_str._replace(path="/postgres"))
    mgr.init(conn, autocommit=True)

    database = conn_str.path[1:]
    logger.info(f"creating db {database}")
    async with mgr.session() as sess:
        try:
            result = await sess.execute(text(f"CREATE DATABASE {database}"))
            return result
        except ProgrammingError as ex:
            original_exception = getattr(ex, "orig")
            if "already exists" in original_exception.args[0]:
                logger.info("database already exists")
                return
            raise original_exception


# This is only for the initial creation during development.
# Migrations are currently not supported.


async def create_schemas(drop=False):
    sessionmanager = DatabaseSessionManager()
    from db.models import SplamPlaylist, SpotifyPlaylist, User

    sessionmanager.init(config.DATABASE_URI)
    if drop:
        await sessionmanager.drop_all()
    await sessionmanager.create_all()


async def first_run(drop=False):
    await create_db()
    await create_schemas(drop=drop)
