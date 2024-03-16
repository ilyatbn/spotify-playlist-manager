import copy

import requests

from core.spotify.const import (
    SPOTIFY_PLAYLIST_ENDPOINT,
    SPOTIFY_PLAYLISTS_ENDPOINT,
    SPOTIFY_SAVED_TRACKS_ENDPOINT,
    SPOTIFY_TRACKS_ENDPOINT,
)
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
        # liked songs / saved items, isn't really a playlist like others, so we'll add it manually
        parsed_playlists.append(
            SpotifyPlaylist(
                username=self.user.username,
                playlist_id=f"me",
                name="Liked Songs",
                snapshot_id="0",
                image_url="https://misc.scdn.co/liked-songs/liked-songs-640.png",
            )
        )
        # I'm lazy so this is done like this because I wanna display Liked Songs and Release Radar first.
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

    def _get_chunk(
        self, url, next_url: str = None, start_pos: int = 0, params: dict = {}
    ) -> tuple:
        if not next_url:
            final_params = copy.deepcopy(params)
            final_params.update({"offset": start_pos, "limit": 50})
            chunk = requests.get(
                url=url,
                params=final_params,
                headers=self.base_headers,
            )
        else:
            chunk = requests.get(
                url=next_url,
                headers=self.base_headers,
            )

        if not chunk.ok:
            raise SpotifyPlaylistRequestException(f"{chunk.status_code, chunk.json()}")

        chunk_dict = chunk.json()
        return chunk_dict["items"], chunk_dict["next"]

    def get_items(self, url, start_pos: int = None, params={}) -> list:
        self.user.auth.refresh_access_token()
        api_response_items = []

        chunk, next_playlist = self._get_chunk(
            url=url,
            start_pos=start_pos,
            params=params,
        )
        api_response_items.extend(chunk)
        while next_playlist:
            chunk, next_playlist = self._get_chunk(
                url=url,
                next_url=next_playlist,
            )
            api_response_items.extend(chunk)
        return api_response_items

    def _parse_tracks(self, tracklist: list, start_date=None) -> list:
        parsed_tracks = []
        # max_added_at = None
        for track in tracklist:
            if (
                track_added_at := item.get("added_at", None)
            ) and track_added_at > start_date:
                item = track
                parsed_tracks.append(item)
        return parsed_tracks

    def get_user_playlists(self, start_pos: int = None) -> list:
        playlist_endpoint = SPOTIFY_PLAYLISTS_ENDPOINT.format(
            user_id=self.user.username
        )
        playlists = self.get_items(url=playlist_endpoint, start_pos=start_pos)
        return self._parse_playlists(playlists)

    def get_playlist_tracks(
        self, playlist_id, start_pos: int = 0, start_date=None
    ) -> list:
        tracks_endpoint = SPOTIFY_TRACKS_ENDPOINT.format(playlist_id=playlist_id)
        # meta = SPOTIFY_PLAYLIST_META_ENDPOINT.format(playlist_id=playlist_id)
        params = {"fields": "items(added_at,track(id,name,artists))"}
        tracks = self.get_items(url=tracks_endpoint, start_pos=start_pos, params=params)
        return self._parse_tracks(tracks)

    def get_liked_tracks(self, start_pos: int = 0) -> list:
        tracks = self.get_items(url=SPOTIFY_SAVED_TRACKS_ENDPOINT, start_pos=start_pos)
        return self._parse_tracks(tracks)

    def process_tracks(self):
        pass
        # sync.
        # playlist_meta_endpoint = SPOTIFY_PLAYLIST_ENDPOINT
        # snapshot_id = playlist_meta_endpoint
        # playlist = get_playlist_from_db.
        # spotify_playlist = get_playlist_from_db.
        # if not spotify_playlist.get("snapshot_id") == playlist.snapshot_id:
        # start_pos = playlist.start_pos-100
        #
        # tracks = get_playlist_tracks(start_pos=start_pos, after=playlist.last_added_at),
        # save last trackss 'added_at'
        # save total.

        # (free mongo atlas instance?)
        # get all tracks' artists and their genres, store in db as cache since this is annoying AF and gonna take forever otherwise.
        # https://developer.spotify.com/documentation/web-api/reference/get-multiple-artists

        # get all tracks' metadata and store in db (free mongo atlas instance?)
        # https://developer.spotify.com/documentation/web-api/reference/get-several-audio-features

        # for each new track:
        # get_artist_genres(track.artist_id) [local or from cloud if not found]
        # get_track_metadata(track.id) [local or from cloud if not found] - check track bpm, check internal genre mapping to bpm range
        # check if there are dst playlists with the genre or subgenre or artist[]
        # if everything fits, add the track to the dst_playlist.
