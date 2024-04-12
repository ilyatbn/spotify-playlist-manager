
## SPLAM - Spotify Playlist Manager
Watch for changes in playlists and generate new playlists based on genres and music metadata.
This service is meant to be an alternative to Spotify's "Genre Filters", which are unavailable in many countries, as well as on non mobile versions, or playlists other than "Liked Songs".

More features might be implemented in the future.

\* Note: Electronic music will be a focus here, with special features that should help with the filtering, since multi-artist, multi genre collaborations and Remixes are more prominent here, as well as many subgenres. Spotify's API doesn't map tracks to genres, so this is a difficult task and will require lots of manual fine-tuning.

## Features:
- Login with Spotify.
- Generate new genre based playlists from a list of source playlists.
- Multi-Genre playlists. User can configure which genres go into which playlist or playlists.


### Prerequisites and Installation
1. Install docker and docker-compose (v2.x)

    See https://docs.docker.com/engine/install/ubuntu/

2. Run make to build, then enter the shell to create the database and tables.
    ```
    make
    make start
    make shell
    ```

3. Inside the IPython shell, run the following to initialize the database and templates:
    ```
    from db.helpers import first_run
    await first_run()
    ```


## Stack
- FastAPI
- SQLAlchemy
- Celery
- PostgreSQL
- Redis
- MongoDB
