import time
from datetime import datetime

from core.logger import logger
from core.spotify.playlists import UserPlaylistHandler
from core.spotify.schemas import Track
from db.models import SplamPlaylist, SpotifyPlaylist, SpotifyPlaylistModel
from db.mongo import MongoDBClient
from main import celery_app as app

spo_model = SpotifyPlaylist()
splam_model = SplamPlaylist()
metadata_cache: MongoDBClient = MongoDBClient()


class SpotifyPlaylistSync:
    def __init__(self) -> None:
        self.spo_playlists = None
        self.splam_playlists = None

    @classmethod
    async def init(cls, playlist=None, user=None):
        # TODO: add option to run by user or playlist.
        instance = cls()
        # filter spo playlists where last_sync_time is less than min_sync_time. this will set an interval.
        # min_sync_time:float = time.time() - 7200
        # instance.spo_playlists = await spo_model.filter({"last_sync_time__ge": min_sync_time})
        instance.spo_playlists = await spo_model.all()
        instance.splam_playlists = await splam_model.all()
        return instance

    async def run(self):
        playlist: SpotifyPlaylistModel
        for playlist in self.spo_playlists:
            wrapper: UserPlaylistHandler = playlist.user.spotify
            # check snapshot ids. if they match, we dont need to do anything.
            playlist.last_sync_time = time.time()
            playlist_metadata = wrapper.get_playlist_metadata(
                playlist_id=pl.spotify_playlist_id, params={"fields": "id,snapshot_id"}
            )
            if playlist_metadata.get("snapshot_id") == playlist.snapshot_id:
                logger.info(f"playlist {playlist.id} unchanged.")
                # await spo_model.save(playlist)
                return

            playlist_tracks, total = wrapper.get_playlist_tracks(
                playlist_id=playlist.spotify_playlist_id,
                start_pos=int(playlist.track_count * 0.9),
                last_track_added_at=playlist.last_track_added_at,
            )
            playlist.track_count = total
            # await spo_model.save(playlist)

            if playlist_tracks:
                playlist.last_track_added_at = max(
                    datetime.fromisoformat(track.added_at) for track in playlist_tracks
                )
                # await spo_model.save(playlist)

            # TODO: support bulks. both mongo and spotify supoprt them so it should be fine..
            for track in playlist_tracks:
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
        album_metadata = self.get_album_metadata(track, wrapper)
        artists_metadata = self.get_artist_metadata(track.artists, wrapper)
        return self.run_decisions(
            track, track_metadata, artists_metadata, album_metadata
        )

    def get_track_metadata(self, track: Track, wrapper: UserPlaylistHandler):
        cached_object = metadata_cache.get_track_metadata(track.id)
        if cached_object:
            logger.debug(f"found cached track meta in mongo, track={track.name}")
            return cached_object
        else:
            logger.debug(f"getting track meta from api, track={track.name}")
            track_meta = wrapper.get_track_metadata(track.id)
            # parse the response into something we wanna work with.
            metadata_cache.set_track_metadata(track_meta)
            return track_meta

    def get_album_metadata(self, track: Track, wrapper: UserPlaylistHandler):
        cached_object = metadata_cache.get_album_metadata(track.album_id)
        if cached_object:
            logger.debug(f"found cached album meta in mongo, track={track.name}")
            return cached_object
        else:
            logger.debug(f"getting album meta from api, track={track.name}")
            album_meta = wrapper.get_album_metadata(track.album_id)
            # parse the response into something we wanna work with.
            metadata_cache.set_album_metadata(album_meta)
            return album_meta

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
                logger.debug(f"getting track meta from api, artist_id={artist_id}")
                artist_meta = wrapper.get_artist_metadata(artist_id)
                metadata_cache.set_artist_metadata(artist_meta)
                metadata.append(artist_meta)
        return metadata

    def remap_genres(self, artist_genres: set) -> set:
        # use this to create genre items that can do.. stuff..
        # metadata_cache.set_genre_metadata({"id":"hardstyle", "alternate_names":['rawstyle', 'classic hardstyle', 'euphoric hardstyle', 'xtra raw']})
        remapped_genres = set()
        for genre in artist_genres:
            # this will find a genre by its id or its alternate_names. this way we can merge multiple genres into one.
            item, *_ = metadata_cache.get_genre_metadata(genre)
            if item:
                remapped_genres.update({item.get("id")})
            else:
                remapped_genres.update({genre})
        return remapped_genres

    def run_decisions(
        self,
        track: Track,
        track_metadata: dict,
        artists_metadata: list,
        album_metadata: dict,
    ):
        artist_names = ",".join([artist["name"] for artist in artists_metadata])
        full_track_name = f"{track.id}: {artist_names} - {track.name}"
        artists_with_genres = [
            artist for artist in artists_metadata if artist.get("genres", None)
        ]

        # album genres are top priority.
        album_genres = set()
        if album_genres := album_metadata.get("genres"):
            logger.info(f"album genres:{album_genres}")
            album_genres = self.remap_genres(set(album_genres))
            logger.info(f"album remapped genres:{album_genres}")
        else:
            logger.info(
                f"no album genres available for track:{full_track_name}, label:{album_metadata.get('label')}"
            )

        # TODO: find genre by label metadata (will only work when you have enough data to work with).
        ## labels are usually focused on specific genres so it might actually be a great source.
        ## get track album's label, cross-reference all other tracks by this label and see what genres they usually release.
        label_genres = set()

        # multiple artists may have many genres which are unrelated to actual track so this takes the least priority for now, but has the most information.
        artist_genres = set()
        if not artists_with_genres:
            logger.warning(f"no artist genres available for track {full_track_name}")
        else:
            for artist in artists_with_genres:
                logger.debug(
                    f"artist '{artist.get('name')}' genres: {artist.get('genres')}"
                )
                artist_genres.update(artist.get("genres"))
            artist_genres = self.remap_genres(artist_genres)
            logger.debug(f"artists remapped genres:{artist_genres}")

        # current priority IMO. will probably add more logic to this later.
        final_genres = album_genres or label_genres or artist_genres

        # okay now this might be fantastic! (and also way too huge to store on my free AF server, but we'll see)
        # https://discogs-data-dumps.s3.us-west-2.amazonaws.com/index.html
        # https://www.discogs.com/developers

        if len(final_genres) > 1:
            # try to reduce further by track metadata. tempo is easiest, rest is kinda hard without doing some ML work which is against Spotify TOS..
            logger.info(
                f"track '{track.name}', possible genres:{artist_genres}, energy:{track_metadata['energy']}, speechiness:{track_metadata['speechiness']}, valence:{track_metadata['valence']}, bpm:{track_metadata['tempo']}"
            )

        if not final_genres:
            # getting here is bad. this means we need more information sources for the track :/
            # at this point we're desperate.. confidence level is very low so we're gonna do some drastic shit..

            # try finding genres by getting "similar artists"
            # https://developer.spotify.com/documentation/web-api/reference/get-an-artists-related-artists

            # look for track by artist and name in beatport.
            # find track release (?)
            # https://api.beatport.com/v4/????
            # get track info
            # https://api.beatport.com/v4/catalog/releases/2429912/tracks/?page=1&per_page=100
            # should result with genre if found. interesting.

            # look for release at Discogs.
            # https://www.discogs.com/service/header/public/api/autocomplete?search=Beatcaster+no+waitin&search_type=RELEASE&currency=USD
            # should respond with url to release if found, then that url will return some crap that has *,"genres":["Electronic"],"styles":["Hardstyle"]* in it. might help.

            logger.info(f"something bad happened with {full_track_name}")
        return artist_genres


