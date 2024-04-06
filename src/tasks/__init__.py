from celery.app import Celery

from core.app_config import config

celery_app = Celery(__name__, broker=config.REDIS_URL, backend=config.REDIS_URL)

from tasks.playlists_sync import SpotifyPlaylistSync


@celery_app.task
def dummy_task():
    pass
