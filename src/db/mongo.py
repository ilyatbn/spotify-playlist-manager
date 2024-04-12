from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from core.app_config import config
from core.helpers import Singleton


class InvalidCollectionSelection(Exception):
    pass


class MongoDBClient:
    def __init__(self) -> None:
        self.client: MongoClient = MongoClient(config.MONGO_URI)
        database: Database = self.client.splam_database
        self.artists: Collection = (
            database.artists
        )  # collection for caching artist metadata. this may need updating once in a while since artists genres may change(?)
        self.track_metadata: Collection = (
            database.track_metadata
        )  # collection for caching tracks metadata
        self.genres: Collection = (
            database.genres
        )  # collection for storing genre/subgenre metadata like decision rules
        self.decisions: Collection = (
            database.decisions
        )  # basically a cache of track_id:genre so we dont have to redo all the checks.

    # add relevant index to speed things up later
    def create_indices(self) -> None:
        self.decisions.create_index([("track_id", ASCENDING)], unique=True)

    def get_track_decision(self, track_id: str) -> str:
        decision = self.find(
            collection="decisions",
            payload={"track_id": track_id},
        )
        return decision

    def set_track_decision(self, decision: dict) -> str:
        decision = self.insert(
            collection="decisions",
            payload=decision,
        )
        return decision

    def get_track_metadata(self, track_id: str) -> str:
        track_meta = self.find(
            collection="track_metadata",
            payload={"track_id": track_id},
        )
        return track_meta

    def set_track_metadata(self, track_metadata: dict) -> str:
        track_meta = self.insert(
            collection="track_metadata",
            payload=track_metadata,
        )
        return track_meta

    def get_artist_metadata(self, artist_id: str) -> str:
        artist_meta = self.find(
            collection="artists",
            payload={"artist_id": artist_id},
        )
        return artist_meta

    def set_artist_metadata(self, artist_metadata: dict) -> str:
        artist_meta = self.find(
            collection="artists",
            payload=artist_metadata,
        )
        return artist_meta

    def find(self, collection: str, query: dict, many: bool = False):
        collection: Collection = getattr(self, collection, None)
        if not collection:
            raise InvalidCollectionSelection("this collection is not available")
        if many:
            pass
        else:
            return collection.find_one(query)

    def insert(self, collection: str, payload: list | dict, many=False) -> dict:
        collection: Collection = getattr(self, collection, None)
        if not collection:
            raise InvalidCollectionSelection("this collection is not available")
        if many:
            response = collection.insert_many(payload)
        else:
            response = collection.insert_one(payload)
        return response