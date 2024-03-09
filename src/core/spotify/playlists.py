import requests

from core.spotify.const import SPOTIFY_PLAYLIST_ENDPOINT
from core.spotify.schemas import SpotifyPlaylist
from exceptions import SpotifyPlaylistRequestException

ALLOWED_NON_OWNER_PLAYLISTS = ["release radar", "liked songs", "neurobreaks"]
PROHIBITED_PLAYLISTS = ["crabhands"]

class UserPlaylistHandler:
    def __init__(self, user) -> None:
        self.user = user

    @property
    def base_headers(self):
        return {"Authorization": f"Bearer {self.user.access_token}"}

    def _get_image_url(self, images: list) -> str:
        image_urls = [item.get("url") for item in images]
        return image_urls[0] if image_urls else f"assets/default_playlist.png"

    def _is_prohibited_playlist(self, playlist_name: str) -> bool:
        return any([True for item in PROHIBITED_PLAYLISTS if item in playlist_name])

    def _parse_playlists(self, user_playlists: list) -> list:
        parsed_playlists = []
        # I'm lazy so this is done like this because I wanna display Liked Songs and Release Radar fist.
        for playlist in user_playlists:
            if playlist.get("name").lower() in ALLOWED_NON_OWNER_PLAYLISTS:
                playlist_item = SpotifyPlaylist(
                    username=self.user.username,
                    playlist_id=playlist.get("id"),
                    name=playlist.get("name"),
                    snapshot_id=playlist.get("snapshot_id"),
                    image_url=self._get_image_url(playlist.get("images", None)),
                )
                parsed_playlists.append(playlist_item)

        for playlist in user_playlists:
            # TODO: (Not sure yet but I don't wanna allow playlists not created by you, even though it's actually pretty useful. maybe if I cache them?)
            if playlist.get("owner").get(
                "id"
            ) == self.user.username and not self._is_prohibited_playlist(
                playlist.get("name").lower()
            ):
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
                url=SPOTIFY_PLAYLIST_ENDPOINT.format(user_id=self.user.username),
                params={"offset": start_pos, "limit": 50},
                headers=self.base_headers,
            )
        else:
            chunk = requests.get(
                url=next,
                headers=self.base_headers,
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
        # get liked songs
        return self._parse_playlists(user_playlists)
