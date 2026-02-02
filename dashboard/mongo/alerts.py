import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from dashboard.mock import is_mock_mode, MockMongoAlerts

logger = logging.getLogger(__name__)


# Global MongoDB client instance for connection pooling
_mongo_client: Optional[MongoClient] = None
_mongo_uri: Optional[str] = None


def get_mongo_client(mongo_uri: str, timeout_ms: int = 3000) -> MongoClient:
    """
    Get MongoDB client with connection pooling (singleton pattern).
    
    Args:
        mongo_uri: MongoDB connection URI
        timeout_ms: Server selection timeout in milliseconds
        
    Returns:
        MongoClient instance
    """
    # Mock mode handling - no real client needed
    if is_mock_mode():
        return None  # type: ignore

    global _mongo_client, _mongo_uri
    
    # Create new client if URI changed or the client doesn't exist
    if _mongo_client is None or _mongo_uri != mongo_uri:
        if _mongo_client is not None:
            _mongo_client.close()
        
        logger.info(f"Creating MongoDB client connection")
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
        _mongo_uri = mongo_uri
    
    return _mongo_client


def fetch_alerts(
    mongo_uri: str,
    db_name: str,
    collection_name: str,
    limit: int,
    sort_field: str = "receivedAt"
) -> list[dict]:
    """
    Fetch alerts from MongoDB with automatic sort field detection.
    In mock mode, uses MockMongoAlerts.
    
    Args:
        mongo_uri: MongoDB connection URI
        db_name: Database name
        collection_name: Collection name
        limit: Maximum number of alerts to fetch
        sort_field: Field to sort by (default: receivedAt)
        
    Returns:
        List of alert documents
        
    Raises:
        ConnectionFailure: If unable to connect to MongoDB
        ServerSelectionTimeoutError: If MongoDB server is unreachable
    """
    if is_mock_mode():
        logger.info(f"[MOCK] Fetching {limit} alerts from {collection_name}")
        return MockMongoAlerts.fetch_alerts(mongo_uri, db_name, collection_name, limit)

    try:
        client = get_mongo_client(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Auto-detect sort field if a collection has documents
        detected_sort_field = sort_field
        if collection.estimated_document_count() > 0:
            sample = collection.find_one()
            if sample is not None:
                # Prefer receivedAt, fallback to alertTimestamp
                if "receivedAt" in sample:
                    detected_sort_field = "receivedAt"
                elif "alertTimestamp" in sample:
                    detected_sort_field = "alertTimestamp"
                else:
                    # Use _id as the last resort (always present)
                    detected_sort_field = "_id"
        
        logger.debug(f"Fetching {limit} alerts from {collection_name}, sorted by {detected_sort_field}")
        
        # Fetch and sort alerts (descending order - newest first)
        cursor = collection.find({}, limit=limit).sort(detected_sort_field, -1)
        alerts = list(cursor)
        
        # Convert ObjectId to string for JSON serialization
        for alert in alerts:
            if "_id" in alert:
                alert["_id"] = str(alert["_id"])
        
        logger.info(f"Fetched {len(alerts)} alerts from {collection_name}")
        return alerts
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise


def close_mongo_client():
    """Close the global MongoDB client connection."""
    if is_mock_mode():
        return MockMongoAlerts.close_mongo_client()

    global _mongo_client, _mongo_uri
    
    if _mongo_client is not None:
        logger.info("Closing MongoDB client connection")
        _mongo_client.close()
        _mongo_client = None
        _mongo_uri = None
    return None
