from datetime import UTC, datetime, timedelta

from db.models import SplamPlaylist, SpotifyPlaylist, SpotifyPlaylistModel

spo_model = SpotifyPlaylist()
splam_model = SplamPlaylist()


class SpotifyPlaylistSync:
    def __init__(self) -> None:
        sync_time = datetime.now(UTC) + timedelta(hours=-1)
        # self.spo_playlists = spo_model.get_items_for_sync(sync_time) # get all playlists that has last update older than an hour ago
        self.spo_playlists = [spo_model.all()[0]]
        self.splam_playlists = splam_model.all()

    async def run(self):
        playlist: SpotifyPlaylistModel
        wrapper = playlist.user.spotify
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

            for track in playlist_metadata:
                genre = get_track_genre(track)

            def get_track_genre(self, track):
                pass
                # cached_genre=get_cached_track_genre(track_id)
                # if not cached_genre:
                # get_track_metadata, # mongo, else api
                # get_artist_metadata,# mongo, else api
                # genre = get_track_genre_decision()

            def get_track_metadata(self, track):
                pass

            def get_artist_metadata(self, artist):
                pass


# spo_model = SpotifyPlaylist()
# item = await spo_model.create_item(username="ilya89", spotify_playlist_id="7nLCkXnsTNSjL5hsQJY2Nu")
# item = await spo_model.create_item(username="ilya89", spotify_playlist_id="43tjfVJIJTzDn4GjaUDAtn")

# from db.models import SpotifyPlaylist
# playlists = await SpotifyPlaylist().all()

# pl = playlists[0]
# playlist_metadata, total = pl.user.spotify.get_playlist_metadata(playlist_id=pl.spotify_playlist_id, start_pos=int(pl.track_count*0.9))
