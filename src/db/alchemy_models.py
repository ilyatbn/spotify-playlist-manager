from sqlalchemy import ARRAY, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

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
    spotify_playlists = relationship(
        "SpotifyPlaylistModel", back_populates="user", lazy="subquery"
    )

    @reconstructor
    def init_on_load(self):
        self.auth: SpotifyAuthHandler = SpotifyAuthHandler(self)
        self.spotify: UserPlaylistHandler = UserPlaylistHandler(self)


class SpotifyPlaylistModel(Base):
    __tablename__ = "spotify_playlists"
    _table_args__ = {"extend_existing": True}

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(ForeignKey("app_user.username"))
    spotify_playlist_id = mapped_column(String, unique=True, nullable=False)
    snapshot_id = mapped_column(String, unique=False, nullable=True)
    last_sync_time = mapped_column(String, unique=False, nullable=True)
    last_track_added_at = mapped_column(String, unique=False, nullable=True)
    track_count = mapped_column(Integer, unique=False, nullable=True, default=0)

    user = relationship(
        "UserModel", back_populates="spotify_playlists", lazy="subquery"
    )

    @reconstructor
    def init_on_load(self):
        self.spotify = UserPlaylistHandler(self)


class SplamPlaylistModel(Base):
    __tablename__ = "splam_playlists"
    _table_args__ = {"extend_existing": True}

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String, unique=False, nullable=False)
    playlist_id = mapped_column(String, unique=True, nullable=False)
    playlist_name = mapped_column(String, unique=False, nullable=True)
    genres = mapped_column(ARRAY(String), unique=False, nullable=True)
    source_playlist_id = mapped_column(String, unique=False, nullable=True)