# spo_model = SpotifyPlaylist()
# item = await spo_model.create_item(username="ilya89", spotify_playlist_id="7nLCkXnsTNSjL5hsQJY2Nu", snapshot_id="MzQzLGFmZDFjM2FjYjM5ZDc1ZDk0Mzc2OTFlMDQxZmRiMjkxYjhmNDIyMWI=", last_sync_time=time.time()-7500)
# item = await spo_model.create_item(username="ilya89", spotify_playlist_id="43tjfVJIJTzDn4GjaUDAtn", snapshot_id="MjkwLGE4YmU1NTQwZGM4ODcyOWI3Njc0ZjdmNmNkMzE4NWM2YWYwNjFmODM=", last_sync_time=time.time()-7500)
async def b():
    from db.models import SpotifyPlaylist

    playlists = await SpotifyPlaylist().all()
    playlist = pl = playlists[0]
    wrapper = pl.user.spotify
    playlist_metadata = wrapper.get_playlist_metadata(
        playlist_id=pl.spotify_playlist_id, params={"fields": "id,snapshot_id"}
    )
    playlist_tracks, total = wrapper.get_playlist_tracks(
        playlist_id=pl.spotify_playlist_id, start_pos=int(pl.track_count * 0.9)
    )
    from tasks.sync_tasks.playlists_sync import SpotifyPlaylistSync

    self = SpotifyPlaylistSync()
    for track in playlist_tracks:
        genre = self.get_track_genre(track, wrapper)
    track = playlist_tracks[0]
    # track_meta = self.get_track_metadata(track.id)
    # artist_id=track.artists[0]
    artists_metadata = self.get_artist_metadata(track.artists, wrapper)
    album_meta = self.get_album_metadata(track, wrapper)


@app.task(bind=True, name="start_sync")
def start_sync(self):
    manager = SpotifyPlaylistSync()
    manager.run()
