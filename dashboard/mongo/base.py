import logging
from abc import ABC
from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection

from dashboard.core.repository import Repository

logger = logging.getLogger(__name__)

# Shared client for connection pooling
_mongo_client: Optional[MongoClient] = None
_mongo_uri: Optional[str] = None


def _get_shared_client(uri: str, timeout_ms: int = 3000) -> MongoClient:
    """Singleton connection helper."""
    global _mongo_client, _mongo_uri
    if _mongo_client is None or _mongo_uri != uri:
        if _mongo_client:
            _mongo_client.close()
        logger.info("Creating MongoDB client connection")
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        _mongo_uri = uri
    return _mongo_client


class MongoBaseRepository(Repository, ABC):
    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name

    def get_collection(self) -> Collection:
        """Get the pymongo Collection object."""
        client = _get_shared_client(self.uri)
        db = client[self.db_name]
        return db[self.collection_name]
