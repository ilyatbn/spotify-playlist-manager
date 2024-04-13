## v0.21
- look into https://python-musicbrainzngs.readthedocs.io/en/v0.7.1/ for better decisions
- https://www.theaudiodb.com/api_guide.php
- https://github.com/shazamio/ShazamIO
## v0.2
- FE for SPLAM creation
    - FE that shows users playlists in a nice paginated grid with selection. (src_playlists) - DONE
    - FE that allows creating N destination playlists and put 1 or more genres in each one. (dst_playlists)
## v0.11
- Celery[Redis]: take the task bellow and execute it once every N minutes (lets say 5), the update itself will be once a day but we wanna spread it throughout the day so we dont hit any 429 limits from Spotify.
- Implement API decorator for token refreshes (401) and backoff retries for rate limiting (429)
## v0.1
- endpoint that returns users playlists - DONE
- endpoint that allows users to pass a list of source playlist ids and destination genre/s for new playlists.
- Spotify Managed Playlists Model (store metadata for playlists we need to sync to SPLAM playlists)
- SPLAM Playlists Model (destination playlists and selected genres to sync songs into)
- Task that syncs from SMP to SPLAM Playlists. (Manually for now)
