import requests

from core.spotify.const import SERVICE_BASE_URL
from core.spotify.schemas import SpotifyPlaylist
from exceptions import SpotifyPlaylistRequestException


class UserPlaylistHandler:
    def __init__(self, user) -> None:
        self.user = user

    def _get_image_url(self, images: list) -> str:
        image_urls = [item.get("url") for item in images]
        return (
            image_urls[0]
            if image_urls
            else f"{SERVICE_BASE_URL}/assets/default_playlist.png"
        )

    def _parse_playlists(self, user_playlists: list) -> list:
        parsed_playlists = []
        for playlist in user_playlists:
            if playlist.get("owner").get("id") == self.user.username:
                # skip crabhands (toggle in user settings or something since these playlists are super huge..idk..),
                playlist_item = SpotifyPlaylist(
                    username=self.user.username,
                    playlist_id=playlist.get("id"),
                    name=playlist.get("name"),
                    snapshot_id=playlist.get("snapshot_id"),
                    image_url=self._get_image_url(playlist.get("images", None)),
                )
                parsed_playlists.append(playlist_item)
        return parsed_playlists

    def _get_playlist_chunk(self, next: str = None, start_pos: int = 0) -> tuple:
        if not next:
            chunk = requests.get(
                url=f"https://api.spotify.com/v1/users/{self.user.username}/playlists",
                params={"offset": start_pos, "limit": 50},
                headers={"Authorization": f"Bearer {self.user.access_token}"},
            )
        else:
            chunk = requests.get(
                url=next, headers={"Authorization": f"Bearer {self.user.access_token}"}
            )

        if not chunk.ok:
            raise SpotifyPlaylistRequestException(f"{chunk.status_code, chunk.json()}")

        chunk_dict = chunk.json()
        return chunk_dict["items"], chunk_dict["next"]

    def get_user_playlists(self, start_pos: int = None) -> list:
        self.user.auth.refresh_access_token()
        user_playlists = []

        chunk, next_playlist = self._get_playlist_chunk(start_pos=start_pos)
        user_playlists.extend(chunk)
        while next_playlist:
            chunk, next_playlist = self._get_playlist_chunk(next_playlist)
            user_playlists.extend(chunk)
        return self._parse_playlists(user_playlists)
