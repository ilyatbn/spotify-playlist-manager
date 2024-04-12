from datetime import UTC, datetime, timedelta

from core.spotify.playlists import UserPlaylistHandler
from core.spotify.schemas import Track
from db.models import SplamPlaylist, SpotifyPlaylist, SpotifyPlaylistModel
from db.mongo import MongoDBClient
from main import celery_app as app

spo_model = SpotifyPlaylist()
splam_model = SplamPlaylist()
metadata_cache = MongoDBClient()


class SpotifyPlaylistSync:
    def __init__(self, playlist=None, user=None) -> None:
        sync_time = datetime.now(UTC) + timedelta(hours=-1)
        # self.spo_playlists = spo_model.get_items_for_sync(sync_time) # get all playlists that has last update older than an hour ago
        # TODO: add option to run by user or playlist.
        self.spo_playlists = [spo_model.all()[0]]
        self.splam_playlists = splam_model.all()

    async def run(self):
        playlist: SpotifyPlaylistModel
        wrapper: UserPlaylistHandler = playlist.user.spotify
        for playlist in self.spo_playlists:
            # get playlist from spotify, check if playlist.snapshot_id matches. if not, no need to resync, just update the last sync time

            playlist_metadata, total = wrapper.get_playlist_metadata(
                playlist_id=playlist.spotify_playlist_id,
                start_pos=int(playlist_metadata.track_count * 0.9),
                last_track_date=playlist.last_track_added_at,
            )
            playlist.track_count = total
            playlist.last_sync_time = str(datetime.utcnow())
            await spo_model.save(playlist)

            if playlist_metadata:
                playlist.last_track_added_at = max(
                    datetime.fromisoformat(track.added_at)
                    for track in playlist_metadata
                )
                await spo_model.save(playlist)

            # TODO: support bulks. both mongo and spotify supoprt them so it should be fine..
            for track in playlist_metadata:
                genre = self.get_track_genre(track, wrapper)
                # find splam playlists for user with genre selected.
                # create playlist if it doesnt exist (no playlist id in result)
                # add track to playlist

    def get_track_genre(self, track: Track, wrapper: UserPlaylistHandler):
        cached_genre = metadata_cache.get_track_decision(track.id)
        if cached_genre:
            return cached_genre

        track_metadata = self.get_track_metadata(track.id, wrapper)
        artists_metadata = self.get_artist_metadata(track.artists, wrapper)
        return self.run_decisions(track_metadata, artists_metadata)

    def get_track_metadata(self, track: Track, wrapper: UserPlaylistHandler):
        cached_object = metadata_cache.get_track_metadata(track.id)
        if cached_object:
            return cached_object
        else:
            track_meta = wrapper.get_track_metadata(track.id)
            # parse the response into something we wanna work with.
            metadata_cache.set_track_metadata(track_meta)
            return track_meta

    def get_artist_metadata(self, artists: list, wrapper: UserPlaylistHandler):
        metadata = list()
        for artist_id in artists:
            cached_object = metadata_cache.get_artist_metadata(artist_id)
            if cached_object:
                metadata.append(cached_object)
            else:
                artist_meta = wrapper.get_artist_metadata(artist_id)
                # parse the response into something we wanna work with.
                metadata_cache.set_track_metadata(artist_meta)
                metadata.append(cached_object)
        return metadata

    def run_decisions(self, track_metadata: dict, artists_metadata: list):
        genre = None
        # if single artist, check genre, chech mongo genre to see if something is there(?), check track bpm, check if track is a remix.
        # if multiple artists, check if remix, if remix figure out who the remixer is(metadata?), if not remix check if all artists have the same genre, if not check track bpm..
        # after everyting is done, add to mongo track_decisions cache.
        return genre


# spo_model = SpotifyPlaylist()
# item = await spo_model.create_item(username="ilya89", spotify_playlist_id="7nLCkXnsTNSjL5hsQJY2Nu")
# item = await spo_model.create_item(username="ilya89", spotify_playlist_id="43tjfVJIJTzDn4GjaUDAtn")

# from db.models import SpotifyPlaylist
# playlists = await SpotifyPlaylist().all()
# pl = playlists[0]
# playlist_metadata, total = pl.user.spotify.get_playlist_metadata(playlist_id=pl.spotify_playlist_id, start_pos=int(pl.track_count*0.9))
# track = playlist_metadata[0]
# self=wrapper = pl.user.spotify
# track_meta = self.get_track_metadata(track.id)
# artist_meta = self.get_artist_metadata(track.artists[0])


@app.task(bind=True, name="start_sync")
def start_sync(self):
    manager = SpotifyPlaylistSync()
    manager.run()
