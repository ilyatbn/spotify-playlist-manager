from datetime import UTC, datetime, timedelta

from core.logger import logger
from core.spotify.playlists import UserPlaylistHandler
from core.spotify.schemas import Artist, Track
from db.models import SplamPlaylist, SpotifyPlaylist, SpotifyPlaylistModel
from db.mongo import MongoDBClient
from main import celery_app as app

spo_model = SpotifyPlaylist()
splam_model = SplamPlaylist()
metadata_cache = MongoDBClient()


class SpotifyPlaylistSync:
    def __init__(self) -> None:
        sync_time = datetime.now(UTC) + timedelta(hours=-1)
        # self.spo_playlists = spo_model.get_items_for_sync(sync_time) # get all playlists that has last update older than an hour ago
        # TODO: add option to run by user or playlist.
        self.spo_playlists = None
        self.splam_playlists = None

    @classmethod
    async def init(cls, playlist=None, user=None):
        instance = cls()
        instance.spo_playlists = await spo_model.all()
        instance.splam_playlists = await splam_model.all()
        return instance

    async def run(self):
        playlist: SpotifyPlaylistModel
        for playlist in self.spo_playlists:
            wrapper: UserPlaylistHandler = playlist.user.spotify
            # get playlist from spotify, check if playlist.snapshot_id matches. if not, no need to resync, just update the last sync time

            playlist_metadata, total = wrapper.get_playlist_metadata(
                playlist_id=playlist.spotify_playlist_id,
                start_pos=int(playlist.track_count * 0.9),
                last_track_added_at=playlist.last_track_added_at,
            )
            playlist.track_count = total
            playlist.last_sync_time = str(datetime.now(UTC))
            # await spo_model.save(playlist)

            if playlist_metadata:
                playlist.last_track_added_at = max(
                    datetime.fromisoformat(track.added_at)
                    for track in playlist_metadata
                )
                # await spo_model.save(playlist)

            # TODO: support bulks. both mongo and spotify supoprt them so it should be fine..
            for track in playlist_metadata:
                genre = self.get_track_genre(track, wrapper)
                # find splam playlists for user with genre selected.
                # create playlist if it doesnt exist (no playlist id in result)
                # add track to playlist

    def get_track_genre(self, track: Track, wrapper: UserPlaylistHandler):
        cached_genre = metadata_cache.get_track_decision(track.id)
        if cached_genre:
            logger.info(
                f"found cached genre for track {track.name}, genre={cached_genre}"
            )
            return cached_genre

        track_metadata = self.get_track_metadata(track, wrapper)
        artists_metadata = self.get_artist_metadata(track.artists, wrapper)
        return self.run_decisions(track, track_metadata, artists_metadata)

    def get_track_metadata(self, track: Track, wrapper: UserPlaylistHandler):
        cached_object = metadata_cache.get_track_metadata(track.id)
        if cached_object:
            logger.debug(f"found cached track meta in mongo, track={track.name}")
            return cached_object
        else:
            logger.debug(f"getting track info from api, track={track.name}")
            track_meta = wrapper.get_track_metadata(track.id)
            # parse the response into something we wanna work with.
            metadata_cache.set_track_metadata(track_meta)
            return track_meta

    def get_artist_metadata(self, artists: list, wrapper: UserPlaylistHandler):
        metadata = list()
        for artist_id in artists:
            cached_object = metadata_cache.get_artist_metadata(artist_id)
            if cached_object:
                logger.debug(
                    f"found cached artist meta in mongo, artist={cached_object.get('name')}"
                )
                metadata.append(cached_object)
            else:
                logger.debug(f"getting track info from api, artist_id={artist_id}")
                artist_meta = Artist(
                    **wrapper.get_artist_metadata(artist_id)
                ).model_dump()
                metadata_cache.set_artist_metadata(artist_meta)
                metadata.append(artist_meta)
        return metadata

    def reduce_genres(self, track_metadata: dict, artist_genres: set) -> set:
        # use this to create genre items that can do.. stuff..
        # metadata_cache.set_genre_metadata({"id":"hardstyle", "alternate_names":['rawstyle', 'classic hardstyle', 'euphoric hardstyle', 'xtra raw']})

        remapped_genres = set()
        for genre in list(artist_genres):
            # this will find a genre by its id or its alternate_names. this way we can merge multiple genres into one.
            item, *_ = metadata_cache.get_genre_metadata(genre)
            if item:
                remapped_genres.update({item.get("id")})
            else:
                remapped_genres.update({genre})
        # do something about bpm ranges. we need to add many genres here and set their bpm ranges. this will be annoying as hell to do.

        return remapped_genres

    def run_decisions(self, track: Track, track_metadata: dict, artists_metadata: list):
        # if multiple artists, check if remix, if remix figure out who the remixer is(metadata?), if not remix check if all artists have the same genre, if not check track bpm..
        artist_genres = set()
        is_remix = False
        parsed_artists = [artist for artist in artists_metadata if artist.get("genres")]
        for artist in parsed_artists:
            logger.debug(
                f"artist '{artist.get('name')}' genres: {artist.get('genres')}"
            )
            artist_genres.update(artist.get("genres"))

        artist_genres = self.reduce_genres(track_metadata, artist_genres)

        if len(artist_genres) > 1:
            logger.info(
                f"track '{track.name}', possible genres:{artist_genres}, energy:{track_metadata['energy']}, speechiness:{track_metadata['speechiness']}, valence:{track_metadata['valence']}, bpm:{track_metadata['tempo']}"
            )
            pass
        if not artist_genres:
            logger.info(f"something bad happened with {track}")
        return artist_genres


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
# artist_id=track.artists[0]
# artist_meta = self.get_artist_metadata(track.artists[0])


@app.task(bind=True, name="start_sync")
def start_sync(self):
    manager = SpotifyPlaylistSync()
    manager.run()
