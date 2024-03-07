v0.2
- FE for SPLAM creation
    - FE that shows users playlists in a nice paginated grid with selection. (src_playlists)
    - FE that allows creating N destination playlists and put 1 or more genres in each one. (dst_playlists)
v0.12
- Lots and lots of tweaking for subgenres. (need to figure this out since this is gonna be a dealbreaker otherwise). probably gonna have to store lots of maps based on artists, bpm, track name regexes and such for Remixes or something. idk.. gonna be annoying
v0.11
- Celery[Redis]! take the task bellow and execute it once every N minutes (lets say 5), the update itself will be once a day but we wanna spread it throughout the day so we dont hit any 429 limits from Spotify. will probably use the same Redis for caching users playlists.
v0.1
- endpoint that returns users playlists.
- endpoint that allows users to pass a list of source playlist ids and destination genre/s for new playlists.
- Spotify Managed Playlists Model (store metadata for playlists we need to sync to SPLAM playlists)
- SPLAM Playlists Model (destination playlists and selected genres to sync songs into)
- Task that syncs from SMP to SPLAM Playlists. (Manually for now)
