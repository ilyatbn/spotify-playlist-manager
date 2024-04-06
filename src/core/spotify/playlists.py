import copy
from datetime import datetime, timezone
from typing import Tuple

import requests

from core.logger import logger
from core.spotify.const import (
    SPOTIFY_PLAYLISTS_ENDPOINT,
    SPOTIFY_SAVED_TRACKS_ENDPOINT,
    SPOTIFY_TRACKS_ENDPOINT,
)
from core.spotify.schemas import SpotifyPlaylist, Track
from exceptions import SpotifyPlaylistRequestException

ALLOWED_NON_OWNER_PLAYLISTS = ["release radar", "liked songs", "neurobreaks"]
PROHIBITED_PLAYLISTS = ["crabhands"]

class UserPlaylistHandler:
    def __init__(self, user) -> None:
        self.user = user

    @property
    def base_headers(self):
        return {"Authorization": f"Bearer {self.user.access_token}"}

    def _get_image_url(self, images: list | None) -> str:
        default_playlist = "assets/default_playlist.png"
        if not images:
            return default_playlist

        image_urls = [item.get("url", None) for item in images]
        return image_urls[0] if image_urls else default_playlist

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
        total = chunk_dict.get("total", None)
        return chunk_dict["items"], chunk_dict["next"], total

    def get_items(self, url, start_pos: int = None, params={}) -> list:
        self.user.auth.refresh_access_token()
        api_response_items = []

        chunk, next_playlist, total = self._get_chunk(
            url=url,
            start_pos=start_pos,
            params=params,
        )
        api_response_items.extend(chunk)
        while next_playlist:
            chunk, next_playlist, total = self._get_chunk(
                url=url,
                next_url=next_playlist,
            )
            api_response_items.extend(chunk)
        return api_response_items, total

    def _parse_tracks(self, tracklist: list, last_track_date=None) -> list:
        if not last_track_date:
            last_track_date = datetime(year=1970, month=1, day=1, tzinfo=timezone.utc)
        parsed_tracks = []
        # max_added_at = None
        for track in tracklist:
            if (
                track_added_at := track.get("added_at", None)
            ) and datetime.fromisoformat(track_added_at) > last_track_date:
                track = track.get("track")
                if not track.get("id"):
                    logger.warning("could not determine track id. skipping")
                    continue
                # find out if there is a remixer in the api, if so, add "remixer", this will help, otherwise it will be in the "genre decisions"
                item = Track(
                    id=track.get("id"),
                    added_at=track_added_at,
                    artists=[artist.get("id") for artist in track.get("artists")],
                )
                parsed_tracks.append(item)
        return parsed_tracks

    def get_user_playlists(self, start_pos: int = None) -> list:
        playlist_endpoint = SPOTIFY_PLAYLISTS_ENDPOINT.format(
            user_id=self.user.username
        )
        playlists, total = self.get_items(url=playlist_endpoint, start_pos=start_pos)
        logger.info(f"total user playlists: {total}")
        return self._parse_playlists(playlists)

    def get_playlist_metadata(
        self, playlist_id, start_pos: int = 0, last_track_added_at=None
    ) -> Tuple[list, int]:
        logger.info(
            f"getting playlist tracks, playlist_id={playlist_id}, start_pos={start_pos}"
        )
        tracks_endpoint = SPOTIFY_TRACKS_ENDPOINT.format(
            playlist_id=playlist_id, user_id=self.user.username
        )
        params = {"fields": "items(added_at,track(id,name,artists)),next,total"}
        tracks, total = self.get_items(
            url=tracks_endpoint, start_pos=start_pos, params=params
        )
        logger.info(f"tracks from api, count={len(tracks)}, total={total}")
        tracks_for_update = self._parse_tracks(tracks, last_track_added_at)
        logger.info(f"tracks for update , count={len(tracks_for_update)}")
        return tracks_for_update, total

    def get_liked_tracks(self, start_pos: int = 0) -> Tuple[list, int]:
        tracks, total = self.get_items(
            url=SPOTIFY_SAVED_TRACKS_ENDPOINT, start_pos=start_pos
        )
        return self._parse_tracks(tracks), total

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
