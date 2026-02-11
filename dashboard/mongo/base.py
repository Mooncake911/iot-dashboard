from abc import ABC
from pymongo import MongoClient
from pymongo.collection import Collection

from dashboard.core.repository import Repository


class MongoBaseRepository(Repository, ABC):
    def __init__(self, client: MongoClient, db_name: str, collection_name: str):
        self._client = client
        self._db_name = db_name
        self._collection_name = collection_name

    @property
    def source_name(self) -> str:
        return f"{self._db_name}.{self._collection_name}"

    def get_collection(self) -> Collection:
        return self._client[self._db_name][self._collection_name]
