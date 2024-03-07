import requests

from db.models import User

users = User()


# genres = requests.get(url='https://api.spotify.com/v1/recommendations/available-genre-seeds', headers={'Authorization': f'Bearer {i.access_token}'}).json()
# map genres to artists, tracks, bpm. will need this probably to recongnize remixes and such
# genres model, so you can select which genres you want to split the source playlists into.


example_playlist = {
    "collaborative": False,
    "description": "Soft, Hard, Slow, Fast, Soothing, Banging, Uplifting, Dark, Different. Mindbending.",
    "external_urls": {
        "spotify": "https://open.spotify.com/playlist/iwenfinwedwdwed_fake"
    },
    "href": "https://api.spotify.com/v1/playlists/iwenfinwedwdwed_fake",
    "id": "iwenfinwedwdwed_fake",
    "images": [
        {
            "height": None,
            "url": "https://image-cdn-ak.spotifycdn.com/image/111",
            "width": None,
        }
    ],
    "name": "idk,stuff",
    "owner": {
        "display_name": "fakeuser",
        "external_urls": {"spotify": "https://open.spotify.com/user/fakeuser"},
        "href": "https://api.spotify.com/v1/users/fakeuser",
        "id": "fakeuser",
        "type": "user",
        "uri": "spotify:user:fakeuser",
    },
    "primary_color": None,
    "public": True,
    "snapshot_id": "123",
    "tracks": {
        "href": "https://api.spotify.com/v1/playlists/iwenfinwedwdwed_fake/tracks",
        "total": 3333,
    },
    "type": "playlist",
    "uri": "spotify:playlist:iwenfinwedwdwed_fake",
}

from pydantic import BaseModel


class SpotifyPlaylistRequestException(Exception):
    pass


class SpotifyPlaylist(BaseModel):
    username: str
    playlist_id: str
    name: str
    snapshot_id: str  # used to trigger updates


def _parse_playlists(user_playlists: list, user):
    parsed_playlists = []
    for playlist in user_playlists:
        if playlist.get("owner").get("id") == user.username:
            # skip crabhands (toggle in user settings or something since these playlists are super huge..idk..),
            playlist_item = SpotifyPlaylist(
                username=user.username,
                playlist_id=playlist.get("id"),
                name=playlist.get("name"),
                snapshot_id=playlist.get("snapshot_id"),
            )
            parsed_playlists.append(playlist_item)
    return parsed_playlists


def _get_playlist_chunk(user, next: str = None, start_pos: int = 0):
    if not next:
        chunk = requests.get(
            url=f"https://api.spotify.com/v1/users/{user.username}/playlists",
            params={"offset": start_pos, "limit": 50},
            headers={"Authorization": f"Bearer {user.access_token}"},
        )
    else:
        chunk = requests.get(
            url=next, headers={"Authorization": f"Bearer {user.access_token}"}
        )

    if not chunk.ok:
        # wrap all requests in a decorator that refreshes the creds and retries
        if chunk.status_code == "401":
            print(f"refreshing access token for {user.id}")
            user.auth.refresh_access_token()
            # TODO: do i even need to store the access token? its daily anyway..
            users.save(user)
            return _get_playlist_chunk(user=user, next=next)
        else:
            raise SpotifyPlaylistRequestException(f"{chunk.status_code, chunk.json()}")

    chunk_dict = chunk.json()
    return chunk_dict["items"], chunk_dict["next"]


def get_user_playlists(user: User.model, start_pos: int = None):
    user_playlists = []

    chunk, next_playlist = _get_playlist_chunk(user, start_pos=start_pos)
    user_playlists.extend(chunk)
    while next_playlist:
        chunk, next_playlist = _get_playlist_chunk(user, next_playlist)
        user_playlists.extend(chunk)
    return _parse_playlists(user_playlists, user)


# in /plm. paginate with starting_pos passed from FE?
async def user_playlists():
    all_users = await users.all()
    user = all_users[0]
    # TODO: cache these dicts somewhere(redis?) for where the user selects them we already have all the relevant info. we dont need to store everything in the db cuze its dumb..
    return get_user_playlists(user)
