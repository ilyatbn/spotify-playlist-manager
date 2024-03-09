SPOTIFY_ACCOUNTS_BASE_URL = "https://accounts.spotify.com"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
SERVICE_BASE_URL = ""
# Auth endpoints
SPOTIFY_AUTH_ENDPOINT = f"{SPOTIFY_ACCOUNTS_BASE_URL}/authorize?"
SPOTIFY_AUTH_TOKEN_ENDPOINT = f"{SPOTIFY_ACCOUNTS_BASE_URL}/api/token"
SPOTIFY_AUTH_CALLBACK_ENDPOINT = f"{SERVICE_BASE_URL}/auth_callback"
SPOTIFY_PLAYLIST_ENDPOINT = SPOTIFY_API_BASE_URL + "/v1/users/{user_id}/playlists"
# API Endpoints
SPOTIFY_USER_ENDPOINT = f"{SPOTIFY_API_BASE_URL}/v1/me"

SPOTIFY_AUTH_SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-modify",
    "user-library-read",
    "user-read-email",
]

#### creds..
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
