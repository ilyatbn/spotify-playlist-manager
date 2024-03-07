from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, reconstructor

from core.db_client import Base
from core.spotify.auth import SpotifyAuthHandler


class UserModel(Base):
    __tablename__ = "app_user"
    _table_args__ = {'extend_existing': True}

    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String, unique=True, nullable=False)
    display_name = mapped_column(String, unique=False, nullable=True)
    access_token = mapped_column(String, unique=False, nullable=True)
    refresh_token = mapped_column(String, unique=False, nullable=True)

    @reconstructor
    def init_on_load(self):
        self.auth = SpotifyAuthHandler(self)
