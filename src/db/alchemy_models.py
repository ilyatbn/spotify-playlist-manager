from sqlalchemy import ARRAY, Boolean, Integer, String
from sqlalchemy.orm import mapped_column, reconstructor

from core.db_client import Base
from core.spotify.auth import SpotifyAuthHandler
from core.spotify.playlists import UserPlaylistHandler


class UserModel(Base):
    __tablename__ = "app_user"
    _table_args__ = {'extend_existing': True}

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String, unique=True, nullable=False)
    display_name = mapped_column(String, unique=False, nullable=True)
    access_token = mapped_column(String, unique=False, nullable=True)
    refresh_token = mapped_column(String, unique=False, nullable=True)
    is_admin = mapped_column(Boolean, unique=False, nullable=True, default=False)

    @reconstructor
    def init_on_load(self):
        self.auth = SpotifyAuthHandler(self)
        self.spotify = UserPlaylistHandler(self)


class SpotifyPlaylistModel(Base):
    __tablename__ = "spotify_playlists"
    _table_args__ = {"extend_existing": True}

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(
        String, unique=False, nullable=False
    )  # fkey? not that I need it..
    spotify_playlist_id = mapped_column(String, unique=True, nullable=False)
    snapshot_id = mapped_column(String, unique=False, nullable=True)
    last_sync_time = mapped_column(String, unique=False, nullable=True)
    last_track_id = mapped_column(String, unique=False, nullable=True)


class SplamPlaylistModel(Base):
    __tablename__ = "splam_playlists"
    _table_args__ = {"extend_existing": True}

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(
        String, unique=False, nullable=False
    )  # fkey? not that I need it..
    playlist_id = mapped_column(String, unique=True, nullable=False)
    playlist_name = mapped_column(String, unique=False, nullable=True)
    genres = mapped_column(ARRAY(String), unique=False, nullable=True)
    source_playlist_id = mapped_column(
        String, unique=False, nullable=True
    )  # fkey? not that I need it..


# splam
# user_id, playlist_id, playlist_name, genres(array), source_playlist_id
# ilya, 1, hardstyle, hard favorites
# ilya, 3, hardstyle, liked songs
# ilya, 2, hardcore, hard favorites
# ilya, 4, hardcore, liked songs

# spo
# user_id, source_playlist_id, snapshot_id, last_sync_time, last_track_id
# ilya, hard favorites, idjjj, 1.1.2024, 888
# ilya, liked songs, ssss1, 1.1.2024, 10001
